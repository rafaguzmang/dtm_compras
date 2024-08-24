from odoo import fields,models
from datetime import datetime


class ComprasOdt(models.Model):
    _name = "dtm.compras.odt"
    _inherit = ['mail.thread']
    _description = "Visualización de la orden de trabajo"
    _order = "ot_number desc"


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
    # materials_ids = fields.Many2many("dtm.materials.line",string="Lista",readonly=True)
    firma = fields.Char(string="Firma Compras", readonly = True)
    firma_compras = fields.Char(string = "Compras", readonly = True)
    firma_diseno = fields.Char(string = "Diseñador", readonly = True)
    firma_almacen = fields.Char(string = "", readonly = True)
    firma_ventas = fields.Char(string = "Ventas", readonly = True)
    firma_proceso = fields.Char(string = "", readonly = True)

    anexos_id = fields.Many2many("dtm.proceso.anexos")

    notes = fields.Text(string="Notas")

    #---------------------Resumen de descripción------------

    description = fields.Text(string="DESCRIPCIÓN")

    pausado = fields.Char(string="Detenido por: ", readonly=True)
    status_pausado = fields.Char()
    pausa_motivo = fields.Text()

    materials = fields.Integer(string="Material")
    firma_parcial = fields.Boolean()
    firma_ventas_kanba = fields.Char(string = "Ventas", readonly = True)
    firma_compras_kanba = fields.Char(string = "Compras", readonly = True)
    firma_almacen_kanba = fields.Char(string = "", readonly = True)
    firma_calidad_kanba = fields.Char(string = "", readonly = True)

    def get_view(self, view_id=None, view_type='form', **options):
        res = super(ComprasOdt,self).get_view(view_id, view_type,**options)

        get_process = self.env['dtm.proceso'].search([])
        for proceso in get_process:
            vals = {
                "status": proceso.status,
                "ot_number": proceso.ot_number,
                "tipe_order": proceso.tipe_order,
                "name_client": proceso.name_client,
                "product_name": proceso.product_name,
                "date_in": proceso.date_in,
                "po_number": proceso.po_number,
                "date_rel": proceso.date_rel,
                "version_ot": proceso.version_ot,
                "color": proceso.color,
                "cuantity": proceso.cuantity,
                "materials_ids": proceso.materials_ids,
                "firma": self.env.user.partner_id.name,
                "firma_diseno": proceso.firma_diseno,
                "firma_almacen": proceso.firma_almacen,
                "firma_proceso": proceso.firma,
                "firma_ventas": proceso.firma_ventas,
                "anexos_id":proceso.anexos_id,
                "description": proceso.description,
                "pausado": proceso.pausado,
                "status_pausado": proceso.status_pausado,
                "materials": proceso.materials,
                "firma_parcial": proceso.firma_parcial,
                "firma_ventas_kanba": proceso.firma_ventas_kanba,
                "firma_compras_kanba": proceso.firma_compras_kanba,
                "firma_almacen_kanba": proceso.firma_almacen_kanba,
                "firma_calidad_kanba": proceso.firma_calidad_kanba,
            }

            get_self = self.env['dtm.compras.odt'].search([("ot_number","=", proceso.ot_number)])
            if get_self:
                get_self.write(vals)
            else:
                get_self.create(vals)

        return res

    def action_firma(self):
        self.firma = self.env.user.partner_id.name
        self.firma_compras_kanba = "Compras"
        get_ot = self.env['dtm.odt'].search([("ot_number","=",self.ot_number)])
        get_ot.write({"firma_compras": self.firma})
        get_procesos = self.env['dtm.proceso'].search([("ot_number","=",self.ot_number)])
        get_procesos.write({
            "firma_compras": self.firma,
            "firma_compras_kanba": "Compras"
        })

    def action_imprimir_formato(self): # Imprime según el formato que se esté llenando
        return self.env.ref("dtm_odt.formato_orden_de_trabajo").report_action(self)

    def action_imprimir_materiales(self): # Imprime según el formato que se esté llenando
        return self.env.ref("dtm_odt.formato_lista_materiales").report_action(self)

