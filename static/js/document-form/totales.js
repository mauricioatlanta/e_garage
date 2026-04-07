/**
 * totales.js - Módulo de cálculo de totales e impuestos
 * 
 * Extraído del código embebido en document_form.html
 */

(function() {
    'use strict';

    const EG = window.EG = window.EG || {};
    var isSerializingRows = false;

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
        var totalEl = document.getElementById('t_total');
        if (totalEl) {
            totalEl.classList.remove('totales-pulse');
            void totalEl.offsetWidth;
            totalEl.classList.add('totales-pulse');
            window.clearTimeout(totalEl.__pulseTimer);
            totalEl.__pulseTimer = window.setTimeout(function() {
                totalEl.classList.remove('totales-pulse');
            }, 180);
        }

        // Programar guardado de borrador
        if (typeof window.scheduleDocumentDraftSave === 'function') {
            window.scheduleDocumentDraftSave();
        }
        if (!isSerializingRows) {
            serializeRows();
        }
    }

    function setText(selOrEl, txt) {
        var el = typeof selOrEl === 'string' ? document.querySelector(selOrEl) : selOrEl;
        if (el) el.textContent = txt;
    }

    function collectServicioRow(row) {
        var servicioId = (row.querySelector('.srv-id') && row.querySelector('.srv-id').value || '').trim();
        var nombre = (row.querySelector('.srv-input') && row.querySelector('.srv-input').value || '').trim();
        var cantidad = 1;
        var precio = EG.utils.parseNumericInput(row.querySelector('.serv-precio') && row.querySelector('.serv-precio').value || 0);
        var descuento = 0;
        var subtotal = EG.utils.parseNumericInput(row.querySelector('.serv-subtotal') && row.querySelector('.serv-subtotal').value || 0);
        var isEmpty = !servicioId && !nombre && !precio;
        var isInvalid = !isEmpty && !servicioId && !!nombre;

        row.classList.toggle('ring-1', isInvalid);
        row.classList.toggle('ring-red-500', isInvalid);

        return {
            servicio_id: servicioId,
            nombre: nombre,
            cantidad: cantidad,
            precio: precio,
            descuento: descuento,
            subtotal: subtotal,
            _empty: isEmpty,
            _invalid: isInvalid
        };
    }

    /**
     * Serializa las filas dinámicas para enviar al servidor
     */
    function serializeRows() {
        isSerializingRows = true;
        console.log('Serializando filas dinamicas...');
        try {
            var rep = Array.from(document.querySelectorAll('#repuestos-container .dynamic-element')).map(function(row) {
                return {
                    id: (row.querySelector('.rep-id') && row.querySelector('.rep-id').value || '').trim(),
                    codigo: (row.querySelector('.rep-codigo') && row.querySelector('.rep-codigo').value || '').trim(),
                    nombre: (row.querySelector('.rep-nombre') && row.querySelector('.rep-nombre').value || '').trim(),
                    cantidad: Number(row.querySelector('.rep-cantidad') && row.querySelector('.rep-cantidad').value || 0),
                    precio: EG.utils.parseNumericInput(row.querySelector('.rep-precio-venta') && row.querySelector('.rep-precio-venta').value || 0),
                    descuento: Number(row.querySelector('.rep-descuento') && row.querySelector('.rep-descuento').value || 0),
                    subtotal: EG.utils.parseNumericInput(row.querySelector('.rep-subtotal') && row.querySelector('.rep-subtotal').value || 0),
                    origen_repuesto: (row.querySelector('.rep-origen') && row.querySelector('.rep-origen').value || 'STOCK_BODEGA').trim(),
                    pieza_desarme_id: (row.querySelector('.rep-pieza-desarme-id') && row.querySelector('.rep-pieza-desarme-id').value || '').trim(),
                    costo_linea: EG.utils.parseNumericInput(row.querySelector('.rep-costo-linea') && row.querySelector('.rep-costo-linea').value || 0)
                };
            });

            var invalidServiceRows = [];
            var serv = Array.from(document.querySelectorAll('#servicios-container .dynamic-element')).reduce(function(acc, row) {
                var item = collectServicioRow(row);
                if (item._empty) return acc;
                if (item._invalid) invalidServiceRows.push(item);
                acc.push({
                    servicio_id: item.servicio_id,
                    nombre: item.nombre,
                    cantidad: item.cantidad,
                    precio: item.precio,
                    descuento: item.descuento,
                    subtotal: item.subtotal
                });
                return acc;
            }, []);

            var otros = Array.from(document.querySelectorAll('#otros-container .dynamic-element')).map(function(row) {
                return {
                    servicio_id: (row.querySelector('.otr-servicio-id') && row.querySelector('.otr-servicio-id').value || '').trim(),
                    nombre: (row.querySelector('.otr-search') && row.querySelector('.otr-search').value || '').trim(),
                    empresa_ext: (row.querySelector('.otr-empresa') && row.querySelector('.otr-empresa').value || '').trim(),
                    precio_taller: EG.utils.parseNumericInput(row.querySelector('.otr-precio-taller') && row.querySelector('.otr-precio-taller').value || 0),
                    precio: EG.utils.parseNumericInput(row.querySelector('.otr-precio') && row.querySelector('.otr-precio').value || 0),
                    ganancia: EG.utils.parseNumericInput(row.querySelector('.otr-precio') && row.querySelector('.otr-precio').value || 0) - EG.utils.parseNumericInput(row.querySelector('.otr-precio-taller') && row.querySelector('.otr-precio-taller').value || 0)
                };
            }).filter(function(row) {
                return !!(row.nombre || row.servicio_id || row.empresa_ext || row.precio_taller > 0 || row.precio > 0);
            });

            var repJsonEl = document.getElementById('id_repuestos_json');
            var servJsonEl = document.getElementById('id_servicios_json');
            var otrosJsonEl = document.getElementById('id_otros_json');

            if (repJsonEl) repJsonEl.value = JSON.stringify(rep);
            if (servJsonEl) servJsonEl.value = JSON.stringify(serv);
            if (otrosJsonEl) otrosJsonEl.value = JSON.stringify(otros);

            window.__EG_INVALID_SERVICE_ROWS__ = invalidServiceRows;

            console.log('Repuestos:', rep.length, 'Servicios:', serv.length, 'Otros:', otros.length);
            return {
                repuestos: rep,
                servicios: serv,
                otros: otros,
                invalidServiceRows: invalidServiceRows
            };
        } finally {
            isSerializingRows = false;
        }
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
        collectServicioRow: collectServicioRow,
        setText: setText,
        init: init
    };
    window.recalcTotales = recalcTotales;
    window.serializeRows = serializeRows;

})();
