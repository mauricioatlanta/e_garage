/**
 * servicios.js - Gestion de servicios internos y externos.
 */

(function() {
    'use strict';

    var EG = window.EG = window.EG || {};
    EG.state = EG.state || {};
    EG.state.servicios = EG.state.servicios || [];
    EG.state.otros = EG.state.otros || [];

    function toggleEmptyHint(containerId, hintId) {
        var container = document.getElementById(containerId);
        var hint = document.getElementById(hintId);
        if (!container || !hint) return;
        hint.classList.toggle('hidden', !!container.querySelector('.dynamic-element'));
    }

    function notifyStateChange() {
        if (typeof EG.state.onChange === 'function') EG.state.onChange();
    }

    function syncSerializedRows() {
        if (typeof window.serializeRows === 'function') window.serializeRows();
    }

    function getPrimaryFocusTarget(row) {
        if (!row || !row.querySelector) return null;
        return row.querySelector('.srv-input, .otr-search, .serv-cantidad, .serv-precio, .serv-descuento, .otr-empresa, .otr-precio, .otr-precio-taller');
    }

    function focusRowInput(row) {
        var target = getPrimaryFocusTarget(row);
        if (!target) return;
        window.setTimeout(function() {
            target.focus();
            if (typeof target.select === 'function' && target.tagName !== 'SELECT') target.select();
        }, 0);
    }

    function focusNeighborRow(row) {
        if (!row) return;
        var targetRow = row.nextElementSibling || row.previousElementSibling;
        if (targetRow) focusRowInput(targetRow);
    }

    function closeRowDropdown(row) {
        if (!row) return;
        row.querySelectorAll('.srv-dropdown, .otr-dropdown').forEach(function(dropdown) {
            dropdown.classList.add('hidden');
        });
        toggleRowOverlay(row, false);
    }

    function closeAllDynamicDropdowns() {
        document.querySelectorAll('#servicios-container .dynamic-element, #otros-container .dynamic-element').forEach(closeRowDropdown);
    }

    function bindGlobalDismissHandlers() {
        if (document.body.dataset.egServiceDismissBound) return;
        document.body.dataset.egServiceDismissBound = '1';

        document.addEventListener('pointerdown', function(e) {
            document.querySelectorAll('#servicios-container .dynamic-element.is-dropdown-open, #otros-container .dynamic-element.is-dropdown-open').forEach(function(row) {
                if (!row.contains(e.target)) closeRowDropdown(row);
            });
        });

        window.addEventListener('scroll', closeAllDynamicDropdowns, true);
        window.addEventListener('resize', closeAllDynamicDropdowns);
    }

    function getStateItem(row, isOtro) {
        if (!row || !row.__stateRef) return null;
        var list = isOtro ? EG.state.otros : EG.state.servicios;
        return list.find(function(item) { return item.__rowId === row.__stateRef.id; }) || null;
    }

    function removeDynamicRow(row, containerId, hintId) {
        if (row && row.__stateRef) {
            var list = row.__stateRef.type === 'otro' ? EG.state.otros : EG.state.servicios;
            var index = list.findIndex(function(item) { return item.__rowId === row.__stateRef.id; });
            if (index !== -1) list.splice(index, 1);
            notifyStateChange();
        }
        if (!row) return;
        closeRowDropdown(row);
        row.classList.add('row-remove');
        window.setTimeout(function() {
            focusNeighborRow(row);
            row.remove();
            toggleEmptyHint(containerId, hintId);
            if (typeof window.recalcTotales === 'function') window.recalcTotales();
            syncSerializedRows();
        }, 140);
    }

    function duplicateServicioRow(row) {
        if (!row) return null;
        var clone = addServicioRow();
        if (clone && clone.__applyServData) {
            clone.__applyServData({
                id: row.querySelector('.srv-id') && row.querySelector('.srv-id').value || '',
                nombre: row.querySelector('.srv-input') && row.querySelector('.srv-input').value || '',
                cantidad: row.querySelector('.serv-cantidad') && row.querySelector('.serv-cantidad').value || 1,
                precio: EG.utils.parseNumericInput(row.querySelector('.serv-precio') && row.querySelector('.serv-precio').value || 0),
                descuento: EG.utils.parseNumericInput(row.querySelector('.serv-descuento') && row.querySelector('.serv-descuento').value || 0)
            });
        }
        closeRowDropdown(clone);
        focusRowInput(clone);
        return clone;
    }

    function duplicateOtroRow(row) {
        if (!row) return null;
        var clone = addOtroServicioRow();
        if (clone && clone.__applyOtroData) {
            clone.__applyOtroData({
                id: row.querySelector('.otr-servicio-id') && row.querySelector('.otr-servicio-id').value || '',
                nombre: row.querySelector('.otr-search') && row.querySelector('.otr-search').value || '',
                empresa: row.querySelector('.otr-empresa') && row.querySelector('.otr-empresa').value || '',
                precio_taller: EG.utils.parseNumericInput(row.querySelector('.otr-precio-taller') && row.querySelector('.otr-precio-taller').value || 0),
                precio: EG.utils.parseNumericInput(row.querySelector('.otr-precio') && row.querySelector('.otr-precio').value || 0)
            });
        }
        closeRowDropdown(clone);
        focusRowInput(clone);
        return clone;
    }

    function toggleRowOverlay(row, isOpen) {
        if (!row) return;
        row.classList.toggle('is-dropdown-open', !!isOpen);
    }

    function renderMessage(dropdown, text, cls) {
        if (!dropdown) return;
        dropdown.innerHTML = '<div class="p-3 ' + (cls || 'text-gray-300') + '">' + text + '</div>';
        dropdown.classList.remove('hidden');
    }

    function buildDropdownItem(item, text, meta) {
        return '<div class="srv-item px-3 py-2 hover:bg-cyan-700 cursor-pointer border-b border-cyan-600" ' +
            'data-id="' + (item.id || item.pk || '') + '" ' +
            'data-name="' + (text || '') + '" ' +
            'data-price="' + (
                item.precio !== undefined ? item.precio :
                (item.precio_base !== undefined ? item.precio_base :
                (item.precio_venta !== undefined ? item.precio_venta :
                (item.precio_cliente !== undefined ? item.precio_cliente :
                (item.precio_sugerido !== undefined ? item.precio_sugerido : 0))))
            ) + '" ' +
            'data-company="' + (item.empresa || item.empresa_ext || item.proveedor || item.proveedor_tipico || '') + '" ' +
            'data-shop-price="' + (item.precio_taller || item.costo || 0) + '">' +
            '<div class="text-cyan-200 font-semibold">' + text + '</div>' +
            (meta ? '<div class="text-xs text-gray-300">' + meta + '</div>' : '') +
            '</div>';
    }

    function normalizeServicioItem(item) {
        var normalized = EG.utils.normalizeServicio(item || {}) || {};
        normalized.nombre = normalized.nombre || normalized.text || normalized.name || normalized.descripcion || normalized.label || '';
        normalized.precio = normalized.precio !== undefined ? normalized.precio :
            (normalized.precio_base !== undefined ? normalized.precio_base :
            (normalized.precio_venta !== undefined ? normalized.precio_venta :
            (normalized.precio_cliente !== undefined ? normalized.precio_cliente :
            (normalized.precio_sugerido !== undefined ? normalized.precio_sugerido : 0))));
        normalized.empresa = normalized.empresa || normalized.empresa_ext || normalized.proveedor || normalized.proveedor_tipico || '';
        normalized.precio_taller = normalized.precio_taller !== undefined ? normalized.precio_taller :
            (normalized.costo !== undefined ? normalized.costo : 0);
        return normalized;
    }

    function normalizeResponseItems(data) {
        var items = [];
        if (Array.isArray(data)) items = data;
        else if (data && Array.isArray(data.results)) items = data.results;
        else if (data && Array.isArray(data.items)) items = data.items;
        else if (data && Array.isArray(data.servicios)) items = data.servicios;
        else if (data && Array.isArray(data.otros_servicios)) items = data.otros_servicios;
        return items.map(normalizeServicioItem);
    }

    function renderResults(dropdown, list, renderer) {
        if (!dropdown) return;
        if (!list.length) return renderMessage(dropdown, EG.I18N.no_results || 'Sin resultados');
        dropdown.innerHTML = list.map(renderer).join('');
        dropdown.classList.remove('hidden');
    }

    function normalizeDiscountPercent(value) {
        var discount = EG.utils.parseNumericInput(value || 0);
        if (discount < 0) return 0;
        if (discount > 100) return 100;
        return discount;
    }

    async function searchWithFallback(options) {
        var local = EG.utils.filterPrefetchItems(options.prefetch || [], options.fields || ['nombre'], options.query, 15)
            .map(normalizeServicioItem);
        if (local.length) options.onResults(local);

        var urls = [options.url].filter(Boolean);
        var lastStatus = null;
        for (var i = 0; i < urls.length; i++) {
            try {
                var response = await EG.utils.egFetch(urls[i] + '?q=' + encodeURIComponent(options.query));
                if (!response.ok) {
                    lastStatus = response.status;
                    if (response.status === 403 || response.status === 404) continue;
                    throw new Error('HTTP ' + response.status);
                }
                var data = await response.json();
                var items = normalizeResponseItems(data);
                if (items.length || !local.length) options.onResults(items);
                return;
            } catch (err) {
                console.error('searchWithFallback', err);
            }
        }

        if (typeof options.onError === 'function') return options.onError(lastStatus);
        if (!local.length) options.onResults([]);
    }

    function markServiceRowValidity(row, valid) {
        row.dataset.serviceValid = valid ? '1' : '0';
        row.classList.toggle('ring-1', !valid);
        row.classList.toggle('ring-red-500', !valid);
    }

    function addServicioRow() {
        var container = document.getElementById('servicios-container');
        if (!container) return null;
        var row = document.createElement('tr');
        row.className = 'dynamic-element servicio-row';
        row.classList.add('row-enter');
        row.innerHTML =
                '<td class="doc-sheet-cell description-field srv-input-container relative field-main">' +
                    '<input type="text" class="srv-input doc-input form-control flex-1 min-w-0" placeholder="' + (EG.I18N.type_to_search_services || EG.I18N.service || 'Service') + '" autocomplete="off">' +
                    '<div class="srv-dropdown absolute z-50 w-full bg-gray-800 border border-cyan-400 rounded-lg shadow-lg hidden max-h-60 overflow-y-auto"></div>' +
                    '<input type="hidden" class="srv-id">' +
                '</td>' +
                '<td class="doc-sheet-cell"><input type="number" class="serv-cantidad doc-input form-control text-sm" min="1" value="1"></td>' +
                '<td class="doc-sheet-cell doc-sheet-money"><span>$</span><input type="text" class="serv-precio doc-input form-control text-sm" placeholder="0"></td>' +
                '<td class="doc-sheet-cell"><input type="number" class="serv-descuento doc-input form-control text-sm" min="0" max="100" step="0.01" value="0" placeholder="0-100" title="Descuento %"></td>' +
                '<td class="doc-sheet-cell field-total"><input type="hidden" class="serv-subtotal" value="0"><div class="serv-subtotal-view doc-sheet-total">$0</div></td>' +
                '<td class="doc-sheet-cell doc-sheet-row-actions"><button type="button" class="btn-row-icon btn-row-icon-duplicate srv-duplicate-btn" title="Duplicar">&#10697;</button><button type="button" class="btn-row-icon btn-row-icon-remove srv-remove-btn doc-row-remove" title="Eliminar">&times;</button></td>';
        container.appendChild(row);
        setupServicioRow(row);
        window.setTimeout(function() { row.classList.remove('row-enter'); }, 180);
        toggleEmptyHint('servicios-container', 'servicios-empty-hint');
        syncSerializedRows();
        focusRowInput(row);
        return row;
    }

    function setupServicioRow(row) {
        if (!row || row.dataset.egInitServicio) return;
        row.dataset.egInitServicio = '1';
        var inputEl = row.querySelector('.srv-input');
        var idEl = row.querySelector('.srv-id');
        var qtyEl = row.querySelector('.serv-cantidad');
        var priceEl = row.querySelector('.serv-precio');
        var discountEl = row.querySelector('.serv-descuento');
        var subtotalEl = row.querySelector('.serv-subtotal');
        var subtotalViewEl = row.querySelector('.serv-subtotal-view');
        var removeBtn = row.querySelector('.srv-remove-btn');
        var duplicateBtn = row.querySelector('.srv-duplicate-btn');
        var dropdown = row.querySelector('.srv-dropdown');
        var timer = null;

        row.__stateRef = { id: 'serv_' + Date.now() + '_' + Math.floor(Math.random() * 1000), type: 'servicio' };
        row.dataset.serviceValid = '0';
        row.dataset.serviceId = '';
        row.dataset.serviceName = '';
        EG.state.servicios.push({ __rowId: row.__stateRef.id, id: '', nombre: '', cantidad: 1, precio: 0, descuento: 0, subtotal: 0, iva: 0 });

        function syncState() {
            var item = getStateItem(row, false);
            if (!item) return;
            item.id = (idEl && idEl.value || '').trim();
            item.nombre = (inputEl && inputEl.value || '').trim();
            item.cantidad = Number(qtyEl && qtyEl.value || 0) || 1;
            item.precio = EG.utils.parseNumericInput(priceEl && priceEl.value || 0);
            item.descuento = EG.utils.parseNumericInput(discountEl && discountEl.value || 0);
            item.subtotal = EG.utils.parseNumericInput(subtotalEl && subtotalEl.value || 0);
            notifyStateChange();
        }

        function applyItem(data) {
            var item = normalizeServicioItem(data);
            var itemId = String(item.id || '').trim();
            var itemName = (item.nombre || '').trim();
            var priceValue = EG.utils.parseNumericInput(item.precio);
            if (idEl) idEl.value = itemId;
            if (inputEl) inputEl.value = itemName;
            if (priceEl) {
                priceEl.value = priceValue ? EG.utils.formatNumberInput(priceValue) : '';
                priceEl.dispatchEvent(new Event('input', { bubbles: true }));
            }
            if (qtyEl && data && data.cantidad !== undefined) qtyEl.value = data.cantidad || 1;
            if (discountEl && data && data.descuento !== undefined) discountEl.value = data.descuento || 0;
            row.dataset.serviceId = itemId;
            row.dataset.serviceName = itemName;
            markServiceRowValidity(row, !!itemId);
            syncState();
            if (dropdown) dropdown.classList.add('hidden');
            toggleRowOverlay(row, false);
        }

        function recalcSubtotal() {
            var quantity = Number(qtyEl && qtyEl.value || 0) || 0;
            var price = EG.utils.parseNumericInput(priceEl && priceEl.value || 0);
            var discount = normalizeDiscountPercent(discountEl && discountEl.value || 0);
            if (discountEl) discountEl.value = discount;
            var subtotal = Math.max(0, (quantity * price) * (1 - (discount / 100)));
            if (subtotalEl) subtotalEl.value = subtotal;
            if (subtotalViewEl) subtotalViewEl.textContent = EG.utils.money(subtotal);
            syncState();
            if (typeof window.recalcTotales === 'function') window.recalcTotales();
        }

        if (priceEl && !priceEl.dataset.egMoneyBound) {
            priceEl.dataset.egMoneyBound = '1';
            priceEl.addEventListener('input', recalcSubtotal);
            priceEl.addEventListener('change', recalcSubtotal);
        }
        if (qtyEl && !qtyEl.dataset.egQtyBound) {
            qtyEl.dataset.egQtyBound = '1';
            qtyEl.addEventListener('input', recalcSubtotal);
            qtyEl.addEventListener('change', recalcSubtotal);
        }
        if (discountEl && !discountEl.dataset.egDiscountBound) {
            discountEl.dataset.egDiscountBound = '1';
            discountEl.addEventListener('input', recalcSubtotal);
            discountEl.addEventListener('change', recalcSubtotal);
        }

        if (inputEl) {
            inputEl.addEventListener('input', function() {
                clearTimeout(timer);
                var query = (inputEl.value || '').trim();
                if (idEl) idEl.value = '';
                row.dataset.serviceId = '';
                row.dataset.serviceName = query;
                markServiceRowValidity(row, !query);
                syncState();
                if (query.length < 2) {
                    if (dropdown) dropdown.classList.add('hidden');
                    toggleRowOverlay(row, false);
                    return;
                }
                timer = setTimeout(function() {
                    searchWithFallback({
                        query: query,
                        url: EG.cfg.URL_SERVICE_SEARCH,
                        prefetch: EG.PREFETCH && EG.PREFETCH.servicios,
                        fields: ['codigo', 'nombre', 'descripcion', 'text'],
                        onResults: function(results) {
                            renderResults(dropdown, results, function(item) {
                                var meta = item.precio ? EG.utils.money(item.precio) : '';
                                return buildDropdownItem(item, item.nombre || '', meta);
                            });
                            toggleRowOverlay(row, true);
                        },
                        onError: function(status) {
                            if (status === 403) return renderMessage(dropdown, 'No tienes permisos para consultar servicios en este momento.', 'text-red-300');
                            renderMessage(dropdown, EG.I18N.server_error || 'Error consultando servicios.', 'text-red-300');
                            toggleRowOverlay(row, true);
                        }
                    });
                }, 250);
            });
            inputEl.addEventListener('focus', function() {
                if ((inputEl.value || '').trim().length >= 2) inputEl.dispatchEvent(new Event('input', { bubbles: true }));
            });
        }

        if (dropdown) dropdown.addEventListener('click', function(e) {
            var itemEl = e.target.closest('.srv-item');
            if (!itemEl) return;
            applyItem({ id: itemEl.dataset.id, nombre: itemEl.dataset.name, precio: itemEl.dataset.price });
        });
        if (removeBtn) removeBtn.addEventListener('click', function() { removeDynamicRow(row, 'servicios-container', 'servicios-empty-hint'); });
        if (duplicateBtn) duplicateBtn.addEventListener('click', function() { duplicateServicioRow(row); });
        row.__applyServData = function(data) {
            applyItem({
                id: data && (data.id || data.servicio_id),
                nombre: data && data.nombre,
                precio: data && data.precio,
                cantidad: data && data.cantidad,
                descuento: data && data.descuento
            });
            recalcSubtotal();
        };
        recalcSubtotal();
    }

    function addOtroServicioRow() {
        var container = document.getElementById('otros-container');
        if (!container) return null;
        var row = document.createElement('tr');
        row.className = 'dynamic-element otro-servicio-row';
        row.classList.add('row-enter');
        row.innerHTML =
                '<td class="doc-sheet-cell description-field otr-search-container relative field-main"><input type="text" class="otr-search doc-input form-control text-sm" placeholder="' + (EG.I18N.type_to_search_external || EG.I18N.service || 'Service') + '" autocomplete="off"><div class="otr-dropdown absolute z-50 w-full bg-gray-800 border border-cyan-400 rounded-lg shadow-lg hidden max-h-60 overflow-y-auto"></div><input type="hidden" class="otr-servicio-id"><input type="hidden" class="otr-subtotal" value="0"></td>' +
                '<td class="doc-sheet-cell"><input type="text" class="otr-empresa doc-input form-control text-sm"></td>' +
                '<td class="doc-sheet-cell doc-sheet-money"><span>$</span><input type="text" class="otr-precio-taller doc-input form-control text-sm" placeholder="0"></td>' +
                '<td class="doc-sheet-cell doc-sheet-money"><span>$</span><input type="text" class="otr-precio doc-input form-control text-sm" placeholder="0"></td>' +
                '<td class="doc-sheet-cell field-total"><div class="otr-subtotal-view doc-sheet-total">$0</div></td>' +
                '<td class="doc-sheet-cell doc-sheet-row-actions"><button type="button" class="btn-row-icon btn-row-icon-duplicate otr-duplicate-btn" title="Duplicar">&#10697;</button><button type="button" class="btn-row-icon btn-row-icon-remove otr-remove-btn doc-row-remove" title="Eliminar">&times;</button></td>';
        container.appendChild(row);
        setupOtroRow(row);
        window.setTimeout(function() { row.classList.remove('row-enter'); }, 180);
        toggleEmptyHint('otros-container', 'otros-empty-hint');
        syncSerializedRows();
        focusRowInput(row);
        return row;
    }

    function setupOtroRow(row) {
        if (!row || row.dataset.egInitOtro) return;
        row.dataset.egInitOtro = '1';
        var idEl = row.querySelector('.otr-servicio-id');
        var searchEl = row.querySelector('.otr-search');
        var empresaEl = row.querySelector('.otr-empresa');
        var tallerEl = row.querySelector('.otr-precio-taller');
        var priceEl = row.querySelector('.otr-precio');
        var subtotalEl = row.querySelector('.otr-subtotal');
        var subtotalViewEl = row.querySelector('.otr-subtotal-view');
        var removeBtn = row.querySelector('.otr-remove-btn');
        var duplicateBtn = row.querySelector('.otr-duplicate-btn');
        var dropdown = row.querySelector('.otr-dropdown');
        var timer = null;

        row.__stateRef = { id: 'otr_' + Date.now() + '_' + Math.floor(Math.random() * 1000), type: 'otro' };
        EG.state.otros.push({ __rowId: row.__stateRef.id, id: '', nombre: '', empresa: '', precio_taller: 0, precio: 0, ganancia: 0 });

        function syncState() {
            var item = getStateItem(row, true);
            if (!item) return;
            item.id = (idEl && idEl.value || '').trim();
            item.nombre = (searchEl && searchEl.value || '').trim();
            item.empresa = (empresaEl && empresaEl.value || '').trim();
            item.precio_taller = EG.utils.parseNumericInput(tallerEl && tallerEl.value || 0);
            item.precio = EG.utils.parseNumericInput(priceEl && priceEl.value || 0);
            item.ganancia = item.precio - item.precio_taller;
            notifyStateChange();
        }

        function applyItem(data) {
            var item = normalizeServicioItem(data);
            if (idEl) idEl.value = String(item.id || '').trim();
            if (searchEl) searchEl.value = item.nombre || '';
            if (empresaEl) empresaEl.value = item.empresa || '';
            if (tallerEl) {
                var shopValue = EG.utils.parseNumericInput(item.precio_taller);
                tallerEl.value = shopValue ? EG.utils.formatNumberInput(shopValue) : '';
            }
            if (priceEl) {
                var clientValue = EG.utils.parseNumericInput(item.precio);
                priceEl.value = clientValue ? EG.utils.formatNumberInput(clientValue) : '';
                priceEl.dispatchEvent(new Event('input', { bubbles: true }));
            }
            syncState();
            if (dropdown) dropdown.classList.add('hidden');
            toggleRowOverlay(row, false);
        }

        function recalcProfit() {
            var shop = EG.utils.parseNumericInput(tallerEl && tallerEl.value || 0);
            var client = EG.utils.parseNumericInput(priceEl && priceEl.value || 0);
            var profit = client - shop;
            if (subtotalEl) subtotalEl.value = client;
            if (subtotalViewEl) subtotalViewEl.textContent = EG.utils.money(profit);
            syncState();
            if (typeof window.recalcTotales === 'function') window.recalcTotales();
        }

        if (priceEl && !priceEl.dataset.egOtroPriceBound) {
            priceEl.dataset.egOtroPriceBound = '1';
            priceEl.addEventListener('input', recalcProfit);
            priceEl.addEventListener('change', recalcProfit);
        }
        if (tallerEl && !tallerEl.dataset.egOtroShopBound) {
            tallerEl.dataset.egOtroShopBound = '1';
            tallerEl.addEventListener('input', recalcProfit);
            tallerEl.addEventListener('change', recalcProfit);
        }
        if (empresaEl && !empresaEl.dataset.egBound) {
            empresaEl.dataset.egBound = '1';
            empresaEl.addEventListener('input', syncState);
            empresaEl.addEventListener('change', syncState);
        }

        if (searchEl) {
            searchEl.addEventListener('input', function() {
                clearTimeout(timer);
                var query = (searchEl.value || '').trim();
                if (idEl) idEl.value = '';
                syncState();
                if (query.length < 2) {
                    if (dropdown) dropdown.classList.add('hidden');
                    toggleRowOverlay(row, false);
                    return;
                }
                timer = setTimeout(function() {
                    searchWithFallback({
                        query: query,
                        url: EG.cfg.URL_OUTSOURCED_SERVICES,
                        prefetch: EG.PREFETCH && EG.PREFETCH.otros,
                        fields: ['nombre', 'empresa', 'empresa_ext', 'proveedor'],
                        onResults: function(results) {
                            renderResults(dropdown, results, function(item) {
                                var meta = [];
                                if (item.empresa) meta.push(item.empresa);
                                if (item.precio) meta.push(EG.utils.money(item.precio));
                                return buildDropdownItem(item, item.nombre || '', meta.join(' • '));
                            });
                            toggleRowOverlay(row, true);
                        },
                        onError: function() {
                            renderMessage(dropdown, EG.I18N.server_error || 'Error consultando servicios externos.', 'text-red-300');
                            toggleRowOverlay(row, true);
                        }
                    });
                }, 250);
            });
            searchEl.addEventListener('focus', function() {
                if ((searchEl.value || '').trim().length >= 2) searchEl.dispatchEvent(new Event('input', { bubbles: true }));
            });
        }

        if (dropdown) dropdown.addEventListener('click', function(e) {
            var itemEl = e.target.closest('.srv-item');
            if (!itemEl) return;
            applyItem({ id: itemEl.dataset.id, nombre: itemEl.dataset.name, empresa: itemEl.dataset.company, precio_taller: itemEl.dataset.shopPrice, precio: itemEl.dataset.price });
        });
        if (removeBtn) removeBtn.addEventListener('click', function() { removeDynamicRow(row, 'otros-container', 'otros-empty-hint'); });
        if (duplicateBtn) duplicateBtn.addEventListener('click', function() { duplicateOtroRow(row); });
        row.__applyOtroData = function(data) { applyItem({ id: data && (data.id || data.servicio_id), nombre: data && data.nombre, empresa: data && (data.empresa || data.empresa_ext), precio_taller: data && data.precio_taller, precio: data && data.precio }); };
        recalcProfit();
    }

    function init() {
        var container = document.getElementById('servicios-container');
        var otrosContainer = document.getElementById('otros-container');
        if (!container && !otrosContainer) return;

        bindGlobalDismissHandlers();
        document.querySelectorAll('#servicios-container .dynamic-element').forEach(setupServicioRow);
        document.querySelectorAll('#otros-container .dynamic-element').forEach(setupOtroRow);
        toggleEmptyHint('servicios-container', 'servicios-empty-hint');
        toggleEmptyHint('otros-container', 'otros-empty-hint');
    }

    EG.servicios = {
        init: init,
        addServicioRow: addServicioRow,
        duplicateServicioRow: duplicateServicioRow,
        setupServicioRow: setupServicioRow,
        addOtroRow: addOtroServicioRow,
        addOtroServicioRow: addOtroServicioRow,
        duplicateOtroRow: duplicateOtroRow,
        setupOtroServicioRow: setupOtroRow,
        setupOtroRow: setupOtroRow,
        searchWithFallback: searchWithFallback
    };
    window.addServicioRow = addServicioRow;
    window.addOtroServicioRow = addOtroServicioRow;
    window.addOtroRow = addOtroServicioRow;
})();
