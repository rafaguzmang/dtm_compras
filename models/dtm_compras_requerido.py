from odoo import fields,models

class Compras(models.Model):
    _name = "dtm.compras.requerido"
    _description = "Modulo de compras"

    orden_trabajo = fields.Char(string="Orden de Trabajo")
    proveedor_id = fields.Many2one("dtm.compras.proveedor",string="Proveedor")
    codigo_id = fields.Many2one("dtm.compras.codigo",string="Codigo")
    nombre = fields.Char(string="Nombre", readonly = True)
    cantidad = fields.Integer(string="Cantidad", readonly = True)
    costo = fields.Float(string="Costo")
    fecha_recepcion = fields.Date(string="Fecha  estimada de Recepción")

    def action_done(self):
        print(self.proveedor_id.nombre , self.codigo_id.codigo,  self.fecha_recepcion)
        if self.proveedor_id.nombre  and self.codigo_id.codigo and self.fecha_recepcion:
            print("Funciona")

            vals = {
                "proveedor":self.proveedor_id.nombre,
                "codigo":self.codigo_id.codigo,
                "descripcion":self.nombre,
                "cantidad":self.cantidad,
                "fecha_recepcion":self.fecha_recepcion,

                "material_correcto":"no",
                "material_cantidad":"no",
                "material_calidad":"no",
                "material_entiempo":"no",
                "material_aprobado":"rechazado",
                "motivo":"",
                "correctiva":""
            }
            # print(self.proveedor_id.nombre)
            get_control = self.env['dtm.control.entradas'].search([("descripcion","=",self.nombre),("proveedor","=",self.proveedor_id.nombre),
                                                                   ("codigo","=",self.codigo_id.codigo)])
            if not get_control:
                get_control.create(vals)
            else:
                cantidad = 0
                for get in get_control:
                    cantidad += get.cantidad
                vals = {
                    "cantidad":cantidad + self.cantidad
                }
                get_control.write(vals)

            self.env.cr.execute("INSERT INTO dtm_compras_realizado (orden_trabajo,nombre,cantidad,description) VALUES ('"+
                                self.orden_trabajo+"','"+self.nombre+"',"+str(self.cantidad)+",'"+str(self.costo)+"')")
            self.env.cr.execute("DELETE FROM dtm_compras_requerido WHERE id="+ str(self._origin.id))


    def get_view(self, view_id=None, view_type='form', **options):
        res = super(Compras,self).get_view(view_id, view_type,**options)
        get_info = self.env['dtm.compras.requerido'].search([])
        mapa = {}
        for get in get_info:
            cadena = get.orden_trabajo + get.nombre + str(get.cantidad) + str(get.costo)
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
    costo = fields.Text(string="Descripción")

class Proveedor(models.Model):
    _name = "dtm.compras.proveedor"
    _descripcion = "Lista de provedores"
    _rec_name = "nombre"

    nombre = fields.Char(string="Nombre")

class Codigo(models.Model):
    _name = "dtm.compras.codigo"
    _descripcion = "Lista de cogigos"
    _rec_name = "codigo"

    codigo = fields.Char(string="Codigo")
