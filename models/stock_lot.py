# Part of Odoo. See LICENSE file for full copyright and licensing details.

import odoo
  
from odoo import api, fields, models
from datetime import datetime
from odoo.exceptions import UserError
 

class Dispositivo(models.Model):
    _inherit = 'stock.lot'
    #===========================================================================
    mir = fields.Boolean( 'Monitorizable', related='product_id.mir'  )
    #===========================================================================
    def crear_dispositivo(self):

        ctx = {
            'default_model'				: 'stock.lot',
            'default_lot_id'			: self.id,
            'default_product_id'		: self.product_id.id, 
        }
        
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'maintenance.equipment',
            'src_model': 'stock.lot' ,
            'multi': False,
            'target': 'current',
            'context': ctx,
        }