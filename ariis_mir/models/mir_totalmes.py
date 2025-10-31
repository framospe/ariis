# -*- coding: iso-8859-1 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import odoo
import logging
import dateutil.relativedelta

from odoo import api, fields, models
from datetime import datetime 
from odoo.exceptions import UserError

I_MESES = "NoSale,Enero,Febrero,Marzo,Abril,Mayo,Junio,Julio,Agosto,Septiempre,Octubre,Noviembre,Diciembre"

_logger = logging.getLogger(__name__)

class TotalMes(models.Model):
    _name         = 'ariis.total.mes'
    _inherit        = ['mail.thread', 'mail.activity.mixin']
    _description  = "Total Mes"
    _order        = "ini_periodo"
    
    def _get_value_crear(self):
        oConfg = self.env['ir.config_parameter'].sudo()
        self.update({ 'crear' :  oConfg.get_param('ariis.totalmes_create') })
    #===========================================================================
    creado				= fields.Datetime( string='Creado' , index=True)
    last_report			= fields.Datetime('Ultima actividad', readonly=True)
    #=====================
    periodo				= fields.Date( string='Periodo' , index=True)
    ini_periodo			= fields.Date( string='Inicio Periodo' , index=True)
    fin_periodo			= fields.Date( string='Fin Periodo'  )
    #=====================
    ini_total_pag_color	= fields.Integer( string='Inicio Color' )
    ini_total_pag_bn	= fields.Integer( string='Inicio B/N' )
    fin_total_pag_color	= fields.Integer( string='Fin Color' )
    fin_total_pag_bn	= fields.Integer( string='Fin B/N' )
    #=====================
    lecturas			= fields.One2many( 'ariis.lectura' ,string='Lecturas' ,copy=False ,inverse_name='totalmes')
    #=====================
    tratado				= fields.Boolean( string='Tratado' )
    iscolor				= fields.Boolean('Color', readonly=True , related='dispositivo.iscolor')
    # iscolor					= fields.Boolean('"Color Ufff', readonly=True   )
    # anual				= fields.Boolean('Factura Acumulativa' , related='contrato_line.contrato_id.tipo_id.anual', copy=False, readonly=False)
    #=====================
    errortext			= fields.Char('Mensaje de error')
    errordesc			= fields.Char('Descripcion del error')
    #=====================
    name				= fields.Char( string='Nombre')
    crear				= fields.Char('Crea Factura' , compute='_get_value_crear' )
    #=====================
    cliente 			= fields.Many2one( 'res.partner', 'Cliente' , index=True  )
    dispositivo			= fields.Many2one( 'maintenance.equipment', string='Dispositivo'   ,index=True  )
    order				= fields.Many2one( 'sale.order', 'Presupuesto' , index=True  )
    lot_id				= fields.Many2one( 'stock.lot', related='dispositivo.lot_id', string='Serial Number' ,  store=True ,index=True  )
    factura				= fields.Many2one( 'account.move', 'Factura' , index=True  )
    #=====================
    aMeses = I_MESES.split(',')

    oProductRefs = {}
    oProductTaxs = {}
    oProductos   = {}
    #===========================================================================
    # runfromUI
    #===========================================================================
    def runfromUI(self):

        # if not 'ariis.product_ariis_cx_mono' in self.oProductos:
            # self.load()

        for oTot in self:
            oTot.runEntry()
    #===========================================================================
    def runEntry(self):
        # _logger.info('==================')
        # _logger.info('Iniciando runEntry ')

        self.errortext = "OK"
        self.errordesc = ""
        
        if self.isValid(): 
            self.preProcesa()
            self.procesa()
            self.postProcesa()
        else:
            self.notValid()
            
        # _logger.info('Fin runEntry ')
    #===========================================================================
    def load(self):

        self.oProductRefs   = {}
        self.oProductTaxs   = {}
        self.oProductos     = {}

        aProducts   = []
        
        aProducts.append('ariis.product_ariis_cx_mono')
        aProducts.append('ariis.product_ariis_cx_color')
        aProducts.append('ariis.product_ariis_cx_pro_mono')
        aProducts.append('ariis.product_ariis_cx_pro_color')

        for sRef in aProducts:
            o = self.getProductoByRef(sRef)

            self.oProductos[sRef] = {
                'ref'       : sRef,
                'id'        : o.id ,
                'obj'       : o ,
                'name'      : o.name ,
                'uom_id'    : o.uom_id.id,
                'leyenda'   : o.description_sale,
                'taxes'     : self.getProductoTaxes(sRef)
            }

            # _logger.info(self.oProductos[sRef])
    #===========================================================================
    def volveratratartotalmes(self):
    
        self.load()

        for lectura in self:
            lectura.runEntry()
    #===========================================================================
    def tratartotalmes(self):
    
        registros = self.search([('tratado','=',False)])
        
        # self.load()
        if len(registros)>0:
        
            _logger.info('==================================================================' )
            _logger.info('INICIO de proceso de tratar Totales Mes')
            
            for lectura in registros:
                lectura.runEntry()
        
            _logger.info('FIN de proceso de tratar Totales Mes')
            _logger.info('==================================================================' )
    #===========================================================================
    def sortLectura(lectura):
        return lectura.create_date
    #===========================================================================
    # isValid
    #===========================================================================
    def isValid(self):
        return (True)
    #===========================================================================
    # preProcesa
    #===========================================================================
    def preProcesa(TotalMes):
    
        lecturas = TotalMes.lecturas
        
        # _logger.info('Len %s' % len(lecturas) )
        #.sort(key = sortLectura )
        
        for oLectura in lecturas:
        
            # _logger.info('Procesa lectura del %s' % oLectura.create_date )
            
            if oLectura.state =='02':
                continue
            
            oLectura.errortext	= ""
            oLectura.errordesc	= ""
            oLectura.state		='02'
            #============================================================
            # Ver si la lectura anterior es mas vieja que la del totalmes
            #============================================================
            if oLectura.previo_lectura < TotalMes.ini_periodo:
            
                if oLectura.previo_total_bn > TotalMes.ini_total_pag_bn or oLectura.previo_total_color > TotalMes.ini_total_pag_color:
                    
                    oLectura.state		='03'
                    #oLectura.tratada	= True
                    oLectura.errortext	= "Datos Incorrectos"
                    oLectura.errordesc	= "Lecturas Erroneas (Total previo mayor que lectura actual)"
                    oLectura.save()
                    
                    TotalMes.errortext = "Datos Incorrectos"
                    TotalMes.errordesc = "Lecturas Erroneas (Total previo mayor que lectura actual)"
                    
                    return
                else:
                    TotalMes.ini_periodo			= oLectura.previo_lectura
                    TotalMes.ini_total_pag_bn		= oLectura.previo_total_bn
                    TotalMes.ini_total_pag_color	= oLectura.previo_total_color
                    
            if oLectura.actual_lectura >= TotalMes.fin_periodo:
                
                if oLectura.actual_total_bn < TotalMes.fin_total_pag_bn or oLectura.actual_total_color < TotalMes.fin_total_pag_color:
                    
                    oLectura.state		='03'
                    #oLectura.tratada	= True
                    oLectura.errortext	= "Datos Incorrectos"
                    oLectura.errordesc	= "Lecturas Erroneas (Total menor que anterior lectura)"
                    oLectura.save()
                    
                    TotalMes.errortext = "Datos Incorrectos"
                    TotalMes.errordesc = "Lecturas Erroneas (Total menor que anterior lectura)"
                    
                    return
                else:
                    TotalMes.fin_periodo			= oLectura.actual_lectura
                    TotalMes.fin_total_pag_bn		= oLectura.actual_total_bn
                    TotalMes.fin_total_pag_color	= oLectura.actual_total_color
            
                    oLectura.state='02'
                
            # oLectura.tratada = True
            oLectura.save()
        
        return 
    #===========================================================================
    # procesa
    #===========================================================================
    def procesa(TotalMes):
        
        # _logger.info('Procesa')
        
        oContrato = TotalMes.contrato_line
 
        if not oContrato or oContrato.partner_id.id != TotalMes.cliente.id or  oContrato.dispositivo_id.id != TotalMes.dispositivo.id:
        
            aSearch = []
            
            aSearch.append(('dispositivo_id'    ,'=',TotalMes.dispositivo.id))
            aSearch.append(('contrato_id.state' ,'=','1'))
            aSearch.append(('partner_id.id'     ,'=',TotalMes.cliente.id))

            
            oContrato = TotalMes.env['contract.line.ariis'].search(aSearch,limit=1)
        
        if not oContrato:	
            TotalMes.errortext = "Datos Incorrectos"
            TotalMes.errordesc = "Contrato No Encontrado"
            
            TotalMes.notificaMir( 'Contrato de dispositivo [%s] no encontrado' % TotalMes.dispositivo.lot_id.name )
    
            return
            
        TotalMes.contrato_line = oContrato 
        
        if oContrato.precio_bn <=0:
            TotalMes.errortext = "Datos Incorrectos"
            TotalMes.errordesc = "Precio Blanco/Negro no es valido"
            return
        
        if oContrato.dispositivo_id.iscolor and oContrato.precio_color <=0:
            TotalMes.errortext = "Datos Incorrectos"
            TotalMes.errordesc = "Precio Color no es valido"
            return
            
        if not TotalMes.dispositivo.contrato_line:
            TotalMes.dispositivo.contrato_line = oContrato.id
            TotalMes.dispositivo.write({})
            
        return
    #===========================================================================
    # postProcesa
    #===========================================================================
    def postProcesa(self):
    
        # _logger.info('postProcesa : %s' % self.errortext)
        # oConfg = self.env['ir.config_parameter'].sudo()

        # if self.errortext=='OK':
            # if oConfg.get_param('ariis.totalmes_create')=="01":
                # self.createOrder()
            # else:
                # self.createFactura()

        # self.write( { 'tratado' : True , 'last_report': fields.Datetime.now() })
        
        return
    #===========================================================================
    # notValid
    #===========================================================================
    def notValid(self):
        return
    #===========================================================================
    # save
    #===========================================================================
    def save(self):
        return self.write({})
    #===========================================================================
    def createOrder(self):
    
        oClssSale = self.env['sale.order']

        aFechas = fields.Date.to_string(self.periodo).split('-')
        aSearch = []
        
        #_logger.info('Contarto tarifa Plana : %s' % str(self.anual))
        
        #TODO
        # if self.anual:
            
            # sOrigen = aFechas[0]+"/"+str(self.cliente.id)
        # else:
            # sOrigen = aFechas[0]+"/"+aFechas[1]+"/"+str(self.cliente.id)
        
        aSearch.append( ('partner_id','=',self.cliente.id) )
        aSearch.append( ('origin','=',sOrigen ) )
        
        oOrder = oClssSale.search(aSearch,limit=1)
    
        if not oOrder:

            oOrder = oClssSale.with_context({'mail_create_nosubscribe':True,'tracking_disable':True}).create({
                                        'partner_id'		: self.cliente.id ,
                                        'origin'			: sOrigen ,
                                        'confirmation_date'	: self.periodo ,
                                        'user_id'			: self.cliente.user_id.id ,
                                        'date_order'		: self.periodo ,
                                        'state'				: 'draft'
                                    })
        self.order = oOrder
        
        #crear linea
        self.creaLinea(  self.getValuesLineaMono(oOrder) )
            
        if self.dispositivo.iscolor:
            self.creaLinea(  self.getValuesLineaColor(oOrder) )
    
        oContrato = self.contrato_line
        if oContrato.promocion not in ('01','04'): 
            return
        
        if oContrato.pag_pro_bn>0 and oContrato.fecha_fin_pro_bn:
            if oContrato.fecha_fin_pro_bn >=fields.Date.today():
                self.creaLinea(  self.getValuesLineaPromoBN(oOrder) )
            
        if oContrato.pag_pro_color>0 and oContrato.fecha_fin_pro_color:
            if oContrato.fecha_fin_pro_color >=fields.Date.today():
                self.creaLinea(  self.getValuesLineaPromoColor(oOrder) )
    #===========================================================================
    def getValuesLineaMono(self,oOrder):
    
        vals = {}
        vals['name']			= 'Coste X Copia MONOCROMO %s (%s) %s' % (self.dispositivo.product_id.name,self.dispositivo.lot_id.name , self.getMes(oOrder.date_order))
        vals['order_id']		= oOrder.id
        vals['price_unit']		= self.contrato_line.precio_bn
        vals['product_uom_qty']	= self.fin_total_pag_bn - self.ini_total_pag_bn
        vals['qty_delivered']	= vals['product_uom_qty']
        
        vals['product_id']		= self.env['product.product'].search([('name','=','Coste X Copia MONO')],limit=1).id
 
        return vals
    #===========================================================================
    def getLineaOrder(self,vals):
        
        # _logger.info('Buscando %s' % vals['name'] )
        
        aSearch = []
        aSearch.append(('name','=',vals['name']))
        aSearch.append(('order_id','=',vals['order_id']))
        aSearch.append(('product_id','=',vals['product_id']))
        
        return self.env['sale.order.line'].search(aSearch ,limit=1)
    #===========================================================================
    def getValuesLineaColor(self,oOrder):
    
        vals = {}
        vals['name']			= 'Coste X Copia COLOR %s (%s) %s' %  (self.dispositivo.product_id.name ,self.dispositivo.lot_id.name , self.getMes(oOrder.date_order))
        vals['order_id']		= oOrder.id
        vals['price_unit']		= self.contrato_line.precio_color
        vals['product_uom_qty']	= self.fin_total_pag_color - self.ini_total_pag_color
        vals['qty_delivered']	= vals['product_uom_qty']
        vals['product_id']		= self.env['product.product'].search([('name','=','Coste X Copia COLOR')],limit=1).id
 
        return vals
    #===========================================================================
    def creaLinea(self,oValues):
    
        oClssSaleLine = self.env['sale.order.line']
        oLinea = self.getLineaOrder(oValues)
        
        if oLinea:
            oLinea.update(oValues)
        else:
            oClssSaleLine.create( oValues)
    #===========================================================================
    def getValuesLineaPromoBN(self,oOrder):
    
        vals = {}
        vals['name']			= 'PROMOCION MONOCROMO %s (%s) (%s pag.)' %  (self.dispositivo.product_id.name ,self.dispositivo.lot_id.name ,str(self.contrato_line.pag_pro_bn))
        vals['order_id']		= oOrder.id
        vals['price_unit']		= -(self.contrato_line.precio_bn)		
        vals['product_uom_qty']	= self.fin_total_pag_bn - self.ini_total_pag_bn
        
        if self.contrato_line.pag_pro_bn <= vals['product_uom_qty']:
            vals['product_uom_qty']	= self.contrato_line.pag_pro_bn
            
        vals['qty_delivered']	= vals['product_uom_qty']
        vals['product_id']		= self.env['product.product'].search([('name','=','Coste X Copia PROMOCION')],limit=1).id
 
        return vals
    #===========================================================================
    def getValuesLineaPromoColor(self,oOrder):
    
        vals = {}
        vals['name']			= 'PROMOCION COLOR %s (%s) (%s pag.)' %  (self.dispositivo.product_id.name ,self.dispositivo.lot_id.name,str(self.contrato_line.pag_pro_color))
        vals['order_id']		= oOrder.id
        vals['price_unit']		= -(self.contrato_line.precio_color)		
        vals['product_uom_qty']	= self.fin_total_pag_color - self.ini_total_pag_color
        
        if self.contrato_line.pag_pro_color <= vals['product_uom_qty']:
            vals['product_uom_qty']	= self.contrato_line.pag_pro_color
            
        vals['qty_delivered']	= vals['product_uom_qty']
        vals['product_id']		= self.env['product.product'].search([('name','=','Coste X Copia PROMOCION')],limit=1).id
 
        return vals
    #===========================================================================
    #===========================================================================
    # def name_get(self):
        # result = []
        # for record in self:
            # name =   str(record.periodo) +  ' (' + record.dispositivo.lot_id.name+')'
            # result.append((record.id, name))
        # return result
    #===========================================================================
    #===========================================================================
    def crear_contrato(self):

        ctx = {
            'default_model'				: 'ariis.contrato',
            'default_dispositivo_id'	: self.dispositivo.id,
            'default_partner_id'		: self.cliente.id ,
            'default_tipo_id'			: self.env.ref('ariis.ariis_contrat_02').id ,
            'default_state'				: '1'  
        }
        
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'ariis.contrato',
            'src_model': 'ariis.total.mes' ,
            'multi': False,
            'target': 'current',
            'context': ctx,
        }
    #===========================================================================
    def add_to_contrato(self):
    
        # aDomain = []
        
        # aDomain.append(('partner_id','=',self.cliente.id))
        # aDomain.append(('state','=','1'))
        
        oContrato = self.env['ariis.contrato'].search([('partner_id','=',self.cliente.id),('state','=','1')] ,limit=1)
        
        if not oContrato:
            raise UserError("No existe ningun contrato vigente para este cliente")
            
        ctx = {
            'default_model'				: 'ariis.contrato_line',
            'default_dispositivo_id'	: self.dispositivo.id, 
            'default_cliente'			: self.cliente.id,
            'default_contrato_id'		: oContrato.id 
        }
        
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'ariis.contrato_line',
            'src_model': 'ariis.total.mes' ,
            'multi': False,
            'target': 'current',
            'context': ctx,
        }
    #===========================================================================
    def notificaMir(self,sMesage):
    
        oMail = self.env['mail.message']
        canal = self.env.ref('ariis.channel_ariis_mir')
        
        values = {	'channel_ids': [(6, 0, [canal.id])] , 
                    'message_type':'notification' , 
                    'subject':sMesage ,
                    'body':sMesage ,
                    }

        oMail.create(values)
    #===========================================================================
    def getMes(self,dFecha):
        
        # if self.anual:
        if True:
            #sMes = dFecha.split('-')[1]
            sMes = dFecha.month
            return self.aMeses[dFecha.month]
        return ""
    #===========================================================================
    def createFactura(self):

        oContrato = self.contrato_line

        if not oContrato.isHasPromo() or oContrato.promocion not in ('01','02','04'): 
            self.errortext = "KO"
            self.errordesc = "Tipo de promocion no valida %s " % oContrato.promocion
            return
        #==========================================================================================
        # Si es promocion tipo 2 entonces solo se crea la factura si el numero de copias
        # actual BN/Color es superior a la indicada en el campo promocion correspondiente
        #==========================================================================================
        if oContrato.promocion == '02':
            if not oContrato.isTotalPrintPromocion02(False ,self.fin_total_pag_bn) and not oContrato.isTotalPrintPromocion02(True ,self.fin_total_pag_color):
                self.errortext = "OK"
                if self.dispositivo.iscolor:
                    self.errordesc = "Se creara factura cuando el dispositivo haya impreso mas de [%s pag. en BN]  o [%s pag. en Color] " % (str(oContrato.pag_pro_bn),str(oContrato.pag_pro_color))
                else:
                    self.errordesc = "Se creara factura cuando el dispositivo haya impreso mas de [%s pag. en BN]" % str(oContrato.pag_pro_bn)
                return

        # _logger.info('Inicio de generar Factura')
        # _logger.info('Es color %s' % str(self.dispositivo.iscolor))

        oClssFactura = self.env['account.invoice']

        date_invoice = self.periodo + dateutil.relativedelta.relativedelta(months=1)
        aFechas = fields.Date.to_string(self.periodo).split('-')
        aSearch = []
        
        if self.anual:
            sOrigen = aFechas[0]+"/"+str(self.cliente.id)
        else:
            sOrigen = aFechas[0]+"/"+aFechas[1]+"/"+str(self.cliente.id)
        
        aSearch.append( ('partner_id','=',self.cliente.id) )
        aSearch.append( ('origin','=',sOrigen ) )
        #============================================================================
        #TODO: Podria no ser la cuenta ya puede estar en la direccion de facturación
        #============================================================================
        account_id  = self.cliente.property_account_receivable_id.id
        oFactura    = oClssFactura.search(aSearch,limit=1)

        if not oFactura:

            oFactura = oClssFactura.with_context({'mail_create_nosubscribe':True,'tracking_disable':True}).create({
                                        'partner_id'		: self.cliente.id ,
                                        'origin'			: sOrigen ,
                                        'type'				: 'out_invoice',
                                        'date_invoice'	    : date_invoice ,
                                        'account_id'        : account_id ,
                                        'user_id'			: self.cliente.user_id.id ,
                                        'state'				: 'draft',
                                        'payment_term_id'	: self.cliente.property_payment_term_id.id,
                                        'payment_mode_id'	: self.cliente.customer_payment_mode_id.id,
                                        'name'				: "CXC "+self.cliente.name+" ( "+self.getMes(self.periodo)+" "+str(self.periodo).split("-")[0]+" )"
                                    })
                                    
        if not oFactura.payment_mode_id and self.cliente.customer_payment_mode_id.id :
            oFactura.payment_mode_id = self.cliente.customer_payment_mode_id.id
                                    
        self.factura = oFactura

        if not 'ariis.product_ariis_cx_mono' in self.oProductos:
            self.load()
        #==========================================
        #Nombre del Mes
        #==========================================
        self.creaLineaFactura(  self.getSeccionFactura(oFactura) )
        #==========================================
        if oContrato.promocion in ('01','04'):
            self.creaLineaFactura(  self.getValuesLineaMonoFactura(oFactura) )

            if self.dispositivo.iscolor:
                self.creaLineaFactura(  self.getValuesLineaColorFactura(oFactura) )
            #==========================================
            #PROMOCION
            #==========================================
            if oContrato.pag_pro_bn>0 and oContrato.fecha_fin_pro_bn:
                if oContrato.fecha_fin_pro_bn >=fields.Date.today():
                    self.creaLineaFactura(  self.getValuesLineaPromoBNFactura(oFactura) )

            if self.dispositivo.iscolor and oContrato.pag_pro_color>0 and oContrato.fecha_fin_pro_color:
                if oContrato.fecha_fin_pro_color >=fields.Date.today():
                    self.creaLineaFactura(  self.getValuesLineaPromoColorFactura(oFactura) )
        else:
            #==========================================================================================
            # Si es promocion tipo 2 entonces solo se crea la lineas de factura si el numero de copias
            # actual del BN o Color es superior a la indicada en el campo promocion correspondiente
            #==========================================================================================
            if oContrato.isTotalPrintPromocion02(False,self.fin_total_pag_bn):
                self.creaLineaFactura( self.getValuesLineaMonoFactura(oFactura) )

            if self.dispositivo.iscolor and oContrato.isTotalPrintPromocion02(True,self.fin_total_pag_color):
                self.creaLineaFactura( self.getValuesLineaColorFactura(oFactura) )

        oFactura.compute_taxes()
        _logger.info('Factura creada' )
    #===========================================================================
    def getLineaFactura(self,vals):
        
        _logger.info('Buscando linea' )
        
        aSearch = []
        
        aSearch.append(('invoice_id','=',vals['invoice_id']))

        if not vals['display_type']:
            aSearch.append(('product_id','=',vals['product_id']))
            aSearch.append(('lot_id','=',oValues['lot_id']))
        else:
            aSearch.append(('name' ,'=',vals['name']))
            
        _logger.info('Buscando linea' )
        _logger.info(aSearch)

        oFound = self.env['account.invoice.line'].search( aSearch ,limit=1)
        
        return oFound
    #===========================================================================
    def creaLineaFactura(self,oValues):
    
        oClssInvoiceLine = self.env['account.invoice.line']

        # _logger.info('Creando linea %s' % oValues['name'] )
        # _logger.info( oValues )

        aSearch = []
        # aSearch.append(('name' ,'=',oValues['name']))
        aSearch.append(('invoice_id','=',oValues['invoice_id']))
        
        if not oValues['display_type']:
            aSearch.append(('product_id','=',oValues['product_id']))
            aSearch.append(('lot_id','=',oValues['lot_id']))
        else:
            aSearch.append(('name' ,'=',oValues['name']))
            
        # _logger.info('Buscando linea' )
        # _logger.info(aSearch)
        
        # oLinea = self.getLineaFactura(oValues)
        oLinea = oClssInvoiceLine.search( aSearch ,limit=1)
        
        if oLinea:
            # _logger.info('Ya Existe %s' % oValues['name'] )
            oLinea.update(oValues)
        else:
            # _logger.info('No existe se crea %s' % oValues['name'] )
            oClssInvoiceLine.create( oValues)

    #===========================================================================
    def getProductoByRef( self , sRef ):
        if not sRef in self.oProductRefs:
            self.oProductRefs[sRef] = self.env.ref(sRef) 
        return self.oProductRefs[sRef]
    #===========================================================================
    def getProductoTaxes( self , sRef ):

        if not sRef in self.oProductTaxs:
            oProducto = self.env.ref(sRef)
            if not oProducto.taxes_id:
                _logger.info( "Sin Impuestos : " +sRef )
                self.oProductTaxs[sRef] = False
            else:
                aTaxes = []
                for o in oProducto.taxes_id:
                    aTaxes.append(o.id)
                self.oProductTaxs[sRef] = [[ 6, 0, aTaxes ]]

        return self.oProductTaxs[sRef]
    #===========================================================================
    def _getSequence(self,nPeriodoInit,nPeriodoFin):
    
        aSearch = []
        aSearch.append(('sequence','>',nPeriodoInit))
        aSearch.append(('sequence','<',nPeriodoFin))
        
        oFound = self.env['account.invoice.line'].search(aSearch ,limit=1, order='sequence desc')
        
        if oFound:
            return oFound['sequence']+1

        return nPeriodoInit+1
    #===========================================================================
    def getValuesLineaColorFactura(self,oFactura):
    
        nSecuencia  = (self.periodo.month * 100)
        oProducto   = self.oProductos['ariis.product_ariis_cx_color']
        sName       = oProducto['leyenda']+' %s (%s) %s'

        vals = {}
        vals['name']			= sName %  (self.dispositivo.product_id.name ,self.dispositivo.lot_id.name , self.getMes(self.periodo))
        vals['invoice_id']		= oFactura.id
        vals['price_unit']		= self.contrato_line.precio_color
        vals['quantity']		= self.fin_total_pag_color - self.ini_total_pag_color
        # vals['account_id']	    = oFactura.account_id.id
        vals['account_id']		= self.with_context({'journal_id': oFactura['journal_id'].id,'type':'out_invoice'})._default_account()
        vals['display_type']	= False
        vals['sequence']		= self._getSequence(nSecuencia ,nSecuencia+99 ) 
        vals['product_id']		= oProducto['id']
        vals['lot_id']			= self.lot_id.id
        vals['invoice_line_tax_ids'] = oProducto['taxes']

        return vals
    #===========================================================================
    def getValuesLineaPromoBNFactura(self,oFactura):
    
        nSecuencia = (self.periodo.month * 100)

        oProducto   = self.oProductos['ariis.product_ariis_cx_pro_mono']
        sName		= oProducto['leyenda']+" %s (%s) (%s pag.) %s"

        vals = {}
        vals['name']			= sName %  (self.dispositivo.product_id.name ,self.dispositivo.lot_id.name ,str(self.contrato_line.pag_pro_bn), self.getMes(self.periodo))
        vals['invoice_id']		= oFactura.id
        vals['price_unit']		= -(self.contrato_line.precio_bn)		
        vals['quantity']	    = self.fin_total_pag_bn - self.ini_total_pag_bn
        vals['display_type']	= False
        vals['account_id']		= self.with_context({'journal_id': oFactura['journal_id'].id,'type':'out_invoice'})._default_account()

        
        if self.contrato_line.pag_pro_bn <= vals['quantity']:
            vals['quantity']	= self.contrato_line.pag_pro_bn
            
        # vals['qty_delivered']	= vals['product_uom_qty']
        vals['product_id']		= oProducto['id']
        vals['lot_id']			= self.lot_id.id
        vals['sequence']		= self._getSequence(nSecuencia ,nSecuencia+99 ) 
        
        vals['invoice_line_tax_ids'] = oProducto['taxes']
        
        vals['name'] = vals['name'].strip()
        
        return vals
    #===========================================================================
    def getValuesLineaPromoColorFactura(self,oFactura):
    
        nSecuencia  = (self.periodo.month * 100)
        oProducto   = self.oProductos['ariis.product_ariis_cx_pro_color'] 
        sName       = oProducto['leyenda']+" %s (%s) (%s pag.) %s"
        
        vals = {}
        vals['name']			= sName %  (self.dispositivo.product_id.name ,self.dispositivo.lot_id.name,str(self.contrato_line.pag_pro_color), self.getMes(self.periodo))
        vals['invoice_id']		= oFactura.id
        vals['price_unit']		= -(self.contrato_line.precio_color)		
        vals['quantity']		= self.fin_total_pag_color - self.ini_total_pag_color
        vals['account_id']		= self.with_context({'journal_id': oFactura['journal_id'].id,'type':'out_invoice'})._default_account()

        if self.contrato_line.pag_pro_color <= vals['quantity']:
            vals['quantity']	= self.contrato_line.pag_pro_color
            
        vals['display_type']	= False
        vals['product_id']		= oProducto['id']
        vals['lot_id']			= self.lot_id.id
        vals['sequence']		= self._getSequence(nSecuencia ,nSecuencia+99 ) 

        vals['invoice_line_tax_ids'] = oProducto['taxes']
        vals['name'] = vals['name'].strip()
        
        return vals
    #===========================================================================
    def getValuesLineaMonoFactura(self,oFactura):
    
        nSecuencia  = (self.periodo.month * 100)
        oProducto   = self.oProductos['ariis.product_ariis_cx_mono']
        sName       = oProducto['leyenda']+" %s (%s) %s"

        vals = {}
        vals['name']			= sName % (self.dispositivo.product_id.name,self.dispositivo.lot_id.name , self.getMes(self.periodo) )
        vals['invoice_id']		= oFactura.id
        vals['price_unit']		= self.contrato_line.precio_bn
        vals['quantity']		= self.fin_total_pag_bn - self.ini_total_pag_bn
        # vals['account_id']	    = oFactura.account_id.id
        vals['display_type']	= False
        vals['sequence']		= self._getSequence(nSecuencia ,nSecuencia+99 ) 
        vals['product_id']		= oProducto['id']
        vals['lot_id']			= self.lot_id.id
        vals['account_id']		= self.with_context({'journal_id': oFactura['journal_id'].id,'type':'out_invoice'})._default_account()
        vals['invoice_line_tax_ids'] =  oProducto['taxes']

        return vals
    #===========================================================================
    def _default_account(self):
        
        # _logger.info(self._context)
        
        if self._context.get('journal_id'):
            journal = self.env['account.journal'].browse(self._context.get('journal_id'))
            if self._context.get('type') in ('out_invoice', 'in_refund'):
                return journal.default_credit_account_id.id
                
        return False
    #===========================================================================
    def getSeccionFactura(self,oFactura):
    
        vals = {}
        vals['name']			= "Mes de " +self.getMes(self.periodo) 
        vals['invoice_id']		= oFactura.id
        vals['display_type']	= 'line_section'
        vals['sequence']		= ( self.periodo.month * 100 )  
 
        return vals
    #===========================================================================
    #===========================================================================
    def _getContador(self,isMono):
        sContadores = '\n==================================='
        if isMono:
            sContadores+= "\nDesde (%s) : %s pag(s). " % (self.ini_periodo,self.ini_total_pag_bn)
            sContadores+= "\nHasta (%s) : %s pag(s). " % (self.fin_periodo,self.fin_total_pag_bn)
        else:
            sContadores+= "\nDesde (%s) : %s pag(s). " % (self.ini_periodo,self.ini_total_pag_color)
            sContadores+= "\nHasta (%s) : %s pag(s). " % (self.fin_periodo,self.fin_total_pag_color)
            
        return sContadores
    #===========================================================================
    def getUbicacion(self):
        
        sDireccion = ""
        
        _logger.info(self.dispositivo.address_id )
        
        # if self.dispositivo.address_id.type=='other' or self.dispositivo.localizacion:
           # sDireccion+= '\n==================================='
           
        if self.dispositivo.address_id.type=='other':
           sDireccion+= '\nUbicado: %s ' % self.dispositivo.direccion
        
        if self.dispositivo.localizacion:
            sDireccion+= '\nLocalizado: %s ' % self.dispositivo.localizacion
            
        sDireccion+= '\n==================================='
        return sDireccion
    #===========================================================================
    def addlecturamir(self):
    
        dispositivo = self.dispositivo
        
        ctx = {
            'default_model'			: 'ariis.mir.lectura',
            'default_dispositivo_id': dispositivo.ariis_id,
            'default_cliente_id'	: dispositivo.partner_id.ariis_id,
            'default_macaddress'	: dispositivo.macaddress ,
            'default_ipaddress'		: dispositivo.ipaddress ,
            'default_creado'		: datetime.now() ,
            'default_origen'		: '03' ,
            'default_unid'			: 'Manual-' +str(datetime.now() ),
            'default_serialnumber'	: dispositivo.lot_id.name ,
            'default_modelo'		: dispositivo.product_id.name ,
            'default_hostname'		: dispositivo.hostnameleido,
            'default_localizacion'	: dispositivo.localizacion,
            'default_nombre'		: dispositivo.name,
            'default_cliente'       : self.cliente.id,
            'default_dispositivo'   : dispositivo.id,
            'default_descripcion'   : 'Lectura Manual de - ' +dispositivo.lot_id.product_id.name,
            'default_contrato_line' : self.contrato_line.id if  self.contrato_line else '' ,
            'default_totalmes'      : self.id
        }
        
        return {
            'type'		: 'ir.actions.act_window',
            'view_type'	: 'form',
            'view_mode'	: 'form',
            'res_model'	: 'ariis.mir.lectura',
            'src_model'	: 'ariis.total.mes' ,
            'multi'		: False,
            'target'	: 'current',
            'context'	: ctx,
        }
    #===========================================================================