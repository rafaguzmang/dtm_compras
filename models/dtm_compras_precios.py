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

        get_realizado = self.env['dtm.compras.realizado'].search([])
        for record in get_realizado:
            if record.codigo in self.env['dtm.compras.precios'].search([]).mapped('codigo'):
                self.env['dtm.compras.precios'].search([('codigo','=',record.codigo)]).write(
                    {'nombre': record.nombre, 'precio': record.unitario})
            else:
                self.env['dtm.compras.precios'].create({'codigo':record.codigo,'nombre':record.nombre,'precio':record.unitario})


        return res
