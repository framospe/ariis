from odoo import fields, models, api
from odoo.tools import date_utils
from datetime import date

class ResPartner(models.Model):
    _inherit = 'res.partner'

    # Campo calculado para determinar la fecha de la última venta/factura
    last_sale_date = fields.Date(
        string="Última Compra",
        compute='_compute_last_sale_date',
        store=True,
    )

    # Campo booleano para identificar inactividad (más de 6 meses sin compra)
    is_inactive_customer = fields.Boolean(
        string="Cliente Inactivo (> 6 meses)",
        compute='_compute_is_inactive_customer',
        store=True,
        help="Indica si el cliente no ha realizado ninguna compra o factura en los últimos 6 meses."
    )

    # Método para calcular la última fecha de venta (optimizado para Odoo)
    @api.depends('sale_order_ids.date_order', 'invoice_ids.invoice_date')
    def _compute_last_sale_date(self):
        for partner in self:
            last_date = False
            # Lógica para encontrar la fecha de la última factura o pedido confirmado
            # Aquí necesitarías la implementación real basada en tus modelos de Venta/Factura
            
            # Placeholder: Asumir que buscas en facturas validadas
            last_invoice = self.env['account.move'].search([
                ('partner_id', '=', partner.id),
                ('state', '=', 'posted'),
                ('type', 'in', ['out_invoice', 'out_refund'])
            ], order='invoice_date desc', limit=1)

            if last_invoice:
                last_date = last_invoice.invoice_date
            
            partner.last_sale_date = last_date

    @api.depends('last_sale_date')
    def _compute_is_inactive_customer(self):
        six_months_ago = date_utils.start_of(date_utils.end_of(date.today(), 'month') - date_utils.relativedelta(months=6), 'day')
        for partner in self:
            if partner.last_sale_date and partner.last_sale_date < six_months_ago:
                partner.is_inactive_customer = True
            else:
                partner.is_inactive_customer = False