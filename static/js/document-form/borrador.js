/**
 * borrador.js - Modulo de auto-guardado y restauracion de borradores
 */

(function() {
    'use strict';

    var EG = window.EG = window.EG || {};

    var DOC_DRAFT_VERSION = 2;
    var DOC_DRAFT_TTL_MS = 7 * 24 * 60 * 60 * 1000;
    var SHOULD_LOAD_DRAFT = true;
    var docDraftSaveTimer = null;
    var docDraftDirty = false;

    function getDocumentFormDraftKey() {
        var form = document.getElementById('document-form');
        if (!form) return null;
        var mode = form.dataset.mode || 'create';
        var docId = (form.dataset.documentId || '').trim() || 'new';
        var path = (window.location.pathname || '').replace(/\/$/, '') || '/';
        return 'doc_draft_v' + DOC_DRAFT_VERSION + ':' + path + ':' + mode + ':' + docId;
    }

    function showDraftIndicator(message) {
        var el = document.getElementById('draft-indicator');
        if (!el) return;
        el.textContent = message || 'Borrador guardado';
        el.classList.remove('hidden');
        clearTimeout(showDraftIndicator._t);
        showDraftIndicator._t = setTimeout(function() {
            el.classList.add('hidden');
        }, 2200);
    }

    function showDraftSavedIndicator() {
        showDraftIndicator('Borrador guardado');
    }

    function showDraftRestoreModal(draft) {
        return new Promise(function(resolve) {
            var existing = document.getElementById('eg-draft-restore-modal');
            if (existing) existing.remove();

            var savedAt = draft && draft.savedAt ? new Date(Number(draft.savedAt)) : null;
            var timeStr = savedAt ? savedAt.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '';
            var dateStr = savedAt ? savedAt.toLocaleDateString([], { day: '2-digit', month: '2-digit', year: 'numeric' }) : '';

            var overlay = document.createElement('div');
            overlay.id = 'eg-draft-restore-modal';
            overlay.style.cssText = [
                'position:fixed;top:0;left:0;right:0;bottom:0',
                'background:rgba(0,0,0,0.72)',
                'display:flex;align-items:center;justify-content:center',
                'z-index:9999'
            ].join(';');

            overlay.innerHTML = '<div style="background:#0f141a;border:1px solid rgba(0,255,255,0.25);border-radius:12px;padding:28px 32px;max-width:400px;width:90%;box-shadow:0 8px 32px rgba(0,0,0,0.65);color:#fff;">' +
                '<h3 style="margin:0 0 8px;font-size:15px;font-weight:700;color:#00ffff;text-transform:uppercase;letter-spacing:0.06em;">Draft Found</h3>' +
                '<p style="margin:0 0 6px;color:#b0b8c1;font-size:14px;">A previous document draft was found.</p>' +
                (timeStr ? '<p style="margin:0 0 22px;color:#606d7a;font-size:12px;">Saved ' + dateStr + ' at ' + timeStr + '</p>' : '<div style="height:22px"></div>') +
                '<div style="display:flex;gap:10px;justify-content:flex-end;">' +
                '<button id="eg-draft-discard-btn" style="background:rgba(255,255,255,0.06);border:1px solid rgba(255,255,255,0.14);color:#9aacba;border-radius:8px;padding:9px 18px;cursor:pointer;font-size:13px;font-weight:600;">Discard Draft</button>' +
                '<button id="eg-draft-restore-btn" style="background:rgba(0,255,255,0.1);border:1px solid rgba(0,255,255,0.38);color:#00ffff;border-radius:8px;padding:9px 18px;cursor:pointer;font-size:13px;font-weight:700;">Restore Draft</button>' +
                '</div></div>';

            document.body.appendChild(overlay);

            overlay.querySelector('#eg-draft-restore-btn').addEventListener('click', function() {
                overlay.remove();
                resolve(true);
            });
            overlay.querySelector('#eg-draft-discard-btn').addEventListener('click', function() {
                overlay.remove();
                resolve(false);
            });
        });
    }

    function collectRows(selector, mapper) {
        return Array.from(document.querySelectorAll(selector)).map(mapper);
    }

    function collectDocumentDraftPayload() {
        var form = document.getElementById('document-form');
        if (!form || window.__DOC_DRAFT_RESTORING__) return null;

        var repuestos = collectRows('#repuestos-container .dynamic-element', function(row) {
            var stockRaw = row.querySelector('.rep-stock-disponible') && row.querySelector('.rep-stock-disponible').value;
            var stockMinRaw = row.querySelector('.rep-stock-minimo') && row.querySelector('.rep-stock-minimo').value;
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
                costo_linea: EG.utils.parseNumericInput(row.querySelector('.rep-costo-linea') && row.querySelector('.rep-costo-linea').value || 0),
                stock: stockRaw !== '' && stockRaw != null ? Number(stockRaw) : null,
                stock_minimo: stockMinRaw !== '' && stockMinRaw != null ? Number(stockMinRaw) : null
            };
        });

        var servicios = collectRows('#servicios-container .dynamic-element', function(row) {
            return {
                rowId: row.dataset.rowId || '',
                servicio_id: (row.querySelector('.srv-id') && row.querySelector('.srv-id').value || '').trim(),
                nombre: (row.querySelector('.srv-input') && row.querySelector('.srv-input').value || '').trim(),
                cantidad: Math.max(1, parseInt(row.querySelector('.serv-cantidad') && row.querySelector('.serv-cantidad').value || 1, 10) || 1),
                precio: EG.utils.parseNumericInput(row.querySelector('.serv-precio') && row.querySelector('.serv-precio').value || 0)
            };
        });

        var otros = collectRows('#otros-container .dynamic-element', function(row) {
            var empresa = (row.querySelector('.otr-empresa') && row.querySelector('.otr-empresa').value || '').trim();
            var precioTaller = EG.utils.parseNumericInput(row.querySelector('.otr-precio-taller') && row.querySelector('.otr-precio-taller').value || 0);
            var precioCliente = EG.utils.parseNumericInput(row.querySelector('.otr-precio') && row.querySelector('.otr-precio').value || 0);
            return {
                rowId: row.dataset.rowId || '',
                servicio_id: (row.querySelector('.otr-servicio-id') && row.querySelector('.otr-servicio-id').value || '').trim(),
                nombre: (row.querySelector('.otr-search') && row.querySelector('.otr-search').value || '').trim(),
                empresa_ext: empresa,
                empresa_externa: empresa,
                precio_taller: precioTaller,
                costo_interno: precioTaller,
                precio: precioCliente,
                precio_cliente: precioCliente
            };
        });

        var kmEl = form.querySelector('[name="kilometraje_ingreso"]');
        var cliEmail = document.getElementById('cliente-email');
        var cliFono = document.getElementById('cliente-telefono');

        return {
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
            cliente_email: (cliEmail && cliEmail.textContent || '').replace(/^Email:\s*/, '').trim().replace(/^[-—]$/, ''),
            cliente_telefono: (cliFono && cliFono.textContent || '').replace(/^Tel:\s*/, '').trim().replace(/^[-—]$/, ''),
            vehiculo_id: (document.getElementById('id_vehiculo') && document.getElementById('id_vehiculo').value) || '',
            repuestos: repuestos,
            servicios: servicios,
            otros: otros
        };
    }

    function saveDocumentDraftNow() {
        // Only save if the user has interacted — prevents overwriting a prior draft
        // with a blank form on the first 10-second tick after page load.
        if (!docDraftDirty) return;
        var key = getDocumentFormDraftKey();
        if (!key) return;
        try {
            var payload = collectDocumentDraftPayload();
            if (!payload) return;
            showDraftIndicator('Guardando...');
            localStorage.setItem(key, JSON.stringify(payload));
            showDraftSavedIndicator();
        } catch (err) {
            console.warn('doc draft save failed', err);
        }
    }

    function scheduleDocumentDraftSave() {
        if (window.__DOC_DRAFT_RESTORING__) return;
        clearTimeout(docDraftSaveTimer);
        docDraftSaveTimer = setTimeout(saveDocumentDraftNow, 480);
    }

    function loadDocumentDraftParsed() {
        if (!SHOULD_LOAD_DRAFT) {
            return null;
        }

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
        } catch (err) {
            console.warn('doc draft load failed', err);
            return null;
        }
    }

    function clearDynamicPosRows() {
        document.querySelectorAll('#repuestos-container .dynamic-element').forEach(function(el) { el.remove(); });
        document.querySelectorAll('#servicios-container .dynamic-element').forEach(function(el) { el.remove(); });
        document.querySelectorAll('#otros-container .dynamic-element').forEach(function(el) { el.remove(); });
        ['servicios-empty-hint', 'otros-empty-hint'].forEach(function(id) {
            var hint = document.getElementById(id);
            if (hint) hint.classList.remove('hidden');
        });
    }

    function clearDocumentFormDraftStorage() {
        var key = getDocumentFormDraftKey();
        if (!key) return;
        try {
            localStorage.removeItem(key);
        } catch (err) {
            console.warn('doc draft clear failed', err);
        }
    }

    function hasReturnContext(urlParams) {
        if (window.EG && window.EG.utils && window.EG.utils.getReturnContextParams) {
            return !!window.EG.utils.getReturnContextParams().hasAny;
        }
        var keys = ['cliente_id', 'vehiculo_id', 'created_cliente_id', 'created_vehiculo_id', 'created_repuesto_id', 'created_servicio_id'];
        return keys.some(function(key) { return urlParams.has(key); });
    }

    async function restoreDocumentDraftAfterHydrate(opts) {
        if (!SHOULD_LOAD_DRAFT) {
            return;
        }

        var hasServerLines = !!(opts && opts.hasServerLines);
        var draft = loadDocumentDraftParsed();
        if (!draft) return;

        var userWantsRestore = await showDraftRestoreModal(draft);
        if (!userWantsRestore) {
            clearDocumentFormDraftStorage();
            return;
        }
        showDraftIndicator('Restaurando borrador...');
        window.__DOC_DRAFT_RESTORING__ = true;
        try {
            var draftHasLines = ((draft.repuestos && draft.repuestos.length) || 0) > 0
                || ((draft.servicios && draft.servicios.length) || 0) > 0
                || ((draft.otros && draft.otros.length) || 0) > 0;

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
            var kmEl = document.getElementById('id_kilometraje_ingreso');
            if (kmEl && typeof draft.kilometraje_ingreso === 'string') kmEl.value = draft.kilometraje_ingreso;

            if (draftHasLines || !hasServerLines) {
                clearDynamicPosRows();

                (draft.repuestos || []).forEach(function(rep) {
                    if (typeof window.addRepuestoRow !== 'function') return;
                    var row = window.addRepuestoRow(rep.rowId || null);
                    if (row && row.__applyRepData) {
                        var repData = {
                            id: rep.id || '',
                            nombre: rep.nombre || rep.nombre_input || '',
                            codigo: rep.codigo || '',
                            cantidad: rep.cantidad || 1,
                            precio_venta: rep.precio_venta != null ? rep.precio_venta : 0,
                            descuento: rep.descuento != null ? rep.descuento : 0,
                            origen_repuesto: rep.origen_repuesto || 'STOCK_BODEGA',
                            pieza_desarme_id: rep.pieza_desarme_id || '',
                            costo_linea: rep.costo_linea != null ? rep.costo_linea : 0
                        };
                        if (rep.stock != null) repData.stock = rep.stock;
                        if (rep.stock_minimo != null) repData.stock_minimo = rep.stock_minimo;
                        row.__applyRepData(repData);
                    }
                });

                (draft.servicios || []).forEach(function(serv) {
                    if (!EG.servicios || !EG.servicios.addServicioRow) return;
                    var row = EG.servicios.addServicioRow(serv.rowId || null);
                    if (row && row.__applyServData) {
                        row.__applyServData({
                            servicio_id: serv.servicio_id || '',
                            nombre: serv.nombre || '',
                            cantidad: serv.cantidad || 1,
                            precio: serv.precio != null ? serv.precio : 0
                        });
                    }
                });

                (draft.otros || []).forEach(function(otro) {
                    if (!EG.servicios || !EG.servicios.addOtroRow) return;
                    var row = EG.servicios.addOtroRow(otro.rowId || null);
                    if (row && row.__applyOtroData) {
                        row.__applyOtroData({
                            servicio_id: otro.servicio_id || '',
                            nombre: otro.nombre || '',
                            empresa_ext: otro.empresa_ext || '',
                            precio_taller: otro.precio_taller != null ? otro.precio_taller : 0,
                            precio: otro.precio != null ? otro.precio : 0
                        });
                    }
                });
            }

            var urlParams = new URLSearchParams(window.location.search || '');
            var skipDraftCliente = hasReturnContext(urlParams) || !!window.__PRESELECT_CLIENTE_ID__;
            if (draft.cliente_id && !skipDraftCliente && EG.cliente && typeof EG.cliente.seleccionarCliente === 'function') {
                await EG.cliente.seleccionarCliente({
                    id: draft.cliente_id,
                    nombre: draft.cliente_nombre || ('Cliente #' + draft.cliente_id),
                    email: draft.cliente_email || '',
                    telefono: draft.cliente_telefono || ''
                }, {
                    vehiculoId: draft.vehiculo_id || null
                });
            }
        } finally {
            window.__DOC_DRAFT_RESTORING__ = false;
            if (typeof window.serializeRows === 'function') window.serializeRows();
            if (typeof window.recalcTotales === 'function') window.recalcTotales();
            showDraftIndicator('Borrador restaurado');
        }
    }

    function init() {
        var form = document.getElementById('document-form');
        if (!form || form.dataset.egDraftBound) {
            return;
        }

        form.dataset.egDraftBound = '1';
        form.addEventListener('input', scheduleDocumentDraftSave);
        form.addEventListener('change', scheduleDocumentDraftSave);
        form.addEventListener('submit', function() {
            clearDocumentFormDraftStorage();
            docDraftDirty = false;
        });

        // Periodic autosave every 10 seconds
        setInterval(saveDocumentDraftNow, 10000);

        // Dirty tracking for beforeunload warning
        form.addEventListener('input', function() { docDraftDirty = true; });
        form.addEventListener('change', function() { docDraftDirty = true; });

        window.addEventListener('beforeunload', function(event) {
            if (!docDraftDirty) return;
            var key = getDocumentFormDraftKey();
            if (!key) return;
            try {
                if (!window.localStorage.getItem(key)) return;
            } catch (e) { return; }
            event.preventDefault();
            event.returnValue = '';
        });
    }

    EG.borrador = {
        getDocumentFormDraftKey: getDocumentFormDraftKey,
        saveDocumentDraftNow: saveDocumentDraftNow,
        scheduleDocumentDraftSave: scheduleDocumentDraftSave,
        loadDocumentDraftParsed: loadDocumentDraftParsed,
        clearDocumentFormDraftStorage: clearDocumentFormDraftStorage,
        restoreDocumentDraftAfterHydrate: restoreDocumentDraftAfterHydrate,
        showDraftRestoreModal: showDraftRestoreModal,
        collectRows: collectDocumentDraftPayload,
        init: init
    };

    window.scheduleDocumentDraftSave = scheduleDocumentDraftSave;
    window.restoreDocumentDraftAfterHydrate = restoreDocumentDraftAfterHydrate;
})();
