# -*- coding: iso-8859-1 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import odoo
import logging
import json

from odoo import api, fields, models
from odoo.exceptions import UserError
from datetime import datetime 
from dateutil.relativedelta import relativedelta

_logger = logging.getLogger(__name__)
_logger.disabled = False
#===========================================================================
class MirLectura(models.Model):
    _name           = 'ariis.mir.lectura'
    _inherit        = ['mail.thread', 'mail.activity.mixin']
    _description    = "Lectura MIR"

    name					= fields.Char( string='Nombre')
    unid					= fields.Char( string='UNID' , readonly=True)
    dispositivo_id			= fields.Char( string='Equipo Ariis' , readonly=True,index=True)
    cliente_id				= fields.Char( string='Cliente Ariis' , readonly=True,index=True)
    addressrequest			= fields.Char( string='Direccion Local', readonly=True )
    contacto				= fields.Char( string='Contacto', readonly=True )
    encendidohace			= fields.Char( string='Encendido desde', readonly=True )
    estado					= fields.Char( string='Estado', readonly=True )
    hostname				= fields.Char( string='Hostname', readonly=True ) 
    ipaddress				= fields.Char( string='IPAddress' , readonly=True)
    localizacion			= fields.Char( string='Localizacion' , readonly=True )
    macaddress				= fields.Char( string='MACAddress' , readonly=True)
    modelo					= fields.Char( string='Modelo' , readonly=True)
    nombre					= fields.Char( string='Nombre Equipo' , readonly=True)
    sysObject				= fields.Char( string='SysObject' , readonly=True)
    serialnumber			= fields.Char( string='Numero de Serie', readonly=True ,index=True)
    esquema					= fields.Char( string='Esquema MIR', readonly=True )
    errortext				= fields.Char('Mensaje de error', readonly=True)
    errordesc				= fields.Char('Descripcion del error', readonly=True)
    #=======================
    creado					= fields.Datetime( string='Leido' , index=True)
    #=======================
    isfusorinverso			= fields.Boolean( string='Fusor Inverso', readonly=True )
    tratada					= fields.Boolean( string='Tratada' )
    preparada				= fields.Boolean( string='Preparada' )
    #=======================
    origen					= fields.Selection([
                                ('01', 'MIR'),
                                ('02', 'Mail'),
                                ('03', 'Manual'),
                                ('99','Other')], string='Origen',copy=False, default='02' , readonly=True )
    #=======================
    total_pag_color			= fields.Integer( string='Total Pag Color'   )
    total_pag_impresas		= fields.Integer( string='Total Pag Impresa' )
    total_pag_mono			= fields.Integer( string='Total Pag Mono'  )	
    totalpaginasdiff		= fields.Integer( string='Total Pag Diferencia' , readonly=True)
    

    descripcion				= fields.Text( string='Descripcion', readonly=True )
    #=======================
    estado_id 				= fields.Many2one( 'ariis.estadodispositivo', string='Resultado'  )
    cliente 				= fields.Many2one( 'res.partner', 'Cliente' , index=True , readonly=True )
    dispositivo				= fields.Many2one( 'maintenance.equipment', string='Equipo'   ,index=True , readonly=True )
    lectura					= fields.Many2one( 'ariis.lectura', string='Lectura' , readonly=True    )
    totalmes				= fields.Many2one( 'ariis.total.mes', string='Total Mes' , readonly=True    )
    iscolor					= fields.Boolean('Color', readonly=True , related='dispositivo.iscolor')
    #=======================
    suministros_ids			= fields.One2many( 'ariis.mir.suministro','mir_lectura', 'Suministros' ,copy=False , ondelete='cascade' )
    #===========================================================================
    oModelo = False
    #===========================================================================
    def getCampos( self , message_id ):

        IrConfigParam = self.env['ir.config_parameter'].sudo()
        I_FIELDS_MAIL_PARSE_STRING = IrConfigParam.get_param('I_FIELDS_MAIL_PARSE', False) 
        I_FIELDS_MAIL_PARSE = json.loads(I_FIELDS_MAIL_PARSE_STRING)

        I_FIELDS_MAIL_PARSE['<>Serial No.'] = 'serialnumber'    #Pufff no hay manera
        
        oRegistro = {}
        oRegistro['Queda poco'] = []

        oValues = {}
        oValues['unid']     = message_id.message_id
        oValues['creado']   = message_id.date
        oValues['tratada']  = False
        oValues['preparada']= True
        oValues['origen']   = '02'
        
        if self.name and ("ariis-SN-" in self.name or "ariis-" in self.name):
            aNames					= self.name.split(':')
            aSerial					= aNames[1].split('-')
            oValues['serialnumber']	= aSerial[2].strip() 
            oValues['estado']		= aNames[2]
            oValues['descripcion']	= self.name

        # _logger.info(message_id.body)
        
        sTest	= (chr(13)+message_id.body).replace('<pre>','').replace('</pre>','').replace('<pre>Serial No.','Serial No.').replace('pre','').replace('</>','').replace('<>','').replace('&gt;=','')

        text	= sTest.replace(': ::',':').replace('<pre>','').replace('</pre>','')
        text	= text.replace(chr(162),'o')
        text	= text.replace(chr(10),chr(13)).replace(chr(13)+chr(13),chr(13))
        text	= text.replace('<pre>','').replace('</pre>','').replace('pre','').replace('<>','').replace('&gt;=','').replace('<>Serial No.','Serial No.')

        # _logger.info(text)

        aLineas = text.split(chr(13)) 
        
        for sLinea in aLineas:

            if 'Ethernet:' in sLinea:
                sLinea = sLinea.replace(':','#').replace('Ethernet#','Ethernet:')
                aLinea = sLinea.split(':')
                aLinea[1] = aLinea[1].replace('#',":")
            else:
                aLinea = sLinea.split(':')

            if len(aLinea)==2 and aLinea[1].strip()!='':
            
                sField = aLinea[0].strip()
                sValue = aLinea[1].strip()

                if sField=='Queda poco':
                    if not sValue in oRegistro[sField]:
                        oRegistro[sField].append(sValue)
                else:
                    oRegistro[sField] = sValue
            
                if sField in I_FIELDS_MAIL_PARSE:
                    oValues[I_FIELDS_MAIL_PARSE[sField]] = oRegistro[sField]

        # _logger.info('=======================')
        # _logger.info(oRegistro)

        return oValues
    #===========================================================================
    def prepara(self):

 
        # _logger.info('=====Preparando==================')
        # _logger.info('Prepara '+self.name)
        # _logger.info(self.message_ids)
        # _logger.info(self.message_ids[0].body)
        
        if self.origen!='02':
            return True

        oValues = self.getCampos(self.message_ids[0])
 
        _logger.info('===========Valores Iniciales============')
        _logger.info(oValues)
        _logger.info('=======================')

        self.update( oValues )
        
        if self.serialnumber or self.hostname or self.macaddress:
            self.setDispositivo(oValues)
            if self.errortext!="OK":
                return False

        self.update( oValues )
        self.checkTotales(oValues)
        
        oValues['preparada'] = True

        self.update( oValues )

        return True
    #===========================================================================
    #===========================================================================
    # updateDispositivo
    #===========================================================================
    def updateDispositivo(self, oDispositivo):

        if oDispositivo:
            
            isSave = False
            
            if self.serialnumber and not self.serialnumber=='' and oDispositivo.serial_no!=self.serialnumber:
                oDispositivo.serial_no = self.serialnumber
                isSave = True

            if self.ipaddress and not self.ipaddress=='' and oDispositivo.ipaddress!=self.ipaddress:
                oDispositivo.ipaddress = self.ipaddress
                isSave = True

            if self.macaddress and not self.macaddress=='' and oDispositivo.macaddress!=self.macaddress:
                oDispositivo.macaddress = self.macaddress
                isSave = True
                
            if  self.nombre and not self.nombre=='' and oDispositivo.name!=self.nombre:
                oDispositivo.nombre = self.nombre
                isSave = True
                
            if  self.modelo and not self.modelo=='' and oDispositivo.model!=self.modelo:
                oDispositivo.model = self.modelo
                isSave = True

            if self.localizacion and not self.localizacion=="":
                if not self.localizacion == oDispositivo.localizacion:
                    oDispositivo.localizacion = self.localizacion
                    isSave = True

            if not oDispositivo.instalado:
                oDispositivo.instalado = self.creado.date()
                isSave = True

            if hasattr(self ,'contrato_line'): 
                if oDispositivo.contrato_line and oDispositivo.partner_id.id != oDispositivo.ariis_contrato_id.partner_id.id:
                    oDispositivo.contrato_line = False
                    isSave = True
                
            if isSave:
                oDispositivo.state = "0"
                oDispositivo.save()
    #===========================================================================
    # setDispositivo
    #===========================================================================
    def setDispositivo(self,oValues):
        
        aSearch = []
        oFieldsValue = {}

        oValues['descripcion']       = self.name

        if self.serialnumber:
            aSearch.append(('lot_id','=',self.serialnumber ))
            sErrordesc  ="Dispositivo no encontrado S/N: "+self.serialnumber
        else:
            if self.hostname:
                aSearch.append(('hostname','=',self.hostname ))
                sErrordesc  ="Dispositivo no encontrado con Hostname: "+self.hostname
            else:
                aSearch.append(('macaddress','=',self.macaddress ))
                sErrordesc  ="Dispositivo no encontrado con MAC: "+self.macaddress

        _logger.info('Buscando ' +str(aSearch))

        oDispositivo = self.env['maintenance.equipment'].search( aSearch , limit=1 )
        
        if oDispositivo:
            
            _logger.info('Encontrado dispositivo ' +str(aSearch))
            
            self.updateDispositivo(oDispositivo)
                
            oValues['dispositivo']		= oDispositivo.id
            oValues['dispositivo_id']	= oDispositivo.ariis_id
            oValues['cliente_id']		= oDispositivo.partner_id.ariis_id

            self.addIsNotContain( oValues ,'serialnumber'	, oDispositivo.lot_id.name  )
            self.addIsNotContain( oValues ,'macaddress'		, oDispositivo.macaddress  )
            self.addIsNotContain( oValues ,'hostname'		, oDispositivo.hostname  )
            self.addIsNotContain( oValues ,'modelo'			, oDispositivo.product_id.name  )
            self.addIsNotContain( oValues ,'cliente'		, oDispositivo.partner_id.id  )
            
            oValues['name']         = 'Ariis Lectura de : ' + oDispositivo.lot_id.name
            oValues['descripcion']  = self.name 
            
            if not 'estado' in oValues:
                oValues['estado']= 'Notificación de Total Paginas : ' + oDispositivo.lot_id.name
 
            self.errortext='OK'

        else:
            self.setEstado({'estado_id': self.env.ref('ariis.ariis_estadodispositivo_10') ,
                            'errortext': "Dispositivo No Encontrado" ,
                            'errordesc': sErrordesc })
    #===========================================================================
    def addIsNotContain(self ,oValues , sKey ,sValue ):
        if not sKey in oValues or not oValues[sKey]:
            oValues[sKey] = sValue
    #===========================================================================
    def setFieldDispositivo( self , sField , sValue , oDispositivo ):

        if sValue and sValue!="":
            if sValue!=self.dispositivo[sField]:
                self.dispositivo[sField] = sValue
    #===========================================================================
    def checkTotales(self,oValues):

        if 'total_pag_mono' in oValues and not 'total_pag_color' in oValues and not 'total_pag_impresas' in oValues:
            oValues['total_pag_color'] = "0"

        if 'total_pag_color' in oValues and 'total_pag_mono' in oValues and not 'total_pag_impresas' in oValues:
            oValues['total_pag_impresas'] = int(oValues['total_pag_color']) + int(oValues['total_pag_mono'])
        else:
            oValues['total_pag_impresas']   = self.dispositivo.total_pag
            oValues['total_pag_color']      = self.dispositivo.total_color
            oValues['total_pag_mono']       = self.dispositivo.total_bn

    #===========================================================================
    def removeOlds(self,nDias):
    
        sfecha = fields.Date.today() 
        dfecha = fields.Date.from_string(sfecha) + relativedelta(days=nDias)
        sfecha = fields.Date.to_string(dfecha)

        founds = self.env[self._name].search(['&',('creado','<=',sfecha),('tratada','=',True)])
        
        founds.unlink()
    #===========================================================================
    def tratarLecturasMail(self):
    
        _logger.info('==================================================================' )
        _logger.info('INICIO de proceso de tratar Lecturas Mail')
        
        registros = self.search([('tratada','=',False)])
        _logger.info('Lecturas Mail encontradas : '+str(len(registros)))
        _logger.info('==================================================================' )

        for lectura in registros:
            lectura.runEntry()
            
        _logger.info('FIN de proceso de tratar Lecturas')
        _logger.info('==================================================================' )


    def prepararLecturasMail(self):
        #===========================================================================
        _logger.info('==================================================================' )
        _logger.info('INICIO de proceso de Preparar Lecturas Mail')
        
        # registros = self.search([('preparada','=',False)])
        # _logger.info('Lecturas Mail encontradas : '+str(len(registros)))
        
        for lectura in self:
            lectura.prepara()
            
        _logger.info('FIN de proceso de Preparar Lecturas Mail')
        _logger.info('==================================================================' )

    #===========================================================================
    # getDispositivo
    #===========================================================================
    def getDispositivo(self,sDispositivoID):
        if not sDispositivoID or sDispositivoID=="":
            if self.dispositivo:
                _logger.info('retorna dispositivo : '+str(self.dispositivo))
                return self.dispositivo
        _logger.info('Buscando dispositivo : '+str(sDispositivoID))
        return self.env['maintenance.equipment'].search([('ariis_id','=',sDispositivoID)] , limit=1 )
    #===========================================================================
    def runEntry (self):
        # _logger.info('==================')
        # _logger.info('Iniciando runEntry ')

        if self.isValid(): 
            self.preProcesa()
            self.procesa()
            self.postProcesa()
        else:
            self.notValid()
            
        # _logger.info('commit')
        self.env.cr.commit()
        
        # _logger.info('Fin runEntry ')
    #===========================================================================
    # isValid
    #===========================================================================
    def isValid(self):
    
        if not self.prepara():
            self.setEstado({	'estado_id': self.env.ref('ariis.ariis_estadodispositivo_10') ,
                                'errortext': self.errortext ,
                                'errordesc': self.errordesc })
                                
            _logger.info('Lecturas Mail '+ str(self.serialnumber) +' runEntry.isValid : False')
            
            return False

        if not self.cliente_id or self.cliente_id=='':
            self.setEstado({	'estado_id': self.env.ref('ariis.ariis_estadodispositivo_10') ,
                                'errortext': "Cliente Ariis vacio no es valido" ,
                                'errordesc': 'Cliente Ariis no es valido' })
            return False

        self.cliente 		= self.getCliente(self.cliente_id)
        
        if not self.cliente:
            self.setEstado({	'estado_id': self.env.ref('ariis.ariis_estadodispositivo_10') ,
                                'errortext': "Cliente No Encontrado" ,
                                'errordesc': 'Cliente no encontrado: '+self.cliente_id })
            return False

        # _logger.info('Buscar dispositivo : ' +str(self.dispositivo_id))
        
        self.dispositivo 	= self.getDispositivo(self.dispositivo_id)
        
        if not self.dispositivo:
            self.setEstado({'estado_id': self.env.ref('ariis.ariis_estadodispositivo_10') ,
                            'errortext': "Equipo No Encontrado" ,
                            'errordesc': "Equipo no encontrado: "+self.dispositivo_id })
            return False
        # else:
            # self.oModelo = self.dispositivo.product_id
            
        if self.serialnumber and 'PBA_i-DPT_USBN' in self.serialnumber:
            self.serialnumber = ""
        #======================================================================
        #Si no tiene numero de serie y coincide la direccion mac entonces copia
        # el numero de serie del dispositivo
        #======================================================================
        if not self.serialnumber or self.serialnumber.rstrip()=="":
            _logger.info('Tratando Lectura sin numero de serie: %s ' % str(self.id))
            if self.dispositivo.macaddress  and self.macaddress and self.dispositivo.macaddress.rstrip()  == self.macaddress.rstrip():
                self.serialnumber = self.dispositivo.lot_id.name.rstrip()
        #======================================================================
        # Si el numero de serie no coincide la maquina se cambio
        #======================================================================
        if self.serialnumber.rstrip() != self.dispositivo.lot_id.name.rstrip() :
            self.setEstado({'estado_id': self.env.ref('ariis.ariis_estadodispositivo_09') ,
                            'errortext': "Numero de Serie no coincide." ,
                            'errordesc': "Numero de Serie leido: " + self.serialnumber.rstrip() if self.serialnumber else self.descripcion })
            self.dispositivo.save()
            
            return False
            
        if self.isTotalesError():
            
            self.setEstado({'estado_id': self.env.ref('ariis.ariis_estadodispositivo_10') ,
                            'errortext': "Numero de Pag. Incorrecto" ,
                            'errordesc': "(Total no valido)" })
            
            self.dispositivo.last_report 	= self.creado
            self.dispositivo.save()
            
            return False
                                
        return True
    #===========================================================================
    # preProcesa
    #===========================================================================
    def preProcesa(self):
        # _logger.info('Preproceso ')
        
        self.setEstado({'estado_id': self.env.ref('ariis.ariis_estadodispositivo_01'), 'errortext': "" , 'errordesc': "" })
        self.dispositivo.hostnameleido = self.hostname   

        if not self.dispositivo.first_report:
            self.dispositivo.first_report 	= self.creado

        if self.origen!="01":
            return
            
            self.historificaAllSuministros()

            
        return
    #===========================================================================
    # Procesa
    #===========================================================================
    def procesa(self):

        # _logger.info('procesa')
        
        self.totalpaginasdiff = (self.total_pag_impresas - self.dispositivo.total_pag )
        self.dispositivo.last_report 	= self.creado
        
        if self.totalpaginasdiff > 0:
            #=======================================
            #Dispositivo con nuevas paginas impresas 
            #=======================================
            self.dispositivo.total_pag		= self.total_pag_impresas
            self.dispositivo.total_bn		= self.total_pag_mono
            self.dispositivo.total_color	= self.total_pag_color
            
            if not self.ipaddress=="":
                self.dispositivo.ipaddress = self.ipaddress
            if self.macaddress and not self.macaddress=="":
                self.dispositivo.macaddress = self.macaddress
            if not self.nombre=="":
                self.dispositivo.nombre = self.nombre
            if not self.dispositivo.instalado:
                self.dispositivo.instalado = self.creado.date()

            if self.localizacion and not self.localizacion=="":
                if not self.localizacion == self.dispositivo.localizacion:
                    self.dispositivo.localizacion = self.localizacion
                    
            self.dispositivo.save()
            
            self.addTotalPrint()
            
            if self.origen=="01":
                self.updateSuministros()
            #=======================================
        else:
            if self.totalpaginasdiff < 0:
                self.setEstado({
                                'estado_id': self.env.ref('ariis.ariis_estadodispositivo_10') ,
                                'errortext': "Total de Pag. Impresas menor." ,
                                'errordesc': "(Leido " +  str(self.total_pag_impresas) + " pag.)"
                                })
            self.dispositivo.save()

        return
    #===========================================================================
    # postProcesa
    #===========================================================================
    def postProcesa(self):
        # _logger.info('postProcesa')

        self.update({ 'tratada' : True })
        # _logger.info('Grabada Lectura Fin OK')
        
        return
    #===========================================================================
    # notValid
    #===========================================================================
    def notValid(self):
        self.update({ 'tratada' : True })
        # _logger.info('Grabada Lectura Fin No Valido')
        return
    #===========================================================================
    # getCliente
    #===========================================================================
    def getCliente(self,sClienteID):
        # _logger.info('Buscando Cliente: '+sClienteID)
        if self.cliente:
            return self.cliente
        return self.env['res.partner'].search([('ariis_id','=',sClienteID)])
    #===========================================================================
    # getDispositivo
    #===========================================================================
    def getDispositivo(self,sDispositivoID):
        oClassEquipo = self.env['maintenance.equipment']
        
        if not sDispositivoID or sDispositivoID=="":
            if self.dispositivo:
                return self.dispositivo

        return oClassEquipo.search([('ariis_id','=',sDispositivoID)] , limit=1)
    #===========================================================================
    # isTotalesError
    #===========================================================================
    def isTotalesError(self):
        return (self.total_pag_color + self.total_pag_mono<=0)
    #===========================================================================
    # addTotalPrint
    #===========================================================================
    def addTotalPrint(self):
        # _logger.info('addTotalPrint')
        
        self.lectura = self.getLectura()
        
        if not self.lectura:
            self.lectura	= self.creaLectura()
        else:
            self.lectura.state ='01'
            
        self.lectura.actual_lectura		= self.creado.date()
        self.lectura.actual_total		= self.total_pag_impresas
        self.lectura.actual_total_bn	= self.total_pag_mono
        self.lectura.actual_total_color	= self.total_pag_color
        
        if not self.totalmes:
            self.totalmes	= self.getTotalMes()
            
        if not self.lectura.totalmes:
            self.lectura.totalmes	= self.totalmes

        # if not self.lectura.contrato:
            # self.lectura.contrato_id	= self.totalmes.contrato_line.contrato_id
            
        self.totalmes.tratado 		= False
        self.totalmes.last_report	= self.creado
        self.totalmes.save()
        
        self.lectura.save()
    #===========================================================================
    # getLectura
    #===========================================================================
    def getLectura(self):
        # _logger.info('getLectura')
    
        oClass = self.env['ariis.lectura']
              
        sFecha = fields.Date.to_string(self.creado.date())
        
        # _logger.info('sFecha')
        # _logger.info(sFecha)
        
        return oClass.search([	('partner_id','=',self.cliente.id),
                                ('dispositivo_id','=',self.dispositivo.id),
                                ('actual_lectura','=',sFecha)],limit=1)
    #===========================================================================
    def getLecturaValuesNew(self ,oLecturaAnterior ):
    
        vals                    = {}
        vals['ariis_id']		= self.unid
        vals['dispositivo_id']	= self.dispositivo.id
        vals['partner_id']		= self.cliente.id
        vals['numeroserie']		= self.dispositivo.lot_id.name
        vals['modelo']			= self.dispositivo.product_id.name 

        vals['state']			= '01'
        vals['origen']			= self.origen
        vals['last_report']		= self.creado

        if oLecturaAnterior:
            # _logger.info('Lectura anteior existe id: ' + str(oLecturaAnterior.id))
            vals['previo_lectura']		= oLecturaAnterior.actual_lectura
            vals['previo_total_bn']		= oLecturaAnterior.actual_total_bn
            vals['previo_total_color']	= oLecturaAnterior.actual_total_color
            vals['previo_total']		= oLecturaAnterior.actual_total
        else:
            vals['previo_lectura']		= self.creado
            vals['previo_total_bn']		= 0
            vals['previo_total_color']	= 0
            vals['previo_total']		= 0
        
        return vals
    #===========================================================================
    # creaLectura
    #===========================================================================
    #===========================================================================
    def creaLectura(self):
        #_logger.info('creaLectura')
        
        oClass = self.env['ariis.lectura']
        
        oLecturaAnterior = oClass.search([	('partner_id','=',self.cliente.id), ('dispositivo_id','=',self.dispositivo.id)] ,limit=1)
                                            
        vals = self.getLecturaValuesNew(oLecturaAnterior)

        return oClass.create(vals)
    #===========================================================================
    # historificaallsuministros()
    #===========================================================================
    def historificaAllSuministros(self):
        # _logger.info('historificaallsuministros')
        
        lSuministros = self.dispositivo.getSuministros(('01','02','99'))
        
        for oSuministro in lSuministros:
            self.dispositivo.historificaSuministro( oSuministro )
            
        return
    #===========================================================================
    # setEstado(self.vals)
    #===========================================================================
    def setEstado(self,vals):
    
        self.update(vals)
        
        if self.dispositivo:
            self.dispositivo.update(vals)
            
        return
    #===========================================================================
    # updateSuministros
    #===========================================================================
    def updateSuministros(self):
        # _logger.info('updateSuministros')

        oClassSuministro = self.env['ariis.suministro']
        
        for oSuministroPos in self.suministros_ids:
        
            isNew 		= False
            oSuministro = self.dispositivo.getSuministroByNumber( oSuministroPos.numero )
        
            if not oSuministro:	
                # _logger.info('updateSuministros: No Encontrado')
                oSuministro = self.dispositivo.getNewSuministroFrom( oSuministroPos )
                isNew = True
            else:
                # _logger.info('updateSuministros: Encontrado')
                
                if oSuministro.isEsperandoCambio():
                    # _logger.info('updateSuministros: Esta esperando cambiarlo')
                    # '==================================================================
                    # ' TODO: Chequear que el suministro no esta esperando ser cambiado y si 
                    # ' lo esta pasar a historico si el porcentaje de la nueva lectura es mayor
                    # ' que el actual. Grabar numero de paginas totales impresas con este
                    # ' suministro
                    # '==================================================================
                    if oSuministro.isNivelMenor( oSuministroPos.nivel ):
                        
                        # _logger.info('updateSuministros: Nivel es Mayor') 
                        last_send = oSuministro.last_send
                        
                        self.dispositivo.historificaSuministro( oSuministro )  
                        # '===========================================================
                        # ' Crear uno nuevo con la nueva lectura
                        # '===========================================================
                        oSuministro	= self.dispositivo.getNewSuministroFrom( oSuministroPos )
                        
                        oSuministro.last_send = last_send
                        # _logger.info('updateSuministros: Suministro Nuevo Creado')
                        isNew 		= True
            # '====================================
            oSuministro.nivel			= oSuministroPos.nivel	
            oSuministro.porcentaje		= oSuministroPos.porcentaje
            oSuministro.last_report 	= self.dispositivo.last_report
            oSuministro.total_pag 		= self.dispositivo.total_pag

            oSuministro.save()
            # '================================================================================
            # ' Aqui se solicita el suministro si el cliente tiene un nivel minimo de solicitud
            # ' y el suministro es consumible y esta por debajo de este nivel 	
            # '================================================================================
            if oSuministro.isConsumible():
                if self.cliente.isCheckSuministro():
                    if oSuministro.isSolicita(self.cliente.solicitasuministros):
                            oSuministro.solicita()
                    # self.dispositivo.solicitaSuministros(self.cliente.solicitasuministros)

        return
    #===========================================================================
    # getTotalMes
    #===========================================================================
    def getTotalMes(self):
        #_logger.info('getTotalMes')
        
        aSearch = []
        
        aSearch.append(('cliente','=',self.cliente.id))
        aSearch.append(('dispositivo','=',self.dispositivo.id))
        aSearch.append(('periodo','=',self.inicioMes()))
        
        totalmes = self.env['ariis.total.mes'].search(aSearch,limit=1)

        if totalmes:
            totalmes.write({'tratado': False})
            return totalmes
        
        totalmes = {}
        
        totalmes['name']			= "Total Mes "+str(self.inicioMes())+ " ("+self.dispositivo.lot_id.name+")"
        totalmes['tratado']			= False
        totalmes['creado']			= self.creado
        totalmes['last_report']		= self.creado
        totalmes['periodo']			= self.inicioMes()
        
        totalmes['cliente']				= self.cliente.id
        totalmes['dispositivo']			= self.dispositivo.id
        
        totalmes['ini_periodo']			= self.lectura.previo_lectura		
        totalmes['ini_total_pag_bn']	= self.lectura.previo_total_bn
        totalmes['ini_total_pag_color']	= self.lectura.previo_total_color
        
        totalmes['fin_periodo']			= self.creado
        totalmes['fin_total_pag_color']	= self.total_pag_color
        totalmes['fin_total_pag_bn']	= self.total_pag_mono
 
        return self.env['ariis.total.mes'].create(totalmes)
    #===========================================================================
    # inicioMes
    #===========================================================================
    def inicioMes(self):
        #aFechas = self.creado.split(" ")[0].split("-")
        aFechas = fields.Date.to_string(self.creado.date()).split("-")
        return (aFechas[0]+"-"+aFechas[1]+"-01")
    #===========================================================================
    def removeOlds(self,nDias):
    
        sfecha = fields.Date.today() 
        dfecha = fields.Date.from_string(sfecha) + relativedelta(days=nDias)
        sfecha = fields.Date.to_string(dfecha)

        founds = self.env["ariis.mir.lectura"].search(['&',('creado','<=',sfecha),('tratada','=',True)])
        
        founds.unlink()
    #===========================================================================
    #===========================================================================
    def tratarlecturas(self,limit=1000):

        registros = self.search([('tratada','=',False)], limit=limit)
        
        if registros:
            _logger.info('==================================================================' )
            _logger.info('INICIO de proceso de tratar Lecturas : '+str(len(registros)))
        
            for lectura in registros:
                lectura.runEntry()
                
            _logger.info('FIN de proceso de tratar Lecturas')
            _logger.info('==================================================================' )
    #===========================================================================
