# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging

from random import randint

from datetime import datetime
from dateutil.relativedelta import relativedelta

from odoo import api, Command, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare, float_is_zero, clean_context
from odoo.tools.misc import format_date, groupby
 
_logger = logging.getLogger(__name__)

class Repair(models.Model):
    _inherit = ['repair.order']

    def _default_motivo(self):
        self.motivo_id = self.env.ref('ariis_repair.ariis_motivosat_00')
    # ===========================================================================================
    state           = fields.Selection(selection_add=[('ko_done', 'Terminado KO')])
    ariis_id        = fields.Char(string='Ariis Referencia ', index=True, tracking=False , readonly=True ,copy=False,related="partner_id.ariis_id")
    isariis         = fields.Boolean( string="Cliente Ariis" , help="Si es cliente de equipos de Ariis" ,compute="_compute_isariis" )
    dispositivo_id  = fields.Many2one( 'maintenance.equipment', 
                                        string='Equipo' ,  
                                        index=True ,
                                        domain="[('partner_id','=', partner_id)]")
                                        

    motivo_id       = fields.Many2one( 'ariis.motivosat', string='Motivo' ,index=True , default=_default_motivo)
    atencion        = fields.Selection([('1',"Presencial"),('2',"Telefonica"),('3',"Remota")] ,string="Atencion" , copy=False ,default="1" )
    address_id      = fields.Many2one( 'res.partner', 'Delivery Address', related="dispositivo_id.address_id" )
    priority        = fields.Selection([ ('0','Normal'), ('1','Alta') , ('2' ,'Urgente') , ('3','Critica') ], default='0', index=True)
    
    fstate_draft        = fields.Datetime('Creado' , readonly=True ,default=fields.Datetime.now )
    fstate_confirmed    = fields.Datetime('Confirmado', readonly=True )
    fstate_under_repair = fields.Datetime('En Reparacion', readonly=True )
    fstate_done         = fields.Datetime('Hecho', readonly=True )
    fstate_cancel       = fields.Datetime('Cancelado', readonly=True )
    fstate_ko_done      = fields.Datetime('Teminado KO', readonly=True )

    tiempo_atender    = fields.Float( string="Tiempo en Atender (Creado/Confirmado)"    , store=True , readonly=True,default=0)
    tiempo_iniciar    = fields.Float( string="Tiempo en Iniciar (Creado/Teminado KO)"   , store=True , readonly=True,default=0)
    tiempo_tarea      = fields.Float( string="Tiempo Tarea (En Reparación/Hecho)"       , store=True , readonly=True,default=0, group_operator ="avg" )
    tiempo_terminar   = fields.Float( string="Tiempo Terminar (Creado/Hecho)"           , store=True , readonly=True,default=0)
    tiempo_cancelar   = fields.Float( string="Tiempo en Entregar (Creado/Cancelado)"    , store=True , readonly=True,default=0)
    tiempo_ko         = fields.Float( string="Tiempo en KO (Creado/Teminado KO)"        , store=True , readonly=True,default=0)

    # ===========================================================================================
    def _compute_tiempo(self ,sftime ):
    # ===========================================================================================
    
        _logger.info("_compute_tiempo fire : "+sftime)
                    
        fstate_1 = False
        fstate_2 = False
            
        if sftime=="tiempo_atender":
            fstate_1 = self.fstate_draft
            fstate_2 = self.fstate_confirmed
        if sftime=="tiempo_iniciar":
            fstate_1 = self.fstate_confirmed
            fstate_2 = self.fstate_under_repair
        elif sftime=="tiempo_tarea":
            fstate_1 = self.fstate_under_repair
            fstate_2 = self.fstate_done
        elif sftime=="tiempo_terminar":
            fstate_1 = self.fstate_draft
            fstate_2 = self.fstate_done
        elif sftime=="tiempo_cancelar":
            fstate_1 = self.fstate_draft
            fstate_2 = self.fstate_cancel
            
        if not fstate_1 or not fstate_2:
            self.update( {sftime : 0 })
        else:
            self.update( {sftime : fstate_2 - fstate_1 })
    # ===========================================================================================
    def _refresh_tiempo(self):
        
        aTiempos = []
        
        if self.fstate_confirmed:
            aTiempos.append('tiempo_atender')
        if self.fstate_under_repair:
            aTiempos.append('tiempo_iniciar')
        if self.fstate_done:
            aTiempos.append('tiempo_tarea')
            aTiempos.append('tiempo_terminar')
        if self.fstate_cancel:
            aTiempos.append('tiempo_cancelar')
        if self.fstate_ko_done:
            aTiempos.append('tiempo_cancelar')
            
        for sTiempo in aTiempos:
            self._compute_tiempo(sTiempo)
        
    # ==========================================
    def _compute_isariis(self):
        for rec in self:
            if rec.ariis_id and rec.ariis_id!='':
                rec.isariis = True
            else:
                rec.isariis = False
    # ===========================================================================================
    @api.onchange("partner_id")
    def onchange_partner_id(self):
        for rec in self:
            # rec.dispositivo_id = False
            rec._compute_isariis()
    # ===========================================================================================
    @api.onchange("dispositivo_id")
    def onchange_dispositivo_id(self):
        for rec in self:
            if rec.dispositivo_id:
                rec.product_id  = rec.dispositivo_id.product_id
                rec.lot_id      = rec.dispositivo_id.lot_id
            else:
                rec.product_id  = False
                rec.lot_id      = False
    # ===========================================================================================
    # ===========================================================================================
    @api.onchange("state")
    def _compute_state(self):
        for rec in self:
            _logger.info("onchange_state fire : "+rec.state)
            sFieldName = "fstate_" + rec.state
            # rec.write({sFieldName:fields.Datetime.now()} )
            rec[sFieldName] = fields.Datetime.now() 
    # ===========================================================================================
    def write(self,vals):

        if "state" in vals:
            state = vals['state']
            sFieldName = "fstate_" + state
            
            if not sFieldName in vals:
 
                if not self[sFieldName]:
                    vals[sFieldName] = fields.Datetime.now()
                    
        super(Repair,self).write(vals)
    # ===========================================================================================
    # ===========================================================================================
    # ===========================================================================================
    # ===========================================================================================
    # ===========================================================================================
    #===========================================================================
	# Campos de servicios
	#===========================================================================
	#===========================================================================
	# name = fields.Char( 
		# 'Referencia',default= lambda self: self.env['ir.sequence'].next_by_code('ariis.sat') , required=True)
	# type = fields.Selection([('1',"Dispositivo"),('2',"Producto")] ,string="Tipo" , copy=False ,default="1" )
	# partner_id = fields.Many2one(
		# 'res.partner', 'Cliente', change_default=True, track_visibility='onchange' ,
		# index=True, states={'03': [('readonly', True)]},
		# help='Choose partner for whom the order will be invoiced and delivered.',required=True)
	# state = fields.Selection([
		# ('01', 'Creado'),
		# ('02', 'Asignado'),
		# ('03', 'Abierto'),
		# ('08', 'Solicitada Pieza'),
		# ('09', 'Pieza en Proceso'),        
		# ('10', 'Pieza Entregada'),
		# ('04', 'Cerrado'),
		# ('05', 'Finalizado OK'),
		# ('06', 'Terminado KO'),
		# ('07', 'Cancelado')], string='Estado',
		# copy=False, default='01', states={'05': [('readonly', True)]}, track_visibility='onchange')


	# location_dest_id = fields.Many2one('stock.location', 'Delivery Location',
							# readonly=True,
							# states={'01': [('readonly', False)] })

	# department_sat	= fields.Many2one('hr.department', string='Departamento S.A.T' ,
						# readonly=True,related='product_id.department_sat')
	# is_responsable	= fields.Boolean('Es Responsable', copy=False, readonly=True ,store=False , compute=_isresponsable )
	# guarantee_limit = fields.Date('Warranty Expiration', states={'02': [('readonly', True)]} , translate=True)
	# quotation_notes = fields.Text(string='Quotation Notes', translate=True)
	# descripcion 	= fields.Text('Descripcion')

	# employee_id 	= fields.Many2one('hr.employee', string='Asignado a',index=True, track_visibility='always',required=True  , store=True  ,default=lambda self:self._gettecnico())


	# visita			= fields.Datetime("Prevista visita" ,required=True , track_visibility='onchange' ,default=_manyanamismahora)
	# duration		= fields.Float('Tiempo estimado',required=True, default=1.25)
	
	# fstate_01		= fields.Datetime('Creado' , readonly=True ,default=fields.Datetime.now )
	# fstate_02		= fields.Datetime('Asignado', readonly=True )
	# fstate_03		= fields.Datetime('Abierto', readonly=True )
	# fstate_04		= fields.Datetime('Cerrado', readonly=True )
	# fstate_05		= fields.Datetime('Finalizado OK', readonly=True )
	# fstate_06		= fields.Datetime('Terminado KO', readonly=True )
	# fstate_07		= fields.Datetime('Cancelado', readonly=True )
	# fstate_08		= fields.Datetime('Solicitada Pieza', readonly=True )
	# fstate_09		= fields.Datetime('Pieza en Proceso', readonly=True )
	# fstate_10		= fields.Datetime('Pieza Entregada', readonly=True )
	# creadopor		= fields.Char("Creado por" , track_visibility='onchange' ,default=lambda self: self.env['res.users'].browse(self._context.get('uid')).name )
	# firma 			= fields.Binary( 'Firma')
	# hace			= fields.Float( string="Hace" , compute="_dias_desde",digits=(2,1) )
	# tiempo_empleado = fields.Float( string="Tiempo empleado (Abrir/Cerrar)"         , store=True , readonly=True,default=0)
	# tiempo_tarea    = fields.Float( string="Tiempo Tarea (Asignado/Cerrado)"        , store=True , readonly=True,default=0 , group_operator ="avg" )
	# tiempo_total    = fields.Float( string="Tiempo Total (Creado/Fin)"              , store=True , readonly=True,default=0)
	# tiempo_entrega  = fields.Float( string="Tiempo en Entregar (Solicita/Entrega)"  , store=True , readonly=True,default=0)