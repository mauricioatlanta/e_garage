```javascript
/**
 * Document Engine - Sistema completo de gestión de documentos
 * Auto-contenido, funcional y bien documentado
 * @version 1.0.0
 */
(function() {
    'use strict';

    console.log("[DOC] Inicializando Document Engine...");

    // =========================================================================
    // 1. UTILITIES
    // =========================================================================
    const EG = {
        /**
         * Obtiene una cookie por nombre
         * @param {string} name - Nombre de la cookie
         * @returns {string|null} Valor de la cookie o null
         */
        utils: {
            getCookie: function(name) {
                try {
                    const value = `; ${document.cookie}`;
                    const parts = value.split(`; ${name}=`);
                    if (parts.length === 2) return parts.pop().split(';').shift();
                    return null;
                } catch (error) {
                    console.error("[DOC] Error obteniendo cookie:", error);
                    return null;
                }
            }
        },

        /**
         * Fetch wrapper con CSRF y credenciales
         * @param {string} url - URL a consultar
         * @param {object} opts - Opciones de fetch
         * @returns {Promise} Promesa con la respuesta
         */
        fetch: function(url, opts = {}) {
            const csrfToken = EG.utils.getCookie('csrftoken');
            const defaultOpts = {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest',
                    ...(csrfToken && { 'X-CSRFToken': csrfToken })
                },
                credentials: 'same-origin'
            };

            const finalOpts = { ...defaultOpts, ...opts };
            
            if (opts.body && typeof opts.body === 'object' && !(opts.body instanceof FormData)) {
                finalOpts.body = JSON.stringify(opts.body);
            }

            console.log(`[DOC] Fetching: ${url}`, finalOpts.method);
            return window.fetch(url, finalOpts);
        },

        /**
         * Configuración del sistema desde data-* attributes
         */
        cfg: (function() {
            const config = {};
            const form = document.querySelector('form[data-doc-engine]') || document.querySelector('form');
            
            if (!form) {
                console.warn("[DOC] No se encontró formulario para configurar");
                return config;
            }

            // Extraer configuración de data-* attributes
            const dataAttrs = [
                'api-base', 'client-search', 'vehicle-list', 'part-search',
                'service-search', 'document-update', 'country', 'language'
            ];

            dataAttrs.forEach(attr => {
                const value = form.getAttribute(`data-${attr}`);
                if (value) config[attr.replace('-', '_')] = value;
            });

            // Fallback country-aware desde location.pathname
            if (!config.country || !config.language) {
                const pathParts = window.location.pathname.split('/').filter(Boolean);
                if (pathParts.length >= 2) {
                    config.country = config.country || pathParts[0];
                    config.language = config.language || pathParts[1];
                } else {
                    config.country = config.country || 'cl';
                    config.language = config.language || 'es';
                }
            }

            // Construir URLs base si no están definidas
            const basePath = `/${config.country}/${config.language}/api`;
            config.api_base = config.api_base || basePath;
            
            // URLs específicas con fallback
            const endpoints = {
                client_search: '/clientes/buscar/',
                vehicle_list: '/vehiculos/cliente/',
                part_search: '/repuestos/buscar/',
                service_search: '/servicios/buscar/',
                document_update: '/documento/actualizar/'
            };

            Object.entries(endpoints).forEach(([key, endpoint]) => {
                if (!config[key]) {
                    config[key] = config.api_base + endpoint;
                }
            });

            console.log("[DOC] Configuración cargada:", config);
            return config;
        })()
    };

    // =========================================================================
    // 2. CORE FUNCTIONS
    // =========================================================================

    /**
     * Actualiza el número de documento según tipo
     * @param {string} tipo - Tipo de documento (OT, PRES, FAC, PTS)
     */
    function updateDocumentNumber(tipo) {
        try {
            console.log(`[DOC] Actualizando número para tipo: ${tipo}`);
            
            const numeroField = document.getElementById('id_numero');
            if (!numeroField) {
                console.warn("[DOC] Campo 'id_numero' no encontrado");
                return;
            }

            // Si ya tiene valor, no hacer nada
            if (numeroField.value.trim()) {
                console.log("[DOC] Número ya asignado:", numeroField.value);
                return;
            }

            // Generar prefijo según tipo
            const prefixes = {
                'OT': 'OT',
                'PRES': 'PR',
                'FAC': 'FC',
                'PTS': 'PT'
            };

            const prefix = prefixes[tipo] || 'DOC';
            const timestamp = new Date().getTime().toString().slice(-6);
            const random = Math.floor(Math.random() * 1000).toString().padStart(3, '0');
            
            numeroField.value = `${prefix}-${timestamp}-${random}`;
            console.log(`[DOC] Nuevo número generado: ${numeroField.value}`);
            
        } catch (error) {
            console.error("[DOC] Error actualizando número:", error);
        }
    }

    /**
     * Busca clientes con autocomplete
     * @param {string} query - Término de búsqueda
     * @returns {Promise} Promesa con resultados
     */
    function buscarClientes(query) {
        return new Promise((resolve, reject) => {
            if (!query || query.length < 2) {
                resolve([]);
                return;
            }

            const url = `${EG.cfg.client_search}?q=${encodeURIComponent(query)}`;
            
            EG.fetch(url)
                .then(response => {
                    if (!response.ok) throw new Error(`HTTP ${response.status}`);
                    return response.json();
                })
                .then(data => {
                    console.log(`[DOC] ${data.length} clientes encontrados`);
                    resolve(data);
                })
                .catch(error => {
                    console.error("[DOC] Error buscando clientes:", error);
                    reject(error);
                });
        });
    }

    /**
     * Selecciona un cliente y carga sus vehículos
     * @param {object} cliente - Datos del cliente
     */
    function seleccionarCliente(cliente) {
        try {
            console.log("[DOC] Seleccionando cliente:", cliente.nombre);
            
            // Actualizar campos del formulario
            const clienteIdField = document.getElementById('id_cliente');
            const clienteNombreField = document.getElementById('cliente_nombre');
            
            if (clienteIdField) clienteIdField.value = cliente.id;
            if (clienteNombreField) clienteNombreField.value = cliente.nombre;
            
            // Cargar vehículos del cliente
            cargarVehiculosPorCliente(cliente.id);
            
        } catch (error) {
            console.error("[DOC] Error seleccionando cliente:", error);
        }
    }

    /**
     * Carga vehículos de un cliente
     * @param {number} clienteId - ID del cliente
     */
    function cargarVehiculosPorCliente(clienteId) {
        if (!clienteId) return;
        
        const url = `${EG.cfg.vehicle_list}${clienteId}/`;
        const select = document.getElementById('id_vehiculo');
        
        if (!select) {
            console.warn("[DOC] Selector de vehículos no encontrado");
            return;
        }

        // Guardar selección actual
        const currentValue = select.value;
        
        // Limpiar opciones excepto la primera
        while (select.options.length > 1) {
            select.remove(1);
        }

        // Prefetch: intentar obtener datos cacheados
        const cacheKey = `vehiculos_${clienteId}`;
        const cached = sessionStorage.getItem(cacheKey);
        
        if (cached) {
            console.log("[DOC] Usando vehículos cacheados");
            populateVehicleSelect(JSON.parse(cached), select, currentValue);
            return;
        }

        // Cargar via AJAX
        console.log(`[DOC] Cargando vehículos para cliente ${clienteId}`);
        
        EG.fetch(url)
            .then(response => {
                if (!response.ok) throw new Error(`HTTP ${response.status}`);
                return response.json();
            })
            .then(data => {
                // Cachear resultados
                sessionStorage.setItem(cacheKey, JSON.stringify(data));
                populateVehicleSelect(data, select, currentValue);
            })
            .catch(error => {
                console.error("[DOC] Error cargando vehículos:", error);
                select.innerHTML = '<option value="">Error cargando vehículos</option>';
            });
    }

    /**
     * Poblar select de vehículos
     * @param {Array} data - Datos de vehículos
     * @param {HTMLSelectElement} select - Elemento select
     * @param {string} currentValue - Valor actual seleccionado
     */
    function populateVehicleSelect(data, select, currentValue) {
        data.forEach(vehiculo => {
            const option = document.createElement('option');
            option.value = vehiculo.id;
            option.textContent = `${vehiculo.marca} ${vehiculo.modelo} - ${vehiculo.patente}`;
            select.appendChild(option);
        });
        
        // Restaurar selección si existe
        if (currentValue && Array.from(select.options).some(opt => opt.value === currentValue)) {
            select.value = currentValue;
        }
        
        console.log(`[DOC] ${data.length} vehículos cargados`);
    }

    /**
     * Agrega fila de repuesto con búsqueda
     */
    function addRepuestoRow() {
        const tbody = document.querySelector('#repuestos-table tbody');
        if (!tbody) {
            console.error("[DOC] Tabla de repuestos no encontrada");
            return;
        }

        const rowId = Date.now();
        const row = document.createElement('tr');
        row.id = `repuesto-row-${rowId}`;
        row.innerHTML = `
            <td>
                <input type="text" class="repuesto-codigo" placeholder="Código" 
                       data-row="${rowId}" autocomplete="off">
                <div class="dropdown-results" id="dropdown-${rowId}" style="display:none;"></div>
            </td>
            <td><input type="text" class="repuesto-nombre" readonly></td>
            <td><input type="number" class="repuesto-cantidad" value="1" min="1" step="1"></td>
            <td><input type="number" class="repuesto-precio" step="0.01" min="0"></td>
            <td><span class="repuesto-subtotal">0.00</span></td>
            <td>
                <input type="checkbox" class="repuesto-taxable" checked>
                <button type="button" class="btn-remove-row" data-row="${rowId}">×</button>
            </td>
        `;

        tbody.appendChild(row);
        console.log(`[DOC] Fila de repuesto ${rowId} agregada`);
        
        // Configurar event listeners
        setupRepuestoRowEvents(rowId);
    }

    /**
     * Configura eventos para fila de repuesto
     * @param {string} rowId - ID de la fila
     */
    function setupRepuestoRowEvents(rowId) {
        const codigoInput = document.querySelector(`#repuesto-row-${rowId} .repuesto-codigo`);
        const removeBtn = document.querySelector(`#repuesto-row-${rowId} .btn-remove-row`);
        const cantidadInput = document.querySelector(`#repuesto-row-${rowId} .repuesto-cantidad`);
        const precioInput = document.querySelector(`#repuesto-row-${rowId} .repuesto-precio`);
        const taxableCheckbox = document.querySelector(`#repuesto-row-${rowId} .repuesto-taxable`);

        // Búsqueda con debounce
        let searchTimeout;
        codigoInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                buscarRepuesto(this.value, rowId);
            }, 300);
        });

        // Eliminar fila
        removeBtn.addEventListener('click', function() {
            const row = document.getElementById(`repuesto-row-${rowId}`);
            if (row) {
                row.remove();
                recalcTotales();
                console.log(`[DOC] Fila ${rowId} eliminada`);
            }
        });

        // Recalcular al cambiar cantidad o precio
        [cantidadInput, precioInput, taxableCheckbox].forEach(input => {
            input.addEventListener('change', recalcTotales);
            input.addEventListener('input', recalcTotales);
        });

        // Cerrar dropdown al hacer clic fuera
        document.addEventListener('click', function(event) {
            const dropdown = document.getElementById(`dropdown-${rowId}`);
            if (dropdown && !dropdown.contains(event.target) && !codigoInput.contains(event.target)) {
                dropdown.style.display = 'none';
            }
        });
    }

    /**
     * Busca repuestos por código o nombre
     * @param {string} query - Término de búsqueda
     * @param {string} rowId - ID de la fila
     */
    function buscarRepuesto(query, rowId) {
        if (!query || query.length < 2) {
            hideDropdown(rowId);
            return;
        }

        const url = `${EG.cfg.part_search}?q=${encodeURIComponent(query)}`;
        
        EG.fetch(url)
            .then(response => {
                if (!response.ok) throw new Error(`HTTP ${response.status}`);
                return response.json();
            })
            .then(data => {
                showRepuestoDropdown(data, rowId);
            })
            .catch(error => {
                console.error("[DOC] Error buscando repuestos:", error);
                hideDropdown(rowId);
            });
    }

    /**
     * Muestra dropdown con resultados de repuestos
     * @param {Array} results - Resultados de búsqueda
     * @param {string} rowId - ID de la fila
     */
    function showRepuestoDropdown(results, rowId) {
        const dropdown = document.getElementById(`dropdown-${rowId}`);
        if (!dropdown) return;

        if (results.length === 0) {
            dropdown.innerHTML = '<div class="dropdown-item">No se encontraron repuestos</div>';
            dropdown.style.display = 'block';
            return;
        }

        dropdown.innerHTML = results.map(repuesto => `
            <div class="dropdown-item" data-repuesto='${JSON.stringify(repuesto)}'>
                <strong>${repuesto.codigo}</strong> - ${repuesto.nombre}<br>
                <small>Stock: ${repuesto.stock} | $${repuesto.precio.toFixed(2)}</small>
            </div>
        `).join('');

        dropdown.style.display = 'block';

        // Configurar selección
        dropdown.querySelectorAll('.dropdown-item').forEach(item => {
            item.addEventListener('click', function() {
                const repuesto = JSON.parse(this.getAttribute('data-repuesto'));
                selectRepuesto(repuesto, rowId);
                dropdown.style.display = 'none';
            });
        });
    }

    /**
     * Selecciona un repuesto para la fila
     * @param {object} repuesto - Datos del repuesto
     * @param {string} rowId - ID de la fila
     */
    function selectRepuesto(repuesto, rowId) {
        const row = document.getElementById(`repuesto-row-${rowId}`);
        if (!row) return;

        row.querySelector('.repuesto-codigo').value = repuesto.codigo;
        row.querySelector('.repuesto-nombre').value = repuesto.nombre;
        row.querySelector('.repuesto-precio').value = repuesto.precio.toFixed(2);
        
        console.log(`[DOC] Repuesto seleccionado: ${repuesto.codigo}`);
        recalcTotales();
    }

    /**
     * Oculta dropdown
     * @param {string} rowId - ID de la fila
     */
    function hideDropdown(rowId) {
        const dropdown = document.getElementById(`dropdown-${rowId}`);
        if (dropdown) dropdown.style.display = 'none';
    }

    /**
     * Agrega fila de servicio
     */
    function addServicioRow() {
        const tbody = document.querySelector('#servicios-table tbody');
        if (!tbody) {
            console.error("[DOC] Tabla de servicios no encontrada");
            return;
        }

        const rowId = Date.now();
        const row = document.createElement('tr');
        row.id = `servicio-row-${rowId}`;
        row.innerHTML = `
            <td>
                <input type="text" class="servicio-codigo" placeholder="Buscar servicio..."
                       data-row="${rowId}" autocomplete="off">
                <div class="dropdown-results" id="servicio-dropdown-${rowId}" style="display:none;"></div>
            </td>
            <td><input type="text" class="servicio-descripcion" readonly></td>
            <td><input type="number" class="servicio-cantidad" value="1" min="1" step="1"></td>
            <td><input type="number" class="servicio-precio" step="0.01" min="0"></td>
            <td><span class="servicio-subtotal">0.00</span></td>
            <td>
                <button type="button" class="btn-remove-row" data-row="${rowId}">