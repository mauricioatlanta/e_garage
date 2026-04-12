/**
 * index.js - Punto de entrada del formulario de documentos
 */

(function() {
    'use strict';

    window.EG = window.EG || {};

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
            script.src = '/static/js/document-form/' + moduleName + '.js';
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
