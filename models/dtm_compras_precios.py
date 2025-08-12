from odoo import fields,api,models

class Precios(models.Model):
    _name = 'dtm.compras.precios'
    _description = 'Registro de precios de los materiales'
    _rec_name = 'nombre'
    _order = 'codigo'

    codigo = fields.Integer(string='Código', readonly=True)
    nombre = fields.Char(string='Nombre', readonly=True)
    precio = fields.Float(string='Mostrador', readonly=True)
    mayoreo = fields.Float(string='Mayoreo', readonly=True)



    def get_view(self, view_id=None, view_type='form', **options):
        res = super(Precios, self).get_view(view_id, view_type, **options)

        # get_codigos = self.env['dtm.materiales'].search([])
        # get_precios_code = self.env['dtm.compras.precios'].search([])
        #
        # cont = 0
        # for diferente in get_codigos:
        #     get_dif = self.env['dtm.compras.precios'].search([('codigo','=',diferente.id),('nombre','!=',f"{diferente.nombre} {diferente.medida}")])
        #     if get_dif:
        #         cont += 1
        # #         print('get_dif',get_dif.codigo)
        # # print(cont)
        #
        # for precio in get_precios_code:
        #     precio.codigo == 1639 and print(precio.codigo)
        #     get_codigos = self.env['dtm.materiales'].search(
        #         [('id', '=', precio.codigo)], limit=1
        #     )
        #
        #     if get_codigos:
        #         nombre_ok = str(get_codigos.nombre).lower() in str(precio.nombre).lower()
        #         medida_ok = str(get_codigos.medida).lower() in str(precio.nombre).lower()
        #
        #         if nombre_ok and medida_ok:
        #             # Ambos están contenidos
        #             get_codigos.write({'mostrador': precio.precio, 'mayoreo': precio.mayoreo})

        # print('-----------------------------------------------')

        get_self = self.env['dtm.compras.precios'].search([])
        for item in get_self:
            get_data = self.env['dtm.materiales'].search([('id','=',item.codigo)])
            get_inv = self.env['dtm.diseno.almacen'].search([('id','=',item.codigo)])
            if get_data:
                item.write({'nombre':f"{get_data.nombre} {get_data.medida}",'precio':get_data.mostrador,'mayoreo':get_data.mayoreo})
            else:
                item.write({'nombre': f"{get_inv.nombre} {get_inv.medida}"})




        return res
