# -*- coding: utf-8 -*-
{
    'name': "Ariis Mir",
    'summary': """
        Monitorización de Impresoras Remotas""",

    'description': """
        Reporting y Control de impresoras CXC
    """,

    'author': "Frank",
    'website': "http://www.ecointegra.es",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Ariis',
    'version': '0.2',

    # any module necessary for this one to work correctly 
    'depends': ['ariis'],

    # always loaded
	'auto_install'	: False,
    'application'	: False,
    'data': [
        "views/menu.xml",
        "views/lectura_views.xml",
        "views/mir_lectura_views.xml",
        'views/mir_totalmes_views.xml',
        'views/mir_suministro_views.xml',
        "views/maintenance_equipment_views.xml",
        "views/suministro_views.xml",
        'views/product_suministro_views.xml',
        'views/product_template_views.xml',
        'data/lectura_cron.xml',
        'data/ir_config_parameter.xml',
        'data/initvalues.xml',
        'security/usuario_security.xml',
        'security/gestion_security.xml',
        'security/ir.model.access.csv',

				
				# 'views/menumap.xml',
				# 'views/suministro.xml',
                # 'views/res_partner.xml',
                	
				# 'data/mir_lectura_cron.xml',
				# 'wizard/wizard_menumap.xml',
                # 'data/sale_data.xml',
				# 'security/usuario_security.xml',
				# 'security/tecnico_security.xml',
				# 'security/gestion_security.xml',
				# 'security/responsable_tecnico_security.xml',
			],
    'license': 'LGPL-3',
}