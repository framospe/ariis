{
    'name': 'ARIIS - FSM Rentabilidad Analítica',
    'version': '18.0.1.0.0',
    'category': 'Accounting/Analytic',
    'summary': 'Extiende el Equipo de Mantenimiento para vincularlo a Cuentas Analíticas y calcular rentabilidad por activo.',
    'author': 'Framospe', # ¡Asegúrate de colocar tu nombre!
    'website': 'https://github.com/framospe/ariis',
    'license': 'AGPL-3',
    'depends': [
        'base',
        'maintenance',        # Para extender el modelo de Equipo
        'analytic',           # ¡CLAVE! Módulo de Contabilidad Analítica de Odoo
        'account',            # Módulo de Contabilidad
        # 'ariis_fsm_sat',    # Opcional: Para depender de nuestro core FSM si lo requerimos
    ],
    'data': [
        'views/maintenance_equipment_views.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'application': False,
}