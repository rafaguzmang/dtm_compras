/** @odoo-module **/

import { Component, useState, useRef, onMounted   } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { DialogMateriales } from "./dialog_materiales"

export class Seguimiento extends Component {
    static components = { DialogMateriales };
    setup() {
        this.state = useState({
            datos: {},
            showDialogMateriales:false,
            dialogOrden:null,
            todosMateriales:[],
            dialogMateriales:[],
        });

        onMounted(async () => {
            try{
                const response = await fetch('/dtm_compras/get_data');

                const data = await response.json();
//                console.log(data);
                this.state.datos = data;

                const materiales_response = await fetch('/seguimiento_materiales',{
                    method:'POST',
                    headers:{
                        'Content-Type': 'application/json',
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    body:JSON.stringify({})
                });
                const material = await materiales_response.json();
                this.todosMateriales = material.result;
//                console.log(this.todosMateriales)


            }catch (error){
                console.log(error)
            }
        });
    }

     mostrarDialogo = (orden =>
         {
            const materialData = this.todosMateriales.find(item => item.orden === orden);
//            console.log('Orden',orden);
//            console.log('materialData',materialData.materiales);
            if (materialData.materiales){
                this.state.showDialogMateriales = true;
                this.state.dialogOrden = orden;
                this.state.dialogMateriales = materialData.materiales;
                console.log(materialData.materiales);
            }else {
                console.error("No se encontraron materiales para la orden:", orden);
            }
        })
}
Seguimiento.template = "dtm_compras.seguimiento_compras";

registry.category("actions").add("dtm_compras.seguimiento_compras", Seguimiento);
