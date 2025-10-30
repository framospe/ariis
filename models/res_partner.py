# -*- coding: iso-8859-1 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


import odoo
import logging


from odoo import api, fields, models
from datetime import datetime 
from odoo.exceptions import UserError
from odoo.addons.base.models.res_partner import WARNING_MESSAGE, WARNING_HELP
from odoo.tools.translate import _
_logger = logging.getLogger(__name__)

class Partner(models.Model):
    _inherit = 'res.partner'

    ariis_id			= fields.Char(string='Ariis Referencia ', index=True , readonly=True ,copy=False)
    horario				= fields.Char( string='Horario' ,copy=False , index=False)
    #=====================
    is_preventivo		= fields.Boolean('Mant. Preventivo', default=False)
    is_bloqueado		= fields.Boolean( string='Bloqueado', default=False,copy=False)
    #=====================

    #=====================
    dispositivo_count 	= fields.Integer(compute='_compute_dispositivo_count', string='# Dispositivos' ,copy=False)	
    total_preventivo	= fields.Integer('Cada (dias)' , default=90)
    contrato_count 		= fields.Integer(compute='_compute_contrato_count', string='# Contratos',copy=False)
    distancia			= fields.Integer('Km desde la oficina' , help="Distancia desde la oficina a este cliente",default=0)
    monitorizar_cada	= fields.Integer('Reportar cada (min)' , default=45) 
    solicitasuministros	= fields.Integer('Pedir suministro al (%)' , help="Porcentaje min al que no solicitar suministro (%)" , default=10)
    #=====================
    alta				= fields.Datetime('Fecha de alta', readonly=True ,default=datetime.today(),copy=False)
    #=====================
    #=====================
    #contrato_ids		= fields.One2many( 'ariis.contrato'	, 'partner_id', 'Contratos' ,copy=False) 
    # vat					= fields.Char(index=True ,string='NIF', help="Tax Identification Number. "
                                         # "Fill it if the company is subjected to taxes. "
                                         # "Used by the some of the legal statements.")

    # doc_count 			= fields.Integer(compute='_compute_attached_count', string="Number of documents attached",copy=False)


    # ischange			= fields.Boolean('Tiene Cambios', default=False,copy=False)

    # categoria			= fields.Selection([
                                    # ('01', 'Vip'), ('02', 'Ideal'),
                                    # ('03', 'Comprometido'), ('04', 'Comprador de Valor'),
                                    # ('05', 'Quiere resultados'), ('06', 'Buscador de gangas'),
                                    # ('99', 'Sin Definir')], string='Categoria', copy=False, default='99' , track_visibility='onchange' ) 
 
    # sepa				= fields.Char( string='Sepa' ,copy=False , index=True) 



    def _compute_dispositivo_count(self):
        for partner in self:
            partner.dispositivo_count = self.env['maintenance.equipment'].search_count([('partner_id', '=', partner.id)])

    def _compute_contrato_count(self):
        # for partner in self:
            # partner.contrato_count = self.env['ariis.contrato'].search_count([('partner_id', '=', partner.id)])
        return 0
    def _compute_attached_count(self):
        # for partner in self:
            # partner.doc_count = self.env['ir.attachment'].search_count([('res_model', '=', 'res.partner'), ('res_id', '=', partner.id)])
        return 0
    def attachment_tree_view(self):
        self.ensure_one()
        domain = [ '&',  ('res_model', '=', 'res.partner'), ('res_id', '=', self.id) ]
        return {
            'name': 'Attachments',
            'domain': domain,
            'res_model': 'ir.attachment',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'view_mode': 'kanban,tree,form',
            'view_type': 'form',
            'help': '''<p class="oe_view_nocontent_create">
                        Documentos son anexados a tu Cliente.</p><p>
                        Send messages or log internal notes with attachments to link
                        documents to your project.
                    </p>''',
            'limit': 80,
            'context': "{" + "'default_res_model': '{0}','default_res_id': {1} ".format(self._name, self.id , self.company_id) +"}"
            }

    def toggle_is_bloqueado(self):
        
        self.ensure_one()
        
        if self.is_bloqueado:
           self.write({ 'is_bloqueado': False ,'sale_warn' : 'no-message' , 'sale_warn_msg': '' })
        else:
           self.write({ 'is_bloqueado': True  ,'sale_warn' : 'block' , 'sale_warn_msg': 'Cliente Bloqeado en Ariis' })
        
        oMail = self.env['mail.message']
        canal = self.env.ref('ariis.channel_ariis')

        if self.is_bloqueado:
           sBody = 'Cliente '+self.name +" fue BLOQUEADO"
           sSimple = 'Cliente BLOQUEADO'
        else:
           sBody = 'Cliente '+self.name +" fue DESBLOQUEADO"
           sSimple = 'Cliente DESBLOQUEADO'
        # values = {	'channel_ids': [(6, 0, [canal.id])] ,
                        # 'message_type':'notification' ,
                        # 'subject': 'Cambio en el estado del cliente ' +self.name ,
                        # 'body': sBody }
                        
        # oMail.create(values)


        canal.message_post( body=_( sBody ) , subject='Cambio de estado del cliente ' +self.name)
        
 
        self.self.message_post( body= sSimple )
        return True

    def isCheckSuministro(self):
        return (self.solicitasuministros>0)

    
    #==============================================================================
    def isHasContractActive(self):
        
        self.ensure_one()
        
        aSearch = []
        aSearch.append(('partner_id','=',self.id))
        aSearch.append(('state','=','1'))
        
        isFound = self.env['ariis.contrato'].search(aSearch,limit=1)

        return isFound
    #==============================================================================
    def bloquea(self):
        self.ensure_one()
        if not self.is_bloqueado and not self.isHasContractActive():
            self.toggle_is_bloqueado()
        return
    #==============================================================================
    def _action_bloquea_sin_contrato(self):
        
        _logger.info('==================================================================' )
        _logger.info('Inicio de proceso de Bloquear clientes sin contratos activos')
        
        aSearch = []
        aSearch.append(('is_bloqueado','=',False))
        aSearch.append(('contrato_count','>','0'))
        
        oFounds = self.search(aSearch,limit=10)
        
        _logger.info('Analizando %s contratos encontrados' % len(oFounds))
        
        for cliente in oFounds:
            cliente.bloquea()
    
        _logger.info('Proceso de Bloquear clientes sin contratos activos finalizo OK')
        _logger.info('==================================================================' )
        
        return
