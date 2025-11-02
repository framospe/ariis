from odoo import fields, models, api

class MaintenanceEquipment(models.Model):
    _inherit = 'maintenance.equipment'

    # Campo que calcula las veces que se ha intervenido el equipo
    # Usaremos una variable related o computed para contar las Tareas FSM (intervenciones)
    interventions_count = fields.Integer(
        string="Total Intervenciones",
        compute='_compute_interventions_count',
        store=True,
    )
    
    # Campo para diferenciar la facturación (Requisito Gestión de Activos)
    genera_facturacion = fields.Boolean(
        string="Genera Facturación (Contrato Activo)",
        # Este campo será calculado basándose en la relación con ariis_contrato
        # compute='_compute_billing_status', 
        store=True,
    )

    @api.depends('project_task_ids') # Dependerá de las Tareas asociadas al Equipo
    def _compute_interventions_count(self):
        for equipment in self:
            # Aquí se implementaría la lógica para contar las tareas FSM (intervenciones)
            # de un periodo específico, por ahora solo contamos todas las tareas
            equipment.interventions_count = self.env['project.task'].search_count([
                ('equipment_id', '=', equipment.id)
            ])
            # La lógica real debería usar filtros de fecha (ej. últimos 12 meses)