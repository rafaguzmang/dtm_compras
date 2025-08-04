from collections import defaultdict
import json
from odoo import http
from odoo.http import request
import unicodedata
from datetime import datetime



class ComprasWebSiteDirections(http.Controller):
    @http.route('/dtm_compras/get_data', type='json', auth='public', csrf=False)
    def get_compras(self, **kw):
        list_ordenes = []
        cont = 0
        # Se obtienen las ordenes de modulo de compras
        ordenes = request.env['dtm.compras.requerido'].sudo().search([])
        ordenes_unicos = list(set(ordenes.mapped('orden_trabajo')))
        ordenes_filtradas = [request.env['dtm.compras.requerido'].sudo().search([('orden_trabajo','=',unico)],limit=1) for unico in ordenes_unicos ]

        # Se busca el todo el material por orden de compra o por requisición
        for orden in ordenes_filtradas:
            # Se obtienen los datos de la orden
            datos_orden = request.env['dtm.odt'].sudo().search([
                ('ot_number', '=', orden.orden_trabajo),
                ('revision_ot', '=', orden.revision_ot)
            ])

            datos_requi = request.env['dtm.requisicion'].sudo().search([
                ('folio', '=', orden.orden_trabajo),
            ])
            # datos_requi and print(datos_requi)
            # Se obtiene la P.O. del modulo de ventas
            po_pdf = request.env['dtm.compras.items'].sudo().search([('orden_trabajo','=',orden.orden_trabajo)],limit=1).model_id.archivos_id
            # print(datos_orden.materials_ids)
            # si es orden de servicio
            if datos_orden:
                for row in datos_orden.materials_ids:
                    # datos de requerido
                    en_compra = request.env['dtm.compras.requerido'].sudo().search([('orden_trabajo','=',orden.orden_trabajo),('revision_ot','=',orden.revision_ot),('codigo','=',row.materials_list.id)])
                    # datos de materiales (requerido nuevo)
                    en_material = request.env['dtm.compras.material'].sudo().search([('codigo','=',row.materials_list.id)],limit=1)
                    list_ordenes.append({
                        'contador':cont,
                        'orden_trabajo': orden.orden_trabajo,
                        'tipo_orden': orden.tipo_orden,
                        'revision_ot': orden.revision_ot,
                        'proveedor_id': en_material.proveedor_id.nombre if en_material and en_material.proveedor_id.nombre else None,
                        'codigo': row.materials_list.id,
                        'nombre': f"{row.materials_list.nombre} {row.materials_list.medida}",
                        'total': row.materials_cuantity,
                        'apartado': row.materials_availabe,
                        'cantidad': row.materials_required,
                        'unitario': en_material.unitario if en_material else 0,
                        'costo': en_material.costo if en_material else 0,
                        'orden_compra': en_material.orden_compra,
                        'fecha_recepcion': en_material.fecha_recepcion.isoformat() if en_material.fecha_recepcion else None,
                        'disenador': orden.disenador,
                        # 'observacion': en_material.observacion if en_material and orden.observacion  else '',
                        # 'aprobacion': en_material.aprobacion if orden.aprobacion else None,
                        'permiso': en_material.permiso if en_material.permiso else None,
                        'servicio': en_material.servicio if en_material.servicio else None,
                        'en_compras':en_material.create_date.isoformat() if en_material else None,
                        # 'listo': orden.listo if orden.listo else None,
                        'nesteo': orden.nesteo if orden.nesteo else None,
                        'cliente': datos_orden.name_client,
                        'date_rel': datos_orden.date_rel.isoformat() if datos_orden.date_rel else None,
                        'product_name': datos_orden.product_name if datos_orden else None,
                        'po_pdf_url': f'/web/content/{po_pdf.id}?mimetype=application/pdf&download=false' if po_pdf else None,
                        'status':   'Entregado' if row.entregado else
                                    'Comprado' if request.env['dtm.compras.realizado'].search(
                                        [('orden_trabajo', '=', orden.orden_trabajo), ('revision_ot', '=', orden.revision_ot),
                                         ('codigo', '=', row.materials_list.id)], limit=1).comprado else
                                    'En cámino' if request.env['dtm.compras.realizado'].search(
                                        [('orden_trabajo', '=', orden.orden_trabajo), ('revision_ot', '=', orden.revision_ot),
                                         ('codigo', '=', row.materials_list.id)], limit=1) else
                                    'Requerido' if request.env['dtm.compras.requerido'].search(
                                        [('orden_trabajo', '=', orden.orden_trabajo), ('revision_ot', '=', orden.revision_ot),
                                         ('codigo', '=', row.materials_list.id)], limit=1) else
                                    'En Almacén' if row.materials_required == 0 and row.materials_cuantity > 0 else
                                    'En Revisión' if not row.almacen else None
                        })
                    cont += 1
            elif datos_requi:
                for row in datos_requi.material_ids:
                    # print('Requi',row.nombre)
                    en_compra = request.env['dtm.compras.requerido'].sudo().search(
                        [('orden_trabajo', '=', orden.orden_trabajo), ('tipo_orden', '=', 'Requi'),
                         ('codigo', '=', row.nombre.id)])

                    en_material = request.env['dtm.compras.material'].sudo().search([('codigo','=',row.nombre.id)],limit=1)

                    # print(en_compra)
                    list_ordenes.append({
                        'contador': cont,
                        'orden_trabajo': orden.orden_trabajo,
                        'tipo_orden': orden.tipo_orden,
                        'revision_ot': orden.revision_ot,
                        'proveedor_id': en_material.proveedor_id.nombre if en_material else False,
                        'codigo': row.nombre.id,
                        'nombre': row.nombre.nombre,
                        'total': row.cantidad,
                        'cantidad': row.cantidad,
                        'unitario': en_material.unitario,
                        'costo': en_material.costo,
                        'orden_compra': en_material.orden_compra,
                        'fecha_recepcion': en_material.fecha_recepcion.isoformat() if en_material.fecha_recepcion else None,
                        'disenador': en_compra.disenador,
                        'observacion': en_material.observacion if en_material.observacion else None,
                        'aprobacion': en_material.aprobacion if en_material.aprobacion else None,
                        'permiso': en_material.permiso if en_material.permiso else None,
                        # 'servicio': en_material.servicio if en_material.servicio else None,
                        'en_compras': en_material.create_date.isoformat() if en_material.create_date else None,
                        # 'listo': en_compra.listo if en_compra.listo else None,
                        # 'nesteo': en_compra.nesteo if en_compra.nesteo else None,
                        'cliente': 'Requisición de Material',
                        'date_rel': datos_orden.date_rel.isoformat() if datos_orden.date_rel else None,
                        'product_name': datos_orden.product_name if datos_orden else None,
                        'po_pdf_url': f'/web/content/{po_pdf.id}?mimetype=application/pdf&download=false' if po_pdf else None,
                        'status':'En compra'
                    })
                    cont += 1

            # print(list_ordenes)

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

        def parse_date(date_str):
            if date_str:
                try:
                    return datetime.strptime(date_str, "%Y-%m-%d")
                except:
                    return datetime.max
            return datetime.max

        for cliente in resultado:
            for orden_id in resultado[cliente]:
                # Ordena la lista de órdenes según 'date_rel', las fechas nulas al final
                resultado[cliente][orden_id].sort(key=lambda orden: parse_date(orden.get('date_rel')))

        key_to_move = "Requisición de Material"
        if key_to_move in resultado:
            valor = resultado.pop(key_to_move)
            resultado[key_to_move] = valor
        # === Fin de la parte de ordenado ===
        return resultado
        # resultado = {'Hola':'Mundo'}
        # return request.make_response(
        #     json.dumps(resultado),
        #     headers={
        #         'Content-Type': 'application/json',
        #         'Access-Control-Allow-Origin': '*',
        #     }
        # )



