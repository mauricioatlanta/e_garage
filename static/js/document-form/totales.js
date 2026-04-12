/**
 * totales.js - Módulo de cálculo de totales e impuestos
 * 
 * Extraído del código embebido en document_form.html
 */

(function() {
    'use strict';

    const EG = window.EG = window.EG || {};

    /**
     * Suma valores desde inputs
     */
    function sumFromInputs(selector) {
        var elements = document.querySelectorAll(selector);
        return Array.from(elements).reduce(function(acc, el) {
            var raw = el.tagName === 'INPUT' ? el.value : el.textContent;
            var num = Number((raw || '').toString().replace(/[^0-9.-]/g, ''));
            return acc + (isNaN(num) ? 0 : num);
        }, 0);
    }

    /**
     * Recalcula todos los totales del documento
     */
    function recalcTotales() {
        var rep = sumFromInputs('.rep-subtotal');
        var serv = sumFromInputs('.serv-subtotal');
        var otros = sumFromInputs('.otr-subtotal');

        console.log('Totales: rep=' + rep + ', serv=' + serv + ', otros=' + otros);

        // Calcular impuestos dinámicamente desde ui_config.tax_lines
        var totalTaxes = 0;
        var taxLines = window.EG && window.EG.cfg && window.EG.cfg.taxLines || [];

        taxLines.forEach(function(taxLine) {
            var checkbox = document.getElementById('include_' + taxLine.id);
            var isEnabled = checkbox ? checkbox.checked : false;

            if (isEnabled) {
                var baseAmount = 0;
                if (taxLine.applies_to === 'repuestos') {
                    baseAmount = rep;
                } else if (taxLine.applies_to === 'servicios') {
                    baseAmount = serv;
                } else if (taxLine.applies_to === 'all') {
                    baseAmount = rep + serv + otros;
                }

                var taxRate = Number(taxLine.rate) / 100;
                var taxAmount = baseAmount * taxRate;
                totalTaxes += taxAmount;

                setText('#t_' + taxLine.id, EG.utils.money(taxAmount));
            } else {
                setText('#t_' + taxLine.id, EG.utils.money(0));
            }
        });

        // Actualizar subtotales
        setText('#t_repuestos', EG.utils.money(rep));
        setText('#t_servicios', EG.utils.money(serv));
        setText('#t_otros', EG.utils.money(otros));

        // Calcular total general
        var grandTotal = rep + serv + otros + totalTaxes;
        setText('#t_total', EG.utils.money(grandTotal));

        // Programar guardado de borrador
        if (typeof window.scheduleDocumentDraftSave === 'function') {
            window.scheduleDocumentDraftSave();
        }
    }

    function setText(selOrEl, txt) {
        var el = typeof selOrEl === 'string' ? document.querySelector(selOrEl) : selOrEl;
        if (el) el.textContent = txt;
    }

    /**
     * Serializa las filas dinámicas para enviar al servidor
     */
    function serializeRows() {
        console.log('Serializando filas dinamicas...');

        var rep = Array.from(document.querySelectorAll('#repuestos-container .dynamic-element')).map(function(row) {
            return {
                id: (row.querySelector('.rep-id') && row.querySelector('.rep-id').value || '').trim(),
                codigo: (row.querySelector('.rep-codigo') && row.querySelector('.rep-codigo').value || '').trim(),
                nombre: (row.querySelector('.rep-nombre') && row.querySelector('.rep-nombre').value || '').trim(),
                cantidad: Number(row.querySelector('.rep-cantidad') && row.querySelector('.rep-cantidad').value || 0),
                precio: EG.utils.parseNumericInput(row.querySelector('.rep-precio-venta') && row.querySelector('.rep-precio-venta').value || 0),
                descuento: Number(row.querySelector('.rep-descuento') && row.querySelector('.rep-descuento').value || 0),
                origen_repuesto: (row.querySelector('.rep-origen') && row.querySelector('.rep-origen').value || 'STOCK_BODEGA').trim(),
                pieza_desarme_id: (row.querySelector('.rep-pieza-desarme-id') && row.querySelector('.rep-pieza-desarme-id').value || '').trim(),
                costo_linea: EG.utils.parseNumericInput(row.querySelector('.rep-costo-linea') && row.querySelector('.rep-costo-linea').value || 0)
            };
        });

        var serv = Array.from(document.querySelectorAll('#servicios-container .dynamic-element')).map(function(row) {
            return {
                servicio_id: (row.querySelector('.srv-id') && row.querySelector('.srv-id').value || '').trim(),
                nombre: (row.querySelector('.srv-input') && row.querySelector('.srv-input').value || '').trim(),
                precio: EG.utils.parseNumericInput(row.querySelector('.serv-precio') && row.querySelector('.serv-precio').value || 0)
            };
        });

        var otros = Array.from(document.querySelectorAll('#otros-container .dynamic-element')).map(function(row) {
            return {
                servicio_id: (row.querySelector('.otr-servicio-id') && row.querySelector('.otr-servicio-id').value || '').trim(),
                nombre: (row.querySelector('.otr-search') && row.querySelector('.otr-search').value || '').trim(),
                empresa_ext: (row.querySelector('.otr-empresa') && row.querySelector('.otr-empresa').value || '').trim(),
                precio_taller: EG.utils.parseNumericInput(row.querySelector('.otr-precio-taller') && row.querySelector('.otr-precio-taller').value || 0),
                precio: EG.utils.parseNumericInput(row.querySelector('.otr-precio') && row.querySelector('.otr-precio').value || 0)
            };
        });

        var repJsonEl = document.getElementById('id_repuestos_json');
        var servJsonEl = document.getElementById('id_servicios_json');
        var otrosJsonEl = document.getElementById('id_otros_json');

        if (repJsonEl) repJsonEl.value = JSON.stringify(rep);
        if (servJsonEl) servJsonEl.value = JSON.stringify(serv);
        if (otrosJsonEl) otrosJsonEl.value = JSON.stringify(otros);

        console.log('Repuestos:', rep.length, 'Servicios:', serv.length, 'Otros:', otros.length);
    }

    /**
     * Inicializar eventos de impuestos
     */
    function init() {
        // Agregar event listeners a todos los checkboxes de impuestos
        document.querySelectorAll('.tax-checkbox').forEach(function(checkbox) {
            checkbox.addEventListener('change', recalcTotales);
        });

        console.log('Totales module initialized');
    }

    // Exports
    EG.totales = {
        sumFromInputs: sumFromInputs,
        recalcTotales: recalcTotales,
        serializeRows: serializeRows,
        setText: setText,
        init: init
    };
    window.recalcTotales = recalcTotales;
    window.serializeRows = serializeRows;

})();
