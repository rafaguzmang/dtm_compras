from collections import defaultdict
import json
from odoo import http
from odoo.http import request
import unicodedata


class ComprasWebSiteDirections(http.Controller):
    @http.route('/dtm_compras/get_data', type='http', auth='public', csrf=False)
    def get_compras(self, **kw):
        list_ordenes = []
        ordenes = request.env['dtm.compras.requerido'].sudo().search([])

        for orden in ordenes:
            datos_orden = request.env['dtm.odt'].sudo().search([
                ('ot_number', '=', orden.orden_trabajo),
                ('revision_ot', '=', orden.revision_ot)
            ])
            po_pdf = request.env['dtm.compras.items'].sudo().search([('orden_trabajo','=',orden.orden_trabajo)],limit=1).model_id.archivos_id
            list_ordenes.append({
                'orden_trabajo': orden.orden_trabajo,
                'tipo_orden': orden.tipo_orden,
                'revision_ot': orden.revision_ot,
                'proveedor_id': orden.proveedor_id.nombre if orden.proveedor_id else False,
                'codigo': orden.codigo,
                'nombre': orden.nombre,
                'cantidad': orden.cantidad,
                'unitario': orden.unitario,
                'costo': orden.costo,
                'orden_compra': orden.orden_compra,
                'fecha_recepcion': orden.fecha_recepcion.isoformat() if orden.fecha_recepcion else None,
                'disenador': orden.disenador,
                'observacion': orden.observacion,
                'aprovacion': orden.aprovacion,
                'permiso': orden.permiso,
                'servicio': orden.servicio,
                'en_compras':orden.create_date.isoformat() if orden.create_date else None,
                'listo': orden.listo,
                'nesteo': orden.nesteo,
                'cliente': datos_orden.name_client if orden.tipo_orden in ['OT', 'NPI'] else 'Requisición de Material',
                'date_rel': datos_orden.date_rel.isoformat() if datos_orden.date_rel else None,
                'product_name': datos_orden.product_name if datos_orden else None,
                'po_pdf_url': f'/web/content/{po_pdf.id}?mimetype=application/pdf&download=false' if po_pdf else None
            })

        # Agrupar por cliente y orden_trabajo
        agrupado = defaultdict(lambda: defaultdict(list))
        for item in list_ordenes:
            cliente = item['cliente']
            orden = item['orden_trabajo']
            agrupado[cliente][orden].append(item)

        resultado = {cliente: dict(ordenes) for cliente, ordenes in agrupado.items()}

        # === Aquí empieza la parte de ordenado ===

        def limpiar_texto(texto):
            if not texto:
                return ''
            texto = unicodedata.normalize('NFKD', texto)
            texto = texto.encode('ASCII', 'ignore').decode('utf-8')
            return texto.lower()

        def obtener_prioridad(item):
            nombre = limpiar_texto(item['nombre'])

            # Primero: Lámina
            if 'lamina' in nombre:
                return 0

            # Segundo: perfilería
            perfileria = ['angulos', 'canales', 'ipr', 'ptr', 'perfil', 'polin', 'tubo', 'varilla', 'viga']
            for palabra in perfileria:
                if palabra in nombre:
                    return 1

            # Tercero: otros
            return 2

        # Ordenar cada lista de items según prioridad
        for cliente, ordenes in resultado.items():
            for orden, items in ordenes.items():
                ordenes[orden] = sorted(items, key=lambda i: (obtener_prioridad(i), limpiar_texto(i['nombre'])))


        # === Fin de la parte de ordenado ===

        return request.make_response(
            json.dumps(resultado),
            headers={
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
            }
        )



class CompradoWebSite(http.Controller):
    @http.route('/dtm_comprado/get_data', type='json', auth='public', csrf=False)
    def get_compras(self, **kw):
        list_ordenes = []
        ordenes = request.env['dtm.compras.realizado'].sudo().search([('comprado','!=','Recibido')])
        print(ordenes)
        for orden in ordenes:
            datos_orden = request.env['dtm.odt'].sudo().search([
                ('ot_number', '=', orden.orden_trabajo),
                ('revision_ot', '=', orden.revision_ot)
            ])

            list_ordenes.append({
                'orden_trabajo': orden.orden_trabajo,
                'revision_ot': orden.revision_ot,
                'proveedor_id': orden.proveedor,
                'codigo': orden.codigo,
                'nombre': orden.nombre,
                'cantidad': orden.cantidad,
                'unitario': orden.unitario,
                'costo': orden.costo,
                'orden_compra': orden.orden_compra,
                'fecha_recepcion': orden.fecha_recepcion.isoformat() if orden.fecha_recepcion else None,
                'en_compras': orden.solicitado.isoformat() if orden.solicitado else None,
                'cliente': datos_orden.name_client if datos_orden.name_client else 'Requisición de Material',
                'date_rel': datos_orden.date_rel.isoformat() if datos_orden.date_rel else None,
                'product_name': datos_orden.product_name if datos_orden else None,
            })
        # Agrupar por cliente y orden_trabajo
        agrupado = defaultdict(lambda: defaultdict(list))
        for item in list_ordenes:
            cliente = item['cliente']
            orden = item['orden_trabajo']
            agrupado[cliente][orden].append(item)

        resultado = {cliente: dict(ordenes) for cliente, ordenes in agrupado.items()}

        # === Aquí empieza la parte de ordenado ===

        def limpiar_texto(texto):
            if not texto:
                return ''
            texto = unicodedata.normalize('NFKD', texto)
            texto = texto.encode('ASCII', 'ignore').decode('utf-8')
            return texto.lower()

        def obtener_prioridad(item):
            nombre = limpiar_texto(item['nombre'])

            # Primero: Lámina
            if 'lamina' in nombre:
                return 0

            # Segundo: perfilería
            perfileria = ['angulos', 'canales', 'ipr', 'ptr', 'perfil', 'polin', 'tubo', 'varilla', 'viga']
            for palabra in perfileria:
                if palabra in nombre:
                    return 1

            # Tercero: otros
            return 2

        # Ordenar cada lista de items según prioridad
        for cliente, ordenes in resultado.items():
            for orden, items in ordenes.items():
                ordenes[orden] = sorted(items, key=lambda i: (obtener_prioridad(i), limpiar_texto(i['nombre'])))

        print(resultado);
        # === Fin de la parte de ordenado ===
        return resultado;
        # resultado = {'hola':'mundo'}
        # return request.make_response(
        # json.dumps(resultado, default=str),
        # headers=[('Content-Type', 'application/json')])