from odoo import fields,api,models

class Precios(models.Model):
    _name = 'dtm.compras.precios'
    _description = 'Registro de precios de los materiales'
    _rec_name = 'nombre'
    _order = 'codigo'

    codigo = fields.Integer(string='Código', readonly=True)
    nombre = fields.Char(string='Nombre', readonly=True)
    precio = fields.Float(string='Precio', readonly=True)


    def get_view(self, view_id=None, view_type='form', **options):
        res = super(Precios, self).get_view(view_id, view_type, **options)




        return res
