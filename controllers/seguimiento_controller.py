from collections import defaultdict
import json
from odoo import http
from odoo.http import request

class ComprasWebSiteDirections(http.Controller):
    @http.route('/dtm_compras/get_data', type='http', auth='public', csrf=False)
    def get_compras(self, **kw):
        list_ordenes = []
        ordenes = request.env['dtm.compras.requerido'].sudo().search([])

        for orden in ordenes:
            list_ordenes.append({
                'orden_trabajo': orden.orden_trabajo,
                'tipo_orden': orden.tipo_orden,
                'revision_ot': orden.revision_ot,
                'proveedor_id': orden.proveedor_id.nombre,
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
                'listo': orden.listo,
                'nesteo': orden.nesteo,
                'cliente': request.env['dtm.odt'].sudo().search([
                    ('ot_number', '=', orden.orden_trabajo),
                    ('revision_ot', '=', orden.revision_ot)
                ]).name_client if orden.tipo_orden in ['OT', 'NPI'] else 'Requisición de Material'
            })

        # Agrupar por cliente y orden_trabajo
        agrupado = defaultdict(lambda: defaultdict(list))
        for item in list_ordenes:
            cliente = item['cliente']
            orden = item['orden_trabajo']
            agrupado[cliente][orden].append(item)

        resultado = {cliente: dict(ordenes) for cliente, ordenes in agrupado.items()}

        return request.make_response(
            json.dumps(resultado),
            headers={
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
            }
        )
