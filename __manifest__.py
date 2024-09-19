{
    "name":"Compras",

    'version': '1.0',
    'author': "Rafael Guzmán",
    "description": "Modulo para el área de compras",
    "depends":['base', 'mail',"dtm_procesos"],
    "data":[
        #Security
        'security/ir.model.access.csv',
        'security/res_groups.xml',
        'security/model_access.xml',
        #Views
        'views/dtm_compras_requerido_views.xml',
        'views/dtm_compras_realizado_views.xml',
        'views/dtm_compras_odt_view.xml',
        'views/dtm_compras_servicios_views.xml',
        #Menú
        'views/dtm_menu.xml'

    ],
    'license': 'LGPL-3',
}

