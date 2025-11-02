{
    'name': 'ARIIS - FSM Integración MIR',
    'version': '18.0.1.0.0',
    'category': 'Services/Field Service',
    'summary': 'Integra los datos de lecturas (ariis_mir) con el Equipo de Mantenimiento para monitorización proactiva y trazabilidad.',
    'author': 'Framospe', 
    'website': 'https://github.com/framospe/ariis',
    'license': 'AGPL-3',
    'depends': [
        'base',
        'maintenance',          # Extender el Equipo
        'ariis_mir',            # ¡CLAVE! Módulos fuente de las lecturas
        'ariis_fsm_analytica',  # Para la imputación de costes (Cuenta Analítica)
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/mir_cron_data.xml',           # Tarea programada del día 20
        'views/maintenance_equipment_views.xml', # Vistas de lectura en el equipo
    ],
    'installable': True,
    'application': False,
}