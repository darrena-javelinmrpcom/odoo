# Part of Odoo. See LICENSE file for full copyright and licensing details.
"""Characterization tests for ``sale.order._compute_partner_credit_warning``.

These are NOT unit tests. They capture what the method currently returns,
byte-for-byte, and do not assert what it *should* return. Every expectation is
a ``assertEqual`` against the full string (no ``assertIn`` / ``assertRegex``).

Target: ``addons/sale/models/sale_order.py:771``.
Language is locked to ``en_US`` through a new environment (never by assigning
``env.context``, which would mutate a shared, cached environment).
"""
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install', 'characterization')
class TestPartnerCreditWarningCharacterization(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, lang='en_US'))

    def test_harness_lang_locked(self):
        """Harness smoke test: proves tag selection and the en_US lock."""
        self.assertEqual(self.env.context.get('lang'), 'en_US')
