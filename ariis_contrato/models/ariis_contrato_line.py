# -*- coding: iso-8859-1 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import odoo
from odoo import api, fields, models
from datetime import datetime 

class ContratoLine(models.Model):
    _name           = 'ariis.contrato_line'
    _description    = "Equipo de Contrato"
    _inherit        = ['mail.thread', 'mail.activity.mixin']
    _order          = "contrato_id desc"

    contrato_id         = fields.Many2one( 'ariis.contrato', string='Contrato' , required=True , index=True , readonly=False )
    dispositivo_id      = fields.Many2one( 'maintenance.equipment', string='Equipo' , required=True ,index=True , store=True , readonly=False )
    cliente             = fields.Many2one( 'res.partner', string='Cliente' , related='contrato_id.partner_id' ,  readonly=False , store=True)
    #=====================
    modelo              = fields.Char(  string='Modelo' , related='dispositivo_id.product_id.name' ,  readonly=True , store=True)
    numeroserie         = fields.Char(  string='Numero de Serie' , related='dispositivo_id.lot_id.name' , store=True,  readonly=True)	
    #=====================
    anyadido            = fields.Datetime('Añadido' , readonly=True , default=datetime.today()) 
    #=====================
    promocion			= fields.Selection([
                                    ('01', 'Hasta Final de Fecha (Restando promocion cada mes) Defecto'),
                                    ('02', 'Hasta final de pag. de promocion (Facturar cuando Total impreso sea mayor que promocion+Total Actual)'),
                                    ('03', 'Hasta Final de Fecha (Restando cada mes si supera promocion)') ,
                                    ('04', 'Tarifa Plana (Promocion aplicable para todo lo facturable (Anual))') ,
                                    ],
                                    string='Promocion', copy=False, default='01' )
    #=====================
    fecha_fin_pro_bn    = fields.Date('Acaba promo. BN')
    fecha_fin_pro_color = fields.Date('Acaba promo. Color') 
    #=====================
    pag_pro_bn          = fields.Integer('Pag. promo. BN')
    pag_pro_color       = fields.Integer('Pag. promo. Color') 
    #=====================
    precio_bn           = fields.Float('Precio Pag. BN',digits=(2, 4))
    precio_color        = fields.Float('Precio Pag. Color',digits=(2, 4))
    #=====================
    iscxc               = fields.Boolean('Es CXC'   , related='dispositivo_id.mir'      ,copy=False ,readonly=True)
    iscolor             = fields.Boolean('Es Color' , related='dispositivo_id.iscolor'  ,copy=False ,readonly=True)
    automatic_price     = fields.Boolean( string="Auto-precio?",  help="If this is marked, the price will be obtained automatically "
             "applying the pricelist to the product. If not, you will be able to introduce a manual price", default=False )
    last_report  = fields.Datetime( string='Ultima actividad' , related='dispositivo_id.last_report' )
    last_periodo = fields.Date( string='Periodo' , index=True)
    #===========================================================================
    def _compute_display_name(self):
        result = []
        for record in self:
            if record.dispositivo_id:
                record.display_name =   str(record.contrato_id.name) +  ' (' + record.dispositivo_id.lot_id.name+')'
            else:
                record.display_name = str(record.contrato_id.name)
    #===========================================================================
    def isTarifaPlana(self):
        return self.contrato_id.isTarifaPlana()
    #===========================================================================
    def isHasPromo(self):
        return self.promocion!=False
    #===========================================================================
    def isValidPromo(self,iscolor):
        # TODO: Comprombar si la fecha de fin de promocion fue superada
        if self.isHasPromo():
            if iscolor and self.pag_pro_color>0:
                return True
            if not iscolor and self.pag_pro_bn>0:
                return True

        return False
    #===========================================================================
    # Retorna si la promocion 02 se cumple para el color (True) o el BN (False)
    #===========================================================================
    def isTotalPrintPromocion02(self , isColor , nTotalPagin ):

        if self.promocion != '02':
            return False

        if isColor:
            nTotalPromo = self.pag_pro_color
        else:
            nTotalPromo = self.pag_pro_bn

        return nTotalPagin>nTotalPromo
    #===========================================================================
    @api.model
    def write(self, vals):
        if not self.dispositivo_id.contrato_line:
            self.dispositivo_id.update({'contrato_line' : self.id })
        return super(ContratoLine,self).write(vals)
        
        
        