class CompradoWebSite(http.Controller):
    @http.route('/dtm_comprado/get_data', type='json', auth='public', csrf=False)
    def get_compras(self, **kw):
        ordenes_dict = []
        ordenes = request.env['dtm.compras.realizado'].sudo().search([('comprado','!=','Recibido')])
        for orden in ordenes:
            datos_orden = request.env['dtm.odt'].sudo().search([
                ('ot_number', '=', orden.orden_trabajo),
                ('revision_ot', '=', orden.revision_ot)
            ])

            ordenes_dict.append({
                'orden_trabajo': orden.orden_trabajo if orden.orden_trabajo else '',
                'revision_ot': orden.revision_ot if orden.revision_ot else '',
                'proveedor_id': orden.proveedor if orden.proveedor else '',
                'codigo': orden.codigo if orden.codigo else '',
                'nombre': orden.nombre if orden.nombre else '',
                'cantidad': orden.cantidad if orden.cantidad else '',
                'unitario': orden.unitario if orden.unitario else '',
                'costo': orden.costo if orden.costo else '',
                'orden_compra': orden.orden_compra if orden.orden_compra else '',
                'fecha_recepcion': orden.fecha_recepcion.isoformat() if orden.fecha_recepcion else None,
                'en_compras': orden.solicitado.isoformat() if orden.solicitado else None,
                'cliente': datos_orden.name_client if datos_orden.name_client else 'Requisición de Material',
                'date_rel': datos_orden.date_rel.isoformat() if datos_orden.date_rel else None,
                'product_name': datos_orden.product_name if datos_orden else None,
            })

        def ordenar(item):
            fecha = item.get("date_rel")
            if fecha:
                try:
                    return datetime.strptime(fecha, "%Y-%m-%d")
                except Exception:
                    pass
            return datetime.max  # Ponemos los nulls al final

        # Ordenamos de más reciente a más antigua, y los null quedan al final
        list_ordenes = sorted(
            ordenes_dict,
            key=lambda x: (ordenar(x) == datetime.min, ordenar(x)),
            reverse=True
        )

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

        # print(resultado);
        # === Fin de la parte de ordenado ===
        return resultado;
        # return request.make_response(
        # json.dumps(resultado, default=str),
        # headers=[('Content-Type', 'application/json')])


