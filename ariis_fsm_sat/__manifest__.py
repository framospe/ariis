{
    'name': 'ARIIS - Field Service Management (SAT Core)',
    'version': '18.0.1.0.0',
    'category': 'Services/Field Service',
    'summary': 'Extiende la funcionalidad de Field Service y Mantenimiento para la trazabilidad y costes del SAT.',
    'author': 'Framospe', 
    'website': 'https://github.com/framospe/ariis',
    'license': 'AGPL-3',
    'depends': [
        'base',
        'project',          # Base para Tareas/FSM
        'maintenance',      # Para la gestión de Equipos (Activos)
        'hr_timesheet',     # Para el control de Mano de Obra (MO)
        'stock',            # Para el control de Piezas consumidas
        'analytic',         # CLAVE para Contabilidad Analítica
        'ariis_fsm_analytica', # CLAVE para obtener la cuenta analítica del Equipo
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/maintenance_equipment_views.xml',
        'views/project_task_views.xml',       # <-- ¡Añadir esta vista!
    ],
    'installable': True,
    'application': False,
}