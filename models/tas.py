# -*- coding: iso-8859-1 -*- 

import odoo
from odoo import api, fields, models

class TA(models.Model):
	_name		= "ariis.tablaauxiliar"
	_description 	= "Tablas auxiliares"

	name		= fields.Char('Name', index=True, required=True) 
	icon		= fields.Char('Icono fa' ,default="info")


class TipoMonitorizacion(models.Model):
	_name = "ariis.tipomonitorizacion"
	_description = "Tipo de Monitorizacion"
	_inherit = "ariis.tablaauxiliar" 

class EstadoDispositivo(models.Model):
	_name = "ariis.estadodispositivo"
	_description = "Estado de Dispositivo"
	_inherit = "ariis.tablaauxiliar" 


 
 