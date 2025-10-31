# -*- coding: iso-8859-1 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import odoo
from datetime import datetime

from odoo import api, fields, models

 

class Suministro(models.Model):
    _name 			= 'ariis.suministro'
    _inherit 		= ['mail.thread']
    _description 	= "Suministro de Dispositivo"
    _order			= "last_report desc"
    #===========================================================================

    modelo 			    = fields.Char(  string='Modelo' , related='dispositivo_id.product_id.name' ,  readonly=True , store=True)
    numeroserie 	    = fields.Char(  string='Numero de Serie' , related='dispositivo_id.lot_id.name' , store=True,  readonly=True)
    proveedor			= fields.Char("ID de Proveedor Suministro" , readonly=True)
    name         		= fields.Char('Nombre de Suministro' , index=True, compute='_compute_name')
    #===========================================================================
    nivel				= fields.Float("Nivel",digits=(3, 2) )
    #===========================================================================
    color				= fields.Selection([
                                    ('0', 'Grey'),
                                    ('1', 'Black'),
                                    ('2', 'Yellow'),
                                    ('3', 'Magenta'),
                                    ('4', 'Cyan'),
                                    ('5','Grey')], string='Color', copy=False, default='0' , required=True)
    porcentaje			= fields.Selection([
                                    ('0', 'Vacio'),
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
                                    ('Listo', 'Listo')], string='Porcentaje', copy=False, default='99'  )
    subestado			= fields.Selection([									
                                    ('01', 'Instalado'),
                                    ('02', 'Solicitado Nuevo (Agotado)'),
                                    ('03', 'En Preparacion'),
                                    ('04', 'Pte. Enviar'),
                                    ('05', 'Enviado'),
                                    ('06', 'Retirado'),
                                    ('07', 'Solicitado Cambio (Defectuoso)'),
                                    ('99','Desconocido')], string='Estado Solicitud', index=True, copy=False, default='01', track_visibility='onchange' )
    state				= fields.Selection([
                                    ('01', 'Operativo'),
                                    ('02', 'Con Fallo'),
                                    ('03', 'Sustituido'),
                                    ('99', 'Desconocido')], index=True, string='Situacion', copy=False, default='01' , track_visibility='onchange'  )
    #===========================================================================
    total_pag			= fields.Integer('Pag. Impresas', readonly=True)
    numero				= fields.Integer( string="Numero" , required=True)
    ini_total_pag		= fields.Integer('Fin Tot. Pag. Impresas', readonly=True)
    ini_total_bn		= fields.Integer('Fin Tot. Pag. Mono', readonly=True)
    ini_total_color		= fields.Integer('Fin Tot. Pag. Color', readonly=True)
    fin_total_pag		= fields.Integer('Fin Tot. Pag. Impresas', readonly=True)
    fin_total_bn		= fields.Integer('Fin Tot. Pag. Mono', readonly=True)
    fin_total_color		= fields.Integer('Fin Tot. Pag. Color', readonly=True)
    #===========================================================================
    last_report			= fields.Datetime('Ultima actividad', track_visibility='onchange' )
    ini_fecha			= fields.Datetime('Instalado suministro', readonly=True)
    fin_fecha			= fields.Datetime('Retirado suministro', readonly=True)
    last_send			= fields.Datetime( string='Ultimo Envio', track_visibility='onchange' , readonly=False)
    #===========================================================================
    is_bloqueado		= fields.Boolean( string='Cliente bloqueado', related='partner_id.is_bloqueado',store=False,copy=False,readonly=True)
    suministro_original	= fields.Boolean('Suministros Orig.', related='dispositivo_id.suministro_original',readonly=True,copy=False, store=False)
    #===========================================================================
    monitorizacion_id 	= fields.Many2one( 'ariis.tipomonitorizacion', string='Tipo de Monitorizacion', readonly=True )
    lot_id 				= fields.Many2one( 'stock.lot', 'Num. de Serie', related='dispositivo_id.lot_id' ,  index=True, readonly=True)
    tipo_id 			= fields.Many2one( 'ariis.tiposuministro', string='Tipo de Suministro', readonly=False, required=True )
    partner_id			= fields.Many2one('res.partner', change_default=True, string='Cliente' , index=True , readonly=True , required=True  )
    dispositivo_id      = fields.Many2one( 'maintenance.equipment', string='Dispositivo' , required=True ,index=True , store=True ,  readonly=True)
    product_suministro 	= fields.Many2one( 'ariis.product.suministro', string='Producto Asociado', readonly=True, required=False )
    stock_picking		= fields.Many2one( 'stock.picking', string='Orden de entrega', readonly=True, required=False )
    product_template	= fields.Many2one(  string='Template' , related='dispositivo_id.product_id.product_tmpl_id' , store=True)
    #===========================================================================
    #delivery_count		= fields.Integer(string='Delivery Orders', compute='_compute_picking_ids')
    # sustituidos			= fields.One2many( 'ariis.suministro','dispositivo_id' , domain=[('state','=','03'),()] ,string='Suministros Sustituidos' ,copy=False)
    
    # @api.depends('picking_ids')
    # def _compute_picking_ids(self):
        # for order in self:
            # order.delivery_count = len(order.picking_ids)
            
    def _compute_name(self):
        for suministro in self:
            dispositivo = suministro.dispositivo_id 
            suministro.name = dispositivo.lot_id.name+" - "+suministro.tipo_id.name+" - "+dict(self._fields['color'].selection).get(suministro.color) 
    #===========================================================================
    def crea_producto_suministro(self): 
        ProductSuministro = self.env['ariis.product.suministro']
        self.product_suministro=ProductSuministro.create_from_suministro(self).id
        # _logger.info('Product Suministro creado '+str(self.product_suministro))
    #===========================================================================
    def action_retirar(self):  
        return self.write({'subestado':'01' , 'stock_picking' : False}) 
    #===========================================================================
    def action_notificar(self):  
        return self.write({'subestado':'03'})
    #===========================================================================
    def action_preparado(self):  
        return self.write({'subestado':'04'})
    #===========================================================================
    # onchange_partner_id
    #===========================================================================
    @api.onchange('partner_id')
    def onchange_partner_id(self):
        
        if not self.partner_id:
            return

        partner = self.partner_id
        if not partner.is_bloqueado:
            return
            
        warning = {}
        title = ("Ariis: Aviso para %s") % partner.name
        message = "Cliente bloqueado no permite solicitar Suministro"
        warning = { 'title': title, 'message': message }
        self.update({'partner_id': False })

        return {'warning': warning }
    #===========================================================================
    # save
    #===========================================================================
    def save(self):
        self.write({})
        return
    #===========================================================================
    # isSolicitado
    #===========================================================================
    def isSolicitado(self):
        return (self.subestado=='02')
    #===========================================================================
    # isNumeric
    #===========================================================================
    def isNumeric(value):
        return str(value).isdigit()
    #===========================================================================
    # isMayor
    #===========================================================================
    def isMayor(self,nNivel):
        return ( self.nivel < nNivel )
    #===========================================================================
    # isToner
    #===========================================================================
    def isToner(self):
        return (self.tipo_id==self.env.ref('ariis_mir.ariis_tiposuministro_3'))
    #===========================================================================
    # isTambor
    #===========================================================================
    def isTambor(self):
        return (self.tipo_id==self.env.ref('ariis_mir.ariis_tiposuministro_9'))
    #===========================================================================
    # solicita
    #===========================================================================
    def solicita(self):
        self.action_solicita()
    #===========================================================================
    def isConsumible(self):
        return self.tipo_id.isConsumible
        # isEsperandoCambio
    #===========================================================================
    def isEsperandoCambio(self):
        self.crea_producto_suministro()
        return (self.subestado in ('02','03','04','05','07'))
    #===========================================================================
    def action_solicita(self):  
    
        self.checkIsConsumible()
        
        self.crea_producto_suministro()
        self.write({'subestado':'02'}) 
        warning = { 'title': 'Solicitar Suministro (por Agotado)', 'message': 'Solicitado OK' }
        return {'warning': warning }
    #===========================================================================
    def action_solicita_defectuoso(self):  
    
        self.checkIsConsumible()
        
        self.crea_producto_suministro()
        self.write({'subestado':'07'}) 
        warning = { 'title': 'Solicitar Suministro (por Defectuoso)', 'message': 'Solicitado OK' }
        
        return {'warning': warning }
    #===========================================================================
    #===========================================================================
    # isSolicitado
    #===========================================================================
    def isSolicitado(self):
        return (self.subestado in ('02','07'))
    #===========================================================================
    # isEsperandoCambio
    #===========================================================================
    def isEsperandoCambio(self):
        self.crea_producto_suministro()
        return (self.subestado in ('02','03','04','05','07'))
    #===========================================================================
    def isNivelMenor(self,nNivel):
    
        if self.isBoteResidual():
            nivel = (100-self.nivel)
            return (nivel<=nNivel)
            
        return ( self.nivel < nNivel )
    #===========================================================================
    def action_notificar(self): 
        
        self.checkIsConsumible()
        
        self.crea_producto_suministro()
        
        if not self.isProductSuministro():
        
            sText = "el producto "
            sText+= "original" if self.isOriginal() else "propuesto"
            raise UserError('Notificar no se puede realizar. Antes defina %s para este tipo de suministro' % sText)
        
        self.crea_orden_entrega()
        
        return self.write({'subestado':'03'})
    #===========================================================================
    def getLineaDesc( self ,sName , sOrigen ):

        desc = sName+' para (S/N:'+sOrigen+') ' 
        desc += "Num: "+str(self.numero)+" "
        desc += dict(self._fields['color'].selection).get(self.color) +" "+self.tipo_id.name 

        return desc
    #===========================================================================
    def crea_orden_entrega(self):
    
        self.checkIsConsumible()
        
        origen = self.dispositivo_id.lot_id.name
        
        ClsStockPicking = self.env["stock.picking"]
        
        aSearch = []
        
        aSearch.append(('origin','=',origen))
        aSearch.append(('state','not in',('done','cancel')))
        
        oPicking = ClsStockPicking.search(aSearch,limit=1)
        #=====================================================
        if not oPicking:
        
            default_picking  = self.env['ir.config_parameter'].get_param("ariis.stock_picking_type", '').strip()
            
            if default_picking=="":
                raise UserError('Picking por defecto no definido')
        
            oPickingType = self.env['stock.picking.type'].browse(int(default_picking))
 
            if self.dispositivo_id.address_id:
                address_id = self.dispositivo_id.address_id.id
            else:
                address_id = self.dispositivo_id.partner_id.id
                
            oPicking = ClsStockPicking.create({
                            # 'company_id' : 1 ,
                            'partner_id'        : address_id,
                            'location_id'       : oPickingType.default_location_src_id.id ,
                            'location_dest_id'  : oPickingType.default_location_dest_id.id ,
                            'origin'            : origen ,
                            'picking_type_id'   : oPickingType.id ,
                            'move_type'         : 'one',
                            'priority'          : '1',
                            'state'             : 'waiting',
                            'scheduled_date'    : datetime.today()
                        })
            
            
            
            _logger.info('Stock Piking creado para  S/N: '+origen)
        #=====================================================
        self.stock_picking =oPicking.id

        oProduct = self.getProducto()
 
        stock_move = {
                        'company_id'        : oPicking.company_id.id ,
                        'product_id'        : oProduct.id,
                        'picking_id'        : oPicking.id ,						
                        'location_id'       : oPicking.location_id.id ,
                        'location_dest_id'  : oPicking.location_dest_id.id ,
                        'product_uom_qty'   : 1,
                        'product_uom'       : 1, 
                        'name'              : self.getLineaDesc( oProduct.name, origen )
                    }
        
        self.env['stock.move'].create(stock_move)
        
        oPicking.action_confirm()
    #===========================================================================
    def getProducto(self):
    
        if not self.product_suministro:
            return False
 
        if self.isOriginal():
            if self.product_suministro.product_original:
                return self.product_suministro.product_original
        else:
            if self.product_suministro.product_suministro:
                return self.product_suministro.product_suministro
        return True
    #===========================================================================
    def isProductSuministro(self):
    
        if not self.product_suministro:
            return False
 
        if self.isOriginal():
            if not self.product_suministro.product_original:
                return False
        else:
            if not self.product_suministro.product_suministro:
                return False
        return True
    #===========================================================================
    def getSuministroName(self):
        oProduct = self.getProducto()
        return self.getLineaDesc(oProduct.name , self.dispositivo_id.lot_id.name )
    #===========================================================================
    def action_preparado(self):  

        if not self.stock_picking:
            self.action_solicita()
            raise UserError('Picking no existe')
            
        if self.stock_picking.state not in ('assigned','done'):
            raise UserError('No es posible marcar el suministro como Preparado, Su orden de entrega debe estar Preparada o Hecha')
            
        return self.write({'subestado':'04'})
    #===========================================================================
    def action_enviado(self):

        if not self.stock_picking:
            self.action_solicita()
            raise UserError('Picking no existe')
            
        if self.stock_picking.state not in ('done'):
            raise UserError('No es posible marcar el suministro como Enviado, la Orden de Entrega no esta Hecha')
            
        return self.write({'subestado':'05' ,'last_send':datetime.today()})
    #===========================================================================
    # isSolicita
    #===========================================================================
    def isSolicita(self,nMin):
        
        if not self.isConsumible():
            return False
        if not self.subestado in ('01','99'):
            return False
        
        #=================================================
        # Waste Toner box
        # Los botes residuales se cambian cuando estan llenos (100%)
        # con lo que solicitarlo es al reves
        #===========================================================
        # if self.isBoteResidual():
            # nivel = (100-self.nivel)
            # return (nivel<=nMin)
            
        return (self.nivel<=nMin)
    #===========================================================================
    #===========================================================================
    def isConsumible(self):
        return self.tipo_id.isConsumible
    #===========================================================================
    # Si es Waste Toner box
    #===========================================================================
    def isBoteResidual(self):
        return (self.tipo_id==self.env.ref("ariis_mir.ariis_tiposuministro_4"))
    #===========================================================================
    def show_picking(self):
        
        self.ensure_one()
        domain = [ ('partner_id', '=', self.partner_id.id ), ( 'origin', 'ilike', self.lot_id.name ) ]
        
        # _logger.info('Suministro Contexto: %s' % domain )
        
        return {
            'name': 'Envios de Suministros de ' + self.lot_id.name,
            'domain': domain,
            'res_model': 'stock.picking',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'view_mode': 'tree,form',
            'view_type': 'form',
            'limit': 80,
             }
    #===========================================================================
    def isOriginal(self):
        return self.suministro_original
    #===========================================================================
    def search_last_picking(self):

        if not self.isProductSuministro():
            self.last_send = False
            raise UserError("Producto de Suministro no definido")
            
        aSearch = []
        # aSearch.append(('partner_id', '='		, self.partner_id.id ))
        aSearch.append(('name'	, '='	, self.getSuministroName() ))
        aSearch.append(('state'	, '='	, 'done' ))
        
        oFound = self.env['stock.move'].search( aSearch,limit=1,order='date_expected desc')
        
        if oFound:
            self.last_send = oFound.picking_id.date_done
        else:
            self.last_send = False
    #===========================================================================
    def action_set_product(self):
        self.crea_producto_suministro()
    #===========================================================================
    def checkIsConsumible(self):
        if not self.isConsumible():
            raise UserError('Accion No permitida. Suministro NO esta definido como Consumible')