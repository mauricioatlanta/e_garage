/**
 * line_items_bootstrap.js - Hidrata o limpia las filas iniciales del formulario
 */

(function() {
    'use strict';

    var EG = window.EG = window.EG || {};

    function getForm() {
        return document.getElementById('document-form');
    }

    function getLineItems() {
        var bootstrap = EG.state && EG.state.getBootstrap ? EG.state.getBootstrap() : {};
        var lineItems = bootstrap && bootstrap.line_items ? bootstrap.line_items : {};

        return {
            repuestos: Array.isArray(lineItems.repuestos) ? lineItems.repuestos : [],
            servicios: Array.isArray(lineItems.servicios) ? lineItems.servicios : [],
            otros: Array.isArray(lineItems.otros) ? lineItems.otros : []
        };
    }

    function clearRows() {
        document.querySelectorAll('#repuestos-container .dynamic-element').forEach(function(row) {
            row.remove();
        });
        document.querySelectorAll('#servicios-container .dynamic-element').forEach(function(row) {
            row.remove();
        });
        document.querySelectorAll('#otros-container .dynamic-element').forEach(function(row) {
            row.remove();
        });

        ['servicios-empty-hint', 'otros-empty-hint'].forEach(function(id) {
            var hint = document.getElementById(id);
            if (hint) {
                hint.classList.remove('hidden');
            }
        });

        ['id_repuestos_json', 'id_servicios_json', 'id_otros_json'].forEach(function(id) {
            var input = document.getElementById(id);
            if (input) {
                input.value = '[]';
            }
        });
    }

    function hydrateRepuestos(rows) {
        console.log('[DESARME] hydrateRepuestos: rows.length=', rows.length, ' window.addRepuestoRow=', typeof window.addRepuestoRow);
        rows.forEach(function(rep) {
            if (typeof window.addRepuestoRow !== 'function') {
                console.warn('[DESARME] window.addRepuestoRow no disponible — fila saltada');
                return;
            }

            var row = window.addRepuestoRow(rep.rowId || null);
            if (!row || !row.__applyRepData) {
                return;
            }

            row.__applyRepData({
                id: rep.id || '',
                nombre: rep.nombre || '',
                codigo: rep.codigo || '',
                cantidad: rep.cantidad || 1,
                precio_venta: rep.precio_venta != null ? rep.precio_venta : rep.precio,
                descuento: rep.descuento != null ? rep.descuento : 0,
                origen_repuesto: rep.origen_repuesto || 'STOCK_BODEGA',
                pieza_desarme_id: rep.pieza_desarme_id || '',
                costo_linea: rep.costo_linea != null ? rep.costo_linea : 0
            });
        });

        if (window.DESARME_PREFILL && rows.length > 0) {
            try {
                sessionStorage.setItem('eg_desarme_rows_backup', JSON.stringify({
                    rows: rows,
                    savedAt: Date.now()
                }));
            } catch (e) {}
        }
    }

    function hydrateServicios(rows) {
        rows.forEach(function(serv) {
            if (!EG.servicios || typeof EG.servicios.addServicioRow !== 'function') {
                return;
            }

            var row = EG.servicios.addServicioRow(serv.rowId || null);
            if (!row || !row.__applyServData) {
                return;
            }

            row.__applyServData({
                servicio_id: serv.servicio_id || serv.id || '',
                nombre: serv.nombre || '',
                cantidad: serv.cantidad || 1,
                precio: serv.precio != null ? serv.precio : (serv.precio_base != null ? serv.precio_base : 0)
            });
        });
    }

    function hydrateOtros(rows) {
        rows.forEach(function(otro) {
            if (!EG.servicios || typeof EG.servicios.addOtroRow !== 'function') {
                return;
            }

            var row = EG.servicios.addOtroRow(otro.rowId || null);
            if (!row || !row.__applyOtroData) {
                return;
            }

            row.__applyOtroData({
                servicio_id: otro.servicio_id || otro.id || '',
                nombre: otro.nombre || '',
                empresa_ext: otro.empresa_ext || otro.empresa_externa || '',
                precio_taller: otro.precio_taller != null ? otro.precio_taller : 0,
                precio: otro.precio != null ? otro.precio : (otro.precio_cliente != null ? otro.precio_cliente : 0)
            });
        });
    }

    function hydrateLineItems() {
        var form = getForm();
        if (!form || form.dataset.egLineItemsHydrated) {
            return;
        }

        if (!window.DESARME_PREFILL && ((window.FORCE_NEW_DOCUMENT) || (EG.state && EG.state.isCleanMode && EG.state.isCleanMode()))) {
            clearRows();
            form.dataset.egLineItemsHydrated = '1';
            return;
        }

        var lineItems = getLineItems();
        var hasLines = lineItems.repuestos.length || lineItems.servicios.length || lineItems.otros.length;
        if (!hasLines) {
            form.dataset.egLineItemsHydrated = '1';
            return;
        }

        clearRows();
        hydrateRepuestos(lineItems.repuestos);
        hydrateServicios(lineItems.servicios);
        hydrateOtros(lineItems.otros);

        form.dataset.egLineItemsHydrated = '1';

        if (typeof window.serializeRows === 'function') {
            window.serializeRows();
        }
        if (typeof window.recalcTotales === 'function') {
            window.recalcTotales();
        }
    }

    function init() {
        if (!window.DESARME_PREFILL) {
            hydrateLineItems();
        }
    }

    EG.lineItemsBootstrap = {
        clearRows: clearRows,
        hydrateLineItems: hydrateLineItems,
        hydrateRepuestos: hydrateRepuestos,
        hydrateServicios: hydrateServicios,
        hydrateOtros: hydrateOtros,
        init: init
    };
})();
