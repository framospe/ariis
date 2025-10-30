# -*- coding: iso-8859-1 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import odoo
from odoo import api, fields, models
from odoo.exceptions import UserError


class ProductTemplate(models.Model):
    _inherit = ['product.template']
 
    ariis_id		= fields.Char(string='Ariis Referencia', readonly=True ,index=True,copy=False)
    mir				= fields.Boolean(string="Monitorizable" , readonly=True ,default=False ,copy=False )
    blogpost_id		= fields.Integer("Post ID", readonly=True )
    # analytic_tag_id = fields.Many2one('account.analytic.tag', string='Analytic tag',copy=False)
    iscolor			= fields.Boolean('Color', readonly=True,copy=False)
    isfax			= fields.Boolean('Fax', readonly=True,copy=False)
    isscanner		= fields.Boolean('Escaner', readonly=True,copy=False)
    iscopiadora		= fields.Boolean('Copiadora', readonly=True,copy=False)
    department_sat	= fields.Many2one('hr.department', string='Departamento S.A.T')
    image			= fields.Binary( 'Imagen')
    rental 			= fields.Char( 'No Se')

    #===========================================================================
    @api.model
    def write(self, vals):
        if not self.image_1920 and self.image: 
            vals['image_1920']= self.image
        return super(ProductTemplate,self).write(vals)