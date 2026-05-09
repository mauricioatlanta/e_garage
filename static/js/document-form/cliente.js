/**
 * cliente.js - Modulo de busqueda y seleccion de clientes
 */

(function() {
    'use strict';

    var EG = window.EG = window.EG || {};
    var elements = {};

    function getElements() {
        if (!elements.clienteBusqueda) {
            elements.clienteBusqueda = document.getElementById('cliente-busqueda');
        }
        if (!elements.clienteResultados) {
            elements.clienteResultados = document.getElementById('cliente-resultados');
        }
        if (!elements.clienteSelect) {
            elements.clienteSelect = document.getElementById('id_cliente');
        }
        if (!elements.clienteInfoBox) {
            elements.clienteInfoBox = document.getElementById('cliente-info');
        }
        if (!elements.cliNombre) {
            elements.cliNombre = document.getElementById('cliente-nombre');
        }
        if (!elements.cliEmail) {
            elements.cliEmail = document.getElementById('cliente-email');
        }
        if (!elements.cliFono) {
            elements.cliFono = document.getElementById('cliente-telefono');
        }
        if (!elements.ultimaVisitaEl) {
            elements.ultimaVisitaEl = document.getElementById('cliente-ultima-visita');
        }
        return elements;
    }

    function ensureClienteOption(id, label) {
        var els = getElements();
        if (!els.clienteSelect || !id) {
            return;
        }

        var option = els.clienteSelect.querySelector('option[value="' + id + '"]');
        if (!option) {
            option = new Option(label || ('Cliente #' + id), id, true, true);
            els.clienteSelect.appendChild(option);
        } else if (label) {
            option.textContent = label;
        }
    }

    function updateClienteCard(data) {
        var els = getElements();
        if (els.cliNombre) els.cliNombre.textContent = data.nombre || '';
        if (els.cliEmail) els.cliEmail.textContent = data.email ? 'Email: ' + data.email : '-';
        if (els.cliFono) els.cliFono.textContent = data.telefono ? 'Tel: ' + data.telefono : '-';
        if (els.ultimaVisitaEl) els.ultimaVisitaEl.textContent = data.meta || '';
        if (els.clienteInfoBox) {
            els.clienteInfoBox.classList.toggle('hidden', !data.id);
        }
    }

    function clearSelection() {
        var els = getElements();
        if (els.clienteBusqueda) els.clienteBusqueda.value = '';
        if (els.clienteResultados) els.clienteResultados.classList.add('hidden');
        if (els.clienteSelect) {
            els.clienteSelect.innerHTML = '<option value="">Select client...</option>';
            els.clienteSelect.value = '';
            els.clienteSelect.dispatchEvent(new Event('change', { bubbles: true }));
        }
        updateClienteCard({});
        if (EG.vehiculo && EG.vehiculo.resetSelection) {
            EG.vehiculo.resetSelection();
        }
    }

    function getSelectedClienteId() {
        var els = getElements();
        if (!els.clienteSelect) {
            return '';
        }
        if (window.jQuery && jQuery(els.clienteSelect).hasClass('select2-hidden-accessible')) {
            return jQuery(els.clienteSelect).val() || '';
        }
        return els.clienteSelect.value || '';
    }

    function resolveClientDataById(id, fallbackLabel) {
        var clientId = String(id || '').trim();
        var label = fallbackLabel || '';
        var email = '';
        var telefono = '';

        if (!clientId) {
            return null;
        }

        var prefetch = (EG.PREFETCH && EG.PREFETCH.clientes) || [];
        var match = prefetch.find(function(item) {
            return String(item && (item.id || item.pk || '')) === clientId;
        });

        if (match) {
            label = label
                || match.text
                || match.nombre_completo
                || [match.nombre, match.apellido].filter(Boolean).join(' ').trim()
                || match.razon_social
                || ('Cliente #' + clientId);
            email = match.email || '';
            telefono = match.telefono || match.fono || '';
        }

        if (!label) {
            var els = getElements();
            if (els.clienteSelect) {
                var option = els.clienteSelect.querySelector('option[value="' + clientId + '"]');
                if (option && option.textContent) {
                    label = option.textContent.trim();
                }
            }
        }

        return {
            id: clientId,
            nombre: label || ('Cliente #' + clientId),
            email: email,
            telefono: telefono,
        };
    }

    function extractClientes(data) {
        var items = EG.utils.extractResponseItems(data, ['results', 'items', 'clientes']);
        if (!items.length && Array.isArray(data)) {
            items = data;
        }
        return items;
    }

    async function buscarClientes(q) {
        var els = getElements();
        if (!els.clienteResultados) {
            return;
        }
        if (!q || q.length < 2) {
            els.clienteResultados.classList.add('hidden');
            return;
        }

        var localMatches = EG.utils.filterPrefetchItems(
            (EG.PREFETCH || {}).clientes || [],
            ['nombre', 'apellido', 'nombre_completo', 'email', 'telefono', 'tax_id', 'razon_social', 'text'],
            q,
            15
        );
        if (localMatches.length) {
            renderResultadosClientes(localMatches);
        }

        try {
            var url = EG.config.buildEndpoint(EG.cfg.URL_CLIENT_SEARCH || '/ajax/clientes/buscar/');
            var response = await EG.utils.egFetch(url + '?q=' + encodeURIComponent(q));
            if (!response.ok) {
                throw new Error('HTTP ' + response.status);
            }
            var data = await response.json();
            renderResultadosClientes(extractClientes(data));
        } catch (err) {
            console.error('buscarClientes', err);
            if (!localMatches.length) {
                els.clienteResultados.innerHTML = '<div class="p-3 text-red-400">Error cargando clientes</div>';
                els.clienteResultados.classList.remove('hidden');
            }
        }
    }

    function renderResultadosClientes(lista) {
        var els = getElements();
        if (!els.clienteResultados) {
            return;
        }

        els.clienteResultados.innerHTML = '';
        if (!lista || !lista.length) {
            els.clienteResultados.innerHTML = '<div class="p-3 text-gray-300">' + (EG.I18N.no_clients || 'Sin clientes') + '</div>';
            els.clienteResultados.classList.remove('hidden');
            return;
        }

        lista.forEach(function(item) {
            var id = item.id || item.pk || '';
            var nombre = item.text || item.nombre_completo || [item.nombre, item.apellido].filter(Boolean).join(' ').trim() || item.razon_social || ('Cliente #' + id);
            var email = item.email || '';
            var telefono = item.telefono || item.fono || '';

            var div = document.createElement('div');
            div.className = 'cliente-item p-3 hover:bg-cyan-700 cursor-pointer border-b border-cyan-600 last:border-b-0';
            div.dataset.id = id;
            div.dataset.nombre = nombre;
            div.dataset.email = email;
            div.dataset.telefono = telefono;
            div.tabIndex = 0;
            div.innerHTML = '<div class="font-semibold text-cyan-200">' + nombre + '</div>'
                + (email ? '<div class="text-sm text-gray-300">' + email + '</div>' : '')
                + (telefono ? '<div class="text-sm text-gray-300">' + telefono + '</div>' : '');
            els.clienteResultados.appendChild(div);
        });

        els.clienteResultados.classList.remove('hidden');
    }

    async function seleccionarCliente(data, options) {
        options = options || {};
        var els = getElements();
        var id = data && data.id ? String(data.id) : '';
        var nombre = (data && data.nombre) || ('Cliente #' + id);
        var email = (data && data.email) || '';
        var telefono = (data && data.telefono) || '';

        ensureClienteOption(id, nombre);

        if (els.clienteBusqueda) {
            els.clienteBusqueda.value = nombre;
        }
        if (els.clienteResultados) {
            els.clienteResultados.classList.add('hidden');
        }
        try {
            if (els.clienteSelect) {
                els.clienteSelect.dataset.egInternalChange = '1';
                if (options.vehiculoId) {
                    els.clienteSelect.dataset.pendingVehiculoId = String(options.vehiculoId);
                } else {
                    delete els.clienteSelect.dataset.pendingVehiculoId;
                }
                els.clienteSelect.value = id;
                els.clienteSelect.dispatchEvent(new Event('change', { bubbles: true }));
            }
            if (window.jQuery && els.clienteSelect && jQuery(els.clienteSelect).hasClass('select2-hidden-accessible')) {
                jQuery(els.clienteSelect).val(id).trigger('change');
            }

            updateClienteCard({
                id: id,
                nombre: nombre,
                email: email,
                telefono: telefono,
                meta: data && data.meta ? data.meta : ''
            });

            document.dispatchEvent(new CustomEvent('cliente:seleccionado', {
                detail: { id: id, nombre: nombre, email: email, telefono: telefono }
            }));

            if (EG.vehiculo && EG.vehiculo.cargarVehiculosPorCliente) {
                await EG.vehiculo.cargarVehiculosPorCliente(id, options.vehiculoId || null);
            }
        } finally {
            if (els.clienteSelect) {
                delete els.clienteSelect.dataset.egInternalChange;
                delete els.clienteSelect.dataset.pendingVehiculoId;
            }
        }
    }

    async function handleClienteSelectChange() {
        var els = getElements();
        if (!els.clienteSelect) {
            return;
        }

        if (els.clienteSelect.dataset.egInternalChange === '1') {
            return;
        }

        var selectedId = getSelectedClienteId();
        if (!selectedId) {
            updateClienteCard({});
            if (els.clienteBusqueda) {
                els.clienteBusqueda.value = '';
            }
            if (EG.vehiculo && EG.vehiculo.resetSelection) {
                EG.vehiculo.resetSelection();
            }
            return;
        }

        var option = els.clienteSelect.options[els.clienteSelect.selectedIndex];
        var selectedLabel = option && option.textContent ? option.textContent.trim() : '';
        var clientData = resolveClientDataById(selectedId, selectedLabel) || {
            id: selectedId,
            nombre: selectedLabel || ('Cliente #' + selectedId),
            email: '',
            telefono: '',
        };

        if (els.clienteBusqueda && clientData.nombre) {
            els.clienteBusqueda.value = clientData.nombre;
        }

        updateClienteCard({
            id: clientData.id,
            nombre: clientData.nombre,
            email: clientData.email,
            telefono: clientData.telefono,
            meta: clientData.meta || ''
        });

        var pendingVehiculoId = els.clienteSelect.dataset.pendingVehiculoId || null;
        delete els.clienteSelect.dataset.pendingVehiculoId;

        if (EG.vehiculo && EG.vehiculo.cargarVehiculosPorCliente) {
            await EG.vehiculo.cargarVehiculosPorCliente(selectedId, pendingVehiculoId);
        }
    }

    function handleClienteInput(value) {
        clearTimeout(window._clienteSearchTimer);
        var query = (value || '').trim();
        if (query.length < 2) {
            var els = getElements();
            if (els.clienteResultados) {
                els.clienteResultados.classList.add('hidden');
            }
            return;
        }
        window._clienteSearchTimer = setTimeout(function() {
            buscarClientes(query);
        }, 200);
    }

    function handleClienteFocus(value) {
        var query = (value || '').trim();
        if (query.length >= 2) {
            buscarClientes(query);
        }
    }

    function handleClienteKeydown(event) {
        var els = getElements();
        if (!els.clienteResultados || els.clienteResultados.classList.contains('hidden')) {
            return true;
        }

        var items = Array.from(els.clienteResultados.querySelectorAll('.cliente-item'));
        if (!items.length) {
            return true;
        }

        var currentIndex = items.findIndex(function(item) {
            return item === document.activeElement;
        });

        if (event.key === 'ArrowDown') {
            event.preventDefault();
            items[(currentIndex + 1 + items.length) % items.length].focus();
            return false;
        }

        if (event.key === 'ArrowUp') {
            event.preventDefault();
            items[(currentIndex - 1 + items.length) % items.length].focus();
            return false;
        }

        if (event.key === 'Enter') {
            event.preventDefault();
            var target = currentIndex >= 0 ? items[currentIndex] : items[0];
            if (target) {
                seleccionarCliente({
                    id: target.dataset.id,
                    nombre: target.dataset.nombre,
                    email: target.dataset.email,
                    telefono: target.dataset.telefono
                });
            }
            return false;
        }

        if (event.key === 'Escape') {
            event.preventDefault();
            els.clienteResultados.classList.add('hidden');
            return false;
        }

        return true;
    }

    async function handleCreatedClienteFromReturn(context) {
        var id = context.created_cliente_id || context.cliente_id || '';
        if (!id) {
            return;
        }

        var resolvedClient = resolveClientDataById(id, context.created_cliente_label || '') || {
            id: id,
            nombre: context.created_cliente_label || ('Cliente #' + id),
            email: '',
            telefono: '',
        };
        ensureClienteOption(id, resolvedClient.nombre);

        await seleccionarCliente({
            id: id,
            nombre: resolvedClient.nombre,
            email: resolvedClient.email,
            telefono: resolvedClient.telefono
        }, {
            vehiculoId: context.created_vehiculo_id || context.vehiculo_id || null
        });
    }

    function init() {
        var els = getElements();
        if (!els.clienteBusqueda || els.clienteBusqueda.dataset.egBound) {
            return;
        }

        els.clienteBusqueda.dataset.egBound = '1';
        els.clienteBusqueda.addEventListener('input', function(event) {
            handleClienteInput(event.target.value);
        });
        els.clienteBusqueda.addEventListener('focus', function(event) {
            handleClienteFocus(event.target.value);
        });
        els.clienteBusqueda.addEventListener('keydown', handleClienteKeydown);

        if (els.clienteResultados) {
            els.clienteResultados.addEventListener('click', function(event) {
                var item = event.target.closest('.cliente-item');
                if (!item) {
                    return;
                }
                seleccionarCliente({
                    id: item.dataset.id,
                    nombre: item.dataset.nombre,
                    email: item.dataset.email,
                    telefono: item.dataset.telefono
                });
            });
        }

        if (els.clienteSelect && !els.clienteSelect.dataset.egSelectBound) {
            els.clienteSelect.dataset.egSelectBound = '1';
            els.clienteSelect.addEventListener('change', function() {
                handleClienteSelectChange().catch(function(err) {
                    console.error('handleClienteSelectChange', err);
                });
            });
        }

        document.addEventListener('click', function(event) {
            if (els.clienteResultados && els.clienteBusqueda && !els.clienteResultados.contains(event.target) && event.target !== els.clienteBusqueda) {
                els.clienteResultados.classList.add('hidden');
            }
        });

        var bootstrap = EG.state && EG.state.getBootstrap ? EG.state.getBootstrap() : {};
        if (bootstrap.cliente && bootstrap.cliente.id) {
            setTimeout(function() {
                seleccionarCliente(bootstrap.cliente, { vehiculoId: bootstrap.vehiculo_id || '' });
            }, 50);
        } else if (getSelectedClienteId()) {
            setTimeout(function() {
                handleClienteSelectChange().catch(function(err) {
                    console.error('handleClienteSelectChange:init', err);
                });
            }, 50);
        }
    }

    EG.cliente = {
        buscarClientes: buscarClientes,
        clearSelection: clearSelection,
        getSelectedClienteId: getSelectedClienteId,
        seleccionarCliente: seleccionarCliente,
        handleClienteInput: handleClienteInput,
        handleClienteFocus: handleClienteFocus,
        handleClienteKeydown: handleClienteKeydown,
        handleCreatedClienteFromReturn: handleCreatedClienteFromReturn,
        init: init
    };
})();
