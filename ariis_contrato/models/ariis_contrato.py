# -*- coding: iso-8859-1 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import odoo
import logging
import time
import datetime
import dateutil.relativedelta

from odoo import api, fields, models
from datetime import datetime
from odoo.tools import date_utils

_logger = logging.getLogger(__name__)
_logger.disabled = False

I_MESES = "NoSale,Enero,Febrero,Marzo,Abril,Mayo,Junio,Julio,Agosto,Septiempre,Octubre,Noviembre,Diciembre"

class Contrato(models.Model):
    _name			= 'ariis.contrato'
    _inherit		= ['mail.thread', 'mail.activity.mixin']
    _description	= "Contrato de Cliente"
    _order			= "partner_id"

    #======================================================================
    def _default_pricelist(self):
        if self.partner_id and self.partner_id.property_product_pricelist:
            self.pricelist_id.id=self.partner_id.property_product_pricelist.id

    name			= fields.Char('Numero de Contrato',default= lambda self: self.env['ir.sequence'].next_by_code('ariis.contrato'),copy=False, required=True )
    albaran			= fields.Char("Albaran")
    #=================
    company_id		= fields.Many2one( 'res.company', string='Compañia', required=True, default=lambda self: self.env.user.company_id )
    tipo_id			= fields.Many2one('ariis.contrato.tipo', string='Tipo de Contrato' , index=True )
    partner_id		= fields.Many2one('res.partner', string='Cliente', change_default=True, required=True,  index=True, track_visibility='onchange'  )
    financiera_id	= fields.Many2one('res.partner', string='Financiera',  index=True , domain="[('category_id.name', '=', 'Financiera')]") 
    pricelist_id	= fields.Many2one( comodel_name='product.pricelist', default=_default_pricelist , string='Tarifa' )
    comercial		= fields.Many2one('hr.employee', string='Comercial' , domain="[('category_ids.name', '=', 'Comercial')]" , required=True)
    journal_id		= fields.Many2one( 'account.journal', string='Diario', domain="[('type', '=', 'sale'),('company_id', '=', company_id)]", )
    #=================
    fecha			= fields.Datetime('Creado el', readonly=True ,default=fields.Datetime.now,copy=False)
    #=================
    fecha_inicio	= fields.Date('Fecha Inicio', required=True )
    fecha_fin		= fields.Date('Fecha Fin', required=True)
    #=================
    precio			= fields.Float('Precio Total',digits=(6, 2) , required=True)
    cuota			= fields.Float('Total Cuota',digits=(4, 2) ) 
    precio_bn		= fields.Float('Precio Pag. BN',digits=(2, 4))
    precio_color	= fields.Float('Precio Pag. Color',digits=(2, 4))
    #=================
    plazos			= fields.Integer("N? de Plazos")
    line_count		= fields.Integer(compute='_compute_line_count', string='# of Contrato')
    #=================
    line_ids			= fields.One2many( 'ariis.contrato_line', 'contrato_id', 'Dispositivos del Contrato'  ,copy=False  )
    #dispositivo_ids	= fields.One2many( 'ariis.dispositivo', 'contrato_id', 'Dispositivos del Contrato'  ,copy=False   )
    lecturas_ids		= fields.One2many( comodel_name='ariis.lectura'     , inverse_name='ariis_contrato_id'   ) 
    totalmes_ids 		= fields.One2many( comodel_name='ariis.total.mes'   , inverse_name='ariis_contrato_id'  )
    facturas_ids 		= fields.One2many( comodel_name='account.move'      , inverse_name='ariis_contrato_id'  )
    #===========================================================================
    lecturas_ids_count = fields.Integer(string="Lecturas", compute='_compute_lecturas_count')
    totalmes_ids_count = fields.Integer(string="Totales Mes", compute='_compute_lecturas_mes_count')
    facturas_ids_count = fields.Integer(string="Facturas", compute='_compute_facturas_count')
    #===========================================================================
    def _compute_lecturas_count(self):
        for equipo in self:
            if equipo.lecturas_ids:
                equipo.lecturas_ids_count= len(equipo.lecturas_ids)
            else:
                 equipo.lecturas_ids_count= 0
    #===========================================================================
    def _compute_lecturas_mes_count(self):
        for equipo in self:
            if equipo.totalmes_ids:
                equipo.totalmes_ids_count=len(equipo.totalmes_ids)
            else:
                equipo.totalmes_ids_count= 0
    #===========================================================================
    def _compute_facturas_count(self):
        self._compute_field_count('facturas_ids','facturas_ids_count')
    #===========================================================================
    def _compute_field_count(self,fieldids,fieldcount):
        for equipo in self:
            if equipo[fieldids]:
                equipo[fieldcount]=len(equipo[fieldids])
            else:
                equipo[fieldcount]= 0
    #===========================================================================
    recurring_invoice_line_ids = fields.One2many( string='Invoice Lines', comodel_name='ariis.analytic.contract.line', inverse_name='analytic_account_id', copy=True )
    #=================
    state			= fields.Selection([
                                    ('0', 'Borrador'),
                                    ('1', 'Activo'),
                                    ('2', 'Terminado'),
                                    ('3', 'Pte. Liquidacion'),
                                    ('4','Liquidado'),
                                    ('5','Cancelado')], string='Estado', copy=False, default='0' , track_visibility='onchange' ,readonly=True )

 
    # tipo				= fields.Selection([
                                    # ('01', 'Buy and Print'),
                                    # ('02', 'Coste x Copia'),
                                    # ('03', 'Contrato Renting'),
                                    # ('04', 'OTS'),
                                    # ('05', 'Fianza'),
                                    # ('06', 'TPV Fianza'),
                                    # ('07', 'Alquiler'),
                                    # ('08', 'Fusionadora'),
                                    # ('09', 'Vehiculo de Alquiler'),
                                    # ('10', 'Mantenimiento'),
                                    # ('11','Cesion')], string='Tipo Contrato Antiguo', copy=False, default='02' )
    #=================
    reload			= fields.Boolean(default=False, string="Recargar")
    #=================
    aMeses = I_MESES.split(',')
    #=========================================================================================================
    def _compute_line_count(self):
        for contrato in self:
            contrato.line_count = self.env['ariis.contrato_line'].search_count([('contrato_id', '=', contrato.id)])

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        
        if not self.partner_id:
            return

        partner = self.partner_id
        if not partner.is_bloqueado:
            return
            
        warning = {}
        title = ("Ariis: Aviso para %s") % partner.name
        message = "Cliente bloqueado no permite Contrato"
        warning = { 'title': title, 'message': message }
        self.update({'partner_id': False })

        return {'warning': warning }

    def _caducar(self):
    
        oMail = self.env['mail.message']
        canal = self.env.ref('ariis.channel_ariis_mir')
        
        for contrato in self:
        
            contrato.write({'state': "2" })
            
            values = {	'channel_ids': [(6, 0, [canal.id])] ,
                        'message_type':'notification' ,
                        'subject':'Contrato '+contrato.name+' Terminado',
                        'body':"Contrato ["+contrato.name+"] de ["+contrato.partner_id.name+"] a Terminado y debe ser Liquidado" }
            oMail.create(values)
            
            contrato.partner_id.bloquea()
            
        return

    def updatePrecioChild(self):
        _logger.info('updatePrecioChild')
        
        for oContrato in self:
            for oLinea in oContrato.line_ids:				
                oLinea.write({ 'precio_bn' : oContrato.precio_bn , 'precio_color' : oContrato.precio_color })
    
    # def setTipo(oContrato):
        # if oContrato.tipo:
            # oContrato.tipo_id = oContrato.env['ariis.contrato.tipo'].search([('codigo','=',oContrato.tipo)])
            
    def terminarcontratosactivos(self):
        
        sfecha = fields.Date.today() 
        dfecha = fields.Date.from_string(sfecha)
        _logger.info('==================================================================' )
        _logger.info('Inicio de proceso de terminar contratos vencidos para %s' % sfecha)
        
        founds = self.search([('fecha_fin','<=',sfecha),('state','=','1')])
        
        if founds:
            _logger.info('Contratos a terminar '+str(len(founds)))
            founds._caducar()
            
        _logger.info('Proceso de terminar contratos finalizo OK')
        _logger.info('==================================================================' )
    #=======================================================================================
    def isActive(self):
        return (self.state=='1')
    #=======================================================================================
    def refreshDispositivos(self):

        for oContrato in self:
        
            if not oContrato.isActive():
                continue
            
            for oLine in oContrato.line_ids:
                oLine.dispositivo_id.contrato_line = oLine.id
            
    #=======================================================================================
    def isTarifaPlana(self):
        _logger.info('Tarifa : '+self.tipo_id.codigo)
        return self.tipo_id.codigo=='13'
    #=======================================================================================
    def activar(self):
        self.state = '1'
    #=======================================================================================
    def cancelar(self):
        self.state = '5'
    #=======================================================================================
    def terminar(self):
        self.state = '2'
    #=======================================================================================
    def pteLiquidar(self):
        self.state = '3'
    #=======================================================================================
    def liquidar(self):
        self.state = '4'
    #=======================================================================================
    def borrador(self):
        self.state = '0'

    #======================================================================

    #======================================================================
    def button_show_recurring_invoices(self):
        self.ensure_one()

        self.asigna_recurring_invoices(self)

        action = self.env.ref( 'ariis_contrato.act_recurring_invoices')
        return action.read()[0]
    #======================================================================
    def button_show_recurring_totmes(self):
        self.ensure_one()
        self.asigna_recurring_totmes(self)
        action = self.env.ref( 'ariis_contrato.act_recurring_totmes')
        return action.read()[0]
    #======================================================================
    def asigna_recurring_invoices(self,oContratos):
        for oContrato in oContratos:
            aSearch = []
            aSearch.append(('source_id' ,'ilike','/' + str(oContrato.partner_id.id)))
            aSearch.append(('invoice_origin' ,'ilike','/' + str(oContrato.partner_id.id)))
            aSearch.append(('partner_id' ,'=', oContrato.partner_id.id ))
            aSearch.append(('name' ,'ilike', 'CXC' ))
            aSearch.append(('ariis_contrato_id' ,'=', False ))

            aFounds = self.env["account.move"].search( aSearch )

            if aFounds:
                for oFactura in aFounds:
                    oFactura.update({'ariis_contrato_id': oContrato.id }) 
    #======================================================================
    def asigna_recurring_totmes(self,oContratos):

        for oContrato in oContratos:
            aSearch = []
            aSearch.append(('cliente' ,'=', oContrato.partner_id.id ))
            # aSearch.append(('dispositivo' ,'=','/' + str(oContrato.partner_id.id)))
            # aSearch.append(('name' ,'ilike', 'CXC' ))
            aSearch.append(('ariis_contrato_id' ,'=', False ))
            aSearch.append(('tratado' ,'=', True ))

            aFounds = self.env["ariis.total.mes"].search( aSearch )

            if aFounds:
                for oFactura in aFounds:
                    oFactura.update({'ariis_contrato_id': oContrato.id })
    #=====================================================================
    @api.model
    def _insert_markers(self, line, date_format ,date_from ,date_to):
        date_from = fields.Date.from_string(date_from)
        date_to = fields.Date.from_string(date_to)
        name = line.name
        name = name.replace('#START#', date_from.strftime(date_format))
        name = name.replace('#END#', date_to.strftime(date_format))
        name = name.replace('#MONTH#', self.getMes(date_from))
        return name
    #======================================================================
    @api.model
    def _prepare_invoice_line(self, oPeriodo ,line, account_id):
        invoice_line = self.env['account.move.line'].new({
            'account_id': account_id,
            'product_id': line.product_id.id,
            'quantity': line.quantity,
            'uom_id': line.uom_id.id,
            'discount': line.discount,
            'sequence' : 2000+line.sequence,
            'display_type': False 
        })
        # Get other invoice line values from product onchange
        invoice_line._onchange_product_id()
        invoice_line_vals = invoice_line._convert_to_write(invoice_line._cache)
        # Insert markers
        contract = line.analytic_account_id
        lang_obj = self.env['res.lang']
        lang = lang_obj.search( [('code', '=', contract.partner_id.lang)])
        date_format = lang.date_format or '%m/%d/%Y'
        name = self._insert_markers(line, date_format , oPeriodo ,self._getInvoiceDate(oPeriodo))

        # 'account_analytic_id': contract.id,
        invoice_line_vals.update({
            'name': name,
            'price_unit': line.price_unit,
        })
        return invoice_line_vals
    #======================================================================
    # Invoice Gets
    #======================================================================
    def _getInvoiceOrigin(self,oPeriodo):
        aFechas = fields.Date.to_string(oPeriodo).split('-')
        return aFechas[0]+"/"+aFechas[1]+"/"+str(self.partner_id.id)
    #======================================================================
    def _getInvoiceDomain(self, oPeriodo):
        aDomain = []
        sOrigen = self._getInvoiceOrigin(oPeriodo)

        aDomain.append( ('partner_id'	,'=',self.partner_id.address_get(['invoice'])['invoice']) )
        # aDomain.append( ('ariis_contrato_id'		,'=',self.id ) )
        aDomain.append( ('invoice_origin'		,'=',sOrigen ) )

        return aDomain
    #======================================================================
    def _getInvoiceName(self, oPeriodo):
        return  "CXC "+self.partner_id.name+" ( "+self.getMes(oPeriodo)+" "+str(oPeriodo).split("-")[0]+" )"
    #======================================================================
    def _getInvoiceDate(self,oPeriodo):
        return date_utils.add(oPeriodo, months=1) 
    #======================================================================
    #======================================================================
    def _prepare_invoice(self, oPeriodo ):
        self.ensure_one()
        if not self.partner_id:
                raise ValidationError(
                    _("You must first select a Customer for Contract %s!") %
                    self.name)

        journal = self.journal_id or self.env['account.journal'].search([
                ('type', '=', 'sale'),
                ('company_id', '=', self.company_id.id) ], limit=1)
        if not journal:
            raise ValidationError(
                _("Please define a %s journal for the company '%s'.") %
                (self.contract_type, self.company_id.name or '')
            )
        currency = (
            self.pricelist_id.currency_id or
            self.partner_id.property_product_pricelist.currency_id or
            self.company_id.currency_id
        )
        
        vals = {
            "move_type"         : 'out_invoice',
            "state"				: 'draft',
            "company_id"        : self.company_id.id,
            "partner_id"        : self.partner_id.address_get(['invoice'])['invoice'],
            'ariis_contrato_id'	: self.id,
            "currency_id"		: currency.id,
            "journal_id"        : journal.id,
            "invoice_date"      : self._getInvoiceDate(oPeriodo) ,
            "invoice_origin"    : self._getInvoiceOrigin(oPeriodo) ,
            "invoice_line_ids": [],
            # "ref"               : self.code,
        }

        # invoice = self.env['account.move'].new({
            # 'move_type'		    : 'out_invoice',

            # 'partner_id'		: self.partner_id.address_get(['invoice'])['invoice'],
            # 'currency_id'		: currency.id,
            # 'journal_id'		: journal.id,
            # 'company_id'		: self.company_id.id,
            # 'ariis_contrato_id'	: self.id,
            # 'user_id'			: self.partner_id.user_id.id,
            # 'account_id'		: self.partner_id.property_account_receivable_id.id ,
            # 'invoice_payment_term_id'	: self.partner_id.property_payment_term_id.id,
            # 'name'				: self._getInvoiceName(oPeriodo) ,
            # 'origin'			: self._getInvoiceOrigin(oPeriodo) ,
            # 'invoice_date'	    : self._getInvoiceDate(oPeriodo) ,
        # })
        # Get other invoice values from partner onchange
        # invoice._onchange_partner_id()
        
        if self.partner_id.property_payment_term_id:
            vals.update(
                {
                    "invoice_payment_term_id": self.partner_id.property_payment_term_id.id,
                }
            )
        # if self.fiscal_position_id:
            # vals.update(
                # {
                    # "fiscal_position_id": self.fiscal_position_id.id,
                # }
            # )
        if  self.partner_id.user_id:
            vals.update(
                {
                    "invoice_user_id": self.partner_id.user_id.id,
                }
            )
        return vals
        
        
        
        # return invoice._convert_to_write(invoice._cache)
    #======================================================================
    def _prepare_invoice_update(self ,oPeriodo , invoice=False):
        vals = self._prepare_invoice(oPeriodo)
        update_vals = {
            'ariis_contrato_id' : self.id,
            'invoice_date'      : vals.get('invoice_date'   , False),
            'reference'         : vals.get('reference'      , invoice.reference),
            'invoice_origin'    : vals.get('invoice_origin' , invoice.invoice_origin),
            'name'              : vals.get('name'           , invoice.name ),
        }
        return update_vals
    #======================================================================
    def getMes(self,dFecha):
        if True:
            sMes = dFecha.month
            return self.aMeses[dFecha.month]
        return ""
    #======================================================================
    def getSeccionFactura(self,oPeriodo,oFactura):
        vals = {}
        vals['name']			= "Mes de " +self.getMes(oPeriodo) 
        vals['account_id']		= oFactura.id
        vals['display_type']	= 'line_section'
        vals['sequence']		= 1  
 
        return vals
    #======================================================================
    def creaLineaFactura(self,oValues):

        oClssInvoiceLine = self.env['account.move.line']

        # _logger.info('Creando linea %s' % oValues['name'] )
        # _logger.info( oValues )

        aSearch = []
        # aSearch.append(('name' ,'=',oValues['name']))
        aSearch.append(('account_id','=',oValues['account_id']))

        if 'lot_id' in oValues:
            aSearch.append(('product_id','=',oValues['product_id']))
            aSearch.append(('lot_id'    ,'=',oValues['lot_id']))
        else:
            if 'product_id' in oValues :
                aSearch.append(('product_id', '=',oValues['product_id']))

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
    #======================================================================
    def _create_invoice(self,oPeriodo, invoice=False):
        """
        :param invoice: If not False add lines to this invoice
        :return: invoice created or updated
        """
        self.ensure_one()
        if invoice and invoice.state == 'draft':
            invoice.update(self._prepare_invoice_update(oPeriodo,invoice))
        else:
            invoice = self.env['account.move'].with_context( {'mail_create_nosubscribe':True,'tracking_disable':True}).create(self._prepare_invoice(oPeriodo))

        self.creaLineaFactura( self.getSeccionFactura(oPeriodo,invoice) )
        
        _logger.info('Tratando Dispositivos de Contrato' )
        self.creaLineasDispositivos( oPeriodo ,invoice)

        _logger.info('Tratando Conceptos de Contrato' )
                
        for line in self.recurring_invoice_line_ids:
            invoice_line_vals = self._prepare_invoice_line(oPeriodo,line, invoice.id)
            if invoice_line_vals:
                _logger.info('Añadiendo Concepto : %s ' % str(invoice_line_vals))
                self.creaLineaFactura( invoice_line_vals )
                # self.env['account.invoice.line'].create(invoice_line_vals)
            else:
                _logger.info('invoice_line_vals vacio ?')
                _logger.info(invoice_line_vals)

        invoice.compute_taxes()

        return invoice
    #======================================================================
    def creaLineasDispositivos( self ,oPeriodo ,oFactura):

        for oContratoLine in self.line_ids:

            _logger.info('Tratando dispositivo : ' +str(oContratoLine.dispositivo_id.lot_id.name))
            _logger.info('=================================')
            aSearch = []
            aSearch.append(('cliente' 		,'=', self.partner_id.id ))
            aSearch.append(('dispositivo' 	,'=', oContratoLine.dispositivo_id.id ))
            aSearch.append(('periodo' 		,'=', oPeriodo ))
            aSearch.append(('contrato_line' ,'=', oContratoLine.id ))

            aFounds = self.env["ariis.total.mes"].search( aSearch , limit=1)

            if not aFounds:
                _logger.info('Lecturas no encontradas ' )
                _logger.info(aSearch)
                continue 
            else:
                _logger.info('Lecturas Encontradas para : ' + str(aSearch))

            oTotMes = aFounds[0]
            # oTotMes.onchange_contrato_line()
            #==========================================
            if not 'ariis.product_ariis_cx_mono' in oTotMes.oProductos:
               oTotMes.load()

            oContrato = oTotMes.contrato_line

            if not oContrato.promocion or oContrato.promocion in ('01','04'):

                _logger.info('Tiene Promocion 1 o 4 ' )

                self.creaLineaFactura( oTotMes.getValuesLineaMonoFactura(oFactura) )

                if oTotMes.dispositivo.iscolor:
                    self.creaLineaFactura( oTotMes.getValuesLineaColorFactura(oFactura) )
                #==========================================
                #PROMOCION
                #==========================================
                if oContrato.promocion:
                    if oContrato.pag_pro_bn>0 and oContrato.fecha_fin_pro_bn:
                        if oContrato.fecha_fin_pro_bn >=fields.Date.today():
                            self.creaLineaFactura( oTotMes.getValuesLineaPromoBNFactura(oFactura) )

                    if oTotMes.dispositivo.iscolor and oContrato.pag_pro_color>0 and oContrato.fecha_fin_pro_color:
                        if oContrato.fecha_fin_pro_color >=fields.Date.today():
                            self.creaLineaFactura( oTotMes.getValuesLineaPromoColorFactura(oFactura) )
            else:

                _logger.info('Tiene Promocion 2 ' )

                # ==========================================================================================
                # Si es promocion tipo 2 entonces solo se crea la lineas de factura si el numero de copias
                # actual del BN o Color es superior a la indicada en el campo promocion correspondiente
                # ==========================================================================================
                if oContrato.isTotalPrintPromocion02(False,oTotMes.fin_total_pag_bn):
                    self.creaLineaFactura( oTotMes.getValuesLineaMonoFactura(oFactura) )

                if oTotMes.dispositivo.iscolor and oContrato.isTotalPrintPromocion02(True,oTotMes.fin_total_pag_color):
                    self.creaLineaFactura( oTotMes.getValuesLineaColorFactura(oFactura) )
                    
            # oTotMes.update({ "factura" : oFactura.id })
    #======================================================================
    def create_invoice_periodo(self,oPeriodo):

        _logger.info('=========================================================')
        _logger.info('Creando Facturas de Periodo : '+str(oPeriodo))
        _logger.info('=========================================================')
        aSearch  = []
        aSearch.append(('cliente'   ,'=', self.partner_id.id )) 
        aSearch.append(('errortext' ,'=', 'OK' ))
        aSearch.append(('factura'   ,'=', False ))
        # aSearch.append(('anual'     ,'=', False ))
        aSearch.append(('tratado'   ,'=', True ))
        aSearch.append(('periodo'   ,'=', oPeriodo ))

        _logger.info('Buscado Totales Mes para periodo : ')
        _logger.info(aSearch)

        aFounds = self.env["ariis.total.mes"].search( aSearch )

        _logger.info('Totales Mes encontrados : '+str(len(aFounds)))

        if not self.recurring_invoice_line_ids and not aFounds:
            return
        
        aSearch = self._getInvoiceDomain( oPeriodo )

        _logger.info("Buscando Factura: " +str(aSearch))
       
        oClssFactura    = self.env['account.move']
        oFactura        = oClssFactura.search(aSearch,limit=1)

        if not oFactura:
            _logger.info("Creando Factura para periodo : " +str(oPeriodo)) 
            oFactura        = self._create_invoice(oPeriodo)
        else:
            if oFactura.state=="draft" :
                _logger.info("Modificando Factura para periodo : " +str(oPeriodo))
                oFactura = self._create_invoice(oPeriodo , oFactura)
            else:
                _logger.info("Factura en estado : " +oFactura.state)
                if not oFactura.ariis_contrato_id:
                    oFactura.update({ "ariis_contrato_id" : self.id })
        if oFactura:
            for oTotMes in aFounds:
                oTotMes.update({ "factura" : oFactura.id })
    #======================================================================
    def recurring_create_invoice(self, currentPeriodo=True):
        _logger.info("Tratando Contratos para : "+self.partner_id.name )
        aPeriodos = self.getPeriodos(currentPeriodo)
        _logger.info(aPeriodos)
        for oPeriodo in aPeriodos:
            # self.create_invoice_periodo(oPeriodo)
            self._cron_recurring_create(oPeriodo, create_type="invoice")
        return
    #======================================================================
    #======================================================================
    def getPeriodos(self, currentPeriodo=True):
    
        aFounds = []
        aSearch = []
        aSearch.append(('cliente'   ,'=', self.partner_id.id ))
        aSearch.append(('errortext' ,'=', 'OK' ))
        aSearch.append(('factura'   ,'=', False ))
        # aSearch.append(('anual'     ,'=', False ))
        aSearch.append(('tratado'   ,'=', True ))

        aFounds = self.env["ariis.total.mes"].search( aSearch )

        aPeriodos = []
        
        if currentPeriodo:
            aPeriodos.append(date_utils.start_of(fields.Date.today(), "month"))

        for oTotMes in aFounds:
            if not oTotMes.periodo in aPeriodos:
                aPeriodos.append(oTotMes.periodo)

        return aPeriodos
    #======================================================================
    #======================================================================
    def _ariis_contrato_crun(self):
        aSearch = []
        aSearch.append(('state' ,'=', '1' ))
        aSearch.append(('reload' ,'=', True ))
        
        aContratosReload = self.env["ariis.contrato"].search( aSearch )
        
        for oContrato in aContratosReload:
            oContrato.recurring_create_invoice(True)
            # oContrato.cron_recurring_create_invoice()
            oContrato.write({ 'reload' : False  })
            self.env.cr.commit()
        return
    #=======================================================================================================================
    @api.model
    def cron_recurring_create_invoice(self, date_ref=None):
        return self._cron_recurring_create(date_ref, create_type="invoice")
    #=======================================================================================================================
    @api.model
    def _cron_recurring_create(self, date_ref=False, create_type="invoice"):
        """
        The cron function in order to create recurrent documents
        from contracts.
        """
        _recurring_create_func = self._get_recurring_create_func(
            create_type=create_type
        )
        if not date_ref:
            date_ref = fields.Date.context_today(self)
        domain = self._get_contracts_to_invoice_domain(date_ref)
        domain = expression.AND(
            [
                domain,
                [("generation_type", "=", create_type)],
            ]
        )
        contracts = self.search(domain)
        companies = set(contracts.mapped("company_id"))
        # Invoice by companies, so assignation emails get correct context
        for company in companies:
            contracts_to_invoice = contracts.filtered(
                lambda contract, comp=company: contract.company_id == comp
                and (
                    not contract.date_end
                    or contract.recurring_next_date <= contract.date_end
                )
            ).with_company(company)
            _recurring_create_func(contracts_to_invoice, date_ref)
        return True
