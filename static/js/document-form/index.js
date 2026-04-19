/**
 * index.js - Punto de entrada del formulario de documentos
 */

(function() {
    'use strict';

    var APP_VERSION = '2.3.7';

    window.EG = window.EG || {};
    window.EG.APP_VERSION = APP_VERSION;

    try {
        if (window.localStorage && window.localStorage.getItem('app_version') !== APP_VERSION) {
            console.log('Nueva version detectada, limpiando cache');

            window.localStorage.clear();
            if (window.sessionStorage) {
                window.sessionStorage.clear();
            }

            window.localStorage.setItem('app_version', APP_VERSION);
        }
    } catch (err) {
        console.warn('No se pudo validar la version del frontend:', err);
    }

    function isNewDocumentPage() {
        var form = document.getElementById('document-form');
        var path = (window.location.pathname || '').toLowerCase();
        var formMode = form && form.dataset ? String(form.dataset.mode || '').toLowerCase() : '';

        return !!window.FORCE_NEW_DOCUMENT
            || formMode === 'create'
            || path.indexOf('/documentos/form') !== -1
            || path.indexOf('/documentos/nuevo') !== -1;
    }

    function clearDraftStorage(storage) {
        if (!storage) {
            return;
        }

        var keysToRemove = [];
        try {
            for (var i = 0; i < storage.length; i += 1) {
                var key = storage.key(i);
                if (!key) {
                    continue;
                }

                var normalizedKey = String(key).toLowerCase();
                if (
                    normalizedKey.indexOf('document') !== -1
                    || normalizedKey.indexOf('draft') !== -1
                    || normalizedKey.indexOf('doc_draft') !== -1
                    || normalizedKey.indexOf('eg.documentform') !== -1
                ) {
                    keysToRemove.push(key);
                }
            }
        } catch (err) {
            console.warn('No se pudo enumerar storage', err);
        }

        keysToRemove.forEach(function(key) {
            try {
                storage.removeItem(key);
            } catch (err) {
                console.warn('No se pudo limpiar storage para ' + key, err);
            }
        });
    }

    function clearDynamicVisualState() {
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
    }

    // Force clean state on new document screens to avoid stale draft data.
    (function forceCleanDocument() {
        try {
            if (!isNewDocumentPage()) {
                return;
            }

            console.log('Limpieza forzada de estado del documento');

            clearDraftStorage(window.localStorage);
            clearDraftStorage(window.sessionStorage);

            if (window.EG.utils && typeof window.EG.utils.clearActiveRowContext === 'function') {
                window.EG.utils.clearActiveRowContext();
            }

            ['id_repuestos_json', 'id_servicios_json', 'id_otros_json'].forEach(function(id) {
                var input = document.getElementById(id);
                if (input) {
                    input.value = '[]';
                }
            });

            ['id_cliente', 'id_vehiculo', 'cliente-busqueda', 'id_observaciones', 'id_kilometraje_ingreso'].forEach(function(id) {
                var field = document.getElementById(id);
                if (!field) {
                    return;
                }

                if (field.tagName === 'SELECT') {
                    field.value = '';
                    field.dispatchEvent(new Event('change', { bubbles: true }));
                    return;
                }

                field.value = '';
            });

            if (window.EG.state && typeof window.EG.state.reset === 'function') {
                window.EG.state.reset();
            }

            clearDynamicVisualState();
            window.setTimeout(clearDynamicVisualState, 50);
        } catch (err) {
            console.warn('Error limpiando estado del documento:', err);
        }
    })();

    var MODULE_LOAD_ORDER = [
        'config',
        'utils',
        'modules/state',
        'i18n',
        'cliente',
        'vehiculo',
        'repuestos',
        'servicios',
        'totales',
        'modules/line_items_bootstrap',
        'borrador',
        'ui'
    ];

    function loadModule(moduleName) {
        return new Promise(function(resolve, reject) {
            var script = document.createElement('script');
            script.src = '/static/js/document-form/' + moduleName + '.js?v=' + encodeURIComponent(APP_VERSION);
            script.onload = resolve;
            script.onerror = function(err) {
                reject(new Error('Failed to load ' + moduleName + ': ' + err));
            };
            document.head.appendChild(script);
        });
    }

    async function initAllModules() {
        var form = document.getElementById('document-form');
        if (!form) {
            return;
        }

        for (var i = 0; i < MODULE_LOAD_ORDER.length; i += 1) {
            try {
                await loadModule(MODULE_LOAD_ORDER[i]);
            } catch (err) {
                console.error(err);
            }
        }

        [
            'config',
            'utils',
            'state',
            'i18n',
            'cliente',
            'vehiculo',
            'repuestos',
            'servicios',
            'totales',
            'lineItemsBootstrap',
            'borrador',
            'ui'
        ].forEach(function(moduleName) {
            var module = window.EG[moduleName];
            if (module && typeof module.init === 'function') {
                module.init();
            }
        });

        setupAddButtons();
        setupFormSubmit();
        await restoreDraftOnLoad();
        await waitForReturnContextModules();
        await processReturnContext();

        if (window.serializeRows) {
            window.serializeRows();
        }
        if (window.recalcTotales) {
            window.recalcTotales();
        }
    }

    function setupAddButtons() {
        var btnAddRepuesto = document.getElementById('add-repuesto');
        if (btnAddRepuesto && !btnAddRepuesto.dataset.egBound) {
            btnAddRepuesto.dataset.egBound = '1';
            btnAddRepuesto.addEventListener('click', function() {
                if (window.EG.repuestos && window.EG.repuestos.addRepuestoRow) {
                    window.EG.repuestos.addRepuestoRow();
                }
            });
        }

        var btnAddServicio = document.getElementById('add-servicio');
        if (btnAddServicio && !btnAddServicio.dataset.egBound) {
            btnAddServicio.dataset.egBound = '1';
            btnAddServicio.addEventListener('click', function() {
                if (window.EG.servicios && window.EG.servicios.addServicioRow) {
                    window.EG.servicios.addServicioRow();
                }
            });
        }

        var btnAddOtro = document.getElementById('add-otro');
        if (btnAddOtro && !btnAddOtro.dataset.egBound) {
            btnAddOtro.dataset.egBound = '1';
            btnAddOtro.addEventListener('click', function() {
                if (window.EG.servicios && window.EG.servicios.addOtroRow) {
                    window.EG.servicios.addOtroRow();
                }
            });
        }

        var btnAddUsed = document.getElementById('add-used-parts');
        if (btnAddUsed && !btnAddUsed.dataset.egBound) {
            btnAddUsed.dataset.egBound = '1';
            btnAddUsed.addEventListener('click', function() {
                if (window.EG.repuestos && window.EG.repuestos.openUsedPartsModal) {
                    window.EG.repuestos.openUsedPartsModal();
                }
            });
        }
    }

    function setupFormSubmit() {
        var form = document.getElementById('document-form');
        if (!form) {
            return;
        }

        form.addEventListener('submit', function() {
            if (window.serializeRows) {
                window.serializeRows();
            }
        });
    }

    async function restoreDraftOnLoad() {
        if (window.EG.state && window.EG.state.isCleanMode && window.EG.state.isCleanMode()) {
            if (window.EG.lineItemsBootstrap && window.EG.lineItemsBootstrap.clearRows) {
                window.EG.lineItemsBootstrap.clearRows();
            }
            return;
        }

        await new Promise(function(resolve) {
            if (document.readyState === 'complete') {
                setTimeout(resolve, 100);
                return;
            }
            window.addEventListener('load', function() {
                setTimeout(resolve, 100);
            }, { once: true });
        });

        if (window.restoreDocumentDraftAfterHydrate) {
            try {
                await window.restoreDocumentDraftAfterHydrate({
                    hasServerLines: !!(
                        window.EG.state
                        && window.EG.state.hasServerLineItems
                        && window.EG.state.hasServerLineItems()
                    )
                });
            } catch (err) {
                console.error('Error restaurando borrador:', err);
            }
        }
    }

    async function waitForModule(name, timeoutMs) {
        var timeout = typeof timeoutMs === 'number' ? timeoutMs : 500;
        var start = Date.now();

        while (!window.EG[name]) {
            if (Date.now() - start > timeout) {
                return false;
            }
            await new Promise(function(resolve) {
                window.setTimeout(resolve, 10);
            });
        }

        return true;
    }

    async function waitForReturnContextModules() {
        await waitForModule('cliente');
        await waitForModule('vehiculo');
        await waitForModule('repuestos');
        await waitForModule('servicios');
    }

    async function processReturnContext() {
        if (!window.EG.utils || !window.EG.utils.getReturnContextParams) {
            return;
        }

        var context = window.EG.utils.getReturnContextParams();
        if (!context.hasAny) {
            return;
        }

        try {
            if ((context.created_cliente_id || context.cliente_id) && window.EG.cliente && window.EG.cliente.handleCreatedClienteFromReturn) {
                await window.EG.cliente.handleCreatedClienteFromReturn(context);
            }

            if ((context.created_vehiculo_id || context.vehiculo_id) && window.EG.vehiculo && window.EG.vehiculo.handleCreatedVehiculoFromReturn) {
                await window.EG.vehiculo.handleCreatedVehiculoFromReturn(context);
            }

            if (context.created_repuesto_id && window.EG.repuestos && window.EG.repuestos.handleCreatedRepuestoFromReturn) {
                window.EG.repuestos.handleCreatedRepuestoFromReturn(context);
            }

            if (context.created_servicio_id && window.EG.servicios && window.EG.servicios.handleCreatedServicioFromReturn) {
                window.EG.servicios.handleCreatedServicioFromReturn(context);
            }
        } finally {
            if (window.EG.utils.cleanReturnContextParamsFromUrl) {
                window.EG.utils.cleanReturnContextParamsFromUrl();
            }
        }
    }

    window.egEncodeDocumentFormNext = function() {
        return encodeURIComponent(window.location.pathname + (window.location.search || ''));
    };

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initAllModules);
    } else {
        initAllModules();
    }

    window.EG.initAllModules = initAllModules;
    window.EG.loadModule = loadModule;
})();
