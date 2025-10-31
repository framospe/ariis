# -*- coding: iso-8859-1 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import odoo
import logging
import dateutil.relativedelta

from odoo import api, fields, models
from datetime import datetime 
from odoo.exceptions import UserError

I_MESES = "NoSale,Enero,Febrero,Marzo,Abril,Mayo,Junio,Julio,Agosto,Septiempre,Octubre,Noviembre,Diciembre"

_logger = logging.getLogger(__name__)
_logger.disabled = True

class TotalMes(models.Model):

    _inherit = ['ariis.total.mes']
    
    #===========================================================================
    contrato_line		= fields.Many2one( 'contract.line', 'Contrato Dispositivo' , index=True , readonly=True )
    ariis_contrato_id	= fields.Many2one( string='Contrato', related='contrato_line.contract_id' )
    generation_type		= fields.Selection('Tipo de Documento a generar en contrato' , related='ariis_contrato_id.generation_type' )
    #===========================================================================
    # postProcesa
    #===========================================================================
    def postProcesa(self):
    
        _logger.info('postProcesa nuevo : %s' % self.errortext)
        # oConfg = self.env['ir.config_parameter'].sudo()

        if self.errortext=='OK':
            if self.contrato_line:
                
                if not self.ariis_contrato_id:
                    self.ariis_contrato_id = self.contrato_line.contrato_id
            if not self.ariis_contrato_id.reload:
                self.ariis_contrato_id.write( {'reload': True })

            self.write( { 'tratado' : True , 'last_report': fields.Datetime.now() , 'factura' : False })
            
            if self.contrato_line:
                self.contrato_line.write( {'last_periodo': self.periodo })
        return
    #===========================================================================
    # def runfromUI(self):

        # for oTotMes in self:
            
            # if oTotMes.ariis_contrato_id:
                # oTotMes.ariis_contrato_id.update({ 'reload' : True } )

            # oTotMes.update( { 'tratado' : False , 'factura': False })
    #===========================================================================
    def runRefreshLine(self):

        for oTotMes in self:
            if oTotMes.ariis_contrato_id:
                oTotMes.ariis_contrato_id.update({ 'reload' : True } )
            oTotMes.update( { 'tratado' : True , 'factura': False })
    #===========================================================================

    #===========================================================================
    #===========================================================================
    #===========================================================================
    #===========================================================================
    #===========================================================================
    #===========================================================================
    #===========================================================================
    #===========================================================================
    @api.model
    def write(self, vals):
        if not self.contrato_line and self.dispositivo and self.dispositivo.contrato_line: 
            vals['contrato_line']= self.dispositivo.contrato_line
        return super(TotalMes,self).write(vals)