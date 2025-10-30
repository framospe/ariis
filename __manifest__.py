# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{

    'name': "Ariis Base",
    'summary': 'Gestión de Coste por Copia',
    'description': """
        Gestión y Monitorización de Impresoras CXC
    """,

    'author'		: "EcoIntegra S.A.",
    'website'		: "http://ariis.es/",
    'category'		: 'Ariis',
    'version'		: '0.2',
    'auto_install'	: False,
    'sequence': 10,
    'depends': [ 'contacts' ,'stock','maintenance'],
    'data': [
        "views/menu.xml",
        "views/tas_views.xml",
        "views/product_template_views.xml",
        "views/res_partner_views.xml",
        "views/stock_lot_views.xml",
        'data/inittas.xml',
        'security/res_groups.xml',
        'data/initvalues.xml',
        "views/maintenance_equipment_views.xml",

    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
