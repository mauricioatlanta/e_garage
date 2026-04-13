/**
 * vehiculo.js - Modulo de gestion de vehiculos
 */

(function() {
    'use strict';

    var EG = window.EG = window.EG || {};
    var elements = {};

    function getElements() {
        if (!elements.vehiculoSelect) {
            elements.vehiculoSelect = document.getElementById('id_vehiculo');
        }
        if (!elements.vehiculoInfoBox) {
            elements.vehiculoInfoBox = document.getElementById('vehiculo-info');
        }
        if (!elements.marcaModeloEl) {
            elements.marcaModeloEl = document.getElementById('vehiculo-marca-modelo');
        }
        if (!elements.anoVinEl) {
            elements.anoVinEl = document.getElementById('vehiculo-ano-vin');
        }
        if (!elements.mileageEl) {
            elements.mileageEl = document.getElementById('vehiculo-mileage');
        }
        if (!elements.ultimaEntradaEl) {
            elements.ultimaEntradaEl = document.getElementById('vehiculo-ultima-entrada');
        }
        return elements;
    }

    function normalizeVehicleItem(item) {
        var vehicle = item || {};
        var id = vehicle.id || vehicle.pk || '';
        var patente = vehicle.patente || vehicle.placa || vehicle.plate || '';
        var marca = vehicle.marca || vehicle.brand || vehicle.make || '';
        var modelo = vehicle.modelo || vehicle.model || '';
        var anio = vehicle.anio || vehicle.year || '';
        var vin = vehicle.vin || vehicle.chassis || '';
        var label = vehicle.text
            || vehicle.label
            || vehicle.display_label
            || [patente, marca, modelo].filter(Boolean).join(' - ')
            || ('Vehiculo #' + id);

        return {
            id: id ? String(id) : '',
            label: label,
            patente: patente,
            marca: marca,
            modelo: modelo,
            anio: anio,
            vin: vin,
            mileage: vehicle.kilometraje || vehicle.mileage || '',
            meta: vehicle.meta || vehicle.ultima_entrada || vehicle.last_visit || '',
        };
    }

    function extractVehicleItems(data) {
        var items = EG.utils.extractResponseItems(data, ['results', 'items', 'vehiculos']);
        if (!items.length && Array.isArray(data)) {
            items = data;
        }
        return items;
    }

    function ensureVehicleOption(id, label, rawItem) {
        var els = getElements();
        if (!els.vehiculoSelect || !id) {
            return null;
        }

        var item = normalizeVehicleItem(rawItem || { id: id, label: label });
        item.label = label || item.label;

        var option = els.vehiculoSelect.querySelector('option[value="' + id + '"]');
        if (!option) {
            option = new Option(item.label || ('Vehiculo #' + id), id, false, false);
            els.vehiculoSelect.appendChild(option);
        } else if (item.label) {
            option.textContent = item.label;
        }

        option.dataset.label = item.label || '';
        option.dataset.patente = item.patente || '';
        option.dataset.marca = item.marca || '';
        option.dataset.modelo = item.modelo || '';
        option.dataset.anio = item.anio || '';
        option.dataset.vin = item.vin || '';
        option.dataset.mileage = item.mileage || '';
        option.dataset.meta = item.meta || '';
        return option;
    }

    function setVehicleOptions(items, selectedId, preferredLabel) {
        var els = getElements();
        if (!els.vehiculoSelect) {
            return;
        }

        els.vehiculoSelect.innerHTML = '';
        els.vehiculoSelect.appendChild(new Option(EG.I18N.select_vehicle || 'Select vehicle...', '', false, false));

        (items || []).forEach(function(item) {
            var normalized = normalizeVehicleItem(item);
            ensureVehicleOption(normalized.id, normalized.label, normalized);
        });

        if (selectedId) {
            ensureVehicleOption(selectedId, preferredLabel || '', { id: selectedId, label: preferredLabel || '' });
            els.vehiculoSelect.value = String(selectedId);
        } else {
            els.vehiculoSelect.value = '';
        }
    }

    function resetSelection() {
        var els = getElements();
        if (els.vehiculoSelect) {
            els.vehiculoSelect.innerHTML = '';
            els.vehiculoSelect.appendChild(new Option(EG.I18N.select_vehicle || 'Select vehicle...', '', false, false));
            els.vehiculoSelect.value = '';
            els.vehiculoSelect.dataset.source = 'clean';
            els.vehiculoSelect.disabled = false;
        }
        if (els.marcaModeloEl) els.marcaModeloEl.textContent = '';
        if (els.anoVinEl) els.anoVinEl.textContent = '';
        if (els.mileageEl) els.mileageEl.textContent = '';
        if (els.ultimaEntradaEl) els.ultimaEntradaEl.textContent = '';
        if (els.vehiculoInfoBox) els.vehiculoInfoBox.classList.add('hidden');
    }

    function updateVehiculoCard(source) {
        var els = getElements();
        if (!els.vehiculoInfoBox || !els.vehiculoSelect) {
            return;
        }

        var item = null;
        if (source && typeof source === 'object' && source.id) {
            item = normalizeVehicleItem(source);
        } else {
            var option = els.vehiculoSelect.options[els.vehiculoSelect.selectedIndex];
            if (!option || !option.value) {
                els.vehiculoInfoBox.classList.add('hidden');
                return;
            }
            item = normalizeVehicleItem({
                id: option.value,
                label: option.dataset.label || option.textContent,
                patente: option.dataset.patente,
                marca: option.dataset.marca,
                modelo: option.dataset.modelo,
                anio: option.dataset.anio,
                vin: option.dataset.vin,
                mileage: option.dataset.mileage,
                meta: option.dataset.meta,
            });
        }

        if (!item || !item.id) {
            els.vehiculoInfoBox.classList.add('hidden');
            return;
        }

        if (els.marcaModeloEl) {
            els.marcaModeloEl.textContent = item.label || [item.patente, item.marca, item.modelo].filter(Boolean).join(' - ');
        }
        if (els.anoVinEl) {
            els.anoVinEl.textContent = [item.anio, item.vin].filter(Boolean).join(' | ');
        }
        if (els.mileageEl) {
            els.mileageEl.textContent = item.mileage || '';
        }
        if (els.ultimaEntradaEl) {
            els.ultimaEntradaEl.textContent = item.meta || '';
        }
        els.vehiculoInfoBox.classList.remove('hidden');

        document.dispatchEvent(new CustomEvent('vehiculo:seleccionado', {
            detail: {
                id: item.id,
                text: item.label || '',
                patente: item.patente || '',
                marca: item.marca || '',
                modelo: item.modelo || '',
            }
        }));
    }

    async function cargarVehiculosPorCliente(clienteId, vehiculoIdToSelect, preferredLabel) {
        var els = getElements();
        if (!els.vehiculoSelect) {
            return;
        }

        var normalizedClienteId = String(clienteId || '').trim();
        if (!normalizedClienteId) {
            console.warn('No hay cliente seleccionado, limpiando vehiculos');
            resetSelection();
            return;
        }

        els.vehiculoSelect.disabled = true;
        els.vehiculoSelect.innerHTML = '<option value="">' + (EG.I18N.loading_vehicles || 'Loading vehicles...') + '</option>';

        try {
            var localMatches = ((EG.PREFETCH && EG.PREFETCH.vehiculos) || []).filter(function(item) {
                return String(item && item.cliente_id) === normalizedClienteId;
            });

            if (localMatches.length) {
                setVehicleOptions(localMatches, vehiculoIdToSelect, preferredLabel);
                els.vehiculoSelect.dataset.source = 'prefetch';
                els.vehiculoSelect.disabled = false;
                if (vehiculoIdToSelect) {
                    preseleccionarVehiculo(vehiculoIdToSelect, preferredLabel);
                }
                return;
            }

            var urlRaw = EG.cfg.URL_VEHICULOS_BY_CLI || '/ajax/vehiculos-por-cliente/';
            var url = EG.config.buildEndpoint(urlRaw);
            var response = await EG.utils.egFetch(url + '?cliente_id=' + encodeURIComponent(normalizedClienteId));
            if (!response.ok) {
                throw new Error('HTTP ' + response.status);
            }

            var data = await response.json();
            var items = extractVehicleItems(data);
            if (!items.length) {
                setVehicleOptions([], '', '');
                els.vehiculoSelect.options[0].textContent = EG.I18N.no_vehicles || 'No vehicles registered';
                els.vehiculoSelect.dataset.source = 'empty';
                return;
            }

            setVehicleOptions(items, vehiculoIdToSelect, preferredLabel);
            els.vehiculoSelect.dataset.source = 'fetch';
            if (vehiculoIdToSelect) {
                preseleccionarVehiculo(vehiculoIdToSelect, preferredLabel);
            }
        } catch (err) {
            console.error('Error cargando vehiculos', err);
            els.vehiculoSelect.innerHTML = '<option value="">' + (EG.I18N.no_vehicles || 'Sin vehiculos') + '</option>';
            els.vehiculoSelect.dataset.source = 'error';
        } finally {
            els.vehiculoSelect.disabled = false;
        }
    }

    function preseleccionarVehiculo(vehiculoId, label) {
        var els = getElements();
        if (!els.vehiculoSelect || !vehiculoId) {
            return;
        }

        ensureVehicleOption(String(vehiculoId), label || '', { id: vehiculoId, label: label || '' });
        els.vehiculoSelect.value = String(vehiculoId);
        els.vehiculoSelect.dispatchEvent(new Event('change', { bubbles: true }));
    }

    function getSelectedVehiculoId() {
        var els = getElements();
        return els.vehiculoSelect ? (els.vehiculoSelect.value || '') : '';
    }

    function openVehiculoModal() {
        var trigger = document.getElementById('btn-nuevo-vehiculo');
        var baseUrl = trigger && trigger.dataset ? trigger.dataset.urlCrearVehiculo : '';
        if (!baseUrl || !EG.utils || !EG.utils.buildContextualCreateUrl) {
            return;
        }

        var clienteId = EG.cliente && EG.cliente.getSelectedClienteId ? EG.cliente.getSelectedClienteId() : '';
        var url = EG.utils.buildContextualCreateUrl(baseUrl, {
            return_to: EG.utils.getDocumentReturnTo(),
            select_field: 'vehiculo',
            cliente_id: clienteId || '',
        });
        window.location.href = url;
    }

    async function handleCreatedVehiculoFromReturn(context) {
        var vehiculoId = context.created_vehiculo_id || context.vehiculo_id || '';
        if (!vehiculoId) {
            return;
        }

        var clienteId = context.cliente_id || (EG.cliente && EG.cliente.getSelectedClienteId ? EG.cliente.getSelectedClienteId() : '');
        var label = context.created_vehiculo_label || '';

        if (clienteId) {
            await cargarVehiculosPorCliente(clienteId, vehiculoId, label);
        }

        preseleccionarVehiculo(vehiculoId, label);
    }

    function init() {
        var els = getElements();
        if (!els.vehiculoSelect || els.vehiculoSelect.dataset.egBound) {
            return;
        }

        els.vehiculoSelect.dataset.egBound = '1';
        els.vehiculoSelect.addEventListener('change', function() {
            updateVehiculoCard();
        });

        var btnNuevoVehiculo = document.getElementById('btn-nuevo-vehiculo');
        if (btnNuevoVehiculo && !btnNuevoVehiculo.dataset.egBound) {
            btnNuevoVehiculo.dataset.egBound = '1';
            btnNuevoVehiculo.addEventListener('click', function(event) {
                event.preventDefault();
                openVehiculoModal();
            });
        }

        if (els.vehiculoSelect.value) {
            updateVehiculoCard();
        }
    }

    EG.vehiculo = {
        cargarVehiculosPorCliente: cargarVehiculosPorCliente,
        resetSelection: resetSelection,
        preseleccionarVehiculo: preseleccionarVehiculo,
        updateVehiculoCard: updateVehiculoCard,
        getSelectedVehiculoId: getSelectedVehiculoId,
        openVehiculoModal: openVehiculoModal,
        handleCreatedVehiculoFromReturn: handleCreatedVehiculoFromReturn,
        init: init
    };
})();
