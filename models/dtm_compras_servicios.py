from odoo import fields,api,models
from datetime import datetime


class Servicios(models.Model):
    _name = "dtm.compras.servicios"
    _description = "Modelo para registrar los servicios externos"

    nombre = fields.Char(string="Nombre del Servicio")
    cantidad = fields.Integer(string="Cantidad")
    tipo_orden = fields.Char(string="OT/NPI")
    revision_ot = fields.Integer(string="VERSIÓN",default=1,readonly=True) # Esto es versión
    numero_orden = fields.Integer(string="Orden")
    proveedor = fields.Char(string="Proveedor")
    fecha_solicitud = fields.Date(string="Fecha de Solicitud", default= datetime.today(),readonly=True)
    fecha_compra = fields.Date(string="Fecha de Compra",readonly=True)
    fecha_entrada = fields.Date(string="Fecha de Entrada",readonly=True)
    material_id = fields.Many2many("dtm.materials.line",readonly=True)
    anexos_id = fields.Many2many("ir.attachment",readonly=True)
    comprado = fields.Char(string="Recibido", readonly=True)
    listo = fields.Boolean()

    def get_view(self, view_id=None, view_type='form', **options):
        res = super(Servicios,self).get_view(view_id, view_type,**options)

        servicios = self.env['dtm.compras.servicios'].search([("comprado","!=","Recibido")])
        for servicio in servicios:
            # print(servicio.nombre,servicio.nombre)
            get_recibo = self.env['dtm.compras.realizado'].search([("nombre","ilike",servicio.nombre),("orden_trabajo","ilike",servicio.numero_orden),("comprado","=","Recibido")])
            get_recibo and servicio.write({'comprado': 'Recibido'})
            sum = 0
            for material in servicio.material_id:
                sum += material.materials_required
            sum == 0 and servicio.write({'listo':True})

        return res
