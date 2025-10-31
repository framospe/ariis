# -*- coding: iso-8859-1 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import odoo
import logging

from odoo import api, fields, models
from datetime import datetime 

_logger = logging.getLogger(__name__)

class MirSuministro(models.Model):
	_name         = 'ariis.mir.suministro'
	_description  = "Suministro Mir"
	_order        = "tipo_id"
	
	mir_lectura			= fields.Many2one( 'ariis.mir.lectura', 'Mir Lectura',index=True,required=True,ondelete='cascade')
	numero				= fields.Integer(string='Numero',required=True)
	tipo_id 			= fields.Many2one( 'ariis.tiposuministro', string='Tipo de Suministro' )
	color				= fields.Selection([
									('0', 'Grey'),
									('1', 'Black'),
									('2', 'Yellow'),
									('3', 'Magenta'),
									('4', 'Cyan'),
									('5','Grey')], string='Color', copy=False, default='0' )
	nivel				= fields.Float("Nivel",digits=(3, 2))
	porcentaje			= fields.Selection([
									('0', 'Vacio'),
									('5', 'Al Limite'),
									('10', '10%'),
									('20', '20%'),
									('30', '30%'),
									('40', '40%'),
									('50', '50%'),
									('60', '60%'),
									('70', '70%'),
									('80', '80%'),
									('90', '90%'),
									('99', 'Desconocido'),
									('100', 'Lleno'),
									('Listo', 'Listo')], string='Porcentaje', copy=False, default='99' )
	serialnumber		= fields.Char( string="Num. de Serie" )
	desc				= fields.Char( string="Descripcion" )
	proveedor			= fields.Char( string="Proveedor" )
