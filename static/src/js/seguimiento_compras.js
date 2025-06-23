/** @odoo-module **/

import { Component, useState, useRef, onMounted   } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class Seguimiento extends Component {
    setup() {
        this.state = useState({
            datos: {}
        });

        onMounted(async () => {
            try{
                const response = await fetch('/dtm_compras/get_data');

                const data = await response.json();
                console.log(data);
                this.state.datos = data;

            }catch (error){
                console.log(error)
            }
        });
    }

//    async cargarDatos() {
//        const response = await fetch('/dtm_compras/get_data');
//        const data = await response.json();
//        this.state.datos = data;
//        console.log(data);
//    }
}
Seguimiento.template = "dtm_compras.seguimiento_compras";

registry.category("actions").add("dtm_compras.seguimiento_compras", Seguimiento);
