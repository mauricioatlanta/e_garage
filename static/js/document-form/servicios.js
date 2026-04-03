/**
 * servicios.js - Modulo de gestion de servicios y otros servicios
 */

(function() {
    'use strict';

    var EG = window.EG = window.EG || {};

    function toggleEmptyHint(containerId, hintId) {
        var container = document.getElementById(containerId);
        var hint = document.getElementById(hintId);
        if (!container || !hint) return;
        hint.classList.toggle('hidden', !!container.querySelector('.dynamic-element'));
    }

    function removeDynamicRow(row, containerId, hintId) {
        if (row) row.remove();
        toggleEmptyHint(containerId, hintId);
        if (typeof window.recalcTotales === 'function') {
            window.recalcTotales();
        }
    }

    function buildDropdownItem(item, text, meta) {
        return '<div class="srv-item px-3 py-2 hover:bg-cyan-700 cursor-pointer border-b border-cyan-600" ' +
            'data-id="' + (item.id || item.pk || '') + '" ' +
            'data-name="' + (text || '') + '" ' +
            'data-price="' + (item.precio || item.precio_venta || item.precio_cliente || 0) + '" ' +
            'data-company="' + (item.empresa || item.empresa_ext || item.proveedor || '') + '" ' +
            'data-shop-price="' + (item.precio_taller || item.costo || 0) + '">' +
            '<div class="text-cyan-200 font-semibold">' + text + '</div>' +
            (meta ? '<div class="text-xs text-gray-300">' + meta + '</div>' : '') +
            '</div>';
    }

    function normalizeServicioItem(item) {
        var normalized = EG.utils.normalizeServicio(item || {}) || {};
        normalized.nombre = normalized.nombre || normalized.name || normalized.descripcion || normalized.label || '';
        normalized.precio = normalized.precio !== undefined ? normalized.precio :
            (normalized.precio_venta !== undefined ? normalized.precio_venta :
            (normalized.precio_cliente !== undefined ? normalized.precio_cliente : 0));
        normalized.empresa = normalized.empresa || normalized.empresa_ext || normalized.proveedor || '';
        normalized.precio_taller = normalized.precio_taller !== undefined ? normalized.precio_taller :
            (normalized.costo !== undefined ? normalized.costo : 0);
        return normalized;
    }

    function bindMoneyField(inputEl, subtotalEl, subtotalViewEl) {
        function recalc() {
            var value = EG.utils.parseNumericInput(inputEl && inputEl.value || 0);
            if (subtotalEl) subtotalEl.value = value;
            if (subtotalViewEl) subtotalViewEl.textContent = EG.utils.money(value);
            if (typeof window.recalcTotales === 'function') {
                window.recalcTotales();
            }
        }

        if (inputEl && !inputEl.dataset.egMoneyBound) {
            inputEl.dataset.egMoneyBound = '1';
            inputEl.addEventListener('input', recalc);
            inputEl.addEventListener('change', recalc);
        }

        recalc();
    }

    function renderResults(dropdown, list, renderer) {
        if (!dropdown) return;
        if (!list.length) {
            dropdown.innerHTML = '<div class="p-3 text-gray-300">' + (EG.I18N.no_results || 'Sin resultados') + '</div>';
            dropdown.classList.remove('hidden');
            return;
        }
        dropdown.innerHTML = list.map(renderer).join('');
        dropdown.classList.remove('hidden');
    }

    async function searchWithFallback(options) {
        var localResults = EG.utils.filterPrefetchItems(options.prefetch || [], options.fields || ['nombre'], options.query, 15)
            .map(normalizeServicioItem);

        if (localResults.length) {
            options.onResults(localResults);
        }

        if (!options.url) {
            if (!localResults.length) {
                options.onResults([]);
            }
            return;
        }

        try {
            var response = await EG.utils.egFetch(options.url + '?q=' + encodeURIComponent(options.query));
            if (!response.ok) throw new Error('HTTP ' + response.status);
            var data = await response.json();
            var items = Array.isArray(data) ? data : (data.results || data.items || []);
            var normalizedItems = items.map(normalizeServicioItem);
            if (normalizedItems.length || !localResults.length) {
                options.onResults(normalizedItems);
            }
        } catch (err) {
            console.error('searchWithFallback', err);
            if (!localResults.length) {
                options.onResults([]);
            }
        }
    }

    function addServicioRow() {
        var container = document.getElementById('servicios-container');
        if (!container) {
            console.error('Contenedor de servicios no encontrado');
            return null;
        }

        var row = document.createElement('div');
        row.className = 'dynamic-element';
        row.innerHTML =
            '<div class="doc-row-grid grid grid-cols-12 gap-2 items-center border border-cyan-400/30 rounded-lg p-2 sm:p-3 bg-black/20">' +
                '<div class="col-span-7 sm:col-span-7 description-field srv-input-container relative min-w-0">' +
                    '<label class="block text-cyan-200 text-sm mb-1">' + (EG.I18N.service || 'Service') + '</label>' +
                    '<input type="text" class="srv-input form-control w-full h-10 text-sm flex-1 min-w-0" placeholder="' + (EG.I18N.type_to_search_services || EG.I18N.service || 'Service') + '" autocomplete="off">' +
                    '<div class="srv-dropdown absolute z-50 w-full bg-gray-800 border border-cyan-400 rounded-lg shadow-lg hidden max-h-60 overflow-y-auto"></div>' +
                    '<input type="hidden" class="srv-id">' +
                '</div>' +
                '<div class="col-span-2 sm:col-span-2 min-w-0">' +
                    '<label class="block text-cyan-200 text-sm mb-1">' + (EG.I18N.client_price || 'Price') + '</label>' +
                    '<div class="relative"><span class="absolute left-2 top-1/2 -translate-y-1/2 text-cyan-300 font-semibold">$</span>' +
                    '<input type="text" class="serv-precio form-control w-full h-10 text-sm pl-6" placeholder="0"></div>' +
                '</div>' +
                '<div class="col-span-2 sm:col-span-2 min-w-0">' +
                    '<label class="block text-cyan-200 text-sm mb-1">' + (EG.I18N.subtotal || 'Subtotal') + '</label>' +
                    '<input type="hidden" class="serv-subtotal" value="0">' +
                    '<div class="serv-subtotal-view subtotal-field w-full h-10 text-right font-bold form-control text-sm flex items-center justify-end">$0</div>' +
                '</div>' +
                '<div class="col-span-1 sm:col-span-1">' +
                    '<button type="button" class="btn-add w-full h-10 srv-remove-btn">X</button>' +
                '</div>' +
            '</div>';

        container.appendChild(row);
        setupServicioRow(row);
        toggleEmptyHint('servicios-container', 'servicios-empty-hint');
        return row;
    }

    function setupServicioRow(row) {
        if (!row || row.dataset.egInitServicio) return;
        row.dataset.egInitServicio = '1';

        var inputEl = row.querySelector('.srv-input');
        var idEl = row.querySelector('.srv-id');
        var priceEl = row.querySelector('.serv-precio');
        var subtotalEl = row.querySelector('.serv-subtotal');
        var subtotalViewEl = row.querySelector('.serv-subtotal-view');
        var removeBtn = row.querySelector('.srv-remove-btn');
        var dropdown = row.querySelector('.srv-dropdown');
        var searchTimer = null;

        function applyItem(data) {
            var item = normalizeServicioItem(data);
            if (idEl) idEl.value = item.id || '';
            if (inputEl) inputEl.value = item.nombre || '';
            if (priceEl) {
                var value = EG.utils.parseNumericInput(item.precio);
                priceEl.value = value ? EG.utils.formatNumberInput(value) : '';
                priceEl.dispatchEvent(new Event('input', { bubbles: true }));
            }
            if (dropdown) dropdown.classList.add('hidden');
        }

        bindMoneyField(priceEl, subtotalEl, subtotalViewEl);

        if (inputEl) {
            inputEl.addEventListener('input', function() {
                if (idEl) idEl.value = '';
                clearTimeout(searchTimer);
                var query = (inputEl.value || '').trim();
                if (query.length < 2) {
                    if (dropdown) dropdown.classList.add('hidden');
                    return;
                }
                searchTimer = setTimeout(function() {
                    searchWithFallback({
                        query: query,
                        url: EG.cfg.URL_SERVICE_SEARCH,
                        prefetch: EG.PREFETCH && EG.PREFETCH.servicios,
                        fields: ['codigo', 'nombre', 'descripcion'],
                        onResults: function(results) {
                            renderResults(dropdown, results, function(item) {
                                var meta = item.precio ? EG.utils.money(item.precio) : '';
                                return buildDropdownItem(item, item.nombre || '', meta);
                            });
                        }
                    });
                }, 250);
            });

            inputEl.addEventListener('focus', function() {
                if ((inputEl.value || '').trim().length >= 2) {
                    inputEl.dispatchEvent(new Event('input'));
                }
            });
        }

        if (dropdown) {
            dropdown.addEventListener('click', function(e) {
                var itemEl = e.target.closest('.srv-item');
                if (!itemEl) return;
                applyItem({
                    id: itemEl.dataset.id,
                    nombre: itemEl.dataset.name,
                    precio: itemEl.dataset.price
                });
            });
        }

        if (removeBtn) {
            removeBtn.addEventListener('click', function() {
                removeDynamicRow(row, 'servicios-container', 'servicios-empty-hint');
            });
        }

        document.addEventListener('click', function(e) {
            if (!row.contains(e.target) && dropdown) {
                dropdown.classList.add('hidden');
            }
        });

        row.__applyServData = function(data) {
            applyItem({
                id: data && (data.id || data.servicio_id),
                nombre: data && data.nombre,
                precio: data && data.precio
            });
        };
    }

    function addOtroServicioRow() {
        var container = document.getElementById('otros-container');
        if (!container) {
            console.error('Contenedor de otros servicios no encontrado');
            return null;
        }

        var row = document.createElement('div');
        row.className = 'dynamic-element';
        row.innerHTML =
            '<div class="doc-row-grid grid grid-cols-12 gap-2 items-center border border-cyan-400/30 rounded-lg p-2 sm:p-3 bg-black/20">' +
                '<div class="col-span-3 sm:col-span-3 description-field otr-search-container relative min-w-0">' +
                    '<label class="block text-cyan-200 text-sm mb-1">' + (EG.I18N.service || 'Service') + '</label>' +
                    '<input type="text" class="otr-search form-control w-full h-10 text-sm" placeholder="' + (EG.I18N.type_to_search_external || EG.I18N.service || 'Service') + '" autocomplete="off">' +
                    '<div class="otr-dropdown absolute z-50 w-full bg-gray-800 border border-cyan-400 rounded-lg shadow-lg hidden max-h-60 overflow-y-auto"></div>' +
                    '<input type="hidden" class="otr-servicio-id">' +
                '</div>' +
                '<div class="col-span-3 sm:col-span-3 min-w-0">' +
                    '<label class="block text-cyan-200 text-sm mb-1">' + (EG.I18N.external_company || 'External Company') + '</label>' +
                    '<input type="text" class="otr-empresa form-control w-full h-10 text-sm">' +
                '</div>' +
                '<div class="col-span-2 sm:col-span-2 min-w-0">' +
                    '<label class="block text-cyan-200 text-sm mb-1">' + (EG.I18N.shop_price || 'Shop Price') + '</label>' +
                    '<div class="relative"><span class="absolute left-2 top-1/2 -translate-y-1/2 text-cyan-300 font-semibold">$</span>' +
                    '<input type="text" class="otr-precio-taller form-control w-full h-10 text-sm pl-6" placeholder="0"></div>' +
                '</div>' +
                '<div class="col-span-2 sm:col-span-2 min-w-0">' +
                    '<label class="block text-cyan-200 text-sm mb-1">' + (EG.I18N.client_price || 'Client Price') + '</label>' +
                    '<div class="relative"><span class="absolute left-2 top-1/2 -translate-y-1/2 text-cyan-300 font-semibold">$</span>' +
                    '<input type="text" class="otr-precio form-control w-full h-10 text-sm pl-6" placeholder="0"></div>' +
                '</div>' +
                '<div class="col-span-1 sm:col-span-1 min-w-0">' +
                    '<label class="block text-cyan-200 text-sm mb-1">' + (EG.I18N.subtotal || 'Subtotal') + '</label>' +
                    '<input type="hidden" class="otr-subtotal" value="0">' +
                    '<div class="otr-subtotal-view subtotal-field w-full h-10 text-right font-bold form-control text-sm flex items-center justify-end">$0</div>' +
                '</div>' +
                '<div class="col-span-1 sm:col-span-1">' +
                    '<button type="button" class="btn-add w-full h-10 otr-remove-btn">X</button>' +
                '</div>' +
            '</div>';

        container.appendChild(row);
        setupOtroRow(row);
        toggleEmptyHint('otros-container', 'otros-empty-hint');
        return row;
    }

    function setupOtroRow(row) {
        if (!row || row.dataset.egInitOtro) return;
        row.dataset.egInitOtro = '1';

        var idEl = row.querySelector('.otr-servicio-id');
        var searchEl = row.querySelector('.otr-search');
        var empresaEl = row.querySelector('.otr-empresa');
        var tallerEl = row.querySelector('.otr-precio-taller');
        var clientPriceEl = row.querySelector('.otr-precio');
        var subtotalEl = row.querySelector('.otr-subtotal');
        var subtotalViewEl = row.querySelector('.otr-subtotal-view');
        var removeBtn = row.querySelector('.otr-remove-btn');
        var dropdown = row.querySelector('.otr-dropdown');
        var searchTimer = null;

        function applyItem(data) {
            var item = normalizeServicioItem(data);
            if (idEl) idEl.value = item.id || '';
            if (searchEl) searchEl.value = item.nombre || '';
            if (empresaEl && item.empresa) empresaEl.value = item.empresa;
            if (tallerEl) {
                var taller = EG.utils.parseNumericInput(item.precio_taller);
                tallerEl.value = taller ? EG.utils.formatNumberInput(taller) : '';
            }
            if (clientPriceEl) {
                var price = EG.utils.parseNumericInput(item.precio);
                clientPriceEl.value = price ? EG.utils.formatNumberInput(price) : '';
                clientPriceEl.dispatchEvent(new Event('input', { bubbles: true }));
            }
            if (dropdown) dropdown.classList.add('hidden');
        }

        bindMoneyField(clientPriceEl, subtotalEl, subtotalViewEl);

        if (searchEl) {
            searchEl.addEventListener('input', function() {
                if (idEl) idEl.value = '';
                clearTimeout(searchTimer);
                var query = (searchEl.value || '').trim();
                if (query.length < 2) {
                    if (dropdown) dropdown.classList.add('hidden');
                    return;
                }
                searchTimer = setTimeout(function() {
                    searchWithFallback({
                        query: query,
                        url: EG.cfg.URL_OUTSOURCED_SERVICES,
                        prefetch: EG.PREFETCH && (EG.PREFETCH.otros || EG.PREFETCH.otroServicios),
                        fields: ['nombre', 'empresa', 'empresa_ext', 'descripcion'],
                        onResults: function(results) {
                            renderResults(dropdown, results, function(item) {
                                var metaParts = [];
                                if (item.empresa) metaParts.push(item.empresa);
                                if (item.precio) metaParts.push(EG.utils.money(item.precio));
                                return buildDropdownItem(item, item.nombre || '', metaParts.join(' | '));
                            });
                        }
                    });
                }, 250);
            });

            searchEl.addEventListener('focus', function() {
                if ((searchEl.value || '').trim().length >= 2) {
                    searchEl.dispatchEvent(new Event('input'));
                }
            });
        }

        if (dropdown) {
            dropdown.addEventListener('click', function(e) {
                var itemEl = e.target.closest('.srv-item');
                if (!itemEl) return;
                applyItem({
                    id: itemEl.dataset.id,
                    nombre: itemEl.dataset.name,
                    precio: itemEl.dataset.price,
                    empresa: itemEl.dataset.company,
                    precio_taller: itemEl.dataset.shopPrice
                });
            });
        }

        if (removeBtn) {
            removeBtn.addEventListener('click', function() {
                removeDynamicRow(row, 'otros-container', 'otros-empty-hint');
            });
        }

        if (tallerEl && !tallerEl.dataset.egBound) {
            tallerEl.dataset.egBound = '1';
            tallerEl.addEventListener('change', function() {
                if (!clientPriceEl.value && tallerEl.value) {
                    clientPriceEl.value = tallerEl.value;
                    clientPriceEl.dispatchEvent(new Event('input', { bubbles: true }));
                }
            });
        }

        document.addEventListener('click', function(e) {
            if (!row.contains(e.target) && dropdown) {
                dropdown.classList.add('hidden');
            }
        });

        row.__applyOtroData = function(data) {
            applyItem({
                id: data && (data.id || data.servicio_id),
                nombre: data && data.nombre,
                empresa: data && (data.empresa || data.empresa_ext),
                precio_taller: data && data.precio_taller,
                precio: data && (data.precio !== undefined ? data.precio : data.precio_cliente)
            });
        };
    }

    function init() {
        document.querySelectorAll('#servicios-container .dynamic-element').forEach(setupServicioRow);
        document.querySelectorAll('#otros-container .dynamic-element').forEach(setupOtroRow);
        toggleEmptyHint('servicios-container', 'servicios-empty-hint');
        toggleEmptyHint('otros-container', 'otros-empty-hint');
    }

    EG.servicios = {
        addServicioRow: addServicioRow,
        setupServicioRow: setupServicioRow,
        addOtroServicioRow: addOtroServicioRow,
        addOtroRow: addOtroServicioRow,
        setupOtroServicioRow: setupOtroRow,
        setupOtroRow: setupOtroRow,
        init: init
    };

    window.addServicioRow = addServicioRow;
    window.addOtroServicioRow = addOtroServicioRow;
    window.addOtroRow = addOtroServicioRow;
})();
