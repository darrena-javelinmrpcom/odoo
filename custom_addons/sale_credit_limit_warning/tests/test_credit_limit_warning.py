# Part of Odoo. See LICENSE file for full copyright and licensing details.

from lxml import etree

from odoo.fields import Command
from odoo.addons.sale.tests.common import TestSaleCommon
from odoo.tests import Form, tagged


@tagged('post_install', '-at_install')
class TestCreditLimitWarning(TestSaleCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.company.account_use_credit_limit = True
        cls.partner_a.credit_limit = 1000.0

        buck_currency = cls.env['res.currency'].create({'name': 'TB', 'symbol': 'TB'})
        cls.env['res.currency.rate'].create({
            'name': '2023-01-01',
            'rate': 2.0,
            'currency_id': buck_currency.id,
            'company_id': cls.env.company.id,
        })
        cls.buck_pricelist = cls.env['product.pricelist'].create({
            'name': 'Test Buck Pricelist',
            'currency_id': buck_currency.id,
        })
        cls.company_data_2 = cls.setup_other_company()
        cls.sales_user = cls.company_data['default_user_salesman']
        cls.sales_user.write({'login': 'notaccountman', 'email': 'bad@accounting.com'})

    # -- helpers ----------------------------------------------------------------

    def _line(self, amount):
        return Command.create({
            'product_id': self.company_data['product_order_no'].id,
            'product_uom_qty': 1,
            'price_unit': amount,
            'tax_id': False,
        })

    def _quote(self, amount, partner=None, **values):
        vals = {'partner_id': (partner or self.partner_a).id, **values}
        if amount:
            vals['order_line'] = [self._line(amount)]
        return self.env['sale.order'].create(vals)

    def _post_invoice(self, amount, partner=None):
        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': (partner or self.partner_a).id,
            'invoice_line_ids': [Command.create({
                'name': 'receivable', 'quantity': 1, 'price_unit': amount, 'tax_ids': False,
            })],
        })
        invoice.action_post()
        self.partner_a.invalidate_recordset(['credit', 'credit_to_invoice'])
        return invoice

    def _lines(self, order):
        return order.credit_warning_message.split('\n')

    # -- tests ------------------------------------------------------------------

    def test_01_yellow_message(self):
        self._post_invoice(700.0)
        order = self._quote(150.0)
        self.assertEqual(order.credit_warning_level, 'warning')
        self.assertEqual(self._lines(order), [
            "partner_a is approaching its credit limit of $\xa01,000.00.",
            "Outstanding receivables (incl. confirmed orders to invoice): $\xa0700.00",
            "This order: $\xa0150.00",
            "Total after this order: $\xa0850.00",
        ])

    def test_02_boundaries(self):
        self._post_invoice(700.0)
        # total == limit is still yellow (red needs strictly over)
        self.assertEqual(self._quote(300.0).credit_warning_level, 'warning')
        # total == 80% is yellow (inclusive)
        self.assertEqual(self._quote(100.0).credit_warning_level, 'warning')
        # total just under 80% -> nothing
        under = self._quote(99.99)
        self.assertFalse(under.credit_warning_level)
        self.assertEqual(under.credit_warning_message, '')
        # just over limit -> red
        self.assertEqual(self._quote(300.01).credit_warning_level, 'danger')

    def test_03_red_message(self):
        self._post_invoice(700.0)
        order = self._quote(400.0)
        self.assertEqual(order.credit_warning_level, 'danger')
        self.assertEqual(self._lines(order), [
            "partner_a exceeds its credit limit of $\xa01,000.00.",
            "Outstanding receivables (incl. confirmed orders to invoice): $\xa0700.00",
            "This order: $\xa0400.00",
            "Total after this order: $\xa01,100.00",
        ])

    def test_04_red_with_empty_order_when_already_over(self):
        self._post_invoice(1200.0)
        order = self._quote(0.0)
        self.assertEqual(order.credit_warning_level, 'danger')
        self.assertIn("This order: $\xa00.00", self._lines(order))
        self.assertIn("Total after this order: $\xa01,200.00", self._lines(order))

    def test_05_no_limit_setting_off_or_no_partner(self):
        self._post_invoice(1200.0)
        order = self._quote(100.0)
        self.assertEqual(order.credit_warning_level, 'danger')

        # (a) no limit on the customer — `credit_limit` is a compute dependency,
        # so changing it recomputes the warning without manual invalidation.
        self.partner_a.credit_limit = 0.0
        self.assertEqual(order.credit_warning_message, '')
        self.assertFalse(order.credit_warning_level)
        self.partner_a.credit_limit = 1000.0
        self.assertEqual(order.credit_warning_level, 'danger')

        # (b) company switch off — `account_use_credit_limit` is a dependency too
        self.env.company.account_use_credit_limit = False
        self.assertEqual(order.credit_warning_message, '')
        self.assertFalse(order.credit_warning_level)
        self.env.company.account_use_credit_limit = True

        # (d) no customer
        no_partner = self.env['sale.order'].new({})
        self.assertEqual(no_partner.credit_warning_message, '')
        self.assertFalse(no_partner.credit_warning_level)

    def test_06_only_draft_and_sent(self):
        self._post_invoice(900.0)
        order = self._quote(500.0)
        self.assertEqual(order.credit_warning_level, 'danger')
        order.state = 'sent'
        self.assertEqual(order.credit_warning_level, 'danger')
        order.action_confirm()
        self.assertEqual(order.credit_warning_message, '')
        self.assertFalse(order.credit_warning_level)
        order._action_cancel()
        self.assertEqual(order.state, 'cancel')
        self.assertEqual(order.credit_warning_message, '')
        self.assertFalse(order.credit_warning_level)

    def test_07_reflects_real_receivables(self):
        invoice = self._post_invoice(300.0)
        confirmed = self._quote(400.0)
        confirmed.action_confirm()
        self.partner_a.invalidate_recordset(['credit', 'credit_to_invoice'])

        quote = self._quote(200.0)
        self.assertEqual(quote.credit_warning_level, 'warning')
        self.assertEqual(self._lines(quote)[1:], [
            "Outstanding receivables (incl. confirmed orders to invoice): $\xa0700.00",
            "This order: $\xa0200.00",
            "Total after this order: $\xa0900.00",
        ])

        # pay the invoice: outstanding drops to 400, total 600 -> no banner
        self.env['account.payment.register'].with_context(
            active_model='account.move', active_ids=invoice.ids,
        ).create({}).action_create_payments()
        self.partner_a.invalidate_recordset(['credit', 'credit_to_invoice'])
        quote.invalidate_recordset(['credit_warning_message', 'credit_warning_level'])
        self.assertEqual(quote.credit_warning_message, '')

        # raise the quote: total 900 again
        quote.order_line.price_unit = 500.0
        self.assertEqual(quote.credit_warning_level, 'warning')
        self.assertEqual(self._lines(quote)[1:], [
            "Outstanding receivables (incl. confirmed orders to invoice): $\xa0400.00",
            "This order: $\xa0500.00",
            "Total after this order: $\xa0900.00",
        ])

    def test_08_multicurrency(self):
        self.partner_a.credit_limit = 50.0
        order = self._quote(45.0, pricelist_id=self.buck_pricelist.id)
        self.assertEqual(order.amount_total / order.currency_rate, 22.5)
        self.assertEqual(order.credit_warning_message, '')

        order.order_line.price_unit = 110.0
        self.assertEqual(order.credit_warning_level, 'danger')
        self.assertEqual(self._lines(order), [
            "partner_a exceeds its credit limit of $\xa050.00.",
            "Outstanding receivables (incl. confirmed orders to invoice): $\xa00.00",
            "This order: $\xa055.00",
            "Total after this order: $\xa055.00",
        ])

    def test_09_recomputes_without_saving(self):
        self._post_invoice(700.0)
        no_limit_partner = self.env['res.partner'].create({'name': 'no limit'})
        order = self.env['sale.order'].new({
            'partner_id': self.partner_a.id,
            'order_line': [Command.create({
                'product_id': self.company_data['product_order_no'].id,
                'product_uom_qty': 1,
                'price_unit': 100.0,
                'tax_id': False,
            })],
        })
        self.assertEqual(order.credit_warning_level, 'warning')  # 800 / 1000
        order.order_line[0].price_unit = 400.0
        self.assertEqual(order.credit_warning_level, 'danger')   # 1100 / 1000
        order.partner_id = no_limit_partner
        self.assertFalse(order.credit_warning_level)
        self.assertEqual(order.credit_warning_message, '')

    def test_10_salesman_without_accounting_rights(self):
        self._post_invoice(900.0)
        order = self._quote(500.0)
        salesman_order = order.with_user(self.sales_user)
        # no AccessError although credit* partner fields are accounting-only
        self.assertEqual(salesman_order.credit_warning_level, 'danger')
        self.assertIn("Total after this order: $\xa01,400.00", salesman_order.credit_warning_message)

    def test_11_degrades_silently(self):
        # no customer, no lines, zero rate: never raises, never renders False/None
        empty = self.env['sale.order'].new({})
        self.assertEqual(empty.credit_warning_message, '')
        no_lines = self._quote(0.0)
        self.assertEqual(no_lines.credit_warning_message, '')
        order = self._quote(2000.0)
        order.currency_rate = 0.0
        self.assertEqual(order.credit_warning_message, '')
        self.assertFalse(order.credit_warning_level)

    def test_12_limit_read_in_order_company(self):
        company2 = self.company_data_2['company']
        company2.account_use_credit_limit = True
        self.partner_a.with_company(company2).credit_limit = 500.0
        order = self.env['sale.order'].with_company(company2).create({
            'company_id': company2.id,
            'partner_id': self.partner_a.id,
            'pricelist_id': self.company_data_2['default_pricelist'].id,
            'order_line': [Command.create({
                'product_id': self.company_data_2['product_order_no'].id,
                'price_unit': 600.0,
                'tax_id': False,
            })],
        })
        # user's current company is company 1 (limit 1000): company 2's limit (500) must win
        order = order.with_company(self.env.company)
        self.assertEqual(order.credit_warning_level, 'danger')
        self.assertIn("500.00", self._lines(order)[0])

    # -- Phase 2: view ----------------------------------------------------------

    def _form_arch(self):
        arch = self.env['sale.order'].get_view(view_type='form')['arch']
        return etree.fromstring(arch)

    def test_13_view_arch(self):
        arch = self._form_arch()
        warning = arch.xpath(
            "//div[contains(@class, 'alert-warning')][@role='alert']"
            "[field[@name='credit_warning_message']]")
        danger = arch.xpath(
            "//div[contains(@class, 'alert-danger')][@role='alert']"
            "[field[@name='credit_warning_message']]")
        self.assertEqual(len(warning), 1)
        self.assertEqual(len(danger), 1)
        self.assertEqual(warning[0].get('invisible'), "credit_warning_level != 'warning'")
        self.assertEqual(danger[0].get('invisible'), "credit_warning_level != 'danger'")
        # hidden level field so the invisible expressions can evaluate
        level = arch.xpath("//field[@name='credit_warning_level']")
        self.assertEqual(len(level), 1)
        self.assertEqual(level[0].get('invisible'), '1')
        # core banner hidden but its field is kept in the arch
        core_field = arch.xpath("//field[@name='partner_credit_warning']")
        self.assertEqual(len(core_field), 1)
        self.assertEqual(core_field[0].getparent().get('invisible'), '1')
        # banners sit between the status bar header and the sheet
        banners = arch.xpath("//form/div[field[@name='credit_warning_message']]")
        self.assertEqual(len(banners), 2)
        self.assertIsNotNone(banners[0].getprevious())
        self.assertEqual(arch.xpath("//form/sheet")[0].getprevious().tag, 'div')

    def test_14_core_field_still_readable_and_form_updates(self):
        self._post_invoice(900.0)
        order = self._quote(500.0, user_id=self.sales_user.id)
        with Form(order.with_user(self.sales_user)) as order_form:
            self.assertEqual(order_form.credit_warning_level, 'danger')
            self.assertIn("Total after this order: $\xa01,400.00", order_form.credit_warning_message)
            # core field still available through the form (core test_credit_limit_access)
            self.assertIn('has reached its credit limit', order_form.partner_credit_warning)
            order_form.partner_id = self.env['res.partner'].create({'name': 'no limit'})
            self.assertFalse(order_form.credit_warning_level)
            self.assertFalse(order_form.credit_warning_message)
