# -*- coding: iso-8859-1 -*- 

import odoo
from odoo import api, fields, models

class Tiposuministro(models.Model):
	_name = "ariis.tiposuministro"
	_description = "Tipo de Suministro"
	_inherit = "ariis.tablaauxiliar" 

	isConsumible	= fields.Boolean('Es Consumible' ,copy=False )
 
 