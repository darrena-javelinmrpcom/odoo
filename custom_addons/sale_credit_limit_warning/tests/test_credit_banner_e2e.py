# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo.fields import Command
from odoo.tests import HttpCase, tagged


@tagged('post_install', '-at_install')
class TestCreditBannerE2E(HttpCase):
    """Browser E2E (Scenario 1 of the UAT spec): the credit banner transitions
    none -> yellow -> yellow at limit -> red -> none, plus a live unsaved update.

    Scenario 2 (mobile 375x667) is deliberately not implemented: accepted gap
    (UAT-REC-01 / OI-2), the HttpCase tour runner cannot set the viewport width.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.company.account_use_credit_limit = True
        cls.partner = cls.env['res.partner'].create({
            'name': 'Credit Banner E2E Customer',
            'credit_limit': 1000.0,
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Credit Warning Demo Product',
            'list_price': 1.0,
            'taxes_id': [Command.clear()],
        })
        cls.order = cls.env['sale.order'].create({
            'partner_id': cls.partner.id,
            'order_line': [Command.create({
                'product_id': cls.product.id,
                'product_uom_qty': 500,
                'price_unit': 1.0,
                'tax_id': [Command.clear()],
            })],
        })

    def test_credit_banner_happy_path(self):
        action = self.env.ref('sale.action_quotations_with_onboarding')
        self.start_tour(
            f"/odoo/action-{action.id}/{self.order.id}",
            'credit_banner_happy',
            login='admin',
        )
