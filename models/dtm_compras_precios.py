from odoo import fields,api,models

class Precios(models.Model):
    _name = 'dtm.compras.precios'
    _description = 'Registro de precios de los materiales'
    _rec_name = 'nombre'
    _order = 'codigo'

    codigo = fields.Integer(string='Código', readonly=True)
    tipo_material = fields.Char(string='Tipo')
    nombre = fields.Char(string='Nombre', readonly=True)
    precio = fields.Float(string='Mostrador', readonly=True)
    mayoreo = fields.Float(string='Mayoreo', readonly=True)



    def get_view(self, view_id=None, view_type='form', **options):
        res = super(Precios, self).get_view(view_id, view_type, **options)

        get_self = self.env['dtm.compras.precios'].search([])
        for item in get_self:
            get_data = self.env['dtm.materiales'].search([('id','=',item.codigo)],limit=1)
            get_inv = self.env['dtm.diseno.almacen'].search([('id','=',item.codigo)],limit=1)

            if get_data.nombre and get_data.nombre in item.nombre:
                # print(get_data.nombre)
                item.write({'nombre':f"{get_data.nombre} {get_data.medida}",'precio':get_data.mostrador,'mayoreo':get_data.mayoreo,'tipo_material':'Indirecto'})
            if get_inv.nombre and get_inv.nombre in item.nombre:
                item.write({'nombre': f"{get_inv.nombre} {get_inv.medida}" ,'tipo_material':'Directo'})

        return res
