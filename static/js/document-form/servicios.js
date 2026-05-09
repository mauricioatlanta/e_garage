/**
 * servicios.js - Modulo de gestion de servicios y otros servicios
 */

(function() {
    'use strict';

    var EG = window.EG = window.EG || {};

    function escapeHtml(text) {
        return String(text || '')
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    function generateRowId(prefix) {
        return (prefix || 'srv') + '_' + Date.now() + '_' + Math.floor(Math.random() * 1000);
    }

    function buildEyeIcon(className) {
        return '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false" class="' + escapeHtml(className || 'otr-eye-icon') + '">'
            + '<path d="M1.5 12s3.75-6 10.5-6 10.5 6 10.5 6-3.75 6-10.5 6S1.5 12 1.5 12Z"></path>'
            + '<circle cx="12" cy="12" r="3.25"></circle>'
            + '</svg>';
    }

    function formatCurrencyInputValue(value) {
        var amount = EG.utils.parseNumericInput(value || 0);
        return amount > 0 ? ('$' + EG.utils.formatNumberInput(amount)) : '';
    }

    function bindCurrencyInput(inputEl, onValueChange) {
        function sync() {
            var amount = EG.utils.parseNumericInput(inputEl && inputEl.value || 0);
            if (inputEl) {
                inputEl.value = formatCurrencyInputValue(amount);
            }
            if (typeof onValueChange === 'function') {
                onValueChange(amount);
            }
            return amount;
        }

        if (inputEl && !inputEl.dataset.egCurrencyBound) {
            inputEl.dataset.egCurrencyBound = '1';
            inputEl.addEventListener('input', sync);
            inputEl.addEventListener('change', sync);
            inputEl.addEventListener('blur', sync);
        }

        return sync();
    }

    function getValidationMessage(key, fallbackEs, fallbackEn) {
        var country = ((EG.cfg && EG.cfg.country) || 'CL').toUpperCase();
        if (EG.I18N && EG.I18N[key]) {
            return EG.I18N[key];
        }
        return country === 'US' ? fallbackEn : fallbackEs;
    }

    function syncSerializedState() {
        if (typeof window.serializeRows === 'function') {
            window.serializeRows();
        }
        if (typeof window.scheduleDocumentDraftSave === 'function') {
            window.scheduleDocumentDraftSave();
        }
    }

    function unwrapTextValue(value) {
        if (!value) return '';
        if (typeof value === 'object') {
            return value.nombre || value.label || value.text || value.code || '';
        }
        return value;
    }

    function firstDefined(values, fallback) {
        for (var i = 0; i < values.length; i += 1) {
            if (values[i] !== undefined && values[i] !== null && values[i] !== '') {
                return values[i];
            }
        }
        return fallback;
    }

    function toggleEmptyHint(containerId, hintId) {
        var container = document.getElementById(containerId);
        var hint = document.getElementById(hintId);
        if (!container || !hint) return;
        hint.classList.toggle('hidden', !!container.querySelector('.dynamic-element'));
    }

    function removeDynamicRow(row, containerId, hintId) {
        if (row) row.remove();
        toggleEmptyHint(containerId, hintId);
        if (typeof window.serializeRows === 'function') window.serializeRows();
        if (typeof window.recalcTotales === 'function') window.recalcTotales();
    }

    function normalizeServicioItem(item) {
        var normalized = EG.utils.normalizeServicio(item || {}) || {};
        normalized.nombre = normalized.nombre || normalized.name || normalized.descripcion || normalized.label || normalized.text || '';
        normalized.categoria = unwrapTextValue(normalized.categoria);
        normalized.subcategoria = unwrapTextValue(normalized.subcategoria);
        normalized.precio = firstDefined([
            normalized.precio,
            normalized.precio_base,
            normalized.precio_venta,
            normalized.precio_cliente,
            normalized.price
        ], 0);
        normalized.empresa = normalized.empresa || normalized.empresa_externa || normalized.empresa_ext || normalized.proveedor || '';
        normalized.precio_taller = firstDefined([
            normalized.precio_taller,
            normalized.costo_taller,
            normalized.costo,
            normalized.shop_price
        ], 0);
        return normalized;
    }

    function extractServicioItems(data) {
        var items = EG.utils.extractResponseItems(data, ['results', 'items', 'servicios', 'otros_servicios']);
        if (!items.length && Array.isArray(data)) {
            items = data;
        }
        return items;
    }

    function buildDropdownItem(item, text, meta) {
        return '<div class="srv-item px-3 py-2 hover:bg-cyan-700 cursor-pointer border-b border-cyan-600" '
            + 'data-id="' + escapeHtml(item.id || item.pk || '') + '" '
            + 'data-name="' + escapeHtml(text || '') + '" '
            + 'data-price="' + escapeHtml(item.precio || item.precio_base || item.precio_venta || item.precio_cliente || 0) + '" '
            + 'data-company="' + escapeHtml(item.empresa || item.empresa_ext || item.proveedor || '') + '" '
            + 'data-shop-price="' + escapeHtml(item.precio_taller || item.costo || 0) + '">'
            + '<div class="text-cyan-200 font-semibold">' + escapeHtml(text) + '</div>'
            + (meta ? '<div class="text-xs text-gray-300">' + escapeHtml(meta) + '</div>' : '')
            + '</div>';
    }

    function bindMoneyField(inputEl, subtotalEl, subtotalViewEl) {
        function recalc(value) {
            if (value === undefined) {
                value = EG.utils.parseNumericInput(inputEl && inputEl.value || 0);
            }
            if (subtotalEl) subtotalEl.value = value;
            if (subtotalViewEl) subtotalViewEl.textContent = EG.utils.money(value);
            syncSerializedState();
            if (typeof window.recalcTotales === 'function') window.recalcTotales();
        }

        bindCurrencyInput(inputEl, recalc);
    }

    function renderResults(dropdown, list, renderer) {
        if (!dropdown) return;
        if (!list.length) {
            dropdown.innerHTML = '<div class="p-3 text-gray-300">' + (EG.I18N.no_services || 'Sin resultados') + '</div>';
            dropdown.classList.remove('hidden');
            return;
        }
        dropdown.innerHTML = list.map(renderer).join('');
        dropdown.classList.remove('hidden');
    }

    async function searchWithFallback(options) {
        var query = String(options.query || '').trim();
        var localResults = [];

        if (!query && options.showAllOnEmpty) {
            localResults = (options.prefetch || []).slice(0, options.emptyLimit || 12).map(normalizeServicioItem);
        } else {
            localResults = EG.utils.filterPrefetchItems(
                options.prefetch || [],
                options.fields || ['nombre'],
                query,
                15
            ).map(normalizeServicioItem);
        }

        if (localResults.length) {
            options.onResults(localResults);
        }

        if (!options.url) {
            if (!localResults.length) {
                options.onResults([]);
            }
            return;
        }

        if (!query && !options.allowEmptyQuery) {
            if (!localResults.length) {
                options.onResults([]);
            }
            return;
        }

        try {
            var response = await EG.utils.egFetch(options.url + '?q=' + encodeURIComponent(query));
            if (!response.ok) throw new Error('HTTP ' + response.status);
            var raw = await response.json(); var data = raw.results || raw;
            var normalizedItems = extractServicioItems(data).map(normalizeServicioItem);
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

    function getServicioRowById(rowId) {
        return rowId ? document.querySelector('#servicios-container .dynamic-element[data-row-id="' + rowId + '"]') : null;
    }

    function resolveServicioTargetRowId(context) {
        if (context && context.target_row) {
            return String(context.target_row);
        }
        var stored = EG.utils.restoreActiveRowContext ? EG.utils.restoreActiveRowContext() : null;
        if (stored && stored.type === 'servicio' && stored.rowId) {
            return String(stored.rowId);
        }
        return '';
    }

    function saveServicioRowContext(row) {
        if (!row || !row.dataset.rowId || !EG.utils.saveActiveRowContext) {
            return;
        }
        EG.utils.saveActiveRowContext('servicio', row.dataset.rowId);
    }

    function addServicioRow(presetRowId) {
        var container = document.getElementById('servicios-container');
        if (!container) {
            console.error('Contenedor de servicios no encontrado');
            return null;
        }

        var rowId = String((presetRowId || '').trim() || generateRowId('srv'));
        var row = document.createElement('div');
        row.className = 'dynamic-element';
        row.dataset.rowId = rowId;
        row.innerHTML = ''
            + '<div class="doc-table-row doc-table-grid doc-table-grid--services servicio-row-layout" data-row-id="' + rowId + '">'
            + '  <div class="doc-table-cell servicio-cell servicio-cell-name description-field srv-input-container">'
            + '    <label class="doc-field-label">' + escapeHtml(EG.I18N.service || 'Service') + '</label>'
            + '    <div class="position-relative-wrapper">'
            + '      <input type="text" class="srv-input form-control text-sm" placeholder="' + escapeHtml(EG.I18N.type_to_search_services || EG.I18N.service || 'Service') + '" autocomplete="off">'
            + '      <div class="srv-dropdown bg-gray-800 border border-cyan-400 rounded-lg shadow-lg hidden max-h-[420px] overflow-y-auto"></div>'
            + '    </div>'
            + '    <input type="hidden" class="srv-id">'
            + '  </div>'
            + '  <div class="doc-table-cell servicio-cell servicio-cell-qty">'
            + '    <label class="doc-field-label">' + escapeHtml(EG.I18N.qty || 'Qty') + '</label>'
            + '    <div class="position-relative-wrapper">'
            + '      <input type="number" class="serv-cantidad form-control text-sm" min="1" step="1" value="1">'
            + '    </div>'
            + '  </div>'
            + '  <div class="doc-table-cell servicio-cell servicio-cell-price">'
            + '    <label class="doc-field-label">' + escapeHtml(EG.I18N.client_price || 'Unit Price') + '</label>'
            + '    <div class="position-relative-wrapper">'
            + '      <input type="text" class="serv-precio form-control text-sm" placeholder="0">'
            + '    </div>'
            + '  </div>'
            + '  <div class="doc-table-cell servicio-cell servicio-cell-total">'
            + '    <label class="doc-field-label">' + escapeHtml(EG.I18N.subtotal || 'Subtotal') + '</label>'
            + '    <input type="hidden" class="serv-subtotal" value="0">'
            + '    <div class="position-relative-wrapper">'
            + '      <div class="serv-subtotal-view subtotal-field text-right font-bold form-control text-sm">' + EG.utils.money(0) + '</div>'
            + '    </div>'
            + '  </div>'
            + '  <div class="doc-table-cell servicio-cell servicio-cell-action">'
            + '    <label class="doc-field-label">' + escapeHtml(EG.I18N.action || 'Action') + '</label>'
            + '    <button type="button" class="btn-add srv-remove-btn">X</button>'
            + '  </div>'
            + '</div>';

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
        var qtyEl = row.querySelector('.serv-cantidad');
        var priceEl = row.querySelector('.serv-precio');
        var subtotalEl = row.querySelector('.serv-subtotal');
        var subtotalViewEl = row.querySelector('.serv-subtotal-view');
        var removeBtn = row.querySelector('.srv-remove-btn');
        var createBtn = row.querySelector('.srv-create-btn');
        var dropdown = row.querySelector('.srv-dropdown');
        var searchTimer = null;
        var searchRequestId = 0;

        function hideDropdown() {
            searchRequestId += 1;
            if (dropdown) {
                dropdown.classList.add('hidden');
            }
        }

        function applyItem(data) {
            var item = normalizeServicioItem(data);
            if (idEl) idEl.value = item.id || '';
            if (inputEl) inputEl.value = item.nombre || '';
            if (qtyEl) {
                qtyEl.value = String(Math.max(1, parseInt(data && data.cantidad || 1, 10) || 1));
            }
            if (priceEl) {
                priceEl.value = formatCurrencyInputValue(item.precio);
                priceEl.dispatchEvent(new Event('input', { bubbles: true }));
            }
            recalcSubtotal();
            hideDropdown();
            saveServicioRowContext(row);
        }

        function openCreatePage() {
            if (!EG.cfg.URL_SERVICE_CREATE || !EG.utils || !EG.utils.buildContextualCreateUrl) {
                console.error('URL_SERVICE_CREATE no configurada');
                return;
            }

            var rowId = row.dataset.rowId || generateRowId('srv');
            row.dataset.rowId = rowId;
            saveServicioRowContext(row);

            var url = EG.utils.buildContextualCreateUrl(EG.cfg.URL_SERVICE_CREATE, {
                return_to: EG.utils.getDocumentReturnTo(),
                select_field: 'servicio',
                target_row: rowId,
                prefill_nombre: inputEl ? inputEl.value.trim() : '',
            });
            window.location.href = url;
        }

        function recalcSubtotal() {
            var qty = Math.max(1, parseInt(qtyEl && qtyEl.value || '1', 10) || 1);
            var amount = EG.utils.parseNumericInput(priceEl && priceEl.value || 0);

            if (qtyEl) {
                qtyEl.value = String(qty);
            }
            if (subtotalEl) {
                subtotalEl.value = amount * qty;
            }
            if (subtotalViewEl) {
                subtotalViewEl.textContent = EG.utils.money(amount * qty);
            }
            syncSerializedState();
            if (typeof window.recalcTotales === 'function') {
                window.recalcTotales();
            }
        }

        bindCurrencyInput(priceEl, recalcSubtotal);

        if (qtyEl && !qtyEl.dataset.egBound) {
            qtyEl.dataset.egBound = '1';
            ['input', 'change', 'blur'].forEach(function(eventName) {
                qtyEl.addEventListener(eventName, recalcSubtotal);
            });
        }

        [row, inputEl, qtyEl, priceEl].forEach(function(node) {
            if (node) {
                node.addEventListener('focus', function() { saveServicioRowContext(row); }, true);
                node.addEventListener('click', function() { saveServicioRowContext(row); });
            }
        });

        if (createBtn) {
            createBtn.addEventListener('click', function(event) {
                event.preventDefault();
                openCreatePage();
            });
        }

        function requestServiceResults(query) {
            var normalizedQuery = String(query || '').trim();
            var requestId = ++searchRequestId;
            searchWithFallback({
                query: normalizedQuery,
                url: EG.cfg.URL_SERVICE_SEARCH,
                prefetch: EG.PREFETCH && EG.PREFETCH.servicios,
                fields: ['codigo', 'codigo_interno', 'nombre', 'descripcion', 'categoria', 'subcategoria', 'text', 'label'],
                showAllOnEmpty: true,
                allowEmptyQuery: true,
                emptyLimit: 12,
                onResults: function(results) {
                    if (requestId !== searchRequestId) return;
                    if (((inputEl.value || '').trim()) !== normalizedQuery) return;
                    renderResults(dropdown, results, function(item) {
                        var metaParts = [];
                        if (item.codigo_interno) metaParts.push(item.codigo_interno);
                        if (item.categoria) metaParts.push(item.categoria);
                        if (item.precio) metaParts.push(EG.utils.money(item.precio));
                        return buildDropdownItem(item, item.nombre || '', metaParts.join(' | '));
                    });
                }
            });
        }

        if (inputEl) {
            inputEl.addEventListener('input', function() {
                if (idEl) idEl.value = '';
                clearTimeout(searchTimer);
                var query = (inputEl.value || '').trim();
                searchTimer = setTimeout(function() {
                    requestServiceResults(query);
                }, query ? 180 : 60);
            });

            inputEl.addEventListener('focus', function() {
                inputEl.dispatchEvent(new Event('input'));
            });

            inputEl.addEventListener('click', function() {
                inputEl.dispatchEvent(new Event('input'));
            });
        }

        if (dropdown) {
            dropdown.addEventListener('click', function(e) {
                var itemEl = e.target.closest('.srv-item');
                if (!itemEl) return;
                clearTimeout(searchTimer);
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
                hideDropdown();
            }
        });

        row.__applyServData = function(data) {
            applyItem({
                id: data && (data.servicio_id || data.id),
                nombre: data && data.nombre,
                cantidad: data && data.cantidad,
                precio: data && data.precio
            });
        };
    }

    function addOtroServicioRow(presetRowId) {
        var container = document.getElementById('otros-container');
        if (!container) {
            console.error('Contenedor de otros servicios no encontrado');
            return null;
        }

        var row = document.createElement('div');
        row.className = 'dynamic-element';
        row.dataset.rowId = String((presetRowId || '').trim() || generateRowId('otr'));
        row.innerHTML = ''
            + '<div class="doc-table-row doc-table-grid doc-table-grid--otros otro-row-layout" data-row-id="' + row.dataset.rowId + '">'
            + '  <div class="doc-table-cell otro-cell otro-cell-name description-field otr-search-container">'
            + '    <label class="doc-field-label">' + escapeHtml(EG.I18N.service || 'Service') + '</label>'
            + '    <div class="position-relative-wrapper">'
            + '      <input type="text" class="otr-search form-control text-sm" placeholder="' + escapeHtml(EG.I18N.type_to_search_external || EG.I18N.service || 'Service') + '" autocomplete="off">'
            + '      <div class="otr-dropdown bg-gray-800 border border-cyan-400 rounded-lg shadow-lg hidden max-h-[420px] overflow-y-auto"></div>'
            + '    </div>'
            + '    <input type="hidden" class="otr-servicio-id">'
            + '  </div>'
            + '  <div class="doc-table-cell otro-cell otro-cell-company">'
            + '    <label class="doc-field-label">' + escapeHtml(EG.I18N.external_company || 'External Company') + '</label>'
            + '    <div class="position-relative-wrapper">'
            + '      <input type="text" class="otr-empresa form-control text-sm">'
            + '    </div>'
            + '  </div>'
            + '  <div class="doc-table-cell otro-cell otro-cell-shop">'
            + '    <label class="doc-field-label">' + escapeHtml(EG.I18N.shop_price || 'Precio taller') + '</label>'
            + '    <div class="otr-shop-toggle-wrap">'
            + '      <button type="button" class="otr-toggle-shop" title="' + escapeHtml(EG.I18N.shop_price || 'Precio taller') + '" aria-label="' + escapeHtml(EG.I18N.shop_price || 'Precio taller') + '" aria-expanded="false">'
            +            buildEyeIcon('otr-eye-icon')
            + '      </button>'
            + '      <div class="otr-shop-panel hidden">'
            + '        <div class="otr-shop-input-wrap">'
            + '          <span class="otr-shop-label">' + escapeHtml(EG.I18N.shop_price || 'Precio taller') + ':</span>'
            + '          <div class="otr-shop-input-shell">'
            + '            <span class="otr-shop-currency">$</span>'
            + '            <input type="text" class="otr-precio-taller form-control text-sm" inputmode="numeric" autocomplete="off" placeholder="0">'
            + '          </div>'
            + '        </div>'
            + '        <span class="otr-shop-value">' + EG.utils.money(0) + '</span>'
            + '      </div>'
            + '    </div>'
            + '  </div>'
            + '  <div class="doc-table-cell otro-cell otro-cell-client">'
            + '    <label class="doc-field-label">' + escapeHtml(EG.I18N.client_price || 'Client Price') + '</label>'
            + '    <div class="otr-client-price-field">'
            + '      <input type="text" class="otr-precio form-control text-sm" placeholder="0">'
            + '      <input type="hidden" class="otr-subtotal" value="0">'
            + '    </div>'
            + '  </div>'
            + '  <div class="doc-table-cell otro-cell otro-cell-action">'
            + '    <label class="doc-field-label">' + escapeHtml(EG.I18N.action || 'Action') + '</label>'
            + '    <button type="button" class="btn-add otr-remove-btn">X</button>'
            + '  </div>'
            + '</div>';

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
        var removeBtn = row.querySelector('.otr-remove-btn');
        var dropdown = row.querySelector('.otr-dropdown');
        var toggleShopBtn = row.querySelector('.otr-toggle-shop');
        var shopPanel = row.querySelector('.otr-shop-panel');
        var shopValueEl = row.querySelector('.otr-shop-value');
        var searchTimer = null;
        var searchRequestId = 0;

        function hideDropdown() {
            searchRequestId += 1;
            if (dropdown) {
                dropdown.classList.add('hidden');
            }
        }

        function hideShopPanel() {
            if (shopPanel) {
                shopPanel.classList.add('hidden');
            }
            if (toggleShopBtn) {
                toggleShopBtn.setAttribute('aria-expanded', 'false');
            }
        }

        function showShopPanel() {
            if (!shopPanel) {
                return;
            }
            document.querySelectorAll('#otros-container .otr-shop-panel').forEach(function(panel) {
                if (panel !== shopPanel) {
                    panel.classList.add('hidden');
                }
            });
            document.querySelectorAll('#otros-container .otr-toggle-shop').forEach(function(button) {
                if (button !== toggleShopBtn) {
                    button.setAttribute('aria-expanded', 'false');
                }
            });
            shopPanel.classList.remove('hidden');
            if (toggleShopBtn) {
                toggleShopBtn.setAttribute('aria-expanded', 'true');
            }
            if (tallerEl) {
                tallerEl.focus();
                tallerEl.select && tallerEl.select();
            }
        }

        function syncShopValue(amount) {
            var shopAmount = amount;
            if (shopAmount === undefined) {
                shopAmount = EG.utils.parseNumericInput(tallerEl && tallerEl.value || 0);
            }
            if (shopValueEl) {
                shopValueEl.textContent = EG.utils.money(shopAmount);
            }
            return shopAmount;
        }

        function recalcOtroTotals() {
            var shopAmount = syncShopValue();
            var clientAmount = EG.utils.parseNumericInput(clientPriceEl && clientPriceEl.value || 0);

            if (subtotalEl) {
                subtotalEl.value = clientAmount;
            }
            syncSerializedState();
            if (typeof window.recalcTotales === 'function') {
                window.recalcTotales();
            }
        }

        function applyItem(data) {
            var item = normalizeServicioItem(data);
            if (idEl) idEl.value = item.id || '';
            if (searchEl) searchEl.value = item.nombre || '';
            if (empresaEl) empresaEl.value = item.empresa || '';
            if (tallerEl) {
                tallerEl.value = formatCurrencyInputValue(item.precio_taller);
            }
            syncShopValue(item.precio_taller);
            if (clientPriceEl) {
                clientPriceEl.value = formatCurrencyInputValue(item.precio);
                clientPriceEl.dispatchEvent(new Event('input', { bubbles: true }));
            }
            recalcOtroTotals();
            hideDropdown();
            syncSerializedState();
        }

        bindCurrencyInput(clientPriceEl, recalcOtroTotals);
        bindCurrencyInput(tallerEl, function(amount) {
            syncShopValue(amount);
            recalcOtroTotals();
        });

        function clearValidation(field) {
            if (!field) return;
            field.setCustomValidity('');
            field.classList.remove('ring-2', 'ring-red-500');
        }

        function markValidation(field, message) {
            if (!field) return;
            field.setCustomValidity(message);
            field.classList.add('ring-2', 'ring-red-500');
        }

        function validateRow(report) {
            var hasAnyValue = [searchEl, empresaEl, tallerEl, clientPriceEl].some(function(field) {
                return field && String(field.value || '').trim() !== '';
            });

            [searchEl, empresaEl, tallerEl, clientPriceEl].forEach(clearValidation);

            if (!hasAnyValue) {
                return true;
            }

            var firstInvalid = null;
            function requireField(field, message, isValid) {
                if (isValid) {
                    clearValidation(field);
                    return;
                }
                markValidation(field, message);
                if (!firstInvalid) {
                    firstInvalid = field;
                }
            }

            requireField(
                searchEl,
                getValidationMessage('service_required', 'Debes indicar el servicio externo', 'External service is required'),
                !!(searchEl && String(searchEl.value || '').trim())
            );
            requireField(
                empresaEl,
                getValidationMessage('external_company_required', 'Debes indicar la empresa externa', 'External company is required'),
                !!(empresaEl && String(empresaEl.value || '').trim())
            );
            requireField(
                tallerEl,
                getValidationMessage('shop_price_required', 'Debes indicar el precio taller', 'Shop price is required'),
                EG.utils.parseNumericInput(tallerEl && tallerEl.value || 0) > 0
            );
            requireField(
                clientPriceEl,
                getValidationMessage('client_price_required', 'Debes indicar el precio cliente', 'Client price is required'),
                EG.utils.parseNumericInput(clientPriceEl && clientPriceEl.value || 0) > 0
            );

            if (firstInvalid && report) {
                if (firstInvalid === tallerEl) {
                    showShopPanel();
                }
                firstInvalid.reportValidity();
                firstInvalid.focus();
            }

            return !firstInvalid;
        }

        if (searchEl) {
            searchEl.addEventListener('input', function() {
                if (idEl) idEl.value = '';
                clearTimeout(searchTimer);
                var query = (searchEl.value || '').trim();
                if (query.length < 2) {
                    hideDropdown();
                    return;
                }
                searchTimer = setTimeout(function() {
                    var requestId = ++searchRequestId;
                    searchWithFallback({
                        query: query,
                        url: EG.cfg.URL_OUTSOURCED_SERVICES,
                        prefetch: EG.PREFETCH && (EG.PREFETCH.otros || EG.PREFETCH.otroServicios),
                        fields: ['nombre', 'empresa', 'empresa_ext', 'descripcion'],
                        onResults: function(results) {
                            if (requestId !== searchRequestId) return;
                            if (((searchEl.value || '').trim()) !== query) return;
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
                clearTimeout(searchTimer);
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

        if (toggleShopBtn) {
            toggleShopBtn.addEventListener('click', function(event) {
                event.preventDefault();
                event.stopPropagation();
                if (!shopPanel) {
                    return;
                }
                if (shopPanel.classList.contains('hidden')) {
                    showShopPanel();
                } else {
                    hideShopPanel();
                }
            });
        }

        if (tallerEl && !tallerEl.dataset.egBound) {
            tallerEl.dataset.egBound = '1';
            tallerEl.addEventListener('input', function() {
                clearValidation(tallerEl);
                if (!clientPriceEl.value && tallerEl.value) {
                    clientPriceEl.value = tallerEl.value;
                    clientPriceEl.dispatchEvent(new Event('input', { bubbles: true }));
                }
            });
            tallerEl.addEventListener('change', function() {
                clearValidation(tallerEl);
            });
        }

        [searchEl, empresaEl, clientPriceEl].forEach(function(field) {
            if (!field || field.dataset.egOtroBound) {
                return;
            }
            field.dataset.egOtroBound = '1';
            field.addEventListener('input', function() {
                clearValidation(field);
                syncSerializedState();
            });
            field.addEventListener('change', function() {
                clearValidation(field);
                syncSerializedState();
            });
        });

        document.addEventListener('click', function(e) {
            if (!row.contains(e.target)) {
                hideDropdown();
                hideShopPanel();
            }
        });

        row.__applyOtroData = function(data) {
            applyItem({
                id: data && (data.servicio_id || data.id),
                nombre: data && data.nombre,
                empresa: data && (data.empresa || data.empresa_ext || data.empresa_externa),
                precio_taller: data && data.precio_taller,
                precio: data && (data.precio !== undefined ? data.precio : data.precio_cliente)
            });
        };

        row.__validateOtroRow = validateRow;
    }

    function handleCreatedServicioFromReturn(context) {
        var servicioId = context.created_servicio_id || '';
        if (!servicioId) {
            return;
        }

        var rowId = resolveServicioTargetRowId(context);
        var row = getServicioRowById(rowId);
        if (!row) {
            row = addServicioRow(rowId || null);
        }
        if (!row || !row.__applyServData) {
            return;
        }

        row.__applyServData({
            servicio_id: servicioId,
            nombre: context.created_servicio_label || '',
            precio: context.created_servicio_precio || 0,
        });

        if (EG.utils.clearActiveRowContext) {
            EG.utils.clearActiveRowContext();
        }

        var focusTarget = row.querySelector('.serv-precio') || row.querySelector('.srv-input');
        if (focusTarget) {
            focusTarget.focus();
            focusTarget.select && focusTarget.select();
        }
    }

    function init() {
        document.querySelectorAll('#servicios-container .dynamic-element').forEach(setupServicioRow);
        document.querySelectorAll('#otros-container .dynamic-element').forEach(setupOtroRow);
        toggleEmptyHint('servicios-container', 'servicios-empty-hint');
        toggleEmptyHint('otros-container', 'otros-empty-hint');
    }

    function validateOtrosRows(report) {
        var rows = Array.from(document.querySelectorAll('#otros-container .dynamic-element'));
        for (var i = 0; i < rows.length; i += 1) {
            if (typeof rows[i].__validateOtroRow === 'function' && !rows[i].__validateOtroRow(report !== false)) {
                return false;
            }
        }
        return true;
    }

    EG.servicios = {
        addServicioRow: addServicioRow,
        setupServicioRow: setupServicioRow,
        addOtroServicioRow: addOtroServicioRow,
        addOtroRow: addOtroServicioRow,
        setupOtroServicioRow: setupOtroRow,
        setupOtroRow: setupOtroRow,
        handleCreatedServicioFromReturn: handleCreatedServicioFromReturn,
        validateOtrosRows: validateOtrosRows,
        init: init
    };

    window.addServicioRow = addServicioRow;
    window.addOtroServicioRow = addOtroServicioRow;
    window.addOtroRow = addOtroServicioRow;
})();
