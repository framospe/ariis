# -*- coding: iso-8859-1 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import odoo
from odoo import api, fields, models
from datetime import datetime 

class ContratoTipo(models.Model):
    _name			= 'ariis.contrato.tipo'
    _description	= "Tipo de Contrato"
    _inherit		= "ariis.tablaauxiliar" 
    _sql_constraints = [ ('codigo', 'unique (codigo)', 'El codigo de contrato debe ser unico!') ]
    
    codigo	= fields.Char("Codigo" , required=True ,index=True , store=True)
    dominio	= fields.Char("Dominio" , default="[]" )
    informe	= fields.Many2one('ir.actions.report', string='Informe'  )
    anual	= fields.Boolean('Factura Acumulativa', copy=False, readonly=False)