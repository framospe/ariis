from odoo import fields, models, api
from datetime import date, timedelta

class MaintenanceEquipment(models.Model):
    _inherit = 'maintenance.equipment'

    # ----------------------------------------------------------------------
    # CAMPOS DE LECTURA (Sincronizados desde ariis_mir)
    # ----------------------------------------------------------------------

    # Asume que existe un modelo de configuración en ariis_mir
    mir_config_id = fields.Many2one(
        'ariis.mir.config', # <-- AJUSTAR ESTE NOMBRE DE MODELO SI ES NECESARIO
        string="Configuración MIR",
        help="Enlace a la configuración del dispositivo para la toma de lecturas."
    )
    
    # Campos que almacenarán la ÚLTIMA LECTURA CONSOLIDADA
    last_reading_bn = fields.Integer(
        string="Última Lectura B/N",
        compute='_compute_mir_data',
        store=True,
    )
    last_reading_color = fields.Integer(
        string="Última Lectura Color",
        compute='_compute_mir_data',
        store=True,
    )
    last_reading_date = fields.Date(
        string="Fecha Última Lectura",
        compute='_compute_mir_data',
        store=True,
    )

    @api.depends('mir_config_id')
    def _compute_mir_data(self):
        """
        Calcula la última lectura B/N y Color a partir de la tabla ariis.mir.totalmes.
        """
        TotalMes = self.env['ariis.mir.totalmes'] # <-- AJUSTAR ESTE NOMBRE DE MODELO SI ES NECESARIO
        for equipment in self:
            if not equipment.mir_config_id:
                equipment.last_reading_bn = 0
                equipment.last_reading_color = 0
                equipment.last_reading_date = False
                continue

            last_totalmes = TotalMes.search([
                ('mir_config_id', '=', equipment.mir_config_id.id),
            ], order='date_end desc', limit=1) 
            
            if last_totalmes:
                equipment.last_reading_bn = last_totalmes.total_bn
                equipment.last_reading_color = last_totalmes.total_color
                equipment.last_reading_date = last_totalmes.date_end
            else:
                equipment.last_reading_bn = 0
                equipment.last_reading_color = 0
                equipment.last_reading_date = False

    # ----------------------------------------------------------------------
    # LÓGICA DE MONITORIZACIÓN PROACTIVA (CRON del Día 20)
    # ----------------------------------------------------------------------
    
    @api.model
    def check_proactive_monitoring(self):
        """
        Ejecutado por la tarea CRON el día 20. Genera el listado de estado.
        """
        today = date.today()
        
        # Define el inicio del mes que vamos a evaluar (el anterior al actual)
        last_month_end = today.replace(day=1) - timedelta(days=1)
        last_month_start = last_month_end.replace(day=1)

        # Buscar equipos con configuración MIR activa
        target_equipment = self.search([('mir_config_id', '!=', False)])

        anomalies = []
        for equipment in target_equipment:
            # 1. Buscar el registro consolidado del mes anterior
            last_month_total = self.env['ariis.mir.totalmes'].search([
                ('mir_config_id', '=', equipment.mir_config_id.id),
                ('date_start', '>=', last_month_start),
                ('date_end', '<=', last_month_end),
            ], limit=1)
            
            # 2. Regla de Anomalía: FALTA DE LECTURA (Requisito del día 20)
            if not last_month_total:
                anomalies.append(f"FALTA LECTURA: Equipo {equipment.name} no tiene registro consolidado del mes anterior ({last_month_start} a {last_month_end}).")
            
            # Aquí se pueden añadir más reglas de anomalía (Bajo/Alto Consumo)

        # 3. Generar la alerta al jefe de servicio
        if anomalies:
            manager_id = self.env['res.users'].search([('login', '=', 'jefe_servicio_mir')], limit=1) # <-- AJUSTAR USUARIO
            if manager_id:
                self.env['mail.activity'].create({
                    'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
                    'summary': f'ALERTA MIR: {len(anomalies)} anomalías de lectura detectadas',
                    'date_deadline': today,
                    'user_id': manager_id.id,
                    'note': "Informe de Monitorización Proactiva (Día 20):\n" + "\n".join(anomalies),
                })
            else:
                self.env.user.notify_warning(message="Alerta de anomalías MIR generada, pero no se encontró un usuario de destino.")