/**
 * cliente.js - Módulo de búsqueda y selección de clientes
 * 
 * Extraído del código embebido en document_form.html
 */

(function() {
    'use strict';

    const EG = window.EG = window.EG || {};

    // Elementos del DOM (cacheados)
    let elements = {};

    /**
     * Obtiene referencias a elementos del DOM
     */
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

    /**
     * Busca clientes (local + AJAX)
     */
    async function buscarClientes(q) {
        const els = getElements();
        if (!q || q.length < 2) {
            els.clienteResultados?.classList.add('hidden');
            return;
        }
        if (!els.clienteResultados) return;

        // Primero buscar en prefetch local
        const localMatches = EG.utils.filterPrefetchItems(
            EG.PREFETCH.clientes,
            ['nombre', 'nombre_completo', 'email', 'telefono'],
            q,
            15
        );
        if (localMatches.length) {
            renderResultadosClientes(localMatches);
        }

        // Luego AJAX
        try {
            const url = EG.config.buildEndpoint(EG.cfg.URL_CLIENT_SEARCH || '/ajax/clientes/buscar/');
            const r = await EG.utils.egFetch(`${url}?q=${encodeURIComponent(q)}`);
            if (!r.ok) throw new Error(`HTTP ${r.status}`);
            const data = await r.json();
            const items = Array.isArray(data) ? data : (data.results || data.items || []);
            renderResultadosClientes(items);
        } catch (err) {
            console.error('❌ buscarClientes:', err);
            els.clienteResultados.innerHTML = `<div class="p-3 text-red-400">${EG.I18N.server_error}</div>`;
            els.clienteResultados.classList.remove('hidden');
        }
    }

    /**
     * Renderiza resultados en el dropdown
     */
    function renderResultadosClientes(lista) {
        const els = getElements();
        if (!els.clienteResultados) return;

        // Si ya hay cliente seleccionado, no mostrar
        if (els.clienteSelect && els.clienteSelect.value) {
            els.clienteResultados.classList.add('hidden');
            return;
        }

        els.clienteResultados.innerHTML = '';
        if (!lista.length) {
            const empty = document.createElement('div');
            empty.className = 'p-3 text-gray-300';
            empty.textContent = EG.I18N.no_clients;
            els.clienteResultados.appendChild(empty);
            els.clienteResultados.classList.remove('hidden');
            return;
        }

        lista.forEach(item => {
            const id = item.id || item.pk || '';
            const nombre = item.text || item.nombre_completo || item.nombre || item.razon_social || `Client #${id}`;
            const email = item.email || '';
            const fono = item.telefono || item.fono || '';

            const div = document.createElement('div');
            div.className = 'cliente-item p-3 hover:bg-cyan-700 cursor-pointer border-b border-cyan-600 last:border-b-0';
            div.setAttribute('role', 'option');
            div.tabIndex = 0;
            div.dataset.id = id;
            div.dataset.nombre = nombre;
            div.dataset.email = email;
            div.dataset.telefono = fono;

            const title = document.createElement('div');
            title.className = 'font-semibold text-cyan-200';
            title.textContent = nombre;
            div.appendChild(title);

            if (email) {
                const em = document.createElement('div');
                em.className = 'text-sm text-gray-300';
                em.textContent = `📧 ${email}`;
                div.appendChild(em);
            }
            if (fono) {
                const ph = document.createElement('div');
                ph.className = 'text-sm text-gray-300';
                ph.textContent = `📞 ${fono}`;
                div.appendChild(ph);
            }

            div.addEventListener('click', () => seleccionarCliente({ id, nombre, email, telefono: fono }));
            els.clienteResultados.appendChild(div);
        });

        els.clienteResultados.setAttribute('role', 'listbox');
        els.clienteResultados.classList.remove('hidden');
    }

    /**
     * Selecciona un cliente y carga sus vehículos
     */
    async function seleccionarCliente({ id, nombre, email, telefono }) {
        console.log(`👤 Cliente seleccionado: ${nombre} (ID: ${id})`);

        const els = getElements();
        els.clienteResultados?.classList.add('hidden');
        if (els.clienteBusqueda) els.clienteBusqueda.value = nombre;

        if (els.clienteSelect) {
            els.clienteSelect.innerHTML = `<option value="${id}" selected>${nombre}</option>`;
            els.clienteSelect.classList.add('hidden');
        }

        if (els.cliNombre) els.cliNombre.textContent = nombre;
        if (els.cliEmail) els.cliEmail.textContent = email ? `📧 ${email}` : '—';
        if (els.cliFono) els.cliFono.textContent = telefono ? `📞 ${telefono}` : '—';
        if (els.ultimaVisitaEl) els.ultimaVisitaEl.textContent = '';
        if (els.clienteInfoBox) els.clienteInfoBox.classList.remove('hidden');

        // Emitir evento para que otros módulos reaccionen
        document.dispatchEvent(new CustomEvent('cliente:seleccionado', {
            detail: { id, nombre, email, telefono }
        }));

        // Cargar vehículos del cliente
        await EG.vehiculo.cargarVehiculosPorCliente(id);
    }

    /**
     * Manejador de input en búsqueda
     */
    function handleClienteInput(value) {
        const els = getElements();
        const query = (value ?? els.clienteBusqueda?.value ?? '').trim();
        clearTimeout(window._clienteSearchTimer);
        if (query.length < 2) {
            els.clienteResultados?.classList.add('hidden');
            return;
        }
        window._clienteSearchTimer = setTimeout(() => buscarClientes(query), 200);
    }

    /**
     * Manejador de focus en búsqueda
     */
    function handleClienteFocus(value) {
        const els = getElements();
        const query = (value ?? els.clienteBusqueda?.value ?? '').trim();
        if (query.length >= 2) buscarClientes(query);
    }

    /**
     * Manejador de teclado en búsqueda
     */
    function handleClienteKeydown(event) {
        const els = getElements();
        const query = els.clienteBusqueda?.value?.trim() || '';

        if (event.key === 'ArrowDown' && query.length >= 2 && (els.clienteResultados?.classList.contains('hidden') ?? true)) {
            event.preventDefault();
            buscarClientes(query);
            return false;
        }

        if (!els.clienteResultados || els.clienteResultados.classList.contains('hidden')) {
            return true;
        }

        const items = Array.from(els.clienteResultados.querySelectorAll('.cliente-item'));
        if (!items.length) return true;

        const active = document.activeElement;
        const currentIndex = items.findIndex(el => el === active);

        if (event.key === 'ArrowDown') {
            event.preventDefault();
            const nextIndex = currentIndex >= 0 ? (currentIndex + 1) % items.length : 0;
            items[nextIndex].focus();
            return false;
        }

        if (event.key === 'ArrowUp') {
            event.preventDefault();
            const prevIndex = currentIndex >= 0 ? (currentIndex - 1 + items.length) % items.length : items.length - 1;
            items[prevIndex].focus();
            return false;
        }

        if (event.key === 'Enter') {
            event.preventDefault();
            const target = active?.classList.contains('cliente-item') ? active : items[0];
            if (target) {
                seleccionarCliente({
                    id: target.dataset.id,
                    nombre: target.dataset.nombre,
                    email: target.dataset.email,
                    telefono: target.dataset.telefono,
                });
                els.clienteBusqueda?.focus();
            }
            return false;
        }

        if (event.key === 'Escape') {
            event.preventDefault();
            els.clienteResultados.classList.add('hidden');
            els.clienteBusqueda?.focus();
            return false;
        }

        return true;
    }

    /**
     * Inicializar eventos de búsqueda
     */
    function init() {
        const els = getElements();

        // Event listeners en el campo de búsqueda
        els.clienteBusqueda?.addEventListener('input', (e) => handleClienteInput(e.target.value));
        els.clienteBusqueda?.addEventListener('focus', (e) => handleClienteFocus(e.target.value));
        els.clienteBusqueda?.addEventListener('keydown', handleClienteKeydown);

        // Click en resultados
        els.clienteResultados?.addEventListener('click', (e) => {
            const item = e.target.closest('.cliente-item');
            if (!item) return;
            seleccionarCliente({
                id: item.dataset.id,
                nombre: item.dataset.nombre,
                email: item.dataset.email,
                telefono: item.dataset.telefono,
            });
            els.clienteBusqueda?.focus();
        });

        // Preselección desde URL o template
        const urlParams = new URLSearchParams(window.location.search);
        const preselectClienteId = window.__PRESELECT_CLIENTE_ID__ || urlParams.get('cliente_id');

        if (preselectClienteId && typeof seleccionarCliente === 'function') {
            const nombre = urlParams.get('cliente_nombre') || `Cliente #${preselectClienteId}`;
            setTimeout(() => {
                seleccionarCliente({
                    id: preselectClienteId,
                    nombre,
                    email: '',
                    telefono: ''
                });
            }, 100);
        }

        console.log('👤 Cliente module initialized');
    }

    // Exports
    EG.cliente = {
        buscarClientes,
        seleccionarCliente,
        handleClienteInput,
        handleClienteFocus,
        handleClienteKeydown,
        init
    };

})();
