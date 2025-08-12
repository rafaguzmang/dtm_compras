from odoo import fields, models, api
import datetime
import re
from odoo.exceptions import ValidationError, AccessError, MissingError, Warning


class Compras(models.Model):
    _name = "dtm.compras.requerido"
    _description = "Modulo de compras"

    orden_trabajo = fields.Char(string="ODT/Folio", readonly=True)
    tipo_orden = fields.Char(string="Tipo", readonly=True)
    revision_ot = fields.Integer(string="VER",default=1,readonly=True) # Esto es versión
    codigo = fields.Integer(string="Codigo", readonly=True)
    nombre = fields.Char(string="Nombre", readonly=True)
    cantidad = fields.Integer(string="Cantidad", readonly=True)
    disenador = fields.Char(string="Solicita", readonly=True)
    nesteo = fields.Boolean()

    def get_view(self, view_id=None, view_type='form', **options):
        res = super(Compras, self).get_view(view_id, view_type, **options)


         # Quita los campos borrados de sus respectivas ordenes

        return res


class Realizado(models.Model):
    _name = "dtm.compras.realizado"
    _description = "Tabla donde se guardan las compras realizadas"
    _order = "id desc"

    orden_trabajo = fields.Char(string="Orden de Trabajo")
    tipo_orden = fields.Char(string="Tipo", readonly=True)
    revision_ot = fields.Integer(string="VER",default=1,readonly=True) # Esto es versión
    solicitado = fields.Datetime(string='Solicitado')
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
    mostrador = fields.Float(string='Mostrador', readonly=True)
    mayoreo = fields.Float(string='Mayoreo', readonly=True)

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
                if self.env['dtm.compras.realizado'].search([('codigo','=',codigo)], limit=1, order='id desc').tipo_orden not in ['OT','NPI']:
                    self.env['dtm.compras.precios'].search([('codigo', '=', record.codigo)]).write(
                        {'nombre': record.nombre, 'precio': record.unitario,'mayoreo':record.mayoreo})
            else:
                self.env['dtm.compras.precios'].create(
                    {'codigo': record.codigo, 'nombre': record.nombre, 'precio': record.unitario,'mayoreo':record.mayoreo})

        get_comprado = self.env['dtm.compras.realizado'].search([('comprado', '!=', 'Recibido')])
        for item in get_comprado:
            if not self.env['dtm.control.entradas'].search([('codigo','=',str(item.codigo)),('orden_trabajo','=',item.orden_trabajo)]):
                self.env['dtm.control.entradas'].create({
                        "proveedor": item.proveedor,
                        "codigo": item.codigo,
                        "descripcion": item.nombre,
                        "cantidad": item.cantidad,
                        "fecha_recepcion": item.fecha_recepcion,
                        "orden_trabajo": item.orden_trabajo,
                        "revision_ot": item.revision_ot
                })

        return res


class Proveedor(models.Model):
    _name = "dtm.compras.proveedor"
    _description = "Lista de provedores"
    _rec_name = "nombre"

    nombre = fields.Char(string="Nombre")

