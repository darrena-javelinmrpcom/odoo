# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Sale Credit Limit Warning',
    'version': '18.0.1.0.0',
    'category': 'Sales/Sales',
    'summary': 'Colour-coded customer credit limit warning on the sales order form',
    'depends': ['sale'],
    'data': [
        'views/sale_order_views.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
}
