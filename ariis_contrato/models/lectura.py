# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import odoo
from odoo import api, fields, models

class Lectura(models.Model):
    _inherit = ['ariis.lectura']
    #===========================================================================
    contrato_line		= fields.Many2one( 'contract.line', 'Contrato Dispositivo' , index=True , readonly=True )
    ariis_contrato_id	= fields.Many2one( string='Contrato', related='contrato_line.contract_id' )
    #===========================================================================
    @api.model
    def write(self, vals):
        if not self.contrato_line and self.totalmes and self.totalmes.contrato_line: 
            vals['contrato_line']= self.totalmes.contrato_line
        return super(Lectura,self).write(vals)