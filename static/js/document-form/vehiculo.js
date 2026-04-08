/**
 * vehiculo.js - Modulo de gestion de vehiculos
 * 
 * Extraido del codigo embebido en document_form.html
 */

(function() {
    'use strict';

    const EG = window.EG = window.EG || {};

    // Elementos del DOM
    let vehiculoSelect;
    let vehiculoInfoBox;
    let marcaModeloEl;
    let anoVinEl;
    let mileageEl;
    let ultimaEntradaEl;

    /**
     * Obtiene referencias a elementos del DOM
     */
    function getElements() {
        if (!vehiculoSelect) {
            vehiculoSelect = document.getElementById('id_vehiculo');
        }
        if (!vehiculoInfoBox) {
            vehiculoInfoBox = document.getElementById('vehiculo-info');
        }
        if (!marcaModeloEl) {
            marcaModeloEl = document.getElementById('vehiculo-marca-modelo');
        }
        if (!anoVinEl) {
            anoVinEl = document.getElementById('vehiculo-ano-vin');
        }
        if (!mileageEl) {
            mileageEl = document.getElementById('vehiculo-mileage');
        }
        if (!ultimaEntradaEl) {
            ultimaEntradaEl = document.getElementById('vehiculo-ultima-entrada');
        }
        return { vehiculoSelect, vehiculoInfoBox, marcaModeloEl, anoVinEl, mileageEl, ultimaEntradaEl };
    }

    /**
     * Carga vehiculos por cliente (desde prefetch o AJAX)
     */
    async function cargarVehiculosPorCliente(clienteId, vehiculoIdToSelect = null) {
        const els = getElements();
        if (!els.vehiculoSelect) {
            console.warn('Elemento #id_vehiculo no encontrado');
            return;
        }

        if (!clienteId) {
            console.warn('No se proporciono clienteId');
            els.vehiculoSelect.innerHTML = `<option value="">${EG.I18N.select_vehicle}</option>`;
            return;
        }

        console.log(`Cargando vehiculos para cliente ID: ${clienteId}${vehiculoIdToSelect ? ` (preseleccionar: ${vehiculoIdToSelect})` : ''}`);

        // Verificar si ya tiene opciones del formulario
        const alreadyHasOptions = els.vehiculoSelect.options && els.vehiculoSelect.options.length > 1;
        if (alreadyHasOptions && els.vehiculoSelect.dataset.source === 'form') {
            console.log('Ya tiene opciones desde el formulario, omitiendo carga');
            if (vehiculoIdToSelect) {
                setTimeout(() => preseleccionarVehiculo(vehiculoIdToSelect), 100);
            }
            return;
        }

        els.vehiculoSelect.disabled = true;
        els.vehiculoSelect.innerHTML = `<option value="">${EG.I18N.loading_vehicles || 'Cargando vehiculos...'}</option>`;

        // Intentar primero con prefetch local
        const localMatches = (EG.PREFETCH?.vehiculos || []).filter(
            (v) => String(v.cliente_id) === String(clienteId)
        );
        if (localMatches.length) {
            console.log(`Encontrados ${localMatches.length} vehiculos en prefetch`);
            const options = localMatches.map((v) =>
                `<option value="${v.id}">${v.label || v.text || ''}</option>`
            ).join('');
            els.vehiculoSelect.innerHTML = `<option value="">${EG.I18N.select_vehicle}</option>${options}`;
            els.vehiculoSelect.dataset.source = 'prefetch';
            els.vehiculoSelect.disabled = false;
            if (vehiculoIdToSelect) {
                setTimeout(() => preseleccionarVehiculo(vehiculoIdToSelect), 100);
            }
            return;
        }

        // Si no hay en prefetch, hacer peticion AJAX
        try {
            const urlRaw = EG.cfg.URL_VEHICULOS_BY_CLI || '/api/v1/vehiculos/0/';
            const url = EG.config.buildEndpoint(urlRaw);
            let fullUrl = '';

            if (/\/0\/?$/.test(url)) {
                fullUrl = url.replace(/\/0\/?$/, `/${encodeURIComponent(clienteId)}/`);
            } else if (url.indexOf('__CLIENTE_ID__') !== -1) {
                fullUrl = url.replace('__CLIENTE_ID__', encodeURIComponent(clienteId));
            } else {
                const separator = url.indexOf('?') === -1 ? '?' : '&';
                fullUrl = `${url}${separator}cliente_id=${encodeURIComponent(clienteId)}`;
            }

            console.log(`Llamando a: ${fullUrl}`);
            const r = await EG.utils.egFetch(fullUrl);

            if (!r.ok) {
                const errorText = await r.text();
                console.error(`HTTP ${r.status}:`, errorText);
                throw new Error(`HTTP ${r.status}: ${errorText}`);
            }

            const data = await r.json();
            console.log('Respuesta recibida:', data);

            const items = Array.isArray(data) ? data : (data.results || data.items || []);
            console.log(`Procesando ${items.length} vehiculos`);

            if (!items.length) {
                console.log('No se encontraron vehiculos');
                els.vehiculoSelect.innerHTML = `<option value="">${EG.I18N.no_vehicles}</option>`;
                els.vehiculoSelect.dataset.source = 'empty';
            } else {
                const options = items.map((v) => {
                    const id = v.id ?? v.pk;
                    const label = v.text || v.label || v.patente || `Vehicle #${id}`;
                    return `<option value="${id}">${label}</option>`;
                }).join('');
                els.vehiculoSelect.innerHTML = `<option value="">${EG.I18N.select_vehicle}</option>${options}`;
                els.vehiculoSelect.dataset.source = 'fetch';
                console.log(`${items.length} vehiculos cargados exitosamente`);

                if (vehiculoIdToSelect) {
                    setTimeout(() => preseleccionarVehiculo(vehiculoIdToSelect), 100);
                }
            }
        } catch (err) {
            console.error('Error cargando vehiculos:', err);
            els.vehiculoSelect.innerHTML = `<option value="">${EG.I18N.error_loading_vehicles}</option>`;
            els.vehiculoSelect.dataset.source = 'error';
        } finally {
            els.vehiculoSelect.disabled = false;
        }
    }

    /**
     * Preselecciona un vehiculo por ID
     */
    function preseleccionarVehiculo(vehiculoId) {
        const els = getElements();
        if (!els.vehiculoSelect) {
            console.warn('Elemento #id_vehiculo no encontrado para preseleccion');
            return;
        }

        const vehiculoIdStr = String(vehiculoId);
        console.log(`Intentando preseleccionar vehiculo ID: ${vehiculoIdStr}`);

        const option = Array.from(els.vehiculoSelect.options).find(
            (opt) => String(opt.value) === vehiculoIdStr
        );

        if (option) {
            els.vehiculoSelect.value = vehiculoIdStr;
            els.vehiculoSelect.dispatchEvent(new Event('change', { bubbles: true }));
            console.log(`Vehiculo ${vehiculoIdStr} preseleccionado exitosamente`);
        } else {
            console.warn(`Vehiculo ${vehiculoIdStr} no encontrado en las opciones`);
            setTimeout(() => {
                const retryOption = Array.from(els.vehiculoSelect.options).find(
                    (opt) => String(opt.value) === vehiculoIdStr
                );
                if (retryOption) {
                    els.vehiculoSelect.value = vehiculoIdStr;
                    els.vehiculoSelect.dispatchEvent(new Event('change', { bubbles: true }));
                    console.log(`Vehiculo ${vehiculoIdStr} preseleccionado en reintento`);
                } else {
                    console.error(`No se pudo preseleccionar vehiculo ${vehiculoIdStr}`);
                }
            }, 500);
        }
    }

    /**
     * Actualiza la tarjeta de informacion del vehiculo
     */
    function updateVehiculoCard() {
        const els = getElements();
        if (!els.vehiculoInfoBox || !els.vehiculoSelect) return;

        const opt = els.vehiculoSelect.options[els.vehiculoSelect.selectedIndex];
        const text = opt ? opt.textContent.trim() : '';

        if (!els.vehiculoSelect.value || !text) {
            els.vehiculoInfoBox.classList.add('hidden');
            return;
        }

        if (els.marcaModeloEl) els.marcaModeloEl.textContent = text;
        if (els.anoVinEl) els.anoVinEl.textContent = '';
        if (els.mileageEl) els.mileageEl.textContent = '';
        if (els.ultimaEntradaEl) els.ultimaEntradaEl.textContent = '';
        els.vehiculoInfoBox.classList.remove('hidden');

        // Emitir evento
        document.dispatchEvent(new CustomEvent('vehiculo:seleccionado', {
            detail: { id: els.vehiculoSelect.value, text }
        }));
    }
    /**
     * Abre alta de vehiculo preservando contexto del documento.
     */
    function openVehiculoModal() {
        try {
            const pathOnly = window.location.pathname || '/';
            const baseUrl = EG.cfg.URL_VEHICULO_CREATE_PAGE || '/vehiculos/crear/';

            let clienteId = '';
            const clienteSelect = document.getElementById('id_cliente');
            if (clienteSelect) {
                if (window.jQuery && jQuery(clienteSelect).hasClass('select2-hidden-accessible')) {
                    clienteId = jQuery(clienteSelect).val() || '';
                } else {
                    clienteId = clienteSelect.value || '';
                }
            }

            if (window.EG && window.EG.borrador && typeof window.EG.borrador.saveDocumentDraftNow === 'function') {
                window.EG.borrador.saveDocumentDraftNow();
            }

            var createUrl = new URL(baseUrl, window.location.origin);
            createUrl.searchParams.set('return_to', pathOnly + (window.location.search || ''));
            createUrl.searchParams.set('field_target', 'vehiculo');
            if (clienteId) {
                createUrl.searchParams.set('cliente_id', clienteId);
            }

            window.location.href = createUrl.toString();
        } catch (error) {
            console.error('Error al abrir alta de vehiculo:', error);
            alert('Error al abrir la pagina de crear vehiculo.');
        }
    }

    async function seleccionarVehiculoById(id, label) {
        const els = getElements();
        if (!els.vehiculoSelect || !id) return;

        const idStr = String(id);
        const found = Array.from(els.vehiculoSelect.options).find(function(opt) {
            return String(opt.value) === idStr;
        });
        if (!found) {
            const option = document.createElement('option');
            option.value = idStr;
            option.textContent = label || ('Vehiculo #' + idStr);
            els.vehiculoSelect.appendChild(option);
        }
        els.vehiculoSelect.value = idStr;
        els.vehiculoSelect.dispatchEvent(new Event('change', { bubbles: true }));
    }
    /**
     * Inicializar eventos
     */
    function init() {
        const els = getElements();

        // Evento change en select de vehiculo
        els.vehiculoSelect?.addEventListener('change', updateVehiculoCard);

        // Actualizar tarjeta inicialmente
        updateVehiculoCard();

        // Boton nuevo vehiculo
        const btnNuevoVehiculo = document.getElementById('btn-nuevo-vehiculo');
        if (btnNuevoVehiculo) {
            btnNuevoVehiculo.addEventListener('click', openVehiculoModal);
        }

        console.log('Vehiculo module initialized');
    }

    // Exports
    EG.vehiculo = {
        cargarVehiculosPorCliente,
        preseleccionarVehiculo,
        seleccionarVehiculoById,
        updateVehiculoCard,
        openVehiculoModal,
        init
    };

})();