#=======================================================================================================================
    def _recurring_create_invoice(self, date_ref=False):
        invoices_values = self._prepare_recurring_invoices_values(date_ref)
        moves = self.env["account.move"].create(invoices_values)
        self._add_contract_origin(moves)
        self._invoice_followers(moves)
        self._compute_recurring_next_date()
        return moves
    #=======================================================================================================================
    def _prepare_recurring_invoices_values(self, date_ref=False):
        """
        This method builds the list of invoices values to create, based on
        the lines to invoice of the contracts in self.
        !!! The date of next invoice (recurring_next_date) is updated here !!!
        :return: list of dictionaries (invoices values)
        """
        invoices_values = []
        for contract in self:
            # if not date_ref:
                # date_ref = contract.recurring_next_date
            if not date_ref:
                # this use case is possible when recurring_create_invoice is
                # called for a finished contract
                continue
            contract_lines = contract._get_lines_to_invoice(date_ref)
            if not contract_lines:
                continue
            invoice_vals = contract._prepare_invoice(date_ref)
            invoice_vals["invoice_line_ids"] = []
            for line in contract_lines:
                invoice_line_vals = line._prepare_invoice_line()
                if invoice_line_vals:
                    # Allow extension modules to return an empty dictionary for
                    # nullifying line. We should then cleanup certain values.
                    if "company_id" in invoice_line_vals:
                        del invoice_line_vals["company_id"]
                    if "company_currency_id" in invoice_line_vals:
                        del invoice_line_vals["company_currency_id"]
                    invoice_vals["invoice_line_ids"].append(
                        Command.create(invoice_line_vals)
                    )
            invoices_values.append(invoice_vals)
            # Force the recomputation of journal items
            contract_lines._update_recurring_next_date()
        return invoices_values
    #=======================================================================================================================
    def _get_lines_to_invoice(self, date_ref):
        """
        This method fetches and returns the lines to invoice on the contract
        (self), based on the given date.
        :param date_ref: date used as reference date to find lines to invoice
        :return: contract lines (contract.line recordset)
        """
        self.ensure_one()

        def can_be_invoiced(contract_line):
            return (
                not contract_line.is_canceled
                and contract_line.recurring_next_date
                and contract_line.recurring_next_date <= date_ref
                and contract_line.next_period_date_start
            )

        lines2invoice = previous = self.env["contract.line"]
        current_section = current_note = False
        
        for line in self.contract_line_ids:
            if line.display_type == "line_section":
                current_section = line
            elif line.display_type == "line_note" and not line.is_recurring_note:
                if line.note_invoicing_mode == "with_previous_line":
                    if previous in lines2invoice:
                        lines2invoice |= line
                    current_note = False
                elif line.note_invoicing_mode == "with_next_line":
                    current_note = line
            elif line.is_recurring_note or not line.display_type:
                if can_be_invoiced(line):
                    if current_section:
                        lines2invoice |= current_section
                        current_section = False
                    if current_note:
                        lines2invoice |= current_note
                    lines2invoice |= line
                    current_note = False
            previous = line
        return lines2invoice.sorted()
    #=======================================================================================================================
    @api.model
    def _get_recurring_create_func(self, create_type="invoice"):
        """
        Allows to retrieve the recurring create function depending
        on generate_type attribute
        """
        if create_type == "invoice":
            return self.__class__._recurring_create_invoice
    #=======================================================================================================================
    #=======================================================================================================================