class Materiales(http.Controller):
    @http.route('/dtm_materiales/get_data', type='json', auth='public')
    def lista_materiales(self, **kwargs):
        ordenes = request.env['dtm.odt'].sudo().search([])

        result = []

        for orden in ordenes:
            # Trae el ide de dtm_odt
            ot_id = orden.id
            lista_materiales = [
                [
                    material.materials_list.id,
                    material.nombre,
                    material.medida,
                    material.materials_cuantity,
                    material.materials_required,
                    'Entregado' if material.entregado else
                    'Comprado' if request.env['dtm.compras.realizado'].search(
                        [('orden_trabajo', '=', orden.ot_number), ('revision_ot', '=', orden.revision_ot),
                         ('codigo', '=', material.materials_list.id)], limit=1).comprado else
                    'En cámino' if request.env['dtm.compras.realizado'].search(
                        [('orden_trabajo', '=', orden.ot_number), ('revision_ot', '=', orden.revision_ot),
                         ('codigo', '=', material.materials_list.id)], limit=1) else
                    'En compra' if request.env['dtm.compras.requerido'].search(
                        [('orden_trabajo', '=', orden.ot_number), ('revision_ot', '=', orden.revision_ot),
                         ('codigo', '=', material.materials_list.id)], limit=1) else
                    'En Almacén' if material.materials_required == 0 and material.materials_cuantity > 0 else
                    'En Revisión' if not material.almacen else None
                ]
                for material in orden.materials_ids]
            lista_ordenada = sorted(lista_materiales, key=lambda item: item[5] in item)
            result.append({
                'orden': orden.ot_number,
                'version': orden.revision_ot,
                'ot_id': orden.id,
                'materiales': lista_ordenada
            })

        return result
        # return request.make_response(
        #     json.dumps(result),
        #     headers={
        #         'Content-Type': 'application/json',
        #         'Access-Control-Allow-Origin': '*',
        #     }
        # )