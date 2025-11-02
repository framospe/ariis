{
    'name': 'ARIIS - FSM Requisitos Comerciales',
    'version': '18.0.1.0.0',
    'category': 'Sales/Customer Relationship Management',
    'summary': 'Gestión de vencimientos de contratos/garantías, clientes inactivos y análisis de ventas para el equipo comercial.',
    'author': 'Framospe', 
    'website': 'https://github.com/framospe/ariis',
    'license': 'AGPL-3',
    'depends': [
        'base',
        'sale',             # Para el análisis de ventas y actividad
        'maintenance',      # Para la gestión de garantías de Equipos
        'mail',             # Para el uso de Actividades (Alertas)
        'ariis_contrato',   # ¡CLAVE! Para gestionar los vencimientos de contratos
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/contract_cron_data.xml',      # Tareas programadas para vencimientos
        'views/res_partner_views.xml',      # Vistas para el cliente (inactividad)
        'views/maintenance_equipment_views.xml', # Vistas para la garantía
    ],
    'installable': True,
    'application': False,
}