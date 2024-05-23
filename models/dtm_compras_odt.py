from odoo import fields,models
from datetime import datetime


class ComprasOdt(models.Model):
    _name = "dtm.compras.odt"
    _description = "Visualización de la orden de trabajo"

    status = fields.Char(readonly=True)
    ot_number = fields.Integer(string="NÚMERO",readonly=True)
    tipe_order = fields.Char(string="TIPO",readonly=True)
    name_client = fields.Char(string="CLIENTE",readonly=True)
    product_name = fields.Char(string="NOMBRE DEL PRODUCTO",readonly=True)
    date_in = fields.Date(string="FECHA DE ENTRADA", default= datetime.today(),readonly=True)
    po_number = fields.Char(string="PO",readonly=True)
    date_rel = fields.Date(string="FECHA DE ENTREGA", default= datetime.today())
    version_ot = fields.Integer(string="VERSIÓN OT",default=1)
    color = fields.Char(string="COLOR",default="N/A")
    cuantity = fields.Integer(string="CANTIDAD",readonly=True)
    materials_ids = fields.Many2many("dtm.materials.line",string="Lista")
    firma = fields.Char(string="Firma Compras", readonly = True)
    disenador = fields.Char(string="Diseñador")

    anexos_id = fields.Many2many("dtm.proceso.anexos")

    notes = fields.Text(string="Notas")

    #---------------------Resumen de descripción------------

    description = fields.Text(string="DESCRIPCIÓN")

    def action_firma(self):
        self.firma = self.env.user.partner_id.name
        get_ot = self.env['dtm.odt'].search([("ot_number","=",self.ot_number)])
        print("resultado",get_ot)
        get_ot.write({"firma_compras": self.firma})


    def action_imprimir_formato(self): # Imprime según el formato que se esté llenando
        return self.env.ref("dtm_odt.formato_orden_de_trabajo").report_action(self)

    def action_imprimir_materiales(self): # Imprime según el formato que se esté llenando
        return self.env.ref("dtm_odt.formato_lista_materiales").report_action(self)
