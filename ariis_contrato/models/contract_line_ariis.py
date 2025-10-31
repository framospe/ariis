# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import odoo
import logging

from odoo import api, fields, models
from datetime import datetime 
from dateutil.relativedelta import relativedelta

_logger = logging.getLogger(__name__)
_logger.disabled = False

class ContractLineAriis(models.Model):
    _name           = "contract.line.ariis"
    _description    = "Equipo de Contrato"
    _inherit        = ['contract.line','mail.thread', 'mail.activity.mixin']
    # _order          = "contrato_id desc"
    _sql_constraints = [ ('dispositivo_id', 'unique (dispositivo_id)', 'Dispositivo ya registrado en un contrato !') ]
    #=====================
    successor_contract_line_id = fields.Many2one(
        comodel_name="contract.line.ariis",
        string="Successor Contract Line Ariis",
        required=False,
        readonly=True,
        index=True,
        copy=False,
        help="In case of restart after suspension, this field contain the new "
        "contract line created.",
    )
    predecessor_contract_line = fields.Many2one(
        comodel_name="contract.line.ariis",
        string="Predecessor Contract Line Ariis",
        required=False,
        readonly=True,
        index=True,
        copy=False,
        help="Contract Line origin of this one.",
    )
    #=====================
    name                = fields.Text(string="Description", required=False)
    partner_id          = fields.Many2one( 'res.partner', string='Cliente' , related='contract_id.partner_id' ,  readonly=True , store=True)
    dispositivo_id      = fields.Many2one( 'maintenance.equipment', string='Equipo' , required=True ,index=True , store=True , readonly=False )
    #=====================
    modelo              = fields.Char(  string='Modelo' , related='dispositivo_id.product_id.name' ,  readonly=True , store=True)
    numeroserie         = fields.Char(  string='Numero de Serie' , related='dispositivo_id.lot_id.name' , store=True,  readonly=True)	
    #=====================
    anyadido            = fields.Datetime('Agregado' , readonly=True , default=datetime.today()) 
    #=====================
    promocion			= fields.Selection([
                                    ('01', 'Hasta Final de Fecha (Restando promocion cada mes) Defecto'),
                                    ('02', 'Hasta final de pag. de promocion (Facturar cuando Total impreso sea mayor que promocion+Total Actual)'),
                                    ('03', 'Hasta Final de Fecha (Restando cada mes si supera promocion)') ,
                                    ('04', 'Tarifa Plana (Promocion aplicable para todo lo facturable (Anual))') ,
                                    ],
                                    string='Promocion', copy=False, default=False )
    #=====================
    fecha_fin_pro_bn    = fields.Date('Acaba promo. BN')
    fecha_fin_pro_color = fields.Date('Acaba promo. Color') 
    #=====================
    pag_pro_bn          = fields.Integer('Pag. promo. BN')
    pag_pro_color       = fields.Integer('Pag. promo. Color') 
    #=====================
    precio_bn           = fields.Float('Precio Pag. BN',digits=(2, 4))
    precio_color        = fields.Float('Precio Pag. Color',digits=(2, 4))
    #=====================
    iscxc               = fields.Boolean('Es CXC'   , related='dispositivo_id.mir'      ,copy=False ,readonly=True)
    # iscolor             = fields.Boolean('Es Color' , related='dispositivo_id.iscolor'  ,copy=False ,readonly=True)
    iscolor					= fields.Boolean('Color Ufff', readonly=True )
    automatic_price     = fields.Boolean( string="Auto-precio?",  help="If this is marked, the price will be obtained automatically "
             "applying the pricelist to the product. If not, you will be able to introduce a manual price", default=False )
    last_report  = fields.Datetime( string='Ultima actividad' , related='dispositivo_id.last_report' )
    last_periodo = fields.Date( string='Periodo' , index=True)
    #===========================================================================
    
    def _compute_display_name(self):
        result = []
        for record in self:
            if record.dispositivo_id:
                record.display_name =   str(record.contract_id.name) +  ' (' + record.dispositivo_id.lot_id.name+')'
            else:
                record.display_name = str(record.contract_id.name)
    #===========================================================================
    def isTarifaPlana(self):
        return self.contrato_id.isTarifaPlana()
    #===========================================================================
    def isHasPromo(self):
        return self.promocion!=False
    #===========================================================================
    def isValidPromo(self,iscolor):
        # TODO: Comprombar si la fecha de fin de promocion fue superada
        if self.isHasPromo():
            if iscolor and self.pag_pro_color>0:
                return True
            if not iscolor and self.pag_pro_bn>0:
                return True

        return False
    #===========================================================================
    # Retorna si la promocion 02 se cumple para el color (True) o el BN (False)
    #===========================================================================
    def isTotalPrintPromocion02(self , isColor , nTotalPagin ):

        if self.promocion != '02':
            return False

        if isColor:
            nTotalPromo = self.pag_pro_color
        else:
            nTotalPromo = self.pag_pro_bn

        return nTotalPagin>nTotalPromo
    #===========================================================================
    @api.onchange( "dispositivo_id"  )
    def _onchange_dispositivo_id(self):
        if not self.name and self.contract_id and self.dispositivo_id:
            self.name = str(self.contract_id.name) +  ' (' + self.dispositivo_id.lot_id.name+')'
            
    #===========================================================================
    @api.model
    def write(self, vals):
        if not self.dispositivo_id.contrato_line:
            self.dispositivo_id.update({'contrato_line' : self.id })
        
        return super(ContractLineAriis,self).write(vals)
    #==================================================================================
    #==================================================================================
    #==================================================================================
    def _prepare_invoice_line_product(self, oTotalMes , isColor  ,oProductos ,pricelist):
    
        self.ensure_one()
        dates = self._get_period_to_invoice( self.last_date_invoiced, self.recurring_next_date )
 
        if isColor:
            oProducto   = oProductos['ariis.product_ariis_cx_color']
            sName       = oProducto['leyenda']+' %s (%s) %s'
            quantity    = oTotalMes.fin_total_pag_bn - oTotalMes.ini_total_pag_bn
            price_unit  = self.precio_bn if not self.automatic_price or not  pricelist else pricelist._get_product_price(oProducto['obj'],quantity)
        else:
            oProducto   = oProductos['ariis.product_ariis_cx_mono']
            sName       = oProducto['leyenda']+' %s (%s) %s'
            quantity    = oTotalMes.fin_total_pag_color - oTotalMes.ini_total_pag_color
            price_unit  = self.precio_color if not self.automatic_price or not  pricelist else pricelist._get_product_price(oProducto['obj'], quantity)
            
            
        sName = sName % (self.dispositivo_id.product_id.name,self.dispositivo_id.lot_id.name , self.getMes(dates[0]) )
        

        return {
            "quantity"              : quantity,
            "product_uom_id"        : oProducto['uom_id'],
            "discount"              : self.discount,
            # "lot_id"                : self.dispositivo_id.lot_id.id,
            "analytic_distribution" : self.analytic_distribution,
            "sequence"              : (oTotalMes.periodo.month*1000)+self.sequence, 
            "name"                  : sName+ oTotalMes._getContador(isColor)+ oTotalMes.getUbicacion(),
            "price_unit"            : price_unit,
            "display_type"          : "product",
            "product_id"            : oProducto['id'],
        }
    #===========================================================================
    def _prepare_invoice_line_promo(self, oTotalMes , isColor ,oProductos ,pricelist):
 
        if isColor:
            oProducto   = oProductos['ariis.product_ariis_cx_pro_color']
            sName       = oProducto['leyenda']+' %s (%s) (%s pag.)' %  (self.dispositivo_id.product_id.name ,self.dispositivo_id.lot_id.name,str(self.pag_pro_color))
            quantity    = self.pag_pro_color
            price_unit  = -(self.precio_color) if not self.automatic_price or not  pricelist else -(pricelist._get_product_price(oProducto['obj'], quantity))
        else:
            oProducto   = oProductos['ariis.product_ariis_cx_pro_mono']
            sName       = oProducto['leyenda']+' %s (%s) (%s pag.)' %  (self.dispositivo_id.product_id.name ,self.dispositivo_id.lot_id.name ,str(self.pag_pro_bn))
            quantity    = self.pag_pro_bn
            price_unit  = -(self.precio_bn) if not self.automatic_price or not  pricelist else -(pricelist._get_product_price(oProducto['obj'], quantity))
            
        return {
                "quantity"              : quantity,
                "product_uom_id"        : oProducto['uom_id'],
                "discount"              : self.discount,
                "analytic_distribution" : self.analytic_distribution,
                "sequence"              : (oTotalMes.periodo.month*1001)+self.sequence,
                "name"                  : sName,
                "price_unit"            : price_unit,
                "display_type"          : "product",
                "product_id"            : oProducto['id'],
            }    
    #===========================================================================
    def toPeriodo(self,dfecha):
        aFechas = fields.Date.to_string(dfecha).split("-")
        return (aFechas[0]+"-"+aFechas[1]+"-01")
    #===========================================================================
    def getTotalMes(self,dfecha):
    
        oClassTotMes = self.env['ariis.total.mes']
        aSearch = []
        aSearch.append(('cliente'       ,'=',self.partner_id.id))
        aSearch.append(('dispositivo'   ,'=',self.dispositivo_id.id))
        aSearch.append(('periodo'       ,'=',self.toPeriodo(dfecha)))

        oFound = oClassTotMes.search( aSearch ,limit=1)
        
        if not oFound:
            _logger.info("No encontrado : "+str(aSearch))
            
        return oFound
    #======================================================================
    def getMes(self,dFecha):
        return self.contract_id.getMes(dFecha)
    #===========================================================================
    def getNameLine(self,isColor,isPromo,oProductos,oTotalMes ,fecha ,pricelist):
 
        if isColor:
            if isPromo:
                oProducto   = oProductos['ariis.product_ariis_cx_pro_color']
                sName   = oProducto['leyenda']+' %s (%s) (%s pag.)' %  (self.dispositivo_id.product_id.name ,self.dispositivo_id.lot_id.name,str(self.pag_pro_color))
                quantity    = self.pag_pro_color
                price_unit  = -(self.precio_color) if not self.automatic_price or not  pricelist else -(pricelist._get_product_price(oProducto['obj'], quantity=1))
                
            else:
                oProducto   = oProductos['ariis.product_ariis_cx_color']
                quantity    = oTotalMes.fin_total_pag_color - oTotalMes.ini_total_pag_color
                price_unit  = self.precio_color if not self.automatic_price or not  pricelist else pricelist._get_product_price(oProducto['obj'], quantity=1)
                
        else:
            if isPromo:
                oProducto   = oProductos['ariis.product_ariis_cx_pro_mono']
                sName       = oProducto['leyenda']+' %s (%s) (%s pag.)' %  (self.dispositivo_id.product_id.name ,self.dispositivo_id.lot_id.name ,str(self.pag_pro_bn))
                quantity    = self.pag_pro_bn
                price_unit  = -(self.precio_bn) if not self.automatic_price or not  pricelist else -(pricelist._get_product_price(oProducto['obj'], quantity=1))
                
            else:
                oProducto   = oProductos['ariis.product_ariis_cx_mono']
                quantity    = oTotalMes.fin_total_pag_bn - oTotalMes.ini_total_pag_bn
                price_unit  = self.precio_bn if not self.automatic_price or not  pricelist else pricelist._get_product_price(oProducto['obj'], quantity=1)

        if not isPromo:

            sName   = oProducto['leyenda']+' %s (%s) %s'
            sName   = sName % (self.dispositivo_id.product_id.name,self.dispositivo_id.lot_id.name , self.getMes(fecha) )
            
            if oTotalMes:
                sName   = sName+oTotalMes._getContador(isColor)+ oTotalMes.getUbicacion() 
            else:
                sName+= "\nMaquina sin reporte para este mes de "+self.getMes(fecha)
                
        return {
                 'name'                 : sName.replace("\n","<br/>"),
                 "display_type"         : "line_product" ,
                 "quantity"             : quantity ,
                 "price_unit"           : price_unit ,
                 "discount"             : self.discount,
                 "price_subtotal"       : price_unit*quantity,
                 "recurring_interval"   : self.recurring_interval ,
                 "recurring_rule_type"  : self.recurring_rule_type ,
                 "recurring_next_date"  : self.recurring_next_date ,
                }
    #===========================================================================
    def getNameLines(self):
        
        self.ensure_one()
        
        dates       = self._get_period_to_invoice( self.last_date_invoiced, self.recurring_next_date )
        pricelist   = ( self.contract_id.pricelist_id or self.contract_id.partner_id.with_company( self.contract_id.company_id  ).property_product_pricelist )
        oTotalMes   = self.getTotalMes(dates[0])
            
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
            
            
            
        aLineas.append({ 'display_type' : 'line_note' , 'name' : 'Mes de ' +self.getMes(dates[0]) } )
            
        aLineas.append(self.getNameLine(False,False ,oProductos ,oTotalMes ,dates[0] ,pricelist))
        
        if self.iscolor:
            aLineas.append(self.getNameLine(True,False,oProductos ,oTotalMes,dates[0],pricelist))
        
        if self.isValidPromo(False):
            aLineas.append(self.getNameLine(False,True,oProductos ,oTotalMes,dates[0],pricelist))
            
        if self.isValidPromo(True):
            aLineas.append(self.getNameLine(True,True,oProductos ,oTotalMes,dates[0],pricelist))
            
        return aLineas
    #===========================================================================
    #===========================================================================
    @api.depends(
        "last_date_invoiced",
        "date_start",
        "date_end",
        "contract_id.last_date_invoiced",
        "contract_id.contract_line_ariis_ids.last_date_invoiced",
    )
    #===========================================================================
    # pylint: disable=missing-return
    def _compute_next_period_date_start(self):
        """Rectify next period date start if another line in the contract has been
        already invoiced previously when the recurrence is by contract.
        """
        _logger.info("_compute_next_period_date_start ariis" )
        
        rest = self.filtered(lambda x: x.contract_id.line_recurrence)
        for rec in self - rest:
            lines = rec.contract_id.contract_line_ariis_ids 
            if not rec.last_date_invoiced and any(lines.mapped("last_date_invoiced")):
                next_period_date_start = max(
                    lines.filtered("last_date_invoiced").mapped("last_date_invoiced")
                ) + relativedelta(days=1)
                if rec.date_end and next_period_date_start > rec.date_end:
                    next_period_date_start = False
                rec.next_period_date_start = next_period_date_start
            else:
                rest |= rec

        super(ContractLineAriis, rest)._compute_next_period_date_start()
    #===========================================================================
    def plan_successor(
        self,
        date_start,
        date_end,
        is_auto_renew,
        recurring_next_date=False,
        post_message=True,
    ):
        """
        Create a copy of a contract line in a new interval
        :param date_start: date_start for the successor_contract_line
        :param date_end: date_end for the successor_contract_line
        :param is_auto_renew: is_auto_renew option for successor_contract_line
        :param recurring_next_date: recurring_next_date for the
        successor_contract_line
        :return: successor_contract_line
        """
        contract_line = self.env["contract.line.ariis"]
        for rec in self:
            if not rec.is_plan_successor_allowed:
                raise ValidationError(_("Plan successor not allowed for this line"))
            rec.is_auto_renew = False
            new_line = self.create(
                rec._prepare_value_for_plan_successor(
                    date_start, date_end, is_auto_renew, recurring_next_date
                )
            )
            rec.successor_contract_line_id = new_line
            contract_line |= new_line
            if post_message:
                msg = _(
                    """Contract line for <strong>%(product)s</strong>
                    planned a successor: <br/>
                    - <strong>Start</strong>: %(new_date_start)s
                    <br/>
                    - <strong>End</strong>: %(new_date_end)s
                    """
                ) % {
                    "product": rec.name,
                    "new_date_start": new_line.date_start,
                    "new_date_end": new_line.date_end,
                }
                rec.contract_id.message_post(body=msg)
        return contract_line
        

    def stop_plan_successor(self, date_start, date_end, is_auto_renew):
        """
        Stop a contract line for a defined period and start it later
        Cases to consider:
            * contract line end's before the suspension period:
                -> apply stop
            * contract line start before the suspension period and end in it
                -> apply stop at suspension start date
                -> apply plan successor:
                    - date_start: suspension.date_end
                    - date_end: date_end    + (contract_line.date_end
                                            - suspension.date_start)
            * contract line start before the suspension period and end after it
                -> apply stop at suspension start date
                -> apply plan successor:
                    - date_start: suspension.date_end
                    - date_end: date_end + (suspension.date_end
                                        - suspension.date_start)
            * contract line start and end's in the suspension period
                -> apply delay
                    - delay: suspension.date_end - contract_line.date_start
            * contract line start in the suspension period and end after it
                -> apply delay
                    - delay: suspension.date_end - contract_line.date_start
            * contract line start  and end after the suspension period
                -> apply delay
                    - delay: suspension.date_end - suspension.start_date
        :param date_start: suspension start date
        :param date_end: suspension end date
        :param is_auto_renew: is the new line is set to auto_renew
        :return: created contract line
        """
        if not all(self.mapped("is_stop_plan_successor_allowed")):
            raise ValidationError(_("Stop/Plan successor not allowed for this line"))
        contract_line = self.env["contract.line.ariis"]
        for rec in self:
            if rec.date_start >= date_start:
                if rec.date_start < date_end:
                    delay = (date_end - rec.date_start) + timedelta(days=1)
                else:
                    delay = (date_end - date_start) + timedelta(days=1)
                rec._delay(delay)
                contract_line |= rec
            else:
                if rec.date_end and rec.date_end < date_start:
                    rec.stop(date_start, post_message=False)
                elif (
                    rec.date_end
                    and rec.date_end > date_start
                    and rec.date_end < date_end
                ):
                    new_date_start = date_end + relativedelta(days=1)
                    new_date_end = (
                        date_end + (rec.date_end - date_start) + relativedelta(days=1)
                    )
                    rec.stop(
                        date_start - relativedelta(days=1),
                        manual_renew_needed=True,
                        post_message=False,
                    )
                    contract_line |= rec.plan_successor(
                        new_date_start,
                        new_date_end,
                        is_auto_renew,
                        post_message=False,
                    )
                else:
                    new_date_start = date_end + relativedelta(days=1)
                    if rec.date_end:
                        new_date_end = (
                            rec.date_end
                            + (date_end - date_start)
                            + relativedelta(days=1)
                        )
                    else:
                        new_date_end = rec.date_end

                    rec.stop(
                        date_start - relativedelta(days=1),
                        manual_renew_needed=True,
                        post_message=False,
                    )
                    contract_line |= rec.plan_successor(
                        new_date_start,
                        new_date_end,
                        is_auto_renew,
                        post_message=False,
                    )
            msg = _(
                """Contract line for <strong>%(product)s</strong>
                suspended: <br/>
                - <strong>Suspension Start</strong>: %(new_date_start)s
                <br/>
                - <strong>Suspension End</strong>: %(new_date_end)s
                """
            ) % {
                "product": rec.name,
                "new_date_start": date_start,
                "new_date_end": date_end,
            }
            rec.contract_id.message_post(body=msg)
        return contract_line


    def renew(self):
        res = self.env["contract.line.ariis"]
        for rec in self:
            company = rec.contract_id.company_id
            date_end = rec._get_renewal_new_date_end()
            date_start = rec.date_end + relativedelta(days=1)
            if company.create_new_line_at_contract_line_renew:
                new_line = rec._renew_create_line(date_end)
            else:
                new_line = rec._renew_extend_line(date_end)
            res |= new_line
            msg = _(
                """Contract line for <strong>%(product)s</strong>
                renewed: <br/>
                - <strong>Start</strong>: %(new_date_start)s
                <br/>
                - <strong>End</strong>: %(new_date_end)s
                """
            ) % {
                "product": rec.name,
                "new_date_start": date_start,
                "new_date_end": date_end,
            }
            rec.contract_id.message_post(body=msg)
        return res
    #===========================================================================
    def _update_recurring_next_date(self):
    
        _logger.info("_update_recurring_next_date = _update_last_date_invoiced")
        # FIXME: Change method name according to real updated field
        # e.g.: _update_last_date_invoiced()
        for rec in self:
            last_date_invoiced = rec.next_period_date_end
            _logger.info("======================= _update_recurring_next_date = _update_last_date_invoiced Init=====================")
            _logger.info(last_date_invoiced)
            _logger.info("======================= _update_recurring_next_date = _update_last_date_invoiced End =====================")
            rec.write(
                {
                    "last_date_invoiced": last_date_invoiced,
                }
            )