{
    'name': 'Actualización USD desde Banxico',
    'version': '14.0.1.0.0',
    'category': 'Accounting',
    'summary': 'Actualiza automáticamente el tipo de cambio USD desde Banxico',
    'author': 'Luis Toledo',
    'depends': ['base', 'account'],
    'data': [
        'data/ir_cron.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'application': False,
}
