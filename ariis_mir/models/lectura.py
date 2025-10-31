 # -*- coding: iso-8859-1 -*- 

import odoo
from odoo import api, fields, models
from datetime import datetime

class Lectura(models.Model):
    _name			= "ariis.lectura"
    _description 	= "Lectura Dispositivo"
    _order			= "actual_lectura desc"

    name				= fields.Char('Nombre de lectura' , index=True, compute='_compute_name')
    ariis_id			= fields.Char(string='Ariis Referencia ', index=True , readonly=True ,copy=False)
    modelo				= fields.Char(  string='Modelo'   ,  readonly=True ,index=True )
    numeroserie			= fields.Char(  string='Numero de Serie' ,  readonly=True)
    nombre				= fields.Char(  string='Nombre' , related='dispositivo_id.name' ,  readonly=True)
    errortext			= fields.Char('Mensaje de error')
    errordesc			= fields.Char('Descripcion del error')
    #=====================
    state = fields.Selection([('01', 'Sin Contabilizar'),
        ('02', 'Contabilizado'),
        ('03', 'Con Errores')], string='Estado',copy=False, default='01' )
    origen				= fields.Selection([
                                ('01', 'MIR'),
                                ('02', 'Mail'),
                                ('03', 'Manual'),
                                ('99','Other')], string='Origen',copy=False, default='02' )
    #=====================
    last_report			= fields.Datetime('Ultima actividad', readonly=True ,default=datetime.today())
    actual_lectura 		= fields.Date('Lectura'  ,default=datetime.today().date() )
    previo_lectura 		= fields.Date('Lectura Anterior'   )
    #=====================
    actual_total_bn 	= fields.Integer('Act. Tot. Pag. BN'   )
    actual_total_color	= fields.Integer('Act. Tot. Pag. Color'  )
    actual_total 		= fields.Integer('Act. Tot. Pag.'   )
    previo_total_bn 	= fields.Integer('Prev. Tot. Pag. BN' )
    previo_total_color	= fields.Integer('Prev. Tot. Pag. Color' )
    previo_total 		= fields.Integer('Prev. Tot. Pag.' )
    total_bn 			= fields.Integer('Tot. Pag. BN' 	, compute='_total_bn' ,store=True  )
    total_color			= fields.Integer('Tot. Pag. Color'	, compute='_total_color'  ,store=True )
    #=====================
    iscolor		        = fields.Boolean('Color', readonly=True , related='dispositivo_id.iscolor')
    #=====================
    partner_id = fields.Many2one( 'res.partner', 'Cliente', domain="[('company_type','=', 'company')]" ,
                        index=True, 
                        state={'03': [('readonly', True)]},required=True)
    dispositivo_id		= fields.Many2one( 'maintenance.equipment', string='Equipo' ,  required=True ,index=True  )
    totalmes			= fields.Many2one( 'ariis.total.mes', string='Total Mes' )
    #===========================================================================
    def _compute_name(self):
        for lectura in self:
            dispositivo = lectura.dispositivo_id 
            if dispositivo:
                lectura.name = str(dispositivo.product_id.name)+" - ("+str(dispositivo.lot_id.name)+")"
            else:
                lectura.name = "Lectura Dispositivo Desconocido"

    def _total_bn(self):
            for lectura in self:
                lectura.total_bn = lectura.actual_total_bn - lectura.previo_total_bn

    def _total_color(self):
            for lectura in self:
                lectura.total_color = lectura.actual_total_color - lectura.previo_total_color
    def save(self):
        self._total_bn()
        self._total_color()
        return self.write({})