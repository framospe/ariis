# -*- coding: iso-8859-1 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import odoo
import logging

from odoo import models, fields, api, exceptions, _
from datetime import datetime 

_logger = logging.getLogger(__name__)
_logger.disabled = False

class MaintenanceEquipment(models.Model):
    _inherit = ['maintenance.equipment']
    #===========================================================================
    contrato_line		= fields.Many2one( 'contract.line', 'Contrato Dispositivo' , index=True , readonly=True )
    ariis_contrato_id	= fields.Many2one( string='Contrato', related='contrato_line.contract_id' )
	#===========================================================================
    #===========================================================================
    def crear_contratos_cxc_cron(self):
 
        isNuevo = False
        
        for oEquipo in self:
            
            if not oEquipo.mir:
                continue
                
            oContrato       = False
            oContratoLinea  = oEquipo.contrato_line
            
            if not oContratoLinea or oContratoLinea.partner_id != oEquipo.partner_id.id or oContratoLinea.dispositivo_id.id != oEquipo.id:
 
                oValues                 = {}
                oValues['partner_id']   = oEquipo.partner_id.id
                oValues['iscxc']        = True

                oContrato = self.getContrato( oValues )
                # =====================================
                if not oContrato:
                    
                    isNuevo = True
                    
                    _logger.info("Creando Contrato: "+str(oValues))
                    
                    oContrato = self.env['contract.contract'].create( { 
                                                'partner_id'    : +oEquipo.partner_id.id  , 
                                                'iscxc'         : True ,
                                                'name'          : "CXC "+oEquipo.partner_id.name ,
                                                'date_start'    : datetime.today() ,
                                                'pricelist_id'  : 1,
                                                'contract_type' : 'sale'
                                             })
                    
                # =====================================
                aSearch = []
                
                aSearch.append(('contract_id'   ,'=', oContrato.id ))
                aSearch.append(('partner_id'    ,'=', oEquipo.partner_id.id ))
                aSearch.append(('dispositivo_id','=', oEquipo.id ))
            
                oContratoLinea = self.env['contract.line'].search(aSearch,limit=1)
                # =====================================
                if not oContratoLinea:
                
                    _logger.info("Equipo sin linea de contrato: "+oEquipo.lot_id.name )
                
                    oValues = {
                                'active'                : True ,
                                'contract_id'           : oContrato.id ,
                                "dispositivo_id"        : oEquipo.id ,
                                'name'                  : oEquipo.product_id.name+" - "+oEquipo.lot_id.name ,
                                'date_start'            : oContrato.date_start,
                                'date_end'              : oContrato.date_end,
                                'state'                 : 'in-progress',
                                'automatic_price'       : True,
                                'anyadido'              : datetime.now() ,
                                'promocion'             : False,
                                'recurring_next_date'   : oContrato.recurring_next_date
                              }
                          
                    _logger.info("Creando Linea de Factura de Contrato: "+str(oValues))
                
                    oContratoLinea = self.env['contract.line'].create( oValues )
                    
                    # subtype='mail.mt_comment',
                    # try:
                        # oContratoLinea.message_post(
                        # subject=(_("Linea de Contrato creada automaticamente")),
                        # body="Creacion automatica desde proceso el %s" % (datetime.now().strftime('%d-%m-%Y')),
                        # message_type='comment',
                        
                    # )
                    # except Exception as e:
                        # _logger.critical(e)
                # =====================================
                else:
                    oValues = {
                                'contract_id'           : oContrato.id ,
                                'name'                  : "Linea de Contrato CXC - "+oEquipo.lot_id.name ,
                                'anyadido'              : datetime.now() ,
                                'recurring_next_date'   : oContrato.recurring_next_date
                              }
                              
                    _logger.info("Modificando Linea de Factura de Contrato: "+str(oValues))
                    
                    oContratoLinea.update( oValues )
                # =====================================
            else:
                _logger.info("Contrato Linea existe: "+oContratoLinea.dispositivo_id.lot_id.name)
                oContrato = oContratoLinea.contract_id
                # =====================================
            oEquipo.update( { 'contrato_line' : oContratoLinea.id })
	#===========================================================================
    def isExisteContrato(self, aSearch ):
        return self.getContrato(aSearch)!=False
	#===========================================================================
    def getContrato(self, aBuscar ):
    
        
        _logger.info("Buscando contrato: "+str(aBuscar))
        
        aSearch = []
        aSearch.append(('partner_id'    ,'=',aBuscar['partner_id'] ))
        aSearch.append(('iscxc'         ,'=',aBuscar['iscxc']))
        
        return self.env['contract.contract'].search(aSearch ,limit=1)
        
	#=========================================================================== 
	#===========================================================================