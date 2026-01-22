from re import search

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

    def write(self,vals):

        res = super(Compras,self).write(vals)

        self.env["bus.bus"]._sendone(
            'canal_compras',
            'compras',
            {'mensaje':'Actualizado por compras'}
        )

        return res

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
    cantidad_almacen = fields.Integer(string="C-Real")
    unitario = fields.Float(string="P.Unitario")
    costo = fields.Float(string="Total")
    orden_compra = fields.Char(string="Orden de Compra", required=False )
    fecha_compra = fields.Date(string="Fecha de compra")
    fecha_recepcion = fields.Date(string="Fecha de estimada de recepción")
    comprado = fields.Char(string="Recibido")
    aprovacion = fields.Char(string="Aprovado", readonly=True)
    mostrador = fields.Float(string='Mostrador', readonly=True)
    mayoreo = fields.Float(string='Mayoreo', readonly=True)
    autoriza = fields.Char(string='Autorizó',readonly=True)
    factura = fields.Char(string='Factura')
    notas = fields.Char(string='Notas')
    notas_almacen = fields.Char(string = 'Notas')
    listo_btn = fields.Boolean()

    def write(self, vals):
        res = super(Realizado, self).write(vals)

        self.env["bus.bus"]._sendone(
            'canal_compras',
            'compras',
            {'mensaje': 'Actualizado por compras'}
        )

        return res

    def get_view(self, view_id=None, view_type='form', **options):
        res = super(Realizado, self).get_view(view_id, view_type, **options)

        get_realizado = self.env['dtm.compras.realizado'].search([('comprado', 'not in', ['Recibido','Parcial'])])
        for record in get_realizado:
            get_entradas = self.env['dtm.control.entradas'].search([('orden_trabajo','=',record.orden_trabajo),('codigo','=',record.codigo),('descripcion','=',record.nombre),('cantidad','=',record.cantidad)],limit=1)
            vals ={
                'proveedor':record.proveedor,
                'orden_trabajo':record.orden_trabajo,
                'codigo':record.codigo,
                'descripcion':record.nombre,
                'cantidad':record.cantidad,
            }
            get_entradas.write(vals) if get_entradas else get_entradas.create(vals)

        return res

class Proveedor(models.Model):
    _name = "dtm.compras.proveedor"
    _description = "Lista de provedores"
    _rec_name = "nombre"

    nombre = fields.Char(string="Nombre")

class SoloMaterial(models.Model):
    _name = "dtm.compras.material"
    _description = "Modelo para llevar acabo la suma de los materiales repetidos de diferentes ordenes"
    _inherit = ['mail.thread','mail.activity.mixin']


    proveedor_id = fields.Many2one("dtm.compras.proveedor", string="Proveedor")
    codigo = fields.Integer(string="Codigo", readonly=True)
    nombre = fields.Char(string="Nombre", readonly=True)
    cantidad = fields.Integer(string="Cantidad", readonly=True)
    unitario = fields.Float(string="P.Unitario")
    costo = fields.Float(string="Total", compute="_compute_costo", store=True)
    orden_compra = fields.Char(string="Orden de Compra",required=False)
    fecha_recepcion = fields.Date(string="Fecha de estimada")
    observacion = fields.Char(string="Observaciones", tracking=True)
    aprobacion = fields.Boolean(string="Aprovado")
    permiso = fields.Boolean(compute="_compute_permiso")
    servicio = fields.Boolean(string="Servicio", readonly=True)
    mostrador = fields.Float(string='Mostrador')
    mayoreo = fields.Float(string='Mayoreo')
    user = fields.Char()

    #----------------------Tracking----------------------------------
    unitario_tracking = fields.Char(compute='_compute_unitario_tracking',tracking=True,store=True)
    mostrador_tracking = fields.Char(compute='_compute_mostrador_tracking',tracking=True,store=True)
    mayoreo_tracking = fields.Char(compute='_compute_mayoreo_tracking',tracking=True,store=True)
    retrazo = fields.Boolean(compute='_compute_retrazo')

    def write(self, vals):
        res = super(SoloMaterial, self).write(vals)
        self.env["bus.bus"]._sendone(
            'canal_compras',
            'compras',
            {'mensaje': 'Actualizado por compras'}
        )
        return res

    def _compute_retrazo(self):
        for record in self:
            diferencia = int(datetime.datetime.today().strftime("%j")) - int(record.create_date.strftime("%j"))
            record.retrazo = False
            if diferencia > 3:
                record.retrazo = True

    @api.depends('unitario')
    def _compute_unitario_tracking(self):
        for record in self:
            record.unitario_tracking = str(record.unitario)

    @api.depends('mostrador')
    def _compute_mostrador_tracking(self):
        for record in self:
            record.mostrador_tracking = str(record.mostrador)

    @api.depends('mayoreo')
    def _compute_mayoreo_tracking(self):
        for record in self:
            record.mayoreo_tracking = str(record.mayoreo)

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
        # print(self.nombre,self.proveedor_id.nombre)
        self.env['dtm.compras.conceptos'].search([]).unlink()
        self.env.cr.execute(f"SELECT setval('dtm_compras_conceptos_id_seq', 1, false);")
        get_material = self.env['dtm.compras.requerido'].search([('codigo', '=', self.codigo),('nombre','=',self.nombre)])
        for result in get_material:
            get_orden = self.env['dtm.odt'].search([('ot_number', '=', result.orden_trabajo)], limit=1)
            vals = {
                    'orden_trabajo':result.orden_trabajo,
                    'nombre':get_orden.product_name,
                    'cliente':get_orden.name_client,
                    'disenador':result.disenador,
                    'cantidad':result.cantidad,
                    'nesteo':True if result.nesteo else False,
                    'material':result.nombre,
                    'codigo':int(result.codigo)
            }
            self.env['dtm.compras.conceptos'].create(vals)


        return{
            'name': 'Confirmar Compra',
            'type': 'ir.actions.act_window',
            'res_model':'dtm.compras.confirm.wizard',
            'view_mode':'form',
            'view_id':self.env.ref('dtm_compras.view_compras_confirm_wizard').id,
            'target':'new',
            'context':{'default_compra_id':self.id,'permiso':self.permiso},
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
            get_material = self.env['dtm.materiales'].search([('id','=',self.codigo)],limit=1)
            if get_material.nombre and get_material.nombre in self.nombre:
                get_material.write({'mostrador':self.mostrador,'mayoreo':self.mayoreo})
                get_precios = self.env['dtm.compras.precios'].search([('codigo','=',self.codigo)])
                vals = {
                    'codigo':get_material.id,
                    'tipo_material':'Indirecto',
                    'nombre':self.nombre,
                    'precio':self.mostrador,
                    'mayoreo':self.mayoreo,
                }
                if get_precios.nombre and get_material.nombre in get_precios.nombre:
                    get_precios.write(vals)
                else:
                    get_precios.create(vals)

            get_requerido = self.env['dtm.compras.requerido'].search([('codigo','=',self.codigo)])
            for material in get_requerido:

                if int(material.orden_trabajo) in self.env['dtm.compras.conceptos'].search([]).mapped('orden_trabajo'):
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
                        'costo':material.cantidad * self.unitario,
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
                # self.unlink()
                self.get_view()

    def get_view(self, view_id=None, view_type='form', **options):
        res = super(SoloMaterial, self).get_view(view_id, view_type, **options)

        requerido = self.env['dtm.compras.requerido'].search([])
        material = self.env['dtm.compras.material'].search([])
        # Vamos a quitar los items que ya fueron borrados de sus respectivas ordenes o en cantidad son cero
        for item in requerido:
            get_odt = self.env['dtm.odt'].search([('ot_number','=',item.orden_trabajo),('tipe_order','=',item.tipo_orden),('revision_ot','=',item.revision_ot)])
            get_materials_line = self.env['dtm.materials.line'].search([('model_id','=',get_odt.id),('materials_list','=',item.codigo)])
            get_requi = self.env['dtm.requisicion'].search([('folio', '=', item.orden_trabajo)])
            get_requi_list = self.env['dtm.requisicion.material'].search([('model_id', '=', get_requi.id), ('codigo', '=', item.codigo)])
            if (not get_materials_line and not get_requi_list) or item.cantidad == 0 :
               item.unlink()
        for item in material:
            get_requerido = self.env['dtm.compras.requerido'].search([('codigo','=',item.codigo),('nombre','=',item.nombre)])
            item.unlink() if not get_requerido else None

        # Se recorre un set con los códigos de requerido para hacer la suma de las cantidades a comprar
        set_requerido = list(set(requerido.mapped('codigo')))
        for codigo in set_requerido:
            suma = sum(self.env['dtm.compras.requerido'].search([('codigo','=',codigo),('tipo_orden','!=','Requi')]).mapped('cantidad'))
            get_requerido = self.env['dtm.compras.requerido'].search([('codigo','=',codigo),('tipo_orden','!=','Requi')],limit=1)
            get_requi = self.env['dtm.compras.requerido'].search([('codigo', '=', codigo), ('tipo_orden', '=', 'Requi')], limit=1)
            if get_requerido:
                codigo == 2157 and print(get_requerido)
                vals = {
                    'codigo': codigo,
                    'nombre': get_requerido.nombre,
                    'cantidad': suma,

                }
                get_material = self.env['dtm.compras.material'].search([('codigo','=',codigo),('nombre','=',get_requerido.nombre)],limit=1)
                get_material.write(vals) if get_material else get_material.create(vals)
            if get_requi:
                vals = {
                    'codigo': codigo,
                    'nombre': get_requi.nombre,
                    'cantidad': get_requi.cantidad,
                }
                get_material = self.env['dtm.compras.material'].search(
                    [('codigo', '=', codigo), ('nombre', '=', get_requi.nombre)], limit=1)
                get_material.write(vals) if get_material else get_material.create(vals)
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

    conceptos_id = fields.Many2many('dtm.compras.conceptos')

    costo = fields.Float(string='Consto', readonly=True)
    total = fields.Float(string='Total', readonly=True)
    material = fields.Char(string='Material', readonly=True)
    codigo = fields.Integer(string='Código', readonly=True)
    ordenes = fields.Text(string='Orden', readonly=True)
    cantidad = fields.Text(string='cantidad', readonly=True)
    proveedor = fields.Text(string='Proveedor', readonly=True)
    permiso = fields.Boolean()

    @api.onchange('conceptos_id')
    def onchange_conceptos_id(self):
        # Todos los conceptos que hay en la BD
        all_conceptos = self.env['dtm.compras.conceptos'].search([])
        # Los IDs que siguen presentes en el wizard
        current_ids = self.conceptos_id.ids

        for concepto in all_conceptos:
            if concepto.id not in current_ids:
                concepto.unlink()  #  elimina de la tabla y de la relación
        nuevo_precio = self.env['dtm.compras.conceptos'].search([('id','in',current_ids)])
        suma_cantidad = sum(nuevo_precio.mapped('cantidad'))
        self.costo = suma_cantidad * self.total
        self.cantidad = suma_cantidad

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
            res['permiso'] = self.env.context.get('permiso')
            res['compra_id'] = get_codigo.id
            res['costo'] = get_codigo.costo
            res['total'] = get_codigo.unitario
            res['material'] = get_codigo.nombre
            res['cantidad'] = get_codigo.cantidad
            res['proveedor'] = get_codigo.proveedor_id.nombre
            res['conceptos_id'] = [(6,0,self.env['dtm.compras.conceptos'].search([]).ids)]

        return res

class Conceptos(models.Model):
    _name = "dtm.compras.conceptos"
    _description = "Tabla para archivar los conceptos a comprar"

    orden_trabajo = fields.Integer(string='Orden', readonly=True)
    nombre = fields.Char(string='Nombre', readonly=True)
    cliente = fields.Char(string='Cliente', readonly=True)
    disenador = fields.Char(string='Diseñador', readonly=True)
    cantidad = fields.Integer(string='Cantidad', readonly=True)
    nesteo = fields.Boolean(string='Nesteo', readonly=True)
    material = fields.Char(readonly=True)
    codigo = fields.Integer(readonly=True)
    permiso = fields.Boolean(compute='_compute_permiso', readonly=True)

    def _compute_permiso(self):
        for record in self:
            record.permiso = False
            if self.env.user.partner_id.email in ['ventas1@dtmindustry.com','rafaguzmang@hotmail.com']:
                record.permiso = True

    def action_rechazar(self):

        return {
            'name': 'Confirmar',
            'type': 'ir.actions.act_window',
            'res_model': 'dtm.compras.rechazo.wizard',
            'view_mode': 'form',
            'view_id': self.env.ref('dtm_compras.view_dtm_compras_rechazo_wizard').id,
            'target': 'new',
            'context': {'orden_trabajo':self.orden_trabajo,'disenador':self.disenador,'cliente':self.cliente,'nombre':self.nombre,'material':self.material,'codigo':self.codigo}
        }

class RechazarWizard(models.TransientModel):
    _name = "dtm.compras.rechazo.wizard"
    _description = "Ventan de diálogo para confirmación de borrado del material"

    orden_trabajo = fields.Integer(readonly=True)
    disenador = fields.Char(readonly=True)
    cliente = fields.Char(readonly=True)
    nombre = fields.Char(readonly=True)
    material = fields.Char(readonly=True)
    codigo = fields.Integer(readonly=True)

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        res['orden_trabajo'] = self.env.context.get('orden_trabajo')
        res['disenador'] = self.env.context.get('disenador')
        res['cliente'] = self.env.context.get('cliente')
        res['nombre'] = self.env.context.get('nombre')
        res['material'] = self.env.context.get('material')
        res['codigo'] = self.env.context.get('codigo')

        return res

    def action_confirmar(self):
        get_orden = self.env['dtm.odt'].search([('ot_number','=',self.orden_trabajo)]).materials_ids.filtered_domain([('materials_list','=',self.codigo)])
        get_orden.unlink()
        return self.env.ref('dtm_compras.dtm_compras_material_act_window').read()[0]

