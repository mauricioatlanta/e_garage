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
        if (btnAddRepuesto) {
            btnAddRepuesto.addEventListener('click', function() {
                if (window.EG.repuestos && window.EG.repuestos.addRepuestoRow) {
                    window.EG.repuestos.addRepuestoRow();
                }
            });
        }

        // Agregar servicio propio
        var btnAddServicio = document.getElementById('add-servicio');
        if (btnAddServicio) {
            btnAddServicio.addEventListener('click', function() {
                if (window.EG.servicios && window.EG.servicios.addServicioRow) {
                    window.EG.servicios.addServicioRow();
                }
            });
        }

        // Agregar otro servicio
        var btnAddOtro = document.getElementById('add-otro');
        if (btnAddOtro) {
            btnAddOtro.addEventListener('click', function() {
                if (window.EG.otros && window.EG.otros.addOtroRow) {
                    window.EG.otros.addOtroRow();
                }
            });
        }

        // Piezas usadas
        var btnAddUsed = document.getElementById('add-used-parts');
        if (btnAddUsed) {
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
            if (window.serializeRows) {
                window.serializeRows();
            }
        });
    }

    /**
     * Restaura borrador al cargar la página
     */
    async function restoreDraftOnLoad() {
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

        // Restaurar borrador
        if (window.restoreDocumentDraftAfterHydrate) {
            try {
                await window.restoreDocumentDraftAfterHydrate({ hasServerLines: false });
            } catch (err) {
                console.error('Error restaurando borrador:', err);
            }
        }

        // Recalcular totales
        if (window.recalcTotales) {
            window.recalcTotales();
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
