from odoo import fields, models

class MaintenanceEquipment(models.Model):
    _inherit = 'maintenance.equipment'

    # Campo clave para la rentabilidad: la Cuenta Analítica
    analytic_account_id = fields.Many2one(
        'account.analytic.account', 
        string='Cuenta Analítica del Equipo',
        required=True, # Se requiere para asegurar la trazabilidad de costes
        ondelete='restrict', 
        help="Cuenta Analítica utilizada para imputar todos los ingresos y costes asociados a este equipo (Rentabilidad por Activo)."
    )