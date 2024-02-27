from odoo import fields,models

class Compras(models.Model):
    _name = "dtm.compras.requerido"
    _description = "Modulo de compras"

    orden_trabajo = fields.Char(string="Orden de Trabajo")
    nombre = fields.Char(string="Nombre")
    cantidad = fields.Integer(string="Cantidad")
    description = fields.Text(string="Descripción")

    def action_done(self):
        self.env.cr.execute("INSERT INTO dtm_compras_realizado (orden_trabajo,nombre,cantidad,description) VALUES ('"+
                            self.orden_trabajo+"','"+self.nombre+"',"+str(self.cantidad)+",'"+self.description+"')")
        self.env.cr.execute("DELETE FROM dtm_compras_requerido WHERE id="+ str(self._origin.id))


    def get_view(self, view_id=None, view_type='form', **options):
        res = super(Compras,self).get_view(view_id, view_type,**options)
        get_info = self.env['dtm.compras.requerido'].search([])
        mapa = {}
        for get in get_info:
            cadena = get.orden_trabajo + get.nombre + str(get.cantidad) + get.description
            if mapa.get(cadena):
                mapa[cadena] = mapa.get(cadena) + 1
                self.env.cr.execute("DELETE FROM dtm_compras_requerido WHERE id ="+str(get._origin.id))
            else:
                mapa[cadena] = 1
        return res


class Realizado(models.Model):
    _name = "dtm.compras.realizado"
    _description = "Tabla donde se guardan las compras realizadas"

    orden_trabajo = fields.Char(string="Orden de Trabajo")
    nombre = fields.Char(string="Nombre")
    cantidad = fields.Integer(string="Cantidad")
    description = fields.Text(string="Descripción")