class SoloMaterial(models.Model):
    _name = "dtm.compras.material"
    _description = "Modelo para llevar acabo la suma de los materiales repetidos de diferentes ordenes"

    proveedor_id = fields.Many2one("dtm.compras.proveedor", string="Proveedor")
    codigo = fields.Integer(string="Codigo", readonly=True)
    nombre = fields.Char(string="Nombre", readonly=True)
    cantidad = fields.Integer(string="Cantidad", readonly=True)
    unitario = fields.Float(string="P.Unitario")
    costo = fields.Float(string="Total", compute="_compute_costo", store=True)
    orden_compra = fields.Char(string="Orden de Compra")
    fecha_recepcion = fields.Date(string="Fecha de estimada")
    observacion = fields.Char(string="Observaciones")
    aprobacion = fields.Boolean(string="Aprovado")
    permiso = fields.Boolean(compute="_compute_permiso")
    servicio = fields.Boolean(string="Servicio", readonly=True)
    mostrador = fields.Float(string='Mostrador')
    mayoreo = fields.Float(string='Mayoreo')


    def _compute_permiso(self):
        # Lógica para dar permisos de compra
        for result in self:
            result.permiso = True if result.env.user.partner_id.email in ["hugo_chacon@dtmindustry.com",
                                                                          'ventas1@dtmindustry.com',
                                                                          "rafaguzmang@hotmail.com",
                                                                          "calidad2@dtmindustry.com"] else False

    @api.depends("cantidad", "unitario")
    def _compute_costo(self):
        for result in self:
            result.costo = result.cantidad * result.unitario

    def action_done(self):
        # Pasa la información a compras realizado

        # Pasa cotización al modulo de ventas y borra la solicitud de compras requerido
        if 'Cotización' in self.env['dtm.compras.requerido'].search([('codigo','=',self.codigo)]).mapped('tipo_orden'):
            ventas = self.env['dtm.cotizacion.materiales'].search([('material_id', '=', self.codigo)], limit=1)
            if ventas:
                ventas.write({'precio': self.unitario, 'mayoreo': self.mayoreo})
                self.unlink()

        elif self.permiso:
            # Se manda el precio mostrador y mayoreo a la tabla de materiales
            get_material = self.env['dtm.materiales'].search([('id','=',self.codigo)])
            if get_material:
                print(get_material)
                get_material.write({'mostrador':self.mostrador,'mayoreo':self.mayoreo})

            get_requerido = self.env['dtm.compras.requerido'].search([('codigo','=',self.codigo)])
            for material in get_requerido:
                vals = {
                    'orden_trabajo':material.orden_trabajo,
                    'tipo_orden':material.tipo_orden,
                    'revision_ot':material.revision_ot,
                    'solicitado':material.create_date,
                    'proveedor':self.proveedor_id.nombre,
                    'codigo':self.codigo,
                    'nombre':self.nombre,
                    'cantidad':material.cantidad,
                    'unitario':self.unitario,
                    'costo':self.costo,
                    'orden_compra':self.orden_compra if self.orden_compra else 'N/A',
                    'fecha_compra':datetime.datetime.today(),
                    'mostrador':self.mostrador,
                    'mayoreo':self.mayoreo,

                }
                # Pasa la información a realizados
                self.env['dtm.compras.realizado'].create(vals)

                vals = {
                    "codigo": self.codigo,
                    "orden_trabajo": material.orden_trabajo,
                    "revision_ot": material.revision_ot,
                    "proveedor": self.proveedor_id.nombre,
                    "descripcion": self.nombre,
                    "cantidad": material.cantidad,
                    "fecha_recepcion": self.fecha_recepcion,
                }
                # Se manda la información a en transito para la espera del material
                self.env['dtm.control.entradas'].search([]).create(vals)
                # Si es una requisición pondrá el status de comprado
                model_id = self.env['dtm.requisicion'].search([('folio', '=', int(material.orden_trabajo))])
                req_material = self.env['dtm.requisicion.material'].search(
                    [('model_id', '=', model_id.id), ('codigo', '=', self.codigo)])
                req_material.write({'comprado': True}) if req_material else None
                # Se borra el material de requerido
                material.unlink()
            # Se quita la fila de este modelo
            self.unlink()


    def get_view(self, view_id=None, view_type='form', **options):
        res = super(SoloMaterial, self).get_view(view_id, view_type, **options)
        # Se obtienen todos los datos de requerido
        get_materiales = self.env['dtm.compras.requerido'].search([])
        # Se hace un set para quitar repetidos
        set_list = list(set(get_materiales.mapped('codigo')))
        # Se obtienen los datos de los materiales más la suma de las cantidades
        for codigo in set_list:
            material_data = self.env['dtm.compras.requerido'].search([('codigo','=',codigo)],limit=1)
            material_suma = self.env['dtm.compras.requerido'].search([('codigo','=',codigo),('tipo_orden','!=','Cotización')])
            get_self = self.env['dtm.compras.material'].search([('codigo','=',codigo)])
            vals = {
                'codigo':codigo,
                'nombre':material_data.nombre,
                'cantidad':sum(material_suma.mapped('cantidad')),
            }

            get_self.write(vals) if get_self else get_self.create(vals)

        # Se encarga de la cotizaciones solicitadas por ventas
        for codigo in set_list:
            material_data = self.env['dtm.compras.requerido'].search([('codigo','=',codigo),('tipo_orden','=','Cotización')],limit=1)
            if material_data:
                # print(material_data)
                get_self = self.env['dtm.compras.material'].search([('codigo','=',codigo),('observacion','=','Cotizar')])
                vals = {
                    'codigo':codigo,
                    'nombre':material_data.nombre,
                    'cantidad':1,
                    'observacion':'Cotizar',
                    'fecha_recepcion':datetime.datetime.today(),
                    'orden_compra':'Cotizar',
                }
#                 print('get_self',get_self)
                get_self.write(vals) if get_self else get_self.create(vals)



        #Quita ordenes que tengan material cero o que se borrarón de la versión vieja de Requerido
        get_info = self.env['dtm.compras.requerido'].search([])
        for orden in get_info:
            # Se busca el item de la orden en las tablas materials.line, requisicion.material y odt
            # print(orden.orden_trabajo,orden.revision_ot,orden.tipo_orden,orden.codigo)
            if orden.tipo_orden != 'Cotización':
                get_odt = self.env['dtm.materials.line'].search([('model_id','=',self.env['dtm.odt'].search([('ot_number','=',orden.orden_trabajo),('revision_ot','=',orden.revision_ot),('tipe_order','=',orden.tipo_orden)]).id if self.env['dtm.odt'].search([('ot_number','=',orden.orden_trabajo),('revision_ot','=',orden.revision_ot)]) else 0),('materials_list','=',orden.codigo)],limit=1)
                get_req = self.env['dtm.requisicion.material'].search([('model_id','=',self.env['dtm.requisicion'].search([('folio','=',orden.orden_trabajo)]).id),('nombre','=',orden.codigo)])
                get_serv = self.env['dtm.odt'].search([('ot_number','=',orden.orden_trabajo),('revision_ot','=',orden.revision_ot)]).maquinados_id
                # list_serv = []
                # [list_serv.extend(item.material_id.materials_list.mapped('id')) for item in get_serv]

                # Si el item no se encontro se borra de compras
                if not get_odt and not get_req:
                    orden.unlink()

                # Borra si el item a comprar es cero
                if get_odt and get_odt.materials_required == 0:
                    orden.unlink()

                elif get_req and get_req.cantidad == 0:
                    orden.unlink()

        #Quita los materiales que ya no existan en la nueva versión de requerido
        get_self = self.env['dtm.compras.material'].search([]).mapped('codigo')
        get_re = self.env['dtm.compras.requerido'].search([]).mapped('codigo')


        borrado_list = list(filter(lambda row: row not in get_re,get_self))
        self.env['dtm.compras.material'].search([('codigo','in',borrado_list)]).unlink()

        return res
