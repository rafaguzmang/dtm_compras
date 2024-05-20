{
    "name":"Compras",

    'version': '1.0',
    'author': "Rafael Guzmán",
    "description": "Modulo para el área de compras",
    "depends":["dtm_procesos"],
    "data":[
        'security/ir.model.access.csv',
        #Views
        'views/dtm_compras_requerido_views.xml',
        'views/dtm_compras_realizado_views.xml',
        'views/dtm_compras_odt_view.xml',
        #Menú
        'views/dtm_menu.xml'

    ]
}

