from odoo import fields, models, api

class ProjectTask(models.Model):
    _inherit = 'project.task'

    # 1. Campo para obtener la Cuenta Analítica del Equipo
    analytic_account_id = fields.Many2one(
        'account.analytic.account',
        string="Cuenta Analítica de Costes",
        compute='_compute_analytic_account',
        store=True,
        readonly=False, # Permitir la edición si no hay equipo
        help="Cuenta Analítica heredada del Equipo de Mantenimiento."
    )

    @api.depends('equipment_id.analytic_account_id')
    def _compute_analytic_account(self):
        for task in self:
            if task.equipment_id and task.equipment_id.analytic_account_id:
                task.analytic_account_id = task.equipment_id.analytic_account_id
            # Odoo ya tiene lógica para imputar costes si la tarea tiene una cuenta analítica.
            # Nuestro objetivo es asegurarnos de que el campo exista y esté lleno.

    # 2. Sobreescribir el create para asegurar la imputación
    @api.model_create_multi
    def create(self, vals_list):
        # La lógica de Odoo ya propaga la analytic_account_id a las hojas de tiempo
        # si está en la tarea. Nos aseguramos de calcularla antes de la creación
        for vals in vals_list:
            if vals.get('equipment_id') and not vals.get('analytic_account_id'):
                equipment = self.env['maintenance.equipment'].browse(vals['equipment_id'])
                if equipment.analytic_account_id:
                    vals['analytic_account_id'] = equipment.analytic_account_id.id
        
        return super().create(vals_list)


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    # Este código es importante: asegura que los gastos asociados a la Tarea
    # (como las hojas de tiempo) utilicen la Cuenta Analítica de la Tarea FSM.
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('task_id') and not vals.get('account_id'):
                task = self.env['project.task'].browse(vals['task_id'])
                if task.analytic_account_id:
                    vals['account_id'] = task.analytic_account_id.id
        return super().create(vals_list)