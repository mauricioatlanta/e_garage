/**
 * index.js - Punto de entrada del formulario de documentos
 * 
 * Carga todos los módulos en el orden correcto
 */

(function() {
    'use strict';

    // Crear namespace global
    window.EG = window.EG || {};

    // Orden de carga: config primero, luego utils, luego módulos de negocio
    var MODULE_LOAD_ORDER = [
        'config',      // Configuración global y URLs
        'utils',       // Utilidades (fetch, money, etc.)
        'i18n',        // Traducciones
        'cliente',     // Búsqueda de clientes
        'vehiculo',    // Gestión de vehículos
        'repuestos',  // CRUD de repuestos
        'servicios',   // CRUD de servicios y otros servicios
        'totales',     // Cálculo de totales
        'borrador',    // Auto-guardado
        'ui'           // Temas y modos
    ];

    /**
     * Carga un módulo desde su archivo
     */
    function loadModule(moduleName) {
        return new Promise(function(resolve, reject) {
            var script = document.createElement('script');
            script.src = '/static/js/document-form/' + moduleName + '.js';
            script.onload = function() {
                console.log('Loaded module: ' + moduleName);
                resolve();
            };
            script.onerror = function(e) {
                console.error('Failed to load module: ' + moduleName, e);
                reject(new Error('Failed to load ' + moduleName));
            };
            document.head.appendChild(script);
        });
    }

    function clearDocumentStateForNewForm() {
        var form = document.getElementById('document-form');
        if (!form || form.dataset.mode !== 'create') return;

        var params = new URLSearchParams(window.location.search || '');
        var hasReturnContext = !!(params.get('cliente_id') || params.get('vehiculo_id') || params.get('target_row'));
        if (hasReturnContext) return;

        try {
            Object.keys(sessionStorage).forEach(function(key) {
                if (key.indexOf('doc_') === 0 || key.indexOf('document_') === 0 || key.indexOf('eg_document') === 0) {
                    sessionStorage.removeItem(key);
                }
            });
        } catch (err) {
            console.warn('No se pudo limpiar sessionStorage del documento', err);
        }

        window.EG.documentState = {};
    }

    function parseJSONScript(id) {
        var el = document.getElementById(id);
        if (!el) return [];
        try {
            var data = JSON.parse(el.textContent || '[]');
            return Array.isArray(data) ? data : [];
        } catch (err) {
            console.warn('No se pudo parsear ' + id, err);
            return [];
        }
    }

    function getInitialLineData() {
        return {
            repuestos: parseJSONScript('initialRepuestosData'),
            servicios: parseJSONScript('initialServiciosData'),
            otros: parseJSONScript('initialOtrosData')
        };
    }

    function hasAnyLineData(data) {
        return !!(
            data &&
            ((data.repuestos && data.repuestos.length) ||
            (data.servicios && data.servicios.length) ||
            (data.otros && data.otros.length))
        );
    }

    function clearTableRows(selector) {
        document.querySelectorAll(selector).forEach(function(row) { row.remove(); });
    }

    function hydrateInitialRows() {
        var data = getInitialLineData();
        if (!hasAnyLineData(data)) return data;

        clearTableRows('#repuestos-container .dynamic-element');
        clearTableRows('#servicios-container .dynamic-element');
        clearTableRows('#otros-container .dynamic-element');

        (data.repuestos || []).forEach(function(rep) {
            if (!window.EG.repuestos || typeof window.EG.repuestos.addRepuestoRow !== 'function') return;
            var row = window.EG.repuestos.addRepuestoRow(rep.rowId || null);
            if (row && row.__applyRepData) {
                row.__applyRepData({
                    id: rep.repuesto_id || rep.id || '',
                    codigo: rep.codigo || '',
                    nombre: rep.nombre || '',
                    cantidad: rep.cantidad || 1,
                    precio_venta: rep.precio_venta != null ? rep.precio_venta : rep.precio,
                    descuento: rep.descuento != null ? rep.descuento : 0,
                    origen_repuesto: rep.origen_repuesto || 'STOCK_BODEGA',
                    pieza_desarme_id: rep.pieza_desarme_id || '',
                    costo_linea: rep.costo_linea != null ? rep.costo_linea : 0
                });
            }
        });

        (data.servicios || []).forEach(function(serv) {
            if (!window.EG.servicios || typeof window.EG.servicios.addServicioRow !== 'function') return;
            var row = window.EG.servicios.addServicioRow();
            if (row && row.__applyServData) {
                row.__applyServData({
                    id: serv.servicio_id || serv.id || '',
                    nombre: serv.nombre || '',
                    cantidad: serv.cantidad || 1,
                    precio: serv.precio != null ? serv.precio : 0,
                    descuento: serv.descuento != null ? serv.descuento : 0
                });
            }
        });

        (data.otros || []).forEach(function(otro) {
            if (!window.EG.servicios || typeof window.EG.servicios.addOtroServicioRow !== 'function') return;
            var row = window.EG.servicios.addOtroServicioRow();
            if (row && row.__applyOtroData) {
                row.__applyOtroData({
                    id: otro.servicio_id || otro.id || '',
                    nombre: otro.nombre || '',
                    empresa_ext: otro.empresa_ext || otro.empresa || '',
                    precio_taller: otro.precio_taller != null ? otro.precio_taller : 0,
                    precio: otro.precio != null ? otro.precio : 0
                });
            }
        });

        return data;
    }

    /**
     * Inicializa todos los módulos en orden
     */
    async function initAllModules() {
        console.log('Inicializando modulo de formulario de documentos...');

        // Verificar que estamos en la página correcta
        var form = document.getElementById('document-form');
        if (!form) {
            console.log('No se encontro el formulario de documento. Omitiendo inicializacion.');
            return;
        }

        clearDocumentStateForNewForm();

        // Cargar módulos secuencialmente para asegurar dependencias
        for (var i = 0; i < MODULE_LOAD_ORDER.length; i++) {
            var moduleName = MODULE_LOAD_ORDER[i];
            try {
                await loadModule(moduleName);
            } catch (err) {
                console.error('Error cargando modulo ' + moduleName + ':', err);
            }
        }

        // Inicializar módulos que tienen init()
        if (window.EG.config && window.EG.config.init) {
            window.EG.config.init();
        }
        if (window.EG.utils && window.EG.utils.init) {
            window.EG.utils.init();
        }
        if (window.EG.i18n && window.EG.i18n.init) {
            window.EG.i18n.init();
        }
        if (window.EG.cliente && window.EG.cliente.init) {
            window.EG.cliente.init();
        }
        if (window.EG.vehiculo && window.EG.vehiculo.init) {
            window.EG.vehiculo.init();
        }
        if (window.EG.repuestos && window.EG.repuestos.init) {
            window.EG.repuestos.init();
        }
        if (window.EG.servicios && window.EG.servicios.init) {
            window.EG.servicios.init();
        }
        if (window.EG.totales && window.EG.totales.init) {
            window.EG.totales.init();
        }
        if (window.EG.borrador && window.EG.borrador.init) {
            window.EG.borrador.init();
        }
        if (window.EG.ui && window.EG.ui.init) {
            window.EG.ui.init();
        }

        // Botones de agregar
        setupAddButtons();

        // Serialización antes de submit
        setupFormSubmit();

        // Restaurar borrador si existe
        restoreDraftOnLoad();

        console.log('Modulo de formulario de documentos inicializado.');
    }

    /**
     * Configura botones de agregar
     */
    function setupAddButtons() {
        // Agregar repuesto
        var btnAddRepuesto = document.getElementById('add-repuesto');
        if (btnAddRepuesto && !btnAddRepuesto.dataset.egBound) {
            btnAddRepuesto.dataset.egBound = '1';
            btnAddRepuesto.addEventListener('click', function() {
                if (window.EG.repuestos && window.EG.repuestos.addRepuestoRow) {
                    window.EG.repuestos.addRepuestoRow();
                }
            });
        }

        // Agregar servicio propio
        var btnAddServicio = document.getElementById('add-servicio');
        if (btnAddServicio && !btnAddServicio.dataset.egBound) {
            btnAddServicio.dataset.egBound = '1';
            btnAddServicio.addEventListener('click', function() {
                if (window.EG.servicios && window.EG.servicios.addServicioRow) {
                    window.EG.servicios.addServicioRow();
                } else {
                    console.warn('Modulo servicios no disponible');
                }
            });
        }

        // Agregar otro servicio
        var btnAddOtro = document.getElementById('add-otro');
        if (btnAddOtro && !btnAddOtro.dataset.egBound) {
            btnAddOtro.dataset.egBound = '1';
            btnAddOtro.addEventListener('click', function() {
                if (window.EG.servicios && window.EG.servicios.addOtroRow) {
                    window.EG.servicios.addOtroRow();
                } else {
                    console.warn('Modulo servicios no disponible para otros servicios');
                }
            });
        }

        // Piezas usadas
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

    /**
     * Configura serialización antes de submit
     */
    function setupFormSubmit() {
        var form = document.getElementById('document-form');
        if (!form) return;

        form.addEventListener('submit', function(e) {
            // Serializar filas antes de enviar
            var serialization = null;
            if (window.serializeRows) {
                serialization = window.serializeRows();
            }

            var invalidRows = serialization && Array.isArray(serialization.invalidServiceRows)
                ? serialization.invalidServiceRows
                : [];

            if (invalidRows.length) {
                e.preventDefault();
                window.alert('Debes seleccionar un servicio valido del listado antes de guardar.');
                var firstInvalidInput = form.querySelector('#servicios-container .dynamic-element.ring-red-500 .srv-input');
                if (firstInvalidInput) firstInvalidInput.focus();
            }
        });
    }

    /**
     * Restaura borrador al cargar la página
     */
    async function restoreDraftOnLoad() {
        var form = document.getElementById('document-form');
        if (!form) return;
        var params = new URLSearchParams(window.location.search || '');
        var hasReturnContext = !!(params.get('cliente_id') || params.get('vehiculo_id') || params.get('target_row'));

        if (form.dataset.mode === 'create' && !hasReturnContext) {
            if (window.EG.cliente && window.EG.cliente.resetClienteUI) {
                window.EG.cliente.resetClienteUI();
            }
            var vehiculoSelect = document.getElementById('id_vehiculo');
            if (vehiculoSelect) {
                vehiculoSelect.innerHTML = '<option value="">' + ((window.EG.I18N && window.EG.I18N.select_vehicle) || 'Select vehicle...') + '</option>';
                vehiculoSelect.value = '';
            }
            var vehiculoInfo = document.getElementById('vehiculo-info');
            if (vehiculoInfo) vehiculoInfo.classList.add('hidden');
        }

        // Esperar a que todo esté cargado
        await new Promise(function(resolve) {
            if (document.readyState === 'complete') {
                setTimeout(resolve, 100);
            } else {
                window.addEventListener('load', function() {
                    setTimeout(resolve, 100);
                });
            }
        });

        var initialLineData = hydrateInitialRows();
        var hasServerLines = hasAnyLineData(initialLineData);

        // Restaurar borrador
        if (window.restoreDocumentDraftAfterHydrate) {
            try {
                await window.restoreDocumentDraftAfterHydrate({ hasServerLines: hasServerLines });
            } catch (err) {
                console.error('Error restaurando borrador:', err);
            }
        }

        // Recalcular totales
        if (window.recalcTotales) {
            window.recalcTotales();
        }
        if (window.serializeRows) {
            window.serializeRows();
        }
    }

    /**
     * Función helper para encode next URL
     */
    window.egEncodeDocumentFormNext = function() {
        return encodeURIComponent(window.location.pathname + (window.location.search || ''));
    };

    // Inicializar cuando el DOM esté listo
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initAllModules);
    } else {
        initAllModules();
    }

    // Exports
    window.EG.initAllModules = initAllModules;
    window.EG.loadModule = loadModule;

})();
