# -*- coding: iso-8859-1 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import odoo
import logging

from datetime import datetime 

from odoo import models, fields, api, exceptions, _

_logger = logging.getLogger(__name__)
_logger.disabled = False
#===============================================================================
class MaintenanceEquipment(models.Model):
    _inherit = ['maintenance.equipment']
    
    repair_ids          = fields.One2many( comodel_name='repair.order'  , inverse_name='dispositivo_id'   ) 
    #===========================================================================
    repair_ids_count    = fields.Integer(string="Reparaciones", compute='_compute_repair_count')
    #===========================================================================
    def _compute_repair_count(self):
        for equipo in self:
            if equipo.repair_ids:
                equipo.repair_ids_count= len(equipo.repair_ids)
            else:
                 equipo.repair_ids_count= 0
    #===========================================================================
    #===========================================================================
    def addreparacion(self):
    
        ctx = {
        
            'default_partner_id'        : self.partner_id.id,
            'default_dispositivo_id'    : self.id,
            'default_product_id'        : self.product_id.id,
            'default_motivo_id'         : 1,

        }
        
        return {
            'type'      : 'ir.actions.act_window',
            'view_type' : 'form',
            'view_mode' : 'form',
            'res_model' : 'repair.order',
            'src_model' : 'maintenance.equipment' ,
            'multi'     : False,
            'target'    : 'current',
            'context'   : ctx,
        }
    #===========================================================================
    