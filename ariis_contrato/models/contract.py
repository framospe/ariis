# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging

from odoo import Command, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression
from odoo.tools.translate import _
from datetime import datetime
from dateutil.relativedelta import relativedelta

_logger = logging.getLogger(__name__)
_logger.disabled = False

I_MESES = "NoSale,Enero,Febrero,Marzo,Abril,Mayo,Junio,Julio,Agosto,Septiempre,Octubre,Noviembre,Diciembre"


 
    
#==============================================================================================================
#==============================================================================================================
class ContractContract(models.Model):
    _inherit    = ['contract.contract']
    #===========================================================================
 
    isautomaticadd  = fields.Boolean(default=True , help="Permite añadir dispositivos Ariis automaticamente" )
    iscxc           = fields.Boolean(default=False , help="Si es un contrato de CXC" )
 
     
    contract_line_ariis_cxc_ids = fields.One2many(
        string="Contract lines (Ariis)",
        comodel_name="contract.line",
        inverse_name="contract_id",
        domain=[('iscxc','=',True)],
        context={"active_test": False , "iscxc": True },
    )    
    #===========================================================================
    contract_line_ariis_ids = fields.One2many(
        string="Contract lines",
        comodel_name="contract.line",
        inverse_name="contract_id",
        context={"active_test": False , "iscxc": False },
    )
    aMeses = I_MESES.split(',')

    oProductRefs = {}
    oProductTaxs = {}

    #===========================================================================
    def getMes(self,dFecha):
        if True:
            sMes = dFecha.month
            return self.aMeses[dFecha.month]
        return ""
    #===========================================================================
    def getProducts(self):

        # _logger.info('Cargando Products Ariis')
 
        oProductos      = {}
        aProducts       = []
        
        aProducts.append('ariis.product_ariis_cx_mono')
        aProducts.append('ariis.product_ariis_cx_color')
        aProducts.append('ariis.product_ariis_cx_pro_mono')
        aProducts.append('ariis.product_ariis_cx_pro_color')

        for sRef in aProducts:
        
            o = self.env.ref(sRef)

            # _logger.info(o)

            oProductos[sRef] = {
                'ref'       : sRef,
                'id'        : o.id ,
                'obj'       : o ,
                'name'      : o.name ,
                'uom_id'    : o.uom_id.id,
                'leyenda'   : o.description_sale,
                'taxes'     : self.getProductoTaxes(sRef,o)
            }

        return oProductos
    #===========================================================================
    def getProductoTaxes( self , sRef ,oProducto):

        if not sRef in self.oProductTaxs:
 
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
    def anadeLinea(self ,invoice_vals,invoice_line_vals):
    
        if invoice_line_vals:
            if "company_id" in invoice_line_vals:
                del invoice_line_vals["company_id"]
            if "company_currency_id" in invoice_line_vals:
                del invoice_line_vals["company_currency_id"]
                
            # _logger.info(invoice_line_vals)
                            
            invoice_vals["invoice_line_ids"].append( Command.create(invoice_line_vals) )
    #===========================================================================
    #===========================================================================
    #===========================================================================
    #===========================================================================
    #===========================================================================
    #===========================================================================
    #===========================================================================
    #===========================================================================
    #===========================================================================
    #===========================================================================
    #===========================================================================
    #===========================================================================
    def _prepare_recurring_invoices_values(self, date_ref=False):
    
        _logger.info("================================================")
        _logger.info("Iniciando generacion de Contrato date_ref : "+str(date_ref))
        _logger.info("================================================")
        # ======================================
        # TODO invoice_origin
        # ======================================
        aProducts   = []
        oProductos  = self.getProducts()
 
        pricelist   = ( self.pricelist_id or self.partner_id.with_company( self.company_id  ).property_product_pricelist )

        invoices_values = []
        
        for contract in self:
        
            if not date_ref:
                date_ref_this = contract.recurring_next_date
            else:
                date_ref_this = date_ref
            
            if not date_ref_this:
                # this use case is possible when recurring_create_invoice is
                # called for a finished contract
                continue

            _logger.info("================================================")
            _logger.info("Inicio de generacion de contrato para : "+contract.name)
            _logger.info("================================================")
            invoice_vals = contract._prepare_invoice(date_ref_this)
            
            invoice_vals['old_contract_id'] = contract.id
            invoice_vals["invoice_line_ids"] = []
            contract_lines_ariis = []

            contract_lines = contract._get_lines_to_invoice(date_ref_this)

            _logger.info("Lineas - Recurrentes a tratar: "+str(len(contract_lines)))
            
            # ========================================================
            # Añadimos lineas recurrentes si hay
            # ========================================================
            if len(contract_lines)>0:
                for line in contract_lines:
                    if not line.iscxc:
                        self.anadeLinea( invoice_vals , line._prepare_invoice_line() )
                    else:
                        contract_lines_ariis.append(line)
                # ========================================================
                # Tratar Equipos Ariis
                # ========================================================
                if not contract_lines_ariis:
                    continue
                
                _logger.info("Dispositivos - Recurrentes a tratar: "+str(len(contract_lines_ariis)))
                # ========================================================
                # Ahora añadimos equipos ariis si hay
                # ========================================================
                invoice_vals["invoice_line_ids"].append(
                            Command.create({
                                "name"          : "CXC - Mes de " +contract.getMes(date_ref_this) ,
                                "display_type"  : "line_section",
                                "sequence"      :  (date_ref_this.month*1000)
                            })
                        )

                for line in contract_lines_ariis:

                    oTotalMes = line.getTotalMes(date_ref_this)

                    

                    if oTotalMes:
                        
                        _logger.info("Tratando dispositivo:  "+str(line.dispositivo_id.lot_id.name))
                        
                        if not line.promocion or line.promocion in ('01','04'):
                            #=============================================
                            # Total Blanco/Negro
                            #=============================================
                            self.anadeLinea( invoice_vals , line._prepare_invoice_line_product( oTotalMes ,False ,oProductos , pricelist) )
                            #=============================================
                            # Total Color
                            #=============================================
                            if line.iscolor:
                                self.anadeLinea( invoice_vals , line._prepare_invoice_line_product( oTotalMes ,True  ,oProductos, pricelist) )
                            
                            if line.promocion:
                                #==========================================
                                #PROMOCION
                                #==========================================
                                if line.pag_pro_bn>0 and line.fecha_fin_pro_bn:
                                    if line.fecha_fin_pro_bn >=fields.Date.today():
                                        self.anadeLinea( invoice_vals , line._prepare_invoice_line_promo( oTotalMes ,False  ,oProductos, pricelist) )
                                        
                                if line.iscolor and line.pag_pro_color>0 and line.fecha_fin_pro_color:
                                    if line.fecha_fin_pro_color >=fields.Date.today():
                                        self.anadeLinea( invoice_vals , line._prepare_invoice_line_promo( oTotalMes ,True ,oProductos , pricelist) )
                        else:
                            #==========================================================================================
                            # Si es promocion tipo 2 entonces solo se crea la lineas de factura si el numero de copias
                            # actual del BN o Color es superior a la indicada en el campo promocion correspondiente
                            #==========================================================================================
                            if line.isTotalPrintPromocion02(False,oTotalMes.fin_total_pag_bn):
                                self.anadeLinea( invoice_vals , line._prepare_invoice_line_product( oTotalMes ,False  ,oProductos, pricelist) )

                            if line.iscolor and line.isTotalPrintPromocion02(True,oTotalMes.fin_total_pag_color):
                                self.anadeLinea( invoice_vals , line._prepare_invoice_line_product( oTotalMes ,True  ,oProductos, pricelist) )

            invoices_values.append(invoice_vals)
            # ============================
            # Force the recomputation of journal items
            # ============================
             
            _logger.info('===============================================')
            _logger.info("#oLineas._update_last_date_invoiced = _update_recurring_next_date()")
            _logger.info('===============================================')
            
            contract_lines._update_recurring_next_date()   #_update_last_date_invoiced

            _logger.info('===============================================')
            _logger.info("FIN de generacion de contrato para : "+contract.name)
            _logger.info('===============================================')
        # =========================================================================
        _logger.info('====================================================')
        _logger.info("FIN de generacion de Contratos date_ref : "+str(date_ref))
        _logger.info('====================================================')
        
        return invoices_values
    #===========================================================================
    def recurring_create_invoice(self):
        """
        This method triggers the creation of the next invoices of the contracts
        even if their next invoicing date is in the future.
        """
        invoices = self._recurring_create_invoice()
        for invoice in invoices:
            self.message_post(
                body=_(
                    "Contrato facturado manualmente - "+invoice._get_html_link(title='Factura') )
                % {
                    "model_name": invoice._name,
                    "rec_id": invoice.id,
                }
            )
        return invoices
    #===========================================================================
    @api.model
    def _add_contract_origin(self, invoices):
        for item in self:
            for move in invoices & item._get_related_invoices():
                move.message_post(
                    body=(
                        _(
                            (
                                "%(msg)s por contrato - " + item._get_html_link(title=item.display_name)
                            ),
                            msg=move._creation_message(),
                            contract_id=item.id,
                            contract=item.display_name,
                        )
                    )
                )
    #===========================================================================
    def _get_lines_to_invoice_ariis(self, date_ref):
        """
        This method fetches and returns the lines to invoice on the contract
        (self), based on the given date.
        :param date_ref: date used as reference date to find lines to invoice
        :return: contract lines (contract.line recordset)
        """
        self.ensure_one()

        def can_be_invoiced_ariis(contract_line):
            return (
                not contract_line.is_canceled
                and contract_line.recurring_next_date
                and contract_line.recurring_next_date <= date_ref
                and contract_line.next_period_date_start
            )

        lines2invoice = previous = self.env["contract.line"]
        current_section = current_note = False
        for line in self.contract_line_ariis_cxc_ids:
            if line.is_recurring_note or not line.display_type:
                if can_be_invoiced_ariis(line):
                    if current_section:
                        lines2invoice |= current_section
                        current_section = False
                    if current_note:
                        lines2invoice |= current_note
                    lines2invoice |= line
                    current_note = False
            previous = line
        return lines2invoice.sorted()
	#===========================================================================
    def getPortalLineas(self,isReporte=False):
 
        self.ensure_one()
        date_ref    = self.recurring_next_date
        pricelist   = ( self.pricelist_id or self.partner_id.with_company( self.company_id  ).property_product_pricelist )
        
        # contract_lines_ariis = self._get_lines_to_invoice_ariis(date_ref)
        contract_lines_ariis = self._get_lines_to_invoice(date_ref)
        
        if not contract_lines_ariis:
            _logger.info("Contrato Sin Lineas Recurrentes que tratar para : "+str(date_ref))
            return []

        _logger.info("Dispositivos - Recurrentes a tratar: "+str(len(contract_lines_ariis)))
        
        aProducts   = []
        oProductos  = {}
        aLineas     = []
        
        aProducts.append('ariis.product_ariis_cx_mono')
        aProducts.append('ariis.product_ariis_cx_color')
        aProducts.append('ariis.product_ariis_cx_pro_mono')
        aProducts.append('ariis.product_ariis_cx_pro_color')

        for sRef in aProducts:
            o = self.env.ref(sRef) 
 
            oProductos[sRef] = {
                'ref'       : sRef,
                'id'        : o.id ,
                'obj'       : o ,
                'name'      : o.name ,
                'uom_id'    : o.uom_id.id,
                'leyenda'   : o.description_sale
            }
            
        
        
        
        if isReporte:
            aLineas.append({ 'display_type' : 'line_note' , 'name' : 'Dispositivos Ariis 1' } )
        else:
            aLineas.append({ 'display_type' : 'line_note' , 'price_subtotal': 0 ,'name' : 'Mes de ' +self.getMes(date_ref) } )
        
        
        
        for oEquipoContrato in contract_lines_ariis:
            
            if oEquipoContrato.display_type:
                display_type = oEquipoContrato.display_type
            else:
                display_type = "line_product"
            
            
            if not oEquipoContrato.iscxc:
                
                aValues = oEquipoContrato._prepare_invoice_line()
                
                aValues['display_type']         = display_type
                aValues['price_subtotal']       = oEquipoContrato.price_subtotal
                aValues['recurring_interval']   = oEquipoContrato.recurring_interval
                aValues['recurring_rule_type']  = oEquipoContrato.recurring_rule_type
                aValues['recurring_next_date']  = oEquipoContrato.recurring_next_date
                
                if not 'price_subtotal' in aValues:
                    aValues['price_subtotal']  = 0
                    
                aLineas.append(aValues)
                
                # aLineas.append( {
                                    # "quantity"              : oEquipoContrato.quantity,
                                    # "discount"              : oEquipoContrato.discount,
                                    # "analytic_distribution" : oEquipoContrato.analytic_distribution,
                                    # "sequence"              : oEquipoContrato.sequence, 
                                    # "name"                  : oEquipoContrato.name,
                                    # "price_unit"            : oEquipoContrato.price_unit,
                                    # "price_subtotal"        : oEquipoContrato.price_subtotal,
                                    # "recurring_interval"    : oEquipoContrato.recurring_interval,
                                    # "recurring_rule_type"   : oEquipoContrato.recurring_rule_type,
                                    # "recurring_next_date"   : oEquipoContrato.recurring_next_date,
                                    # "display_type"          : display_type,
                 
                                # })
            else:
                if isReporte:
                    
                    aLineas.append(oEquipoContrato.getNameLineReport(False,False ,oProductos ,False ,date_ref ,pricelist))
                
                    if oEquipoContrato.iscolor:
                        aLineas.append(oEquipoContrato.getNameLineReport(True,False,oProductos ,False,date_ref,pricelist))
                
                    if oEquipoContrato.isValidPromo(False):
                        aLineas.append(oEquipoContrato.getNameLineReport(False,True,oProductos ,False,date_ref,pricelist))
                        
                    if oEquipoContrato.isValidPromo(True):
                        aLineas.append(oEquipoContrato.getNameLineReport(True,True,oProductos ,False,date_ref,pricelist))
 
                else:
                    oTotalMes = oEquipoContrato.getTotalMes(date_ref)
                            
                    aLineas.append(oEquipoContrato.getNameLine(False,False ,oProductos ,oTotalMes ,date_ref ,pricelist))
                
                    if oEquipoContrato.iscolor:
                        aLineas.append(oEquipoContrato.getNameLine(True,False,oProductos ,oTotalMes,date_ref,pricelist))
                
                    if oEquipoContrato.isValidPromo(False):
                        aLineas.append(oEquipoContrato.getNameLine(False,True,oProductos ,oTotalMes,date_ref,pricelist))
                        
                    if oEquipoContrato.isValidPromo(True):
                        aLineas.append(oEquipoContrato.getNameLine(True,True,oProductos ,oTotalMes,date_ref,pricelist))
            
        return aLineas
    #===========================================================================
    def crea_contratos_cxc_cron(self):
    
        aSearch = []
        aSearch.append(('contrato_line','=',False))
        # aSearch.append(('cliente','=',83))
        
        oFounds = self.env['ariis.total.mes'].search( aSearch )
        
        _logger.info("Tratando totales mes sin contrato: "+str(len(oFounds)))
        
        for oTotalMes in oFounds:
            
            oContrato       = False
            oContratoLinea  = oTotalMes.contrato_line
            
            if not oContratoLinea:
 
                oValues = {}
                oValues['partner_id']   = oTotalMes.cliente.id
                oValues['iscxc']        = True

                # _logger.info("Totales mes sin contrato para : "+oTotalMes.cliente.name )
                
                oContrato = self.getContrato( oValues )
                # =====================================
                if not oContrato:
 
                    # _logger.info("Creando Contrato: "+str(oValues))
 
                    oContrato = self.create( { 
                                                'partner_id'            : oTotalMes.cliente.id  , 
                                                'iscxc'                 : True ,
                                                'name'                  : "CXC "+oTotalMes.cliente.name ,
                                                'date_start'            : datetime.today() , 
                                                'pricelist_id'          : 1,
                                                'contract_type'         : 'sale' ,
                                                'recurring_rule_type'   : 'daily'
                                                
                                             })
                # else:
                    # oContrato.update({ 'name'   : "CXC "+oTotalMes.cliente.name })
                                # =====================================
                aSearch = []
                
                aSearch.append(('contract_id'   ,'=', oContrato.id ))
                aSearch.append(('partner_id'    ,'=', oContrato.partner_id.id ))
                aSearch.append(('dispositivo_id','=', oTotalMes.dispositivo.id ))
            
                oContratoLinea = self.env['contract.line'].search(aSearch,limit=1)
                # =====================================
                if not oContratoLinea:
                
                    # _logger.info("Totales mes sin linea de contrato: "+oTotalMes.dispositivo.lot_id.name )
                
                    oValues = {
                                'active'                : True ,
                                'contract_id'           : oContrato.id ,
                                "dispositivo_id"        : oTotalMes.dispositivo.id ,
                                'name'                  : "Linea de Contrato CXC - "+oTotalMes.dispositivo.lot_id.name ,
                                'date_start'            : oContrato.date_start,
                                'date_end'              : oContrato.date_end,
                                'state'                 : 'in-progress',
                                'automatic_price'       : True,
                                'anyadido'              : datetime.now() ,
                                'promocion'             : False,
                                'recurring_next_date'   : oContrato.recurring_next_date
                              }
                              
                    # _logger.info("Creando Linea a Factura de Contrato: "+str(oValues))
                    
                    oContratoLinea = self.env['contract.line'].create( oValues )
                    
                    # subtype='mail.mt_comment',
                    try:
                        oContratoLinea.message_post(
                        subject=(_("Linea de Contrato creada automaticamente")),
                        body="Creacion automatica desde proceso el %s" % (datetime.now().strftime('%d-%m-%Y')),
                        message_type='comment',
                        
                    )
                    except Exception as e:
                        _logger.critical(e)
                # =====================================
                else:
                    oValues = {
                                'contract_id'           : oContrato.id ,
                                'name'                  : "Linea de Contrato CXC - "+oTotalMes.dispositivo.lot_id.name ,
                                'anyadido'              : datetime.now() ,
                                'recurring_next_date'   : oContrato.recurring_next_date
                              }
                              
                    # _logger.info("Modificando Linea de Factura de Contrato: "+str(oValues))
                    
                    oContratoLinea.update( oValues )
                # =====================================
            else:
                # _logger.info("Contrato Linea existe: "+oContratoLinea.dispositivo_id.lot_id.name)
                oContrato = oContratoLinea.contract_id
                # =====================================
            oTotalMes.dispositivo.update( { 'contrato_line' : oContratoLinea.id })
            oTotalMes.update( { 'contrato_line' : oContratoLinea.id })
	#===========================================================================
    def isExisteContrato(self, aSearch ):
        return self.getContrato(aSearch)!=False
	#===========================================================================
    def getContrato(self, aBuscar ):
 
        _logger.info("Buscando contrato: "+str(aBuscar))
        
        aSearch = []
        aSearch.append(('partner_id'    ,'=',aBuscar['partner_id'] ))
        aSearch.append(('iscxc'         ,'=',aBuscar['iscxc']))
        
        return self.env['contract.contract'].search(aSearch ,limit=1)
    #===========================================================================
    def action_contract_send(self):
    
        self.ensure_one()
        template = self.env.ref("ariis_contrato.email_contract_template", False)
        compose_form = self.env.ref("mail.email_compose_message_wizard_form")
 
        ctx = dict(
            default_model="contract.contract",
            default_res_ids=[self.id],
            default_use_template=bool(template),
            default_template_id=template and template.id or False,
            default_composition_mode="comment",
        )
        return {
            "name": _("Compose Email"),
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "mail.compose.message",
            "views": [(compose_form.id, "form")],
            "view_id": compose_form.id,
            "target": "new",
            "context": ctx,
        }
    #===========================================================================
    #===========================================================================
    #===========================================================================
    #===========================================================================
    #===========================================================================
    #===========================================================================
    #===========================================================================
    #===========================================================================