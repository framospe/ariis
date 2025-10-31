# -*- coding: utf-8 -*-

{
   'name': "Ariis Contrato CXC version del 2025",
    'summary': 'Añade a Contratos los dispositivos CXC de Ariis',
    'description': """
        Añade  Contratos CXC para generar las facturas de CXC V3
    """,

    'author'		: "EcoIntegra S.A.",
    'website'		: "http://ariis.es/",
    'category'		: 'Ariis',
    'version'		: '0.3',
    'installable'	: True,
    'auto_install'	: False,
    'application'	: False,
    'depends'		: ['ariis_mir','sale_management','account' ,'contract'],
    'data'			: [
        "views/contract.xml",
        # "security/contract_security.xml",
        "views/contract_line_ariis_views.xml",
        "views/maintenance_equipment_views.xml",
        "views/mir_totalmes.xml",
        "views/mir_lectura_views.xml",
        "views/lectura_views.xml",
        "views/contract_portal_templates.xml",
        "views/res_partner_view.xml",
        "report/report_contract.xml",
        "report/contract_views.xml",
        "data/contrato_cron.xml",
        "data/mail_template.xml",
		] ,
    'license': 'LGPL-3'
}