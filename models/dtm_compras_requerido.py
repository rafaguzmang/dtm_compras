from odoo import fields, models, api
import datetime
import re
from odoo.exceptions import ValidationError, AccessError, MissingError, Warning


class Compras(models.Model):
    _name = "dtm.compras.requerido"
    _description = "Modulo de compras"

    orden_trabajo = fields.Char(string="ODT/Folio", readonly=True)
    tipo_orden = fields.Char(string="Tipo", readonly=True)
    proveedor_id = fields.Many2one("dtm.compras.proveedor", string="Proveedor")
    codigo = fields.Integer(string="Codigo", readonly=True)
    nombre = fields.Char(string="Nombre", readonly=True)
    cantidad = fields.Integer(string="Cantidad", readonly=True)
    unitario = fields.Float(string="P.Unitario")
    costo = fields.Float(string="Total", compute="_compute_costo", store=True)
    orden_compra = fields.Char(string="Orden de Compra")
    fecha_recepcion = fields.Date(string="Fecha  estimada de Recepción")
    disenador = fields.Char(string="Solicita", readonly=True)
    observacion = fields.Char(string="Observaciones")
    aprovacion = fields.Boolean(string="Aprovado")
    permiso = fields.Boolean(compute="_compute_permiso")
    servicio = fields.Boolean(string="Servicio", readonly=True)
    listo = fields.Boolean()

    def _compute_permiso(self):
        # Lógica para dar permisos de compra
        for result in self:
            result.permiso = True if result.env.user.partner_id.email in ["hugo_chacon@dtmindustry.com",
                                                                          'ventas1@dtmindustry.com',
                                                                          "rafaguzmang@hotmail.com","calidad2@dtmindustry.com"] else False

    def action_enlace(self):
        get_id = self.env['dtm.proceso'].search([("ot_number", "=", self.orden_trabajo)])
        if len(get_id) == 1:
            return {
                'type': 'ir.actions.act_url',
                'url': f'/web#id={get_id.id}&cids=2&menu_id=811&action=910&model=dtm.proceso&view_type=form',
                # 'target': 'self',  # Abre la URL en la misma ventana
            }
        else:

            return {
                'type': 'ir.actions.act_url',
                'url': f'/web#action=910&model=dtm.proceso&view_type=list&cids=2&menu_id=811&ordenes={self.orden_trabajo}',
                # 'target': 'self',  # Abre la URL en la misma ventana
            }

    @api.depends("cantidad", "unitario")
    def _compute_costo(self):
        for result in self:
            result.costo = result.cantidad * result.unitario

    def action_done(self):
        # Pasa la información a compras realizado
        if self.proveedor_id.nombre and self.unitario and self.orden_compra and self.fecha_recepcion:
            vals = {
                "proveedor": self.proveedor_id.nombre,
                "codigo": self.codigo,
                "descripcion": self.nombre,
                "cantidad": self.cantidad,
                "fecha_recepcion": self.fecha_recepcion,
                "orden_trabajo": self.orden_trabajo
                # "unitario": self.unitario,
                # "aprovacion": self.aprovacion and "Aprobado",
            }
            get_control = self.env['dtm.control.entradas'].search(
                [("descripcion", "=", self.nombre), ("proveedor", "=", self.proveedor_id.nombre),
                 ("codigo", "=", self.codigo)])
            # print(vals)
            # print(get_control)
            if not get_control:
                get_control.create(vals)
            else:
                cantidad = 0
                for get in get_control:
                    cantidad += get.cantidad
                vals = {
                    "cantidad": cantidad + self.cantidad
                }
                get_control.write(vals)

            self.env.cr.execute(
                "INSERT INTO dtm_compras_realizado (orden_trabajo,proveedor,codigo,nombre,cantidad,costo,fecha_compra,fecha_recepcion,orden_compra) VALUES ('" +
                str(self.orden_trabajo) + "','" + self.proveedor_id.nombre + "', '" + str(
                    self.codigo) + "','" + self.nombre + "'," + str(self.cantidad) + "," + str(self.costo) +
                ", '" + str(datetime.datetime.today()) + "','" + str(self.fecha_recepcion) + "','" + str(
                    self.orden_compra) + "')")
            self.env.cr.execute("DELETE FROM dtm_compras_requerido WHERE id=" + str(self._origin.id))
            # Indica que el material se ha pedido
            # obtiene el id de la orden de trabajo
            if len(self.orden_trabajo)< 4 :
                get_orden = self.env['dtm.odt'].search([('ot_number','=',int(self.orden_trabajo))])
                get_material = self.env['dtm.materials.line'].search([('model_id','=',get_orden.id),("materials_list","=",self.codigo)])
                if get_material:
                    for material in get_material:
                        material.write({
                                            "comprado":True,
                                            "revicion":False
                                        })
            else:
                ordenes = self.orden_trabajo.split(" ")
                for orden in ordenes:
                    get_orden = self.env['dtm.odt'].search([('ot_number','=',int(orden))])
                    get_material = self.env['dtm.materials.line'].search([('model_id','=',get_orden.id),("materials_list","=",self.codigo)])
                    if get_material:
                        for material in get_material:
                            material.write({
                                                "comprado":True,
                                                "revicion":False
                                            })

        else:
            raise ValidationError("Campos obligatorios:\n"
                                  "- Proveedor.\n"
                                  "- Unitario.\n"
                                  "- Orden de compra del proveedor.\n"
                                  "- Fecha de recepción.\n")

    def get_view(self, view_id=None, view_type='form', **options):
        res = super(Compras, self).get_view(view_id, view_type, **options)
        get_info = self.env['dtm.compras.requerido'].search([])

        orden_map = {}
        for orden in get_info:
            orden_cons = " ".join(sorted(str(orden.orden_trabajo).split(' ')))
            if orden_map.get(f"{orden_cons}-{orden.codigo}"):
                orden.unlink()
            else:
                orden_map[f"{orden_cons}-{orden.codigo}"] = 1

        # Lógica para detectar materiales solicitados por varias Ordenes, suma el total de todas ellas
        mapa_repe = {}
        repeList = []
        for material in get_info:#Quita materiales repetidos
            if mapa_repe.get(material.codigo):
                repeList.append(material.codigo)
            else:
                mapa_repe[material.codigo] = 1
        if repeList:
            for item in list(set(repeList)):
                get_col = self.env['dtm.compras.requerido'].search([('codigo','=',item)])
                lista_ordenes = " ".join(list(set([num for elem in get_col.mapped('orden_trabajo') for num in elem.split()])))
                suma = 0
                disenador = " ".join(list(set(get_col.mapped('disenador'))))
                servicio =  True if True in get_col.mapped('servicio') else False
                nombre = get_col.mapped('nombre')[0]
                for orden in lista_ordenes.split():
                    get_servicios = self.env['dtm.odt'].search([('ot_number','=',orden)]).maquinados_id
                    servicio = 0
                    # Busca el servicio que contiene el material en caso de que sea un servicio
                    for serv in get_servicios:
                        for material in serv.material_id:
                            if material.materials_list.id == item:
                                servicio = serv.id
                    # Busca el material en caso de que sea un material
                    if self.env['dtm.materials.line'].search([('model_id','=',self.env['dtm.odt'].search([('ot_number','=',orden)]).id),('materials_list','=',item)]):
                        suma += sum(self.env['dtm.materials.line'].search([('model_id','=',self.env['dtm.odt'].search([('ot_number','=',orden)]).id),('materials_list','=',item)]).mapped('materials_required'))
                    if servicio != 0:
                        suma += sum(self.env['dtm.materials.line'].search([('servicio_id','=',servicio),('materials_list','=',item)]).mapped('materials_required'))
                # print(item,lista_ordenes,nombre,disenador,servicio,suma)
                get_new = self.env['dtm.compras.requerido'].search([('orden_trabajo','=',lista_ordenes),('codigo','=',item)])
                # print(suma,disenador,servicio,item,nombre)
                if get_new:
                    get_new.write({'cantidad':suma,
                                    'disenador':disenador,'servicio': servicio,
                                    'codigo':item,'nombre':nombre
                                    })
                else:
                    get_new.create({'orden_trabajo':lista_ordenes,'cantidad':suma,
                                    'disenador':disenador,'servicio': servicio,
                                    'codigo':item,'nombre':nombre
                                    })

                get_old = self.env['dtm.compras.requerido'].search([('codigo','=',item)])
                maxleng_list = get_old.mapped('orden_trabajo')
                # print(maxleng_list)
                # print(len(max(maxleng_list)))
                for orden in get_old:
                    if len(orden.orden_trabajo) < len(max(maxleng_list)):
                        # print(orden.orden_trabajo)
                        orden.unlink()

                # print('------------------------------------')

         # Quita los campos borrados de sus respectivas ordenes
        for orden in get_info:
            if len(orden.orden_trabajo) <= 3:
                get_odt = self.env['dtm.materials.line'].search([('model_id','=',self.env['dtm.odt'].search([('ot_number','=',orden.orden_trabajo),('tipe_order','=',orden.tipo_orden)]).id if self.env['dtm.odt'].search([('ot_number','=',orden.orden_trabajo)]) else 0),('materials_list','=',orden.codigo)])
                get_req = self.env['dtm.requisicion.material'].search([('model_id','=',self.env['dtm.requisicion'].search([('folio','=',orden.orden_trabajo)]).id),('nombre','=',orden.codigo)])
                get_serv = self.env['dtm.odt'].search([('ot_number','=',orden.orden_trabajo)]).maquinados_id
                list_serv = []
                [list_serv.extend(item.material_id.materials_list.mapped('id')) for item in get_serv]
                # print([list_serv.extend(lista) for lista in [item.material_id.materials_list.mapped('id') for item in get_serv]])
                # print(list_serv)
                # print(get_odt,get_req,"Código",orden.codigo,"ODT",orden.orden_trabajo,len(orden.orden_trabajo))
                if not get_odt and not get_req and not orden.codigo in list_serv:
                    orden.unlink()
        return res


