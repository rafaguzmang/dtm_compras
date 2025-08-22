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
    autoriza = fields.Char(string='Autorizó',readonly=True)

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
    user = fields.Char()


    def _compute_permiso(self):
        # Lógica para dar permisos de compra
        for result in self:
            result.user = self.env.user.partner_id.name
            result.permiso = True if result.env.user.partner_id.email in ["hugo_chacon@dtmindustry.com",
                                                                          'ventas1@dtmindustry.com',
                                                                          "rafaguzmang@hotmail.com",
                                                                          "calidad2@dtmindustry.com"] else False

    @api.depends("cantidad", "unitario")
    def _compute_costo(self):
        for result in self:
            result.costo = result.cantidad * result.unitario

    def action_wizard(self):
        return{
            'name': 'Confirmar Compra',
            'type': 'ir.actions.act_window',
            'res_model':'dtm.compras.confirm.wizard',
            'view_mode':'form',
            'view_id':self.env.ref('dtm_compras.view_compras_confirm_wizard').id,
            'target':'new',
            'context':{'default_compra_id':self.id},
        }

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
                # print(get_material)
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
                    'autoriza':self.user,

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

        Requerido = self.env['dtm.compras.requerido']
        Material = self.env['dtm.compras.material']

        # 1️⃣ Obtener sumas de materiales no Cotización usando read_group
        materiales_suma = Requerido.read_group(
            [('tipo_orden', '!=', 'Cotización')],
            fields=['codigo', 'cantidad'],
            groupby=['codigo']
        )

        # 2️⃣ Obtener todas las Cotizaciones
        cotizaciones = Requerido.search([('tipo_orden', '=', 'Cotización')])

        # 3️⃣ Materiales existentes en dtm.compras.material de manera masiva
        todos_codigos = list(set([m['codigo'] for m in materiales_suma] + cotizaciones.mapped('codigo')))
        materiales_existentes = Material.search([('codigo', 'in', todos_codigos)])
        materiales_dict = {m.codigo: m for m in materiales_existentes}

        # 4️⃣ Actualizar o crear materiales no Cotización
        for m in materiales_suma:
            codigo = m['codigo']
            nombre = Requerido.search([('codigo', '=', codigo)], limit=1).nombre
            vals = {
                'codigo': codigo,
                'cantidad': m['cantidad'],
                'nombre': nombre
            }
            if codigo in materiales_dict:
                materiales_dict[codigo].write(vals)
            else:
                Material.create(vals)

        # 5️⃣ Actualizar o crear Cotizaciones
        for cot in cotizaciones:
            codigo = cot.codigo
            vals = {
                'codigo': codigo,
                'nombre': cot.nombre,
                'cantidad': 1,
                'observacion': 'Cotizar',
                'fecha_recepcion': datetime.datetime.today(),
                'orden_compra': 'Cotizar'
            }
            if codigo in materiales_dict:
                materiales_dict[codigo].write(vals)
            else:
                Material.create(vals)

        # 6️⃣ Limpiar materiales que ya no existen en Requerido
        codigos_requerido = set(Requerido.mapped('codigo'))
        codigos_material = set(Material.mapped('codigo'))
        codigos_borrar = list(codigos_material - codigos_requerido)
        if codigos_borrar:
            Material.search([('codigo', 'in', codigos_borrar)]).unlink()

        # 7️⃣ Limpiar registros con cantidad cero
        cero_materiales = Material.search([('cantidad', '=', 0)])
        if cero_materiales:
            cero_materiales.unlink()

        return res


class CompraConfirmacionWizard(models.TransientModel):
    _name = "dtm.compras.confirm.wizard"
    _description = "Ventana de diálogo para la confirmación de una compra"

    compra_id = fields.Many2one(
        'dtm.compras.material',
        string='Compra',
        readonly=True,
        required=True
    )

    costo = fields.Float(string='Consto', readonly=True)
    total = fields.Float(string='Total', readonly=True)
    material = fields.Char(string='Material', readonly=True)
    codigo = fields.Integer(string='Código', readonly=True)
    ordenes = fields.Text(string='Orden', readonly=True)
    cantidad = fields.Text(string='cantidad', readonly=True)
    proveedor = fields.Text(string='Proveedor', readonly=True)

    def action_confirmar_compra(self):
        if self.compra_id:
            self.compra_id.action_done()
        return {'type': 'ir.actions.act_window_close'}

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        compra_id = self.env.context.get('default_compra_id')
        if compra_id:
            get_codigo = self.env['dtm.compras.material'].browse(compra_id)
            # Asignar valores al diccionario res, no a self
            res['compra_id'] = get_codigo.id
            res['costo'] = get_codigo.costo
            res['total'] = get_codigo.unitario
            res['material'] = get_codigo.nombre
            res['cantidad'] = get_codigo.cantidad
            res['proveedor'] = get_codigo.proveedor_id.nombre

            # Si quieres recorrer las órdenes
            get_material = self.env['dtm.compras.requerido'].search([('codigo', '=', get_codigo.codigo)])
            ordenes = ''
            for result in get_material:
                get_orden = self.env['dtm.odt'].search([('ot_number','=',result.orden_trabajo)],limit=1)
                ordenes += f'{result.orden_trabajo} - {get_orden.product_name} - {get_orden.name_client} - {result.disenador} - {result.cantidad} {"Falta Nesteo" if not result.nesteo else ""}\n'

            res['ordenes'] = ordenes

        return res
