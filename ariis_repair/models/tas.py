# -*- coding: iso-8859-1 -*- 

import odoo
from odoo import api, fields, models

	
class MotivoSat(models.Model):
	_name = "ariis.motivosat"
	_description = "Motivo Servicio"
	_inherit = "ariis.tablaauxiliar" 

  