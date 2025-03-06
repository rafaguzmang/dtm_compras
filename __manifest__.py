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
        'views/dtm_compras_odt_view.xml',
        'views/dtm_compras_servicios_views.xml',
        'views/dtm_compras_precios_view.xml',
        # Angular assets
        # 'views/angular_assets.xml',
        # Menú
        'views/dtm_menu.xml',
    ],
    # 'assets': {
    #     'web.assets_frontend': [
    #         'dtm_compras/static/src/angular/ordenes-seguimiento/browser/polyfills.js',
    #         'dtm_compras/static/src/angular/ordenes-seguimiento/browser/main.js',
    #         'dtm_compras/static/src/angular/ordenes-seguimiento/browser/scripts.js',
    #         'dtm_compras/static/src/angular/ordenes-seguimiento/browser/styles.css',
    #     ],
    # },
    'license': 'LGPL-3',
}
