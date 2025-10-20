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
            transitoList:{},
            activeDiv: 'div1'
        });
        this.showDiv = this.showDiv.bind(this);


        onMounted(async () => {
            try{
                const response = await fetch('/dtm_compras/get_data',{
                    method:'POST',
                    headers:{
                        'Content-Type': 'application/json',
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    body:JSON.stringify({})
                });

                const data = await response.json();
                this.state.datos = data.result || {};   // 👈 aseguras objeto vacío

//                console.log(data.result);
                this.state.datos = data.result;

                const materiales_response = await fetch('/dtm_materiales/get_data',{
                    method:'POST',
                    headers:{
                        'Content-Type': 'application/json',
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    body:JSON.stringify({})
                });
                const material = await materiales_response.json();
                this.todosMateriales = material.result;
                console.log('material1',material.result);
                console.log('material',this.todosMateriales);

                const transito_data = await fetch('/dtm_comprado/get_data',{
                    method:'POST',
                    headers:{
                        'Content-Type': 'application/json',
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    body:JSON.stringify({})
                });
                const transito = await transito_data.json();
                this.state.transitoList = transito.result || {};   // 👈 aseguras objeto vacío

//                console.log(transito.result);
                this.state.transitoList = transito.result;
//                console.log(this.state.transitoList);


            }catch (error){
                console.log(error)
            }
        });
    }

    showDiv(div) {
        this.state.activeDiv = div;
    }

    mostrarDialogo = (orden =>
         {
             console.log('Orden',this.todosMateriales);
            const materialData = this.todosMateriales.find(item => item.orden == orden);
            console.log('materialData',materialData,orden);
            if (materialData.materiales){
                this.state.showDialogMateriales = true;
                this.state.dialogOrden = orden;
                this.state.dialogMateriales = materialData.materiales;
            }else {
                console.error("No se encontraron materiales para la orden:", orden);
            }
        })
}
Seguimiento.template = "dtm_compras.seguimiento_compras";

registry.category("actions").add("dtm_compras.seguimiento_compras", Seguimiento);
