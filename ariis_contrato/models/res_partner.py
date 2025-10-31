# -*- coding: iso-8859-1 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

 
import logging

import odoo
import base64
from odoo import api, fields, models
from datetime import datetime 
from odoo.exceptions import UserError
from odoo.addons.base.models.res_partner import WARNING_MESSAGE, WARNING_HELP

_logger = logging.getLogger(__name__)

class Partner(models.Model):
    _inherit = 'res.partner'
 
    contrato_ids        = fields.One2many( 'ariis.contrato' , 'partner_id', 'Contratos'  ) 
    #===========================================================================
    contrato_ids_count  = fields.Integer(string="Contratos", compute='_compute_contratos_count')
    #===========================================================================
    def _compute_contratos_count(self):
        for partner in self:
            if partner.contrato_ids:
                partner.contrato_ids_count= len(partner.contrato_ids)
            else:
                 partner.contrato_ids_count= 0
    #===========================================================================