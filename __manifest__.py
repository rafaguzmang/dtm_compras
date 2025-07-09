{
    'name': 'Compras',
    'version': '1.0',
    'author': 'Rafael Guzmán',
    'description': 'Módulo para el área de compras',
    'depends': ['base', 'mail', 'dtm_procesos','web'],
    'data': [
        # Security
        'security/ir.model.access.csv',
        'security/res_groups.xml',
        'security/model_access.xml',
        # Views
        'views/dtm_compras_requerido_views.xml',
        'views/dtm_compras_realizado_views.xml',
        'views/dtm_compras_servicios_views.xml',
        'views/dtm_compras_precios_view.xml',
        'views/seguimiento_compras_view.xml',
        # Angular assets
        # 'views/angular_assets.xml',
        # Menú
        'views/dtm_menu.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'dtm_compras/static/src/js/seguimiento_compras.js',
            'dtm_compras/static/src/xml/seguimiento_compras.xml',
            'dtm_compras/static/src/js/dialog_materiales.js',
            'dtm_compras/static/src/xml/dialog_material_template.xml'
        ],
    },
    'license': 'LGPL-3',
}
