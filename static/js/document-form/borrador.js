/**
 * borrador.js - Módulo de auto-guardado y restauración de borradores
 * 
 * Extraído del código embebido en document_form.html
 */

(function() {
    'use strict';

    const EG = window.EG = window.EG || {};

    var DOC_DRAFT_VERSION = 1;
    var DOC_DRAFT_TTL_MS = 7 * 24 * 60 * 60 * 1000; // 7 días
    var __docDraftSaveTimer = null;

    /**
     * Genera clave única para el borrador
     */
    function getDocumentFormDraftKey() {
        var form = document.getElementById('document-form');
        if (!form) return null;
        var mode = form.dataset.mode || 'create';
        var docId = (form.dataset.documentId || '').trim() || 'new';
        var path = (window.location.pathname || '').replace(/\/$/, '') || '/';
        return 'doc_draft_v' + DOC_DRAFT_VERSION + ':' + path + ':' + mode + ':' + docId;
    }

    /**
     * Muestra indicador de guardado
     */
    function showDraftSavedIndicator() {
        var el = document.getElementById('draft-indicator');
        if (!el) return;
        el.classList.remove('hidden');
        clearTimeout(showDraftSavedIndicator._t);
        showDraftSavedIndicator._t = setTimeout(function() {
            el.classList.add('hidden');
        }, 1600);
    }

    /**
     * Recolecta datos del formulario para el borrador
     */
    function collectDocumentDraftPayload() {
        var form = document.getElementById('document-form');
        if (!form || window.__DOC_DRAFT_RESTORING__) return null;

        var rep = Array.from(document.querySelectorAll('#repuestos-container .dynamic-element')).map(function(row) {
            return {
                rowId: row.dataset.rowId || '',
                id: (row.querySelector('.rep-id') && row.querySelector('.rep-id').value || '').trim(),
                codigo: (row.querySelector('.rep-codigo') && row.querySelector('.rep-codigo').value || '').trim(),
                nombre: (row.querySelector('.rep-nombre') && row.querySelector('.rep-nombre').value || '').trim(),
                nombre_input: (row.querySelector('.rep-search') && row.querySelector('.rep-search').value || '').trim(),
                cantidad: Number(row.querySelector('.rep-cantidad') && row.querySelector('.rep-cantidad').value || 0) || 1,
                precio_venta: EG.utils.parseNumericInput(row.querySelector('.rep-precio-venta') && row.querySelector('.rep-precio-venta').value || 0),
                descuento: Number(row.querySelector('.rep-descuento') && row.querySelector('.rep-descuento').value || 0) || 0,
                origen_repuesto: (row.querySelector('.rep-origen') && row.querySelector('.rep-origen').value || 'STOCK_BODEGA').trim(),
                pieza_desarme_id: (row.querySelector('.rep-pieza-desarme-id') && row.querySelector('.rep-pieza-desarme-id').value || '').trim(),
                costo_linea: EG.utils.parseNumericInput(row.querySelector('.rep-costo-linea') && row.querySelector('.rep-costo-linea').value || 0)
            };
        });

        var serv = Array.from(document.querySelectorAll('#servicios-container .dynamic-element')).map(function(row) {
            return {
                servicio_id: (row.querySelector('.srv-id') && row.querySelector('.srv-id').value || '').trim(),
                nombre: (row.querySelector('.srv-input') && row.querySelector('.srv-input').value || '').trim(),
                cantidad: Number(row.querySelector('.serv-cantidad') && row.querySelector('.serv-cantidad').value || 0) || 1,
                precio: EG.utils.parseNumericInput(row.querySelector('.serv-precio') && row.querySelector('.serv-precio').value || 0),
                descuento: EG.utils.parseNumericInput(row.querySelector('.serv-descuento') && row.querySelector('.serv-descuento').value || 0)
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

        var kmEl = form.querySelector('[name="kilometraje_ingreso"]');
        var cliEmail = document.getElementById('cliente-email');
        var cliFono = document.getElementById('cliente-telefono');

        var draft = {
            v: DOC_DRAFT_VERSION,
            savedAt: Date.now(),
            path: (window.location.pathname || '').replace(/\/$/, '') || '/',
            mode: form.dataset.mode || 'create',
            documentId: (form.dataset.documentId || '').trim() || null,
            tipo: (document.getElementById('id_tipo') && document.getElementById('id_tipo').value) || '',
            fecha_emision: (document.getElementById('id_fecha_emision') && document.getElementById('id_fecha_emision').value) || '',
            doc_mode: (document.getElementById('doc_mode') && document.getElementById('doc_mode').value) || '',
            payment_status: (document.getElementById('id_payment_status') && document.getElementById('id_payment_status').value) || '',
            observaciones: (document.getElementById('id_observaciones') && document.getElementById('id_observaciones').value) || '',
            kilometraje_ingreso: kmEl ? (kmEl.value || '') : '',
            apply_all_taxes: (function() {
                var v = document.getElementById('id_apply_vat');
                return v ? !!v.checked : null;
            })(),
            tax_line_checks: (window.EG.cfg && window.EG.cfg.taxLines || []).map(function(tl) {
                return {
                    id: String(tl.id),
                    checked: !!document.getElementById('include_' + tl.id) && document.getElementById('include_' + tl.id).checked
                };
            }),
            cliente_id: (document.getElementById('id_cliente') && document.getElementById('id_cliente').value) || '',
            cliente_nombre: (document.getElementById('cliente-busqueda') && document.getElementById('cliente-busqueda').value) || '',
            cliente_email: (cliEmail && cliEmail.textContent || '').replace(/^📧\s*/, '').trim().replace(/^—$/, ''),
            cliente_telefono: (cliFono && cliFono.textContent || '').replace(/^📞\s*/, '').trim().replace(/^—$/, ''),
            vehiculo_id: (document.getElementById('id_vehiculo') && document.getElementById('id_vehiculo').value) || '',
            repuestos: rep,
            servicios: serv,
            otros: otros
        };
        return draft;
    }

    /**
     * Guarda borrador inmediatamente
     */
    function saveDocumentDraftNow() {
        var key = getDocumentFormDraftKey();
        if (!key) return;
        try {
            var payload = collectDocumentDraftPayload();
            if (!payload) return;
            localStorage.setItem(key, JSON.stringify(payload));
            showDraftSavedIndicator();
        } catch (e) {
            console.warn('doc draft save failed', e);
        }
    }

    /**
     * Programa guardado de borrador (debounced)
     */
    function scheduleDocumentDraftSave() {
        if (window.__DOC_DRAFT_RESTORING__) return;
        clearTimeout(__docDraftSaveTimer);
        __docDraftSaveTimer = setTimeout(saveDocumentDraftNow, 480);
    }

    /**
     * Carga borrador desde localStorage
     */
    function loadDocumentDraftParsed() {
        var key = getDocumentFormDraftKey();
        if (!key) return null;
        try {
            var raw = localStorage.getItem(key);
            if (!raw) return null;
            var data = JSON.parse(raw);
            if (!data || data.v !== DOC_DRAFT_VERSION || !data.savedAt) return null;
            if (Date.now() - Number(data.savedAt) > DOC_DRAFT_TTL_MS) {
                localStorage.removeItem(key);
                return null;
            }
            if (data.path && data.path !== (window.location.pathname || '').replace(/\/$/, '')) return null;
            var form = document.getElementById('document-form');
            if (form && data.mode && data.mode !== (form.dataset.mode || 'create')) return null;
            var did = (form && form.dataset.documentId || '').trim() || null;
            if (did && data.documentId && String(data.documentId) !== String(did)) return null;
            if (did && !data.documentId) return null;
            if (!did && data.documentId) return null;
            return data;
        } catch (e) {
            console.warn('doc draft load failed', e);
            return null;
        }
    }

    /**
     * Limpia las filas dinámicas
     */
    function clearDynamicPosRows() {
        document.querySelectorAll('#repuestos-container .dynamic-element').forEach(function(el) { el.remove(); });
        document.querySelectorAll('#servicios-container .dynamic-element').forEach(function(el) { el.remove(); });
        document.querySelectorAll('#otros-container .dynamic-element').forEach(function(el) { el.remove(); });
        var hint = document.getElementById('servicios-empty-hint');
        if (hint) hint.classList.remove('hidden');
    }

    /**
     * Limpia borrador del storage
     */
    function clearDocumentFormDraftStorage() {
        var key = getDocumentFormDraftKey();
        if (key) {
            try {
                localStorage.removeItem(key);
            } catch (e) { /* ignore */ }
        }
    }

    /**
     * Restaura borrador después de hidratar
     */
    async function restoreDocumentDraftAfterHydrate(opts) {
        var hasServerLines = !!(opts && opts.hasServerLines);
        var draft = loadDocumentDraftParsed();
        if (!draft) return;

        window.__DOC_DRAFT_RESTORING__ = true;
        try {
            var draftHasLines = ((draft.repuestos && draft.repuestos.length) || 0) > 0 ||
                ((draft.servicios && draft.servicios.length) || 0) > 0 ||
                ((draft.otros && draft.otros.length) || 0) > 0;

            // Aplicar campos básicos
            var tipoEl = document.getElementById('id_tipo');
            if (tipoEl && draft.tipo) {
                tipoEl.value = draft.tipo;
                tipoEl.dispatchEvent(new Event('change', { bubbles: true }));
            }
            var fechaEl = document.getElementById('id_fecha_emision');
            if (fechaEl && draft.fecha_emision) fechaEl.value = draft.fecha_emision;
            var modeEl = document.getElementById('doc_mode');
            if (modeEl && draft.doc_mode) {
                modeEl.value = draft.doc_mode;
                modeEl.dispatchEvent(new Event('change', { bubbles: true }));
            }
            var payEl = document.getElementById('id_payment_status');
            if (payEl && draft.payment_status) {
                payEl.value = draft.payment_status;
                payEl.dispatchEvent(new Event('change', { bubbles: true }));
            }
            var applyVat = document.getElementById('id_apply_vat');
            if (applyVat && draft.apply_all_taxes !== undefined && draft.apply_all_taxes !== null) {
                applyVat.checked = !!draft.apply_all_taxes;
            }
            (draft.tax_line_checks || []).forEach(function(tc) {
                var tel = document.getElementById('include_' + tc.id);
                if (tel) tel.checked = !!tc.checked;
            });
            var obs = document.getElementById('id_observaciones');
            if (obs && typeof draft.observaciones === 'string') obs.value = draft.observaciones;

            // Restaurar filas si corresponde
            if (draftHasLines || !hasServerLines) {
                clearDynamicPosRows();
                (draft.repuestos || []).forEach(function(rep) {
                    if (typeof window.addRepuestoRow === 'function') {
                        var row = window.addRepuestoRow(rep.rowId || null);
                        if (row && row.__applyRepData) {
                            row.__applyRepData({
                                id: rep.id || '',
                                nombre: rep.nombre || rep.nombre_input || '',
                                codigo: rep.codigo || '',
                                cantidad: rep.cantidad || 1,
                                precio_venta: rep.precio_venta != null ? rep.precio_venta : 0,
                                descuento: rep.descuento != null ? rep.descuento : 0,
                                origen_repuesto: rep.origen_repuesto || 'STOCK_BODEGA',
                                pieza_desarme_id: rep.pieza_desarme_id || '',
                                costo_linea: rep.costo_linea != null ? rep.costo_linea : 0
                            });
                        }
                    }
                });
                (draft.servicios || []).forEach(function(serv) {
                    if (window.EG && window.EG.servicios && typeof window.EG.servicios.addServicioRow === 'function') {
                        var row = window.EG.servicios.addServicioRow();
                        if (row && row.__applyServData) {
                            row.__applyServData({
                                servicio_id: serv.servicio_id || '',
                                nombre: serv.nombre || '',
                                cantidad: serv.cantidad || 1,
                                precio: serv.precio != null ? serv.precio : 0,
                                descuento: serv.descuento != null ? serv.descuento : 0
                            });
                        }
                    }
                });
                (draft.otros || []).forEach(function(otro) {
                    if (window.EG && window.EG.servicios && typeof window.EG.servicios.addOtroServicioRow === 'function') {
                        var row = window.EG.servicios.addOtroServicioRow();
                        if (row && row.__applyOtroData) {
                            row.__applyOtroData({
                                servicio_id: otro.servicio_id || '',
                                nombre: otro.nombre || '',
                                empresa_ext: otro.empresa_ext || '',
                                precio_taller: otro.precio_taller != null ? otro.precio_taller : 0,
                                precio: otro.precio != null ? otro.precio : 0
                            });
                        }
                    }
                });
            }

            // Restaurar cliente si aplica
            var urlParams = new URLSearchParams(window.location.search || '');
            var skipDraftCliente = !!(urlParams.get('cliente_id') || window.__PRESELECT_CLIENTE_ID__);
            if (draft.cliente_id && !skipDraftCliente) {
                if (typeof EG.cliente && EG.cliente.seleccionarCliente) {
                    await EG.cliente.seleccionarCliente({
                        id: draft.cliente_id,
                        nombre: draft.cliente_nombre || ('Cliente #' + draft.cliente_id),
                        email: draft.cliente_email || '',
                        telefono: draft.cliente_telefono || ''
                    });
                }
            }
        } finally {
            window.__DOC_DRAFT_RESTORING__ = false;
            if (typeof window.serializeRows === 'function') window.serializeRows();
        }
    }

    /**
     * Inicializar eventos de borrador
     */
    function init() {
        var form = document.getElementById('document-form');
        if (form) {
            form.addEventListener('input', scheduleDocumentDraftSave);
            form.addEventListener('change', scheduleDocumentDraftSave);
            form.addEventListener('submit', clearDocumentFormDraftStorage);
        }
        console.log('Borrador module initialized');
    }

    // Exports
    EG.borrador = {
        getDocumentFormDraftKey: getDocumentFormDraftKey,
        saveDocumentDraftNow: saveDocumentDraftNow,
        scheduleDocumentDraftSave: scheduleDocumentDraftSave,
        loadDocumentDraftParsed: loadDocumentDraftParsed,
        clearDocumentFormDraftStorage: clearDocumentFormDraftStorage,
        restoreDocumentDraftAfterHydrate: restoreDocumentDraftAfterHydrate,
        init: init
    };
    window.scheduleDocumentDraftSave = scheduleDocumentDraftSave;
    window.restoreDocumentDraftAfterHydrate = restoreDocumentDraftAfterHydrate;

})();
