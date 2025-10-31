# -*- coding: iso-8859-1 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import odoo
import logging

from odoo import api, fields, models, exceptions, _
from datetime import datetime 
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)
_logger.disabled = True

class MirLectura(models.Model):
    _inherit = ['ariis.mir.lectura']

    contrato_line		= fields.Many2one( 'contract.line', 'Contrato Dispositivo' , index=True , readonly=True )
    ariis_contrato_id	= fields.Many2one( string='Contrato', related='contrato_line.contract_id' )
    #===========================================================================
    # notValid
    #===========================================================================
    # Ver que la fecha de la lectura no corresponde a una factura ya generada y configurada
    #===========================================================================
    @api.constrains('creado')
    def _constrains_creado(self):
        if not self.creado:
            raise  ValidationError(_('Fecha de Lectura Vacia no es Valida'))

        if self.origen=="03":
            aSearch = []
            aSearch.append(('ariis_id','=',self.cliente_id))
            oCliente = self.env["res.partner"].search( aSearch , limit=1)
            if not oCliente:
                raise  ValidationError(_('Cliente no encontrado con Ariis ID : ' + str(self.cliente_id)))

            aFechas = fields.Date.to_string(self.creado).split('-')
            sOrigen =  aFechas[0]+"/"+aFechas[1]+"/"+str(oCliente.id)

            oFactura = self.env["account.move"].search( [("invoice_origin","=",sOrigen)] , limit=1)

            if oFactura and oFactura.state != 'draft':
                raise  ValidationError(_('Fecha de lectura no es valida (Leido)\nFactura %s de %s ya no esta en borrador.' % (  oFactura.number ,oFactura.name )))
    #===========================================================================
    @api.model
    def write(self, vals):
        if not self.contrato_line and self.dispositivo and self.dispositivo.contrato_line: 
            vals['contrato_line']= self.dispositivo.contrato_line
        return super(MirLectura,self).write(vals)
    #===========================================================================
    #===========================================================================
    # def getLecturaValuesNew(self ,oLecturaAnterior ):
    
        vals  = super(MirLectura,self).getLecturaValuesNew(oLecturaAnterior)

        # if self.dispositivo and self.dispositivo.contrato_line:
            # vals['contrato_line']		= self.dispositivo.contrato_line
        # else:
            # if oLecturaAnterior and oLecturaAnterior.contrato_line:
                # vals['contrato_line']   = oLecturaAnterior.contrato_line
                
        # return vals
    #===========================================================================