from odoo import fields,api,models
from datetime import datetime


class Servicios(models.Model):
    _name = "dtm.compras.servicios"
    _description = "Modelo para registrar los servicios externos"

    nombre = fields.Char(string="Nombre del Servicio")
    cantidad = fields.Integer(string="Cantidad")
    tipo_orden = fields.Char(string="OT/NPI")
    numero_orden = fields.Integer(string="Orden")
    proveedor = fields.Char(string="Proveedor")
    fecha_solicitud = fields.Date(string="Fecha de Solicitud", default= datetime.today(),readonly=True)
    fecha_compra = fields.Date(string="Fecha de Compra",readonly=True)
    fecha_entrada = fields.Date(string="Fecha de Entrada",readonly=True)
    material_id = fields.Many2many("dtm.materials.line",readonly=True)
    anexos_id = fields.Many2many("ir.attachment",readonly=True)
