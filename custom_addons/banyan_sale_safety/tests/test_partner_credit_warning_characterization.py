# Part of Odoo. See LICENSE file for full copyright and licensing details.
"""Characterization tests for ``sale.order._compute_partner_credit_warning``.

These are NOT unit tests. They capture what the method currently returns,
byte-for-byte, and do not assert what it *should* return. Every expectation is
a ``assertEqual`` against the full string (no ``assertIn`` / ``assertRegex``).

Target: ``addons/sale/models/sale_order.py:771``.
Language is locked to ``en_US`` through a new environment (never by assigning
``env.context``, which would mutate a shared, cached environment).

Notes on observed behaviour (recorded, not fixed):
* ``order.with_company(order.company_id)`` on the first line of the compute is
  a no-op (result discarded).
* formatLang puts a NO-BREAK SPACE (``\\xa0``) between the currency symbol and
  the amount; it is written as an explicit escape in the literals below.
* Branches A/B (state 'sale' / 'cancel') short-circuit in the sale.order
  compute and never reach ``_build_credit_warning_message``.
"""
from odoo.fields import Command
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install', 'characterization')
class TestPartnerCreditWarningCharacterization(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, lang='en_US'))
        cls.company = cls.env.company
        cls.company.account_use_credit_limit = True
        # Pin the company currency so symbol / position / decimals are stable.
        usd = cls.env.ref('base.USD')
        usd.active = True
        assert cls.company.currency_id == usd, "fixture requires USD company currency"

        cls.product = cls.env['product.product'].create({
            'name': 'Characterization Service',
            'type': 'service',
            'list_price': 100.0,
            'taxes_id': [Command.clear()],
        })
        cls.pricelist_usd = cls.env['product.pricelist'].create({
            'name': 'Characterization USD',
            'currency_id': usd.id,
        })
        cls.partner = cls._make_partner('Charact Partner', credit_limit=1000.0)

    @classmethod
    def _make_partner(cls, name, credit_limit=0.0, **vals):
        return cls.env['res.partner'].create(dict(
            name=name, credit_limit=credit_limit, **vals))

    def _make_order(self, partner, price, pricelist=None, **vals):
        return self.env['sale.order'].create(dict(
            partner_id=partner.id,
            company_id=self.company.id,
            pricelist_id=(pricelist or self.pricelist_usd).id,
            order_line=[Command.create({
                'product_id': self.product.id,
                'product_uom_qty': 1,
                'price_unit': price,
                'tax_id': False,
            })],
            **vals))

    def _post_invoice(self, partner, price):
        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': partner.id,
            'invoice_line_ids': [Command.create({
                'name': 'characterization line',
                'quantity': 1,
                'price_unit': price,
                'tax_ids': False,
            })],
        })
        invoice.action_post()
        partner.invalidate_recordset(['credit', 'credit_to_invoice'])
        return invoice

    def test_harness_lang_locked(self):
        """Harness smoke test: proves tag selection and the en_US lock."""
        self.assertEqual(self.env.context.get('lang'), 'en_US')

    def test_branch_a_state_sale_returns_empty(self):
        order = self._make_order(self.partner, 1500.0)
        order.action_confirm()
        self.assertEqual(order.state, 'sale')
        self.assertEqual(order.partner_credit_warning, '')

    def test_branch_b_state_cancel_returns_empty(self):
        order = self._make_order(self.partner, 1500.0)
        order._action_cancel()
        self.assertEqual(order.state, 'cancel')
        self.assertEqual(order.partner_credit_warning, '')

    def test_branch_c_company_flag_off_over_limit(self):
        self.company.account_use_credit_limit = False
        order = self._make_order(self.partner, 1500.0)
        self.assertEqual(order.partner_credit_warning, '')

    def test_branch_d_flag_on_no_credit_limit(self):
        partner = self._make_partner('Charact No Limit', credit_limit=0.0)
        order = self._make_order(partner, 1500.0)
        self.assertEqual(order.partner_credit_warning, '')

    def test_branch_e_flag_on_below_limit(self):
        order = self._make_order(self.partner, 999.0)
        self.assertEqual(order.partner_credit_warning, '')

    def test_branch_f_boundary_total_equals_limit(self):
        order = self._make_order(self.partner, 1000.0)
        self.assertEqual(order.partner_credit_warning, '')

    def test_branch_g_over_limit_only_this_draft_order(self):
        order = self._make_order(self.partner, 1500.0)
        self.assertEqual(order.state, 'draft')
        self.assertEqual(order.partner_credit_warning, (
            'Charact Partner has reached its credit limit of: $\xa01,000.00\n'
            'Total amount due (including this document): $\xa01,500.00'
        ))

    def test_branch_h_other_confirmed_so_plus_this_document(self):
        partner = self._make_partner('Charact H', credit_limit=1000.0)
        other = self._make_order(partner, 800.0)
        other.action_confirm()
        partner.invalidate_recordset(['credit', 'credit_to_invoice'])
        self.assertEqual(partner.credit_to_invoice, 800.0)
        order = self._make_order(partner, 500.0)
        self.assertEqual(order.partner_credit_warning, (
            'Charact H has reached its credit limit of: $\xa01,000.00\n'
            'Total amount due (including sales orders and this document): $\xa01,300.00'
        ))

    def test_branch_i_credit_to_invoice_only_current_amount_zero(self):
        partner = self._make_partner('Charact I', credit_limit=1000.0)
        other = self._make_order(partner, 1500.0)
        other.action_confirm()
        partner.invalidate_recordset(['credit', 'credit_to_invoice'])
        order = self._make_order(partner, 0.0)
        self.assertEqual(order.amount_total, 0.0)
        self.assertEqual(order.partner_credit_warning, (
            'Charact I has reached its credit limit of: $\xa01,000.00\n'
            'Total amount due (including sales orders): $\xa01,500.00'
        ))

    def test_branch_j_posted_invoice_only_current_amount_zero(self):
        partner = self._make_partner('Charact J', credit_limit=1000.0)
        self._post_invoice(partner, 1500.0)
        self.assertEqual(partner.credit, 1500.0)
        self.assertEqual(partner.credit_to_invoice, 0.0)
        order = self._make_order(partner, 0.0)
        self.assertEqual(order.partner_credit_warning, (
            'Charact J has reached its credit limit of: $\xa01,000.00\n'
            'Total amount due: $\xa01,500.00'
        ))

    def test_branch_k_child_contact_uses_commercial_partner(self):
        parent = self._make_partner(
            'Charact Parent Co', credit_limit=1000.0, is_company=True)
        child = self._make_partner(
            'Charact Child Contact', credit_limit=0.0,
            parent_id=parent.id, type='contact')
        # Captured: the parent's name AND limit are used (child limit 0 ignored).
        order = self._make_order(child, 1500.0)
        self.assertEqual(order.partner_credit_warning, (
            'Charact Parent Co has reached its credit limit of: $\xa01,000.00\n'
            'Total amount due (including this document): $\xa01,500.00'
        ))

    def test_branch_l_state_sent_over_limit(self):
        order = self._make_order(self.partner, 1500.0)
        order.action_quotation_sent()
        self.assertEqual(order.state, 'sent')
        self.assertEqual(order.partner_credit_warning, (
            'Charact Partner has reached its credit limit of: $\xa01,000.00\n'
            'Total amount due (including this document): $\xa01,500.00'
        ))

    def test_branch_m_foreign_currency_non_unit_rate(self):
        currency = self.env['res.currency'].create({
            'name': 'TB', 'symbol': 'TB', 'rounding': 0.01})
        self.env['res.currency.rate'].create({
            'name': '2020-01-01',
            'rate': 2.0,
            'currency_id': currency.id,
            'company_id': self.company.id,
        })
        pricelist = self.env['product.pricelist'].create({
            'name': 'Characterization TB',
            'currency_id': currency.id,
        })
        order = self._make_order(self.partner, 2400.0, pricelist=pricelist)
        self.assertEqual(order.amount_total, 2400.0)
        self.assertEqual(order.currency_rate, 2.0)
        self.assertEqual(order.partner_credit_warning, (
            'Charact Partner has reached its credit limit of: $\xa01,000.00\n'
            'Total amount due (including this document): $\xa01,200.00'
        ))
