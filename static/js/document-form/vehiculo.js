/**
 * vehiculo.js - Módulo de gestión de vehículos
 * 
 * Extraído del código embebido en document_form.html
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
     * Carga vehículos por cliente (desde prefetch o AJAX)
     */
    async function cargarVehiculosPorCliente(clienteId, vehiculoIdToSelect = null) {
        const els = getElements();
        if (!els.vehiculoSelect) {
            console.warn('⚠️ Elemento #id_vehiculo no encontrado');
            return;
        }

        if (!clienteId) {
            console.warn('⚠️ No se proporcionó clienteId');
            els.vehiculoSelect.innerHTML = `<option value="">${EG.I18N.select_vehicle}</option>`;
            return;
        }

        console.log(`🚗 Cargando vehículos para cliente ID: ${clienteId}${vehiculoIdToSelect ? ` (preseleccionar: ${vehiculoIdToSelect})` : ''}`);

        // Verificar si ya tiene opciones del formulario
        const alreadyHasOptions = els.vehiculoSelect.options && els.vehiculoSelect.options.length > 1;
        if (alreadyHasOptions && els.vehiculoSelect.dataset.source === 'form') {
            console.log('ℹ️ Ya tiene opciones desde el formulario, omitiendo carga');
            if (vehiculoIdToSelect) {
                setTimeout(() => preseleccionarVehiculo(vehiculoIdToSelect), 100);
            }
            return;
        }

        els.vehiculoSelect.disabled = true;
        els.vehiculoSelect.innerHTML = `<option value="">${EG.I18N.loading_vehicles || 'Cargando vehículos...'}</option>`;

        // Intentar primero con prefetch local
        const localMatches = (EG.PREFETCH?.vehiculos || []).filter(
            (v) => String(v.cliente_id) === String(clienteId)
        );
        if (localMatches.length) {
            console.log(`✅ Encontrados ${localMatches.length} vehículos en prefetch`);
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

        // Si no hay en prefetch, hacer petición AJAX
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

            console.log(`📡 Llamando a: ${fullUrl}`);
            const r = await EG.utils.egFetch(fullUrl);

            if (!r.ok) {
                const errorText = await r.text();
                console.error(`❌ HTTP ${r.status}:`, errorText);
                throw new Error(`HTTP ${r.status}: ${errorText}`);
            }

            const data = await r.json();
            console.log('📦 Respuesta recibida:', data);

            const items = Array.isArray(data) ? data : (data.results || data.items || []);
            console.log(`📋 Procesando ${items.length} vehículos`);

            if (!items.length) {
                console.log('ℹ️ No se encontraron vehículos');
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
                console.log(`✅ ${items.length} vehículos cargados exitosamente`);

                if (vehiculoIdToSelect) {
                    setTimeout(() => preseleccionarVehiculo(vehiculoIdToSelect), 100);
                }
            }
        } catch (err) {
            console.error('❌ Error cargando vehículos:', err);
            els.vehiculoSelect.innerHTML = `<option value="">${EG.I18N.error_loading_vehicles}</option>`;
            els.vehiculoSelect.dataset.source = 'error';
        } finally {
            els.vehiculoSelect.disabled = false;
        }
    }

    /**
     * Preselecciona un vehículo por ID
     */
    function preseleccionarVehiculo(vehiculoId) {
        const els = getElements();
        if (!els.vehiculoSelect) {
            console.warn('⚠️ Elemento #id_vehiculo no encontrado para preselección');
            return;
        }

        const vehiculoIdStr = String(vehiculoId);
        console.log(`🎯 Intentando preseleccionar vehículo ID: ${vehiculoIdStr}`);

        const option = Array.from(els.vehiculoSelect.options).find(
            (opt) => String(opt.value) === vehiculoIdStr
        );

        if (option) {
            els.vehiculoSelect.value = vehiculoIdStr;
            els.vehiculoSelect.dispatchEvent(new Event('change', { bubbles: true }));
            console.log(`✅ Vehículo ${vehiculoIdStr} preseleccionado exitosamente`);
        } else {
            console.warn(`⚠️ Vehículo ${vehiculoIdStr} no encontrado en las opciones`);
            setTimeout(() => {
                const retryOption = Array.from(els.vehiculoSelect.options).find(
                    (opt) => String(opt.value) === vehiculoIdStr
                );
                if (retryOption) {
                    els.vehiculoSelect.value = vehiculoIdStr;
                    els.vehiculoSelect.dispatchEvent(new Event('change', { bubbles: true }));
                    console.log(`✅ Vehículo ${vehiculoIdStr} preseleccionado en reintento`);
                } else {
                    console.error(`❌ No se pudo preseleccionar vehículo ${vehiculoIdStr}`);
                }
            }, 500);
        }
    }

    /**
     * Actualiza la tarjeta de información del vehículo
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
     * Abre modal para crear nuevo vehículo
     */
    function openVehiculoModal() {
        try {
            const pathOnly = window.location.pathname || '/';
            const nextUrl = window.egEncodeDocumentFormNext?.() || encodeURIComponent(pathOnly);

            let countryPrefix = 'cl';
            let langPrefix = 'es';

            const pathParts = pathOnly.split('/').filter(function(part) {
                return part && part.length > 0;
            });

            if (pathParts.length > 0) {
                if (['es', 'en', 'pt'].indexOf(pathParts[0]) !== -1) {
                    langPrefix = pathParts[0];
                    countryPrefix = langPrefix === 'en' ? 'us' : (langPrefix === 'pt' ? 'br' : 'cl');
                } else {
                    countryPrefix = pathParts[0];
                    if (pathParts.length > 1 && ['es', 'en', 'pt'].indexOf(pathParts[1]) !== -1) {
                        langPrefix = pathParts[1];
                    }
                }
            }

            // Obtener cliente seleccionado
            let clienteId = '';
            const clienteSelect = document.getElementById('id_cliente');
            if (clienteSelect) {
                if (window.jQuery && jQuery(clienteSelect).hasClass('select2-hidden-accessible')) {
                    clienteId = jQuery(clienteSelect).val() || '';
                } else {
                    clienteId = clienteSelect.value || '';
                }
            }

            let createUrl = `/${countryPrefix}/${langPrefix}/vehiculos/crear/?next=${nextUrl}`;
            if (clienteId) {
                createUrl += `&cliente_id=${encodeURIComponent(clienteId)}`;
            }

            console.log('🚗 Abriendo modal de vehículo:', createUrl);
            window.location.href = createUrl;
        } catch (error) {
            console.error('❌ Error al abrir modal de vehículo:', error);
            alert('Error al abrir la página de crear vehículo.');
        }
    }

    /**
     * Inicializar eventos
     */
    function init() {
        const els = getElements();

        // Evento change en select de vehículo
        els.vehiculoSelect?.addEventListener('change', updateVehiculoCard);

        // Actualizar tarjeta inicialmente
        updateVehiculoCard();

        // Botón nuevo vehículo
        const btnNuevoVehiculo = document.getElementById('btn-nuevo-vehiculo');
        if (btnNuevoVehiculo) {
            btnNuevoVehiculo.addEventListener('click', openVehiculoModal);
        }

        console.log('🚗 Vehiculo module initialized');
    }

    // Exports
    EG.vehiculo = {
        cargarVehiculosPorCliente,
        preseleccionarVehiculo,
        updateVehiculoCard,
        openVehiculoModal,
        init
    };

})();
