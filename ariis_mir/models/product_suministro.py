 # -*- coding: iso-8859-1 -*- 

import odoo
import logging

from odoo import api, fields, models
from datetime import datetime

_logger = logging.getLogger(__name__)

class ProductoSuministro(models.Model):
	_name			= "ariis.product.suministro"
	_description 	= "Producto de Sumistro"
	_order			= "numero desc"

	product_id 		= fields.Many2one( 'product.template', string='Modelo', readonly=True, required=True )
	tipo 			= fields.Many2one( 'ariis.tiposuministro', string='Tipo de Suministro', readonly=True, required=True )
	numero			= fields.Integer( string="Numero" , required=True, readonly=True)
	color			= fields.Selection([
									('0', 'Grey'),
									('1', 'Black'),
									('2', 'Yellow'),
									('3', 'Magenta'),
									('4', 'Cyan'),
									('5','Grey')], string='Color', copy=False, default='0' , required=True, readonly=True)
	product_suministro	= fields.Many2one( 'product.product', string='Producto Propuesto', readonly=False, required=False )
	product_original	= fields.Many2one( 'product.product', string='Producto Original', readonly=False, required=False )
	#========================================================================
	def create_from_suministro(self ,oSuministro):
		
		# ProductSuministro = self.env['ariis.product.suministro']
 
		aSearch = []
		aSearch.append(('product_id'	,'=',oSuministro.dispositivo_id.product_id.product_tmpl_id.id))
		aSearch.append(('tipo'			,'=',oSuministro.tipo_id.id))
		aSearch.append(('numero'		,'=',oSuministro.numero ))
		aSearch.append(('color'			,'=',oSuministro.color ))
		
		# print(aSearch)
		
		isFound = self.search(aSearch,limit=1)
		
		if not isFound:
			# _logger.info('Creando Product Suministro')
			id= self.create({
						'product_id'	: oSuministro.dispositivo_id.product_id.product_tmpl_id.id,
						'tipo' 			: oSuministro.tipo_id.id,
						'numero'		: oSuministro.numero,
						'color'			: oSuministro.color
						})
			return id
		else:
			# _logger.info('Existe '+str(oSuministro.dispositivo_id.product_id.id))
			return isFound
	#===========================================================================
	#===========================================================================
	def name_get(self):
		
		isOriginal          = False
		isDesdeSuministo    = False

		if self.env.context.get('desde_suministro',False):
			isDesdeSuministo = True
			# _logger.info('Contexto de producto suministro')
			# _logger.info(self.env.context)
			isOriginal = self.env.context.get('is_original',False)

		result = []
		for record in self:
			color   = dict(record._fields['color'].selection).get(record.color) 
			name    = str(record.numero)+" "+record.tipo.name + ' '+color+" "

			if not record.product_suministro and not record.product_original:
				name += "(-Sin Definir-)"
			else:
				if record.product_suministro and record.product_original:
					if isDesdeSuministo:
						if isOriginal:
							name+="("+record.product_original.name+")"
						else:
							name +="("+record.product_suministro.name+")"
					else:
						name += "(- Los 2 Definidos OK-)"
				else:
					if isDesdeSuministo:
						if isOriginal:
							if record.product_original:
								name +="("+record.product_original.name+")"
							else:
								name +="(Producto Original NO definido)"
						else:
							if record.product_suministro:
								name +="("+record.product_suministro.name+")"
							else:
								name +="(producto Propuesto NO definido)"
					else:
						if record.product_original:
							name+="("+record.product_original.name+")"
						else:
							name +="("+record.product_suministro.name+")"
                            
			result.append((record.id, name))

		return result