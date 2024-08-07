from odoo import fields,models
import datetime

class Compras(models.Model):
    _name = "dtm.compras.requerido"
    _description = "Modulo de compras"

    orden_trabajo = fields.Char(string="ODT", readonly=True)
    proveedor_id = fields.Many2one("dtm.compras.proveedor",string="Proveedor")
    codigo = fields.Integer(string="Codigo")
    nombre = fields.Char(string="Nombre", readonly = True)
    cantidad = fields.Integer(string="Cantidad")
    costo = fields.Float(string="Costo")
    orden_compra = fields.Char(string="Orden de Compra")
    fecha_recepcion = fields.Date(string="Fecha  estimada de Recepción")
    disenador = fields.Char(string="Diseñador")
    observacion = fields.Char(string="Observaciones")

    def action_done(self):
        if self.proveedor_id.nombre:
            vals = {
                "proveedor":self.proveedor_id.nombre,
                "codigo":self.codigo,
                "descripcion":self.nombre,
                "cantidad":self.cantidad,
                "fecha_recepcion":self.fecha_recepcion
            }
            get_control = self.env['dtm.control.entradas'].search([("descripcion","=",self.nombre),("proveedor","=",self.proveedor_id.nombre),
                                                                   ("codigo","=",self.codigo)])
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

            self.env.cr.execute("INSERT INTO dtm_compras_realizado (orden_trabajo,proveedor,codigo,nombre,cantidad,costo,fecha_compra,fecha_recepcion,orden_compra) VALUES ('"+
                               str( self.orden_trabajo)+"','"+self.proveedor_id.nombre+"', '"+str(self.codigo)+"','"+self.nombre+"',"+str(self.cantidad)+","+str(self.costo)+
                                ", '"+str(datetime.datetime.today())+"','"+str(self.fecha_recepcion)+ "','"+str(self.orden_compra)+"')")
            self.env.cr.execute("DELETE FROM dtm_compras_requerido WHERE id="+ str(self._origin.id))


    def get_view(self, view_id=None, view_type='form', **options):
        res = super(Compras,self).get_view(view_id, view_type,**options)
        get_info = self.env['dtm.compras.requerido'].search([])
        mapa = {}
        for get in get_info:#Borra filas repetidas basadas en número de orden, codigo de material y cantidad
            cadena = str(get.orden_trabajo) + str(get.codigo) + get.nombre + str(get.cantidad)
            if mapa.get(cadena):
                mapa[cadena] = mapa.get(cadena) + 1
                get.unlink()
            else:
                mapa[cadena] = 1
        mapa2 = {}
        for material in get_info:
            if mapa2.get(material.codigo):
                mapa2[material.codigo] = mapa2.get(material.codigo) + 1
                get_col = self.env['dtm.compras.requerido'].search([('codigo','=',material.codigo)],order='id asc', limit=1)
                odt = f"{get_col.orden_trabajo} {material.orden_trabajo}"
                disenador = f"{get_col.disenador} {material.disenador}"
                cantidad = get_col.cantidad + material.cantidad
                val = {
                    "orden_trabajo":odt,
                    "disenador":disenador,
                    "cantidad":cantidad,
                }
                get_col.write(val)
                material.unlink()
            else:
                mapa2[material.codigo] = 1

        return res


class Realizado(models.Model):
    _name = "dtm.compras.realizado"
    _description = "Tabla donde se guardan las compras realizadas"
    _order = "id desc"

    orden_trabajo = fields.Char(string="Orden de Trabajo")
    proveedor = fields.Char(string="Proveedor")
    codigo = fields.Integer(string="Codigo")
    nombre = fields.Char(string="Nombre")
    cantidad = fields.Integer(string="Cantidad")
    cantidad_almacen = fields.Integer(string="C-Real")
    costo = fields.Float(string="Costo")
    orden_compra = fields.Char(string="Orden de Compra")
    fecha_compra = fields.Date(string="Fecha de compra")
    fecha_recepcion = fields.Date(string="Fecha de estimada de recepción")
    comprado = fields.Char(string="Comprado")

class Proveedor(models.Model):
    _name = "dtm.compras.proveedor"
    _descripcion = "Lista de provedores"
    _rec_name = "nombre"

    nombre = fields.Char(string="Nombre")