class Realizado(models.Model):
    _name = "dtm.compras.realizado"
    _description = "Tabla donde se guardan las compras realizadas"
    _order = "id desc"

    orden_trabajo = fields.Char(string="Orden de Trabajo")
    proveedor = fields.Char(string="Proveedor")
    codigo = fields.Integer(string="Código")
    nombre = fields.Char(string="Nombre")
    cantidad = fields.Integer(string="Cantidad")
    unitario = fields.Float(string="P.Unitario")
    costo = fields.Float(string="Total")
    cantidad_almacen = fields.Integer(string="C-Real")
    orden_compra = fields.Char(string="Orden de Compra")
    fecha_compra = fields.Date(string="Fecha de compra")
    fecha_recepcion = fields.Date(string="Fecha de estimada de recepción")
    comprado = fields.Char(string="Recibido")
    aprovacion = fields.Char(string="Aprovado", readonly=True)

    def get_view(self, view_id=None, view_type='form', **options):
        res = super(Realizado, self).get_view(view_id, view_type, **options)

        # get_self = self.env['dtm.compras.realizado'].search([]).mapped('orden_trabajo')
        # ordenes_list = set(list(filter(lambda x: len(x) < 4, get_self)))
        # get_facturado = self.env['dtm.facturado.odt'].search([]).mapped('ot_number')
        # [int(odt) in get_facturado and self.env['dtm.compras.realizado'].search([("orden_trabajo", "=", odt)]).unlink()
        #  for odt in ordenes_list]
        # get_facturado = self.env['dtm.facturado.npi'].search([]).mapped('ot_number')
        # [int(odt) in get_facturado and self.env['dtm.compras.realizado'].search([("orden_trabajo", "=", odt)]).unlink()
        #  for odt in ordenes_list]

        return res


class Proveedor(models.Model):
    _name = "dtm.compras.proveedor"
    _description = "Lista de provedores"
    _rec_name = "nombre"

    nombre = fields.Char(string="Nombre")
