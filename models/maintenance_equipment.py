# -*- coding: iso-8859-1 -*-
# Copyright 2021 Exo Software, Lda.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import odoo

from datetime import datetime 
from odoo import api, fields, models
from odoo.exceptions import UserError


class MaintenanceEquipment(models.Model):
    _inherit    = ["maintenance.equipment", "image.mixin"]
    _name       = 'maintenance.equipment'
    
    mir				= fields.Boolean( 'Monitorizable', related='product_id.mir',store=True )
    active			= fields.Boolean(default=True )
    iscolor			= fields.Boolean('Color', readonly=True , related='product_id.iscolor')
    isfax			= fields.Boolean('Fax', readonly=True, related='product_id.isfax')
    isscanner		= fields.Boolean('Escaner', readonly=True, related='product_id.isscanner')
    iscopiadora		= fields.Boolean('Copiadora', readonly=True, related='product_id.iscopiadora')
    #=====================
    state			= fields.Selection([
                                    ('0', 'Pte. Sincronizar'),
                                    ('1', 'Volver a Sincronizar'),
                                    ('2', 'Creado'),
                                    ('9', 'Enlazado')], string='Enlace Mir', copy=False, default='0'   )
    log_level		= fields.Selection([
                                    ('DEBUG', 'Depuracion'),
                                    ('ERROR', 'Errores'),
                                    ('INFO', 'Informacion'),
                                    ('WARN', 'Avisos'),
                                    ('OFF', 'Desactivado')], string='Nivel de Log', copy=False, default='OFF'  )
    #=====================
    total_pag		= fields.Integer('Pag. Impresas', readonly=True)
    total_bn		= fields.Integer('Pag. Impr. BW', readonly=True)
    total_color		= fields.Integer('Pg. Impr. Color', readonly=True)
    #=====================
    instalado		= fields.Date('Fecha Instalacion', readonly=True,copy=False)
    last_report		= fields.Datetime('Ultima actividad', readonly=True,copy=False)
    first_report	= fields.Datetime('Primera actividad', readonly=True,copy=False)
    last_tried		= fields.Datetime('Ultimo intento fallido', readonly=True)
    #=====================
    errortext		= fields.Char('Mensaje de error')
    errordesc		= fields.Text('Descripcion del error')
    #=====================
    ariis_id        = fields.Char(string='Ariis Referencia ', index=True )
    nombre          = fields.Char('Nomber de Maquina')
    snmp_port       = fields.Char('Puerto Snmp', default='161' )
    http_port       = fields.Char('Puerto Http', default='80' )
    macaddress      = fields.Char('Direccion Mac', readonly=True,copy=False)
    hostname        = fields.Char('Host Name')
    hostnameleido   = fields.Char( string='HostName leido' )
    ipaddress       = fields.Char('Direccion IP Actual')
    direccion       = fields.Char('Direccion Maquina' ,compute='_get_direccion' ,store=False, index=True)
    localizacion    = fields.Char('Localizacion', readonly=True,copy=False)
    #=====================
    lot_id				= fields.Many2one( 'stock.lot', string='Num. de Serie', help="Products nº de serie",store=True )
    product_id			= fields.Many2one( 'product.product',  related='lot_id.product_id', string='Producto', 
                            index=True ,readonly=True ,store=True )
    estado_id 			= fields.Many2one( 'ariis.estadodispositivo', string='Estado'  )
    monitorizacion_id 	= fields.Many2one( 'ariis.tipomonitorizacion', string='Tipo de Monitorizacion', readonly=False  )
    owner_id			= fields.Many2one('res.partner', string='Propietario' , index=True )
    address_id 			= fields.Many2one( 'res.partner', 'Direccion Cliente' ,domain="[('type', '=', 'other'),('parent_id','=',partner_id)]")
    #===========================================================================
    def name_get(self):
        result = []
        for record in self:
            if record.lot_id and (not record.name or record.name==""):
                name = record.product_id.name +" ("+record.lot_id.name+")"
                result.append((record.id, name))
            else:
                if record.lot_id and record.name:
                    result.append((record.id, record.name+" ("+record.lot_id.name+")"))
                else:
                    result.append(record.id, record.name)
        return result
    #===========================================================================
    def _get_direccion(self):
        if not self.mir==True:
            self.direccion = ""
            return False
        dir_id = False
        for dispositivo in self:
            if dispositivo.address_id:
                dir_id = dispositivo.address_id
            else:
                dir_id = dispositivo.partner_id
        
            if dir_id:
                dispositivo.direccion ="%s - %s - %s" % (dir_id.street, dir_id.zip , dir_id.city )
    #===========================================================================
    def save(self):
        self.write({})
        return
    #===========================================================================
	# getSuministroByNumber(self,numero)
	#===========================================================================
    def getSuministroByNumber(self,numero):
        return self.env['ariis.suministro'].search([('partner_id','=',self.partner_id.id),
                                                    ('dispositivo_id','=',self.id),
                                                    ('state','in',('01','02','99')),
                                                    ('numero','=',numero)],limit=1)
    #===========================================================================
    # getNewSuministroFrom
    #===========================================================================
    def getNewSuministroFrom(self,oSuministroPos):
    
        # _logger.info('getNewSuministroFrom: Inicio') 
        
        vals = {}
        vals['state']				= '01'
        
        vals['partner_id']			= self.partner_id.id
        vals['dispositivo_id']		= self.id
        #vals['product_id']			= self.product_id.id
        vals['lot_id']				= self.lot_id.id
        #vals['monitorizacion_id']	= self.env.ref('ariis.ariis_tipomonitorizacion_01')
        
        vals['ini_fecha']			= self.last_report
        vals['total_pag']			= self.total_pag
        vals['ini_total_pag']		= self.total_pag		
        vals['ini_total_bn']		= self.total_bn
        vals['ini_total_color']		= self.total_color
        
        vals['numero']				= oSuministroPos.numero
        # vals['serialnumber']		= oSuministroPos.serialnumber
        # vals['des'] 				= oSuministroPos.desc
        vals["proveedor"]			= oSuministroPos.proveedor
 
        vals['nivel']				= oSuministroPos.nivel
        vals['color']				= oSuministroPos.color
        vals['tipo_id'] 			= oSuministroPos.tipo_id.id
        
        vals['state']				= '01'
        vals['subestado']			= '01'
        
        # _logger.info('Retornando suministros') 
        
        return self.env['ariis.suministro'].create(vals)
    #===========================================================================
    @api.model
    def write(self, vals):
        if self.mir:
            if not self.image_1920 and self.product_id.image_1920: 
                vals['image_1920']= self.product_id.image_1920
            if not self.serial_no:
                vals['serial_no'] = self.lot_id.name

        return super(MaintenanceEquipment,self).write(vals)