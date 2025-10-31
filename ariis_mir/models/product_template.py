# -*- coding: iso-8859-1 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import odoo
from odoo import api, fields, models
from odoo.exceptions import UserError

class ProductTemplate(models.Model):
	_inherit = ['product.template']
 
	product_suministros	= fields.One2many( 'ariis.product.suministro', 'product_id', 'Suministros Asociados'  ,copy=False  ) 