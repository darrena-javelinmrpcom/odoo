# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.tools.misc import formatLang

# Share of the credit limit from which (inclusive) the yellow warning shows.
CREDIT_WARNING_THRESHOLD = 0.8


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    credit_warning_message = fields.Text(
        string="Credit Limit Warning",
        compute='_compute_credit_warning',
    )
    credit_warning_level = fields.Selection(
        selection=[('warning', "Warning"), ('danger', "Danger")],
        string="Credit Limit Warning Level",
        compute='_compute_credit_warning',
    )

    @api.depends(
        'partner_id', 'company_id', 'state', 'amount_total', 'currency_rate',
        'partner_id.commercial_partner_id.credit_limit',
        'partner_id.commercial_partner_id.credit',
        'company_id.account_use_credit_limit',
    )
    @api.depends_context('company')
    def _compute_credit_warning(self):
        for order in self:
            order.credit_warning_message = ''
            order.credit_warning_level = False
            company = order.company_id
            if (
                order.state not in ('draft', 'sent')
                or not company.account_use_credit_limit
                or not order.partner_id
                or not order.currency_rate
            ):
                continue

            # `credit*` fields are restricted to accounting groups: read with sudo,
            # in the order's company (limit is company dependent).
            partner = order.partner_id.commercial_partner_id.with_company(company).sudo()
            limit = partner.credit_limit
            if limit <= 0:
                continue

            currency = company.currency_id
            outstanding = partner.credit + partner.credit_to_invoice
            order_amount = order.amount_total / order.currency_rate
            total = outstanding + order_amount

            if currency.compare_amounts(total, limit) > 0:
                level = 'danger'
                headline = self.env._(
                    "%(partner)s exceeds its credit limit of %(limit)s.",
                    partner=partner.name,
                    limit=formatLang(self.env, limit, currency_obj=currency),
                )
            elif currency.compare_amounts(total, limit * CREDIT_WARNING_THRESHOLD) >= 0:
                level = 'warning'
                headline = self.env._(
                    "%(partner)s is approaching its credit limit of %(limit)s.",
                    partner=partner.name,
                    limit=formatLang(self.env, limit, currency_obj=currency),
                )
            else:
                continue

            order.credit_warning_level = level
            order.credit_warning_message = "\n".join([
                headline,
                self.env._(
                    "Outstanding receivables (incl. confirmed orders to invoice): %s",
                    formatLang(self.env, outstanding, currency_obj=currency),
                ),
                self.env._(
                    "This order: %s",
                    formatLang(self.env, order_amount, currency_obj=currency),
                ),
                self.env._(
                    "Total after this order: %s",
                    formatLang(self.env, total, currency_obj=currency),
                ),
            ])
