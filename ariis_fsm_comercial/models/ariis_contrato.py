from odoo import fields, models, api
from datetime import date, timedelta
from odoo.exceptions import UserError

class AriisContrato(models.Model):
    _inherit = 'ariis.contrato'

    # ------------------------------------------------
    # Lógica de Alerta por Vencimiento (CRON)
    # ------------------------------------------------
    
    @api.model
    def _check_contract_expiration(self):
        """
        Revisa todos los contratos próximos a vencer (en 30 o 60 días)
        y crea una Actividad programada para el comercial asignado.
        """
        today = date.today()
        
        # Rango de 60 días para la primera alerta
        date_in_60_days = today + timedelta(days=60)
        
        # Rango de 30 días para la segunda alerta
        date_in_30_days = today + timedelta(days=30)
        
        # Buscar contratos que expiran en 60 o 30 días y que estén activos
        # Se asume que el campo de fecha de finalización es 'date_end'
        expiring_contracts = self.search([
            ('state', '=', 'activo'), # Asumimos un campo 'state' en ariis.contrato
            ('date_end', 'in', [date_in_60_days, date_in_30_days]),
        ])
        
        for contract in expiring_contracts:
            # Determinar el número de días restantes
            days_remaining = (contract.date_end - today).days
            
            # Obtener el usuario comercial responsable (asumimos campo 'user_id')
            user_id = contract.user_id or self.env.user 
            
            # Crear el tipo de alerta (Actividad)
            activity_type = self.env.ref('mail.mail_activity_data_todo') # Tipo "A hacer"
            
            # 1. Verificar si ya existe una actividad para evitar duplicados
            existing_activity = self.env['mail.activity'].search([
                ('res_id', '=', contract.id),
                ('res_model_id', '=', self.env['ir.model']._get('ariis.contrato').id),
                ('summary', 'like', 'VENCIMIENTO:'),
                ('date_deadline', '>=', today),
            ], limit=1)
            
            if not existing_activity:
                # 2. Crear la actividad (Alerta)
                self.env['mail.activity'].create({
                    'activity_type_id': activity_type.id,
                    'summary': f'VENCIMIENTO: Contrato expira en {days_remaining} días',
                    'date_deadline': today, # Debe ser hoy para que aparezca en el panel de control
                    'user_id': user_id.id,
                    'res_id': contract.id,
                    'res_model_id': self.env['ir.model']._get('ariis.contrato').id,
                    'note': f'Contrato {contract.name} con cliente {contract.partner_id.name} expira el {contract.date_end}. ¡Contactar para renovación!',
                })