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
    
    #===========================================================================
    def _default_so(self):
        return self.partner_id.suministro_original if self.partner_id else False
    #===========================================================================
    suministro_ids	    = fields.One2many( comodel_name='ariis.suministro',inverse_name='dispositivo_id' , domain=[('state','in',('01','02'))] ,string='Suministros' ,copy=False)
    lecturas_ids		= fields.One2many( comodel_name='ariis.lectura'  , inverse_name='dispositivo_id'   ) 
    totalmes_ids 		= fields.One2many( comodel_name='ariis.total.mes', inverse_name='dispositivo'  )
    suministro_original	= fields.Boolean('Suministros Orig.', default=_default_so,copy=False ,store=True , help='Suministros Originales')
    #===========================================================================
    lecturas_ids_count = fields.Integer(string="Lecturas", compute='_compute_lecturas_count')
    totalmes_ids_count = fields.Integer(string="Totales Mes", compute='_compute_lecturas_mes_count')
    #===========================================================================
    
    def _compute_lecturas_count(self):
        for equipo in self:
            if equipo.lecturas_ids:
                equipo.lecturas_ids_count= len(equipo.lecturas_ids)
            else:
                 equipo.lecturas_ids_count= 0
    #===========================================================================
    def _compute_lecturas_mes_count(self):
        for equipo in self:
            if equipo.totalmes_ids:
                equipo.totalmes_ids_count=len(equipo.totalmes_ids)
            else:
                equipo.totalmes_ids_count= 0
    #===========================================================================
    def addlecturamir(self):
    
        ctx = {
            'default_origen'            : '03',
            'default_model'             : 'ariis.mir.lectura',
            'default_dispositivo_id'    : self.ariis_id,
            'default_cliente_id'        : self.partner_id.ariis_id,
            'default_macaddress'        : self.macaddress ,
            'default_ipaddress'         : self.ipaddress ,
            'default_creado'            : datetime.now() ,
            'default_manual'            : True ,
            'default_unid'              : 'Manual-' +str( datetime.now() ),
            'default_serialnumber'      : self.lot_id.name ,
            'default_modelo'            : self.product_id.name ,
            'default_hostname'          : self.hostnameleido,
            'default_localizacion'      : self.localizacion,
            'default_nombre'            : self.name,
            'default_cliente'           : self.partner_id.id,
            'default_dispositivo'       : self.id,
            'default_descripcion'       : 'Lectura Manual de - ' +self.lot_id.product_id.name,
            'default_contrato_line'     : self.contrato_line.id if  self.contrato_line else '' ,
        }
        
        return {
            'type'      : 'ir.actions.act_window',
            'view_type' : 'form',
            'view_mode' : 'form',
            'res_model' : 'ariis.mir.lectura',
            'src_model' : 'maintenance.equipment' ,
            'multi'     : False,
            'target'    : 'current',
            'context'   : ctx,
        }
    #===========================================================================
    #===========================================================================
    # historificaSuministro(self)
    #===========================================================================
    def historificaSuministro(self,oSuministro):
    
        _logger.info('historificaSuministro: Inicio')
        #=======================================
        # Sustituido
        #=======================================
        oValues = {}
        oValues['state']        = '03'
        #=======================================
        #'Retirado'
        #=======================================
        oValues['subestado']		= '06'		
        #=======================================
        oValues['fin_fecha']		= datetime.today()
        
        oValues['fin_total_pag']	= self.total_pag
        oValues['fin_total_bn']		= self.total_bn
        oValues['fin_total_color']	= self.total_color
        
        oSuministro.write(oValues)
        
        _logger.info('historificaSuministro: Suministro historificado') 