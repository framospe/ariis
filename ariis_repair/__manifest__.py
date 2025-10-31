# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'Ariis Reparaciones',
    'version': '0.1',
    'sequence': 230,
    'category': 'Ariis/Inventory',
    'summary': 'Repair damaged products for Ariis',
    'description': """
The aim is to have a complete module to manage all products repairs.
====================================================================

The following topics are covered by this module:
------------------------------------------------------
    * Add/remove products in the reparation
    * Impact for stocks
    * Warranty concept
    * Repair quotation report
    * Notes for the technician and for the final customer
""",
    'depends': ['ariis','repair'],
    'data': [
        'views/repair_views.xml',
        'views/maintenance_equipment_views.xml',
        'data/data.xml',
        'security/gestion_security.xml',
    ],
    'demo': [],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
