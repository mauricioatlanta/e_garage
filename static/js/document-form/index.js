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
        var hasReturnContext = !!(
            params.get('cliente_id') ||
            params.get('vehiculo_id') ||
            params.get('target_row') ||
            params.get('created_id') ||
            params.get('entity_type')
        );
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

    function getCurrentReturnPath() {
        return window.location.pathname + (window.location.search || '');
    }

    function buildEntityCreateUrl(entity) {
        var form = document.getElementById('document-form');
        if (!form || !entity) return '';

        var map = {
            cliente: form.dataset.urlClientCreatePage || '',
            vehiculo: form.dataset.urlVehiculoCreatePage || '',
            repuesto: form.dataset.urlRepuestoCreatePage || '',
            servicio: form.dataset.urlServiceCreate || '',
            otro_servicio: form.dataset.urlOtroServiceCreatePage || ''
        };
        var base = map[entity] || '';
        if (!base) return '';

        var url = new URL(base, window.location.origin);
        url.searchParams.set('return_to', getCurrentReturnPath());
        url.searchParams.set('field_target', entity);

        if (entity === 'vehiculo') {
            var clienteId = (document.getElementById('id_cliente') && document.getElementById('id_cliente').value) || '';
            if (clienteId) url.searchParams.set('cliente_id', clienteId);
        }
        return url.toString();
    }

    function buildInlineCreateUrl(entity, row, prefillName) {
        var targetUrl = buildEntityCreateUrl(entity);
        if (!targetUrl) return '';
        var url = new URL(targetUrl, window.location.origin);
        var rowId = row && row.dataset ? (row.dataset.rowId || '') : '';
        if (rowId) url.searchParams.set('target_row', rowId);
        var nombre = (prefillName || '').trim();
        if (nombre) url.searchParams.set('prefill_nombre', nombre);
        return url.toString();
    }

    function navigateToInlineCreate(entity, row, prefillName) {
        var targetUrl = buildInlineCreateUrl(entity, row, prefillName);
        if (!targetUrl) return;
        if (window.EG && window.EG.borrador && typeof window.EG.borrador.saveDocumentDraftNow === 'function') {
            window.EG.borrador.saveDocumentDraftNow();
        }
        window.location.href = targetUrl;
    }

    function ensureDynamicRowId(row, prefix) {
        if (!row || !row.dataset) return '';
        if (!row.dataset.rowId) {
            row.dataset.rowId = prefix + '_' + Date.now() + '_' + Math.floor(Math.random() * 1000);
        }
        return row.dataset.rowId;
    }

    function findDynamicRowById(containerId, rowId) {
        if (!rowId) return null;
        var container = document.getElementById(containerId);
        if (!container) return null;
        return Array.prototype.find.call(container.querySelectorAll('.dynamic-element'), function(row) {
            return (row.dataset.rowId || '') === String(rowId);
        }) || null;
    }

    function decorateInlineCreateCell(row, options) {
        if (!row) return;
        ensureDynamicRowId(row, options.prefix);
        var input = row.querySelector(options.inputSelector);
        if (!input) return;
        input.classList.add('doc-input-with-create');
        if (row.querySelector(options.buttonSelector)) return;
        var cell = input.closest('td') || input.parentElement;
        if (!cell) return;
        var button = document.createElement('button');
        button.type = 'button';
        button.className = options.buttonClass + ' btn-row-icon btn-row-icon-create doc-inline-create-btn';
        button.setAttribute('data-inline-create-entity', options.entity);
        button.setAttribute('title', options.title);
        button.setAttribute('aria-label', options.title);
        button.textContent = '+';
        cell.appendChild(button);
    }

    function decorateCatalogCreateButtons() {
        var isEnglish = (document.documentElement.lang || '').toLowerCase().indexOf('en') === 0;
        [
            {
                id: 'btn-nuevo-repuesto',
                title: isEnglish ? 'Create part in catalog' : 'Crear repuesto en sistema',
                label: isEnglish ? 'Catalog' : 'Catálogo'
            },
            {
                id: 'btn-nuevo-servicio',
                title: isEnglish ? 'Create service in catalog' : 'Crear servicio en sistema',
                label: isEnglish ? 'Catalog' : 'Catálogo'
            },
            {
                id: 'btn-nuevo-otro-servicio',
                title: isEnglish ? 'Create external service in catalog' : 'Crear servicio externo en sistema',
                label: isEnglish ? 'Catalog' : 'Catálogo'
            }
        ].forEach(function(config) {
            var button = document.getElementById(config.id);
            if (!button) return;
            button.setAttribute('title', config.title);
            var label = button.querySelector('.doc-action-label');
            if (label) label.textContent = config.label;
        });

        document.querySelectorAll('#repuestos-container .dynamic-element').forEach(function(row) {
            ensureDynamicRowId(row, 'rep');
            var repBtn = row.querySelector('.rep-create-btn');
            if (repBtn) {
                repBtn.classList.add('btn-row-icon-create');
                repBtn.setAttribute('title', repBtn.getAttribute('title') || 'Crear repuesto en sistema');
            }
        });

        document.querySelectorAll('#servicios-container .dynamic-element').forEach(function(row) {
            decorateInlineCreateCell(row, {
                prefix: 'serv',
                entity: 'servicio',
                inputSelector: '.srv-input',
                buttonSelector: '.srv-create-btn',
                buttonClass: 'srv-create-btn',
                title: 'Crear servicio en sistema'
            });
        });

        document.querySelectorAll('#otros-container .dynamic-element').forEach(function(row) {
            decorateInlineCreateCell(row, {
                prefix: 'otr',
                entity: 'otro_servicio',
                inputSelector: '.otr-search',
                buttonSelector: '.otr-create-btn',
                buttonClass: 'otr-create-btn',
                title: 'Crear servicio externo en sistema'
            });
        });
    }

    function bindCatalogCreateButtons() {
        if (document.body.dataset.egCatalogCreateBound) return;
        document.body.dataset.egCatalogCreateBound = '1';

        decorateCatalogCreateButtons();

        ['repuestos-container', 'servicios-container', 'otros-container'].forEach(function(containerId) {
            var container = document.getElementById(containerId);
            if (!container) return;
            var observer = new MutationObserver(function() {
                decorateCatalogCreateButtons();
            });
            observer.observe(container, { childList: true });
        });

        document.addEventListener('click', function(event) {
            var button = event.target.closest('[data-inline-create-entity]');
            if (!button) return;
            event.preventDefault();
            var entity = button.getAttribute('data-inline-create-entity');
            var row = button.closest('tr');
            if (!row) return;
            var input = null;
            if (entity === 'servicio') input = row.querySelector('.srv-input');
            if (entity === 'otro_servicio') input = row.querySelector('.otr-search');
            navigateToInlineCreate(entity, row, input && input.value || '');
        });
    }

    function bindCreateEntityButtons() {
        document.querySelectorAll('[data-create-entity]').forEach(function(btn) {
            if (btn.dataset.egCreateBound) return;
            btn.dataset.egCreateBound = '1';
            btn.addEventListener('click', function(event) {
                var entity = btn.getAttribute('data-create-entity');
                // Cliente y vehiculo ya tienen flujo dedicado en sus modulos.
                if (entity === 'cliente' || entity === 'vehiculo') return;
                event.preventDefault();
                var targetUrl = buildEntityCreateUrl(entity);
                if (!targetUrl) return;
                if (window.EG && window.EG.borrador && typeof window.EG.borrador.saveDocumentDraftNow === 'function') {
                    window.EG.borrador.saveDocumentDraftNow();
                }
                window.location.href = targetUrl;
            });
        });
    }

    async function processCreatedEntityFromParams() {
        var params = new URLSearchParams(window.location.search || '');
        var targetRow = (params.get('target_row') || '').trim();

        // Compatibilidad legacy de repuestos.
        if (params.get('created_repuesto_id')) {
            var repEntity = {
                id: params.get('created_repuesto_id'),
                nombre: params.get('created_repuesto_nombre') || '',
                codigo: params.get('created_repuesto_codigo') || '',
                precio_venta: params.get('created_repuesto_precio_venta') || 0,
                precio_compra: params.get('created_repuesto_precio_compra') || 0,
                target_row: params.get('target_row') || ''
            };
            if (window.EG.repuestos && typeof window.EG.repuestos.addRowFromCreatedEntity === 'function') {
                window.EG.repuestos.addRowFromCreatedEntity(repEntity);
            }
        }

        var entityType = (params.get('entity_type') || '').trim();
        var createdId = (params.get('created_id') || '').trim();
        var createdLabel = (params.get('created_label') || '').trim();
        var fieldTarget = (params.get('field_target') || '').trim();
        if (!entityType || !createdId) {
            return;
        }

        if (entityType === 'cliente' && window.EG.cliente && typeof window.EG.cliente.seleccionarClienteById === 'function') {
            await window.EG.cliente.seleccionarClienteById(createdId, createdLabel);
        } else if (entityType === 'vehiculo' && window.EG.vehiculo && typeof window.EG.vehiculo.seleccionarVehiculoById === 'function') {
            await window.EG.vehiculo.seleccionarVehiculoById(createdId, createdLabel);
        } else if (entityType === 'repuesto' && window.EG.repuestos && typeof window.EG.repuestos.addRowFromCreatedEntity === 'function') {
            window.EG.repuestos.addRowFromCreatedEntity({
                id: createdId,
                nombre: createdLabel,
                target_row: targetRow,
                precio_venta: params.get('created_repuesto_precio_venta') || 0,
                precio_compra: params.get('created_repuesto_precio_compra') || 0
            });
        } else if (entityType === 'servicio' && window.EG.servicios && typeof window.EG.servicios.addServicioFromCreatedEntity === 'function') {
            var serviceEntity = {
                id: createdId,
                nombre: createdLabel,
                target_row: targetRow
            };
            var targetServiceRow = findDynamicRowById('servicios-container', targetRow);
            if (targetServiceRow && typeof targetServiceRow.__applyServData === 'function') {
                targetServiceRow.__applyServData(serviceEntity);
            } else {
                window.EG.servicios.addServicioFromCreatedEntity(serviceEntity);
            }
        } else if ((entityType === 'otro_servicio' || fieldTarget === 'otro_servicio') && window.EG.servicios && typeof window.EG.servicios.addOtroServicioFromCreatedEntity === 'function') {
            var otherEntity = {
                id: createdId,
                nombre: createdLabel,
                target_row: targetRow
            };
            var targetOtherRow = findDynamicRowById('otros-container', targetRow);
            if (targetOtherRow && typeof targetOtherRow.__applyOtroData === 'function') {
                targetOtherRow.__applyOtroData(otherEntity);
            } else {
                window.EG.servicios.addOtroServicioFromCreatedEntity(otherEntity);
            }
        }
    }

    function clearReturnParamsFromUrl() {
        var url = new URL(window.location.href);
        [
            'entity_type',
            'field_target',
            'created_id',
            'created_label',
            'created_repuesto_id',
            'created_repuesto_nombre',
            'created_repuesto_codigo',
            'created_repuesto_precio_venta',
            'created_repuesto_precio_compra',
            'target_row',
            'cliente_id',
            'vehiculo_id'
        ].forEach(function(key) {
            url.searchParams.delete(key);
        });
        window.history.replaceState({}, document.title, url.pathname + (url.search ? url.search : ''));
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
        bindCreateEntityButtons();
        bindCatalogCreateButtons();

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
        var hasReturnContext = !!(
            params.get('cliente_id') ||
            params.get('vehiculo_id') ||
            params.get('target_row') ||
            params.get('created_id') ||
            params.get('entity_type')
        );

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

        await processCreatedEntityFromParams();
        clearReturnParamsFromUrl();
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
