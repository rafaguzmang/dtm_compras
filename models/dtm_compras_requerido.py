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

    def action_devolver(self):
        self.env['dtm.materials.line'].search([('model_id','=',self.env['dtm.odt'].search([('ot_number','=',self.orden_trabajo)]).id),('materials_list','=',self.codigo)]).write({'revision':False})

    def _compute_permiso(self):
        # Lógica para dar permisos de compra
        for result in self:
            result.permiso = True if result.env.user.partner_id.email in ["hugo_chacon@dtmindustry.com",
                                                                          'ventas1@dtmindustry.com',
                                                                          "rafaguzmang@hotmail.com",
                                                                          "calidad2@dtmindustry.com"] else False
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


            self.env['dtm.compras.realizado'].create({
                'orden_trabajo': self.orden_trabajo,
                'proveedor': self.proveedor_id.nombre,
                'codigo': self.codigo,
                'nombre': self.nombre,
                'cantidad': self.cantidad,
                'costo': self.costo,
                'unitario':self.unitario,
                'fecha_compra': datetime.datetime.today(),
                'fecha_recepcion': self.fecha_recepcion,
                'orden_compra': self.orden_compra,
            })
            self.env.cr.execute("DELETE FROM dtm_compras_requerido WHERE id=" + str(self._origin.id))

        else:
            raise ValidationError("Campos obligatorios:\n"
                                  "- Proveedor.\n"
                                  "- Unitario.\n"
                                  "- Orden de compra del proveedor.\n"
                                  "- Fecha de recepción.\n")

    def get_view(self, view_id=None, view_type='form', **options):
        res = super(Compras, self).get_view(view_id, view_type, **options)
        get_info = self.env['dtm.compras.requerido'].search([])

         # Quita los campos borrados de sus respectivas ordenes
        for orden in get_info:
            # Se busca el item de la orden en las tablas materials.line, requisicion.material y odt
            get_odt = self.env['dtm.materials.line'].search([('model_id','=',self.env['dtm.odt'].search([('ot_number','=',orden.orden_trabajo),('tipe_order','=',orden.tipo_orden)]).id if self.env['dtm.odt'].search([('ot_number','=',orden.orden_trabajo)]) else 0),('materials_list','=',orden.codigo)])
            get_req = self.env['dtm.requisicion.material'].search([('model_id','=',self.env['dtm.requisicion'].search([('folio','=',orden.orden_trabajo)]).id),('nombre','=',orden.codigo)])
            get_serv = self.env['dtm.odt'].search([('ot_number','=',orden.orden_trabajo)]).maquinados_id
            list_serv = []
            [list_serv.extend(item.material_id.materials_list.mapped('id')) for item in get_serv]
            # Si el item no se encontro se borra de compras
            if not get_odt and not get_req and not orden.codigo in list_serv:
                orden.unlink()
            # Borra si el item a comprar es cero
            if get_odt and get_odt.materials_required == 0:
                orden.unlink()
            elif get_req and get_req.cantidad == 0:
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

        get_this = self.env['dtm.compras.realizado'].search([])
        for row in get_this:
            row.cantidad > 0 and row.write({'unitario':row.costo/row.cantidad})

        # Carga el último precio cotizado al modelo dtm.compras.precios
        get_realizado = list(set(self.env['dtm.compras.realizado'].search([]).mapped('codigo')))
        for codigo in get_realizado:
            record = self.env['dtm.compras.realizado'].search([('codigo', '=', codigo)], limit=1, order='id desc')
            if codigo in self.env['dtm.compras.precios'].search([]).mapped('codigo'):
                self.env['dtm.compras.precios'].search([('codigo', '=', record.codigo)]).write(
                    {'nombre': record.nombre, 'precio': record.unitario})
            else:
                self.env['dtm.compras.precios'].create(
                    {'codigo': record.codigo, 'nombre': record.nombre, 'precio': record.unitario})

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
