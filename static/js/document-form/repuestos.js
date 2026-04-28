/**
 * repuestos.js - Modulo de gestion de repuestos
 */

(function() {
    'use strict';

    var EG = window.EG = window.EG || {};

    function money(value) {
        return EG.utils.money(EG.utils.parseNumericInput(value || 0));
    }

    function escapeHtml(text) {
        return String(text || '')
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    function getContainer() {
        return document.getElementById('repuestos-container');
    }

    function generateRowId() {
        return 'rep_' + Date.now() + '_' + Math.floor(Math.random() * 1000);
    }

    function toggleRepuestosEmptyHint() {
        var container = getContainer();
        if (!container) return;
        container.classList.toggle('has-rows', !!container.querySelector('.dynamic-element'));
    }

    function refreshHeaderLabels() {
        var rows = Array.from(document.querySelectorAll('#repuestos-container .dynamic-element'));
        rows.forEach(function(row, index) {
            row.querySelectorAll('[data-first-row-label]').forEach(function(label) {
                label.classList.toggle('hidden', index !== 0);
            });
            row.querySelectorAll('[data-repeat-row-label]').forEach(function(label) {
                label.classList.toggle('hidden', index === 0);
            });
        });
    }

    function removeRow(row) {
        if (!row) return;
        row.remove();
        refreshHeaderLabels();
        toggleRepuestosEmptyHint();
        if (typeof window.serializeRows === 'function') window.serializeRows();
        if (typeof window.recalcTotales === 'function') window.recalcTotales();
    }

    function buildLabel(text, isFirstRow) {
        var baseClass = isFirstRow ? 'block text-cyan-200 text-sm mb-1' : 'hidden';
        return '<label class="' + baseClass + '" data-first-row-label>' + text + '</label>'
            + '<label class="hidden" data-repeat-row-label>' + text + '</label>';
    }

    function buildEyeIcon() {
        return '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false" class="rep-eye-icon">'
            + '<path d="M1.5 12s3.75-6 10.5-6 10.5 6 10.5 6-3.75 6-10.5 6S1.5 12 1.5 12Z"></path>'
            + '<circle cx="12" cy="12" r="3.25"></circle>'
            + '</svg>';
    }

    function buildRepuestoRowHTML(rowId, isFirstRow) {
        return ''
            + '<div class="doc-row-grid repuesto-row-grid grid gap-2 items-center border border-cyan-400/30 rounded-lg p-2 sm:p-3 bg-black/20" data-row-id="' + rowId + '">'
            + '  <div class="repuesto-cell repuesto-cell-code relative min-w-0">'
            +        buildLabel(EG.I18N.code || 'Code', isFirstRow)
            + '    <input type="text" class="rep-codigo form-control w-full h-10 text-sm" placeholder="' + escapeHtml(EG.I18N.code || 'Code') + '" autocomplete="off">'
            + '    <div class="rep-codigo-dropdown absolute z-50 w-full bg-gray-800 border border-cyan-400 rounded-lg shadow-lg hidden max-h-60 overflow-y-auto"></div>'
            + '    <input type="hidden" class="rep-id">'
            + '    <input type="hidden" class="rep-origen" value="STOCK_BODEGA">'
            + '    <input type="hidden" class="rep-pieza-desarme-id">'
            + '    <input type="hidden" class="rep-costo-linea">'
            + '    <input type="hidden" class="rep-stock-disponible">'
            + '    <input type="hidden" class="rep-stock-minimo">'
            + '  </div>'
            + '  <div class="repuesto-cell repuesto-cell-name description-field rep-search-container relative min-w-0">'
            +        buildLabel(EG.I18N.name || 'Name', isFirstRow)
            + '    <span class="rep-desarme-badge hidden text-[10px] font-semibold px-2 py-0.5 rounded-full bg-amber-900/60 border border-amber-400/70 text-amber-200 uppercase">Usado</span>'
            + '    <input type="text" class="rep-search form-control w-full h-10 text-sm" style="min-width: 0; width: 100%;" placeholder="' + escapeHtml(EG.I18N.type_to_search_parts || 'Buscar...') + '" autocomplete="off">'
            + '    <div class="rep-dropdown absolute z-50 w-full bg-gray-800 border border-cyan-400 rounded-lg shadow-lg hidden max-h-60 overflow-y-auto"></div>'
            + '    <input type="hidden" class="rep-nombre">'
            + '    <div class="rep-stock-alert hidden mt-2 rounded-md border px-2 py-1 text-xs leading-5"></div>'
            + '  </div>'
            + '  <div class="repuesto-cell repuesto-cell-qty min-w-0">'
            +        buildLabel(EG.I18N.qty || 'Qty', isFirstRow)
            + '    <input type="number" class="rep-cantidad form-control w-full h-10 text-sm" min="1" value="1">'
            + '  </div>'
            + '  <div class="repuesto-cell repuesto-cell-price min-w-0">'
            +        buildLabel(EG.I18N.sale_price || 'Price', isFirstRow)
            + '    <div class="rep-price-field relative min-w-0">'
            + '      <div class="relative">'
            + '        <span class="absolute left-2 top-1/2 -translate-y-1/2 text-cyan-300">$</span>'
            + '        <input type="text" class="rep-precio-venta form-control w-full h-10 text-sm pl-6 pr-10" placeholder="0">'
            + '        <button type="button" class="rep-toggle-cost" title="' + escapeHtml(EG.I18N.cost || 'Costo') + '" aria-label="' + escapeHtml(EG.I18N.cost || 'Costo') + '" aria-expanded="false">'
            +              buildEyeIcon()
            + '        </button>'
            + '      </div>'
            + '      <div class="rep-cost-panel hidden">'
            + '        <div class="rep-cost-input-wrap">'
            + '          <span class="rep-cost-label">' + escapeHtml(EG.I18N.cost || 'Costo') + ':</span>'
            + '          <div class="rep-cost-input-shell">'
            + '            <span class="rep-cost-currency">$</span>'
            + '            <input type="text" class="rep-cost-input" inputmode="numeric" autocomplete="off" placeholder="0">'
            + '          </div>'
            + '        </div>'
            + '        <span class="rep-cost-value">' + money(0) + '</span>'
            + '      </div>'
            + '    </div>'
            + '  </div>'
            + '  <div class="repuesto-cell repuesto-cell-total min-w-0">'
            +        buildLabel(EG.I18N.subtotal || 'Subtotal', isFirstRow)
            + '    <input type="hidden" class="rep-subtotal" value="0">'
            + '    <div class="rep-subtotal-view subtotal-field w-full h-10 text-right font-bold form-control text-sm flex items-center justify-end">' + money(0) + '</div>'
            + '  </div>'
            + '  <div class="repuesto-cell repuesto-cell-action">'
            +        buildLabel('&nbsp;', isFirstRow)
            + '    <button type="button" class="btn-add w-full h-10 rep-remove-btn" title="' + escapeHtml(EG.I18N.remove_row || 'Remove row') + '">X</button>'
            + '  </div>'
            + '</div>';
    }

    function normalizePartItem(item) {
        var part = item || {};
        return {
            id: part.id || part.pk || '',
            codigo: part.codigo || part.part_number || part.code || '',
            nombre: part.nombre || part.name || part.label || part.text || '',
            proveedor: part.proveedor || part.supplier || part.vendor || '',
            precio_venta: part.precio_venta_sugerido !== undefined ? part.precio_venta_sugerido :
                (part.precio_venta !== undefined ? part.precio_venta :
                (part.precio !== undefined ? part.precio : 0)),
            precio_compra: part.precio_compra !== undefined ? part.precio_compra : 0,
            stock: part.stock !== undefined ? part.stock :
                (part.cantidad_stock !== undefined ? part.cantidad_stock : 0),
            stock_minimo: part.stock_minimo !== undefined ? part.stock_minimo :
                (part.stockMinimo !== undefined ? part.stockMinimo :
                (part.stock_min !== undefined ? part.stock_min : 0)),
            origen_repuesto: part.origen_repuesto || 'STOCK_BODEGA',
            pieza_desarme_id: part.pieza_desarme_id || '',
            costo_linea: part.costo_linea !== undefined ? part.costo_linea : 0,
        };
    }

    function getRowById(rowId) {
        return rowId ? document.querySelector('#repuestos-container .dynamic-element[data-row-id="' + rowId + '"]') : null;
    }

    function resolveTargetRowId(context) {
        if (context && context.target_row) {
            return String(context.target_row);
        }
        var stored = EG.utils.restoreActiveRowContext ? EG.utils.restoreActiveRowContext() : null;
        if (stored && stored.type === 'repuesto' && stored.rowId) {
            return String(stored.rowId);
        }
        return '';
    }

    function markRowAsActive(row) {
        if (!row || !row.dataset.rowId || !EG.utils.saveActiveRowContext) {
            return;
        }
        EG.utils.saveActiveRowContext('repuesto', row.dataset.rowId);
    }

    function addRepuestoRow(presetRowId) {
        var container = getContainer();
        if (!container) {
            console.error('Contenedor de repuestos no encontrado');
            return null;
        }

        var rowId = String((presetRowId || '').trim() || generateRowId());
        var isFirstRow = !container.querySelector('.dynamic-element');
        var row = document.createElement('div');
        row.className = 'dynamic-element';
        row.dataset.rowId = rowId;
        row.innerHTML = buildRepuestoRowHTML(rowId, isFirstRow);
        container.appendChild(row);
        setupRepuestoRow(row);
        refreshHeaderLabels();
        toggleRepuestosEmptyHint();
        return row;
    }

    function setupRepuestoRow(row) {
        if (!row || row.dataset.egInitRepuesto) {
            return;
        }
        row.dataset.egInitRepuesto = '1';

        var searchInput = row.querySelector('.rep-search');
        var drop = row.querySelector('.rep-dropdown');
        var idHidden = row.querySelector('.rep-id');
        var inpCode = row.querySelector('.rep-codigo');
        var codeDrop = row.querySelector('.rep-codigo-dropdown');
        var inpPV = row.querySelector('.rep-precio-venta');
        var qEl = row.querySelector('.rep-cantidad');
        var sub = row.querySelector('.rep-subtotal');
        var view = row.querySelector('.rep-subtotal-view');
        var repOrigen = row.querySelector('.rep-origen');
        var repPiezaDesarmeId = row.querySelector('.rep-pieza-desarme-id');
        var repCostoLinea = row.querySelector('.rep-costo-linea');
        var repStockDisponible = row.querySelector('.rep-stock-disponible');
        var repStockMinimo = row.querySelector('.rep-stock-minimo');
        var repNombre = row.querySelector('.rep-nombre');
        var stockAlert = row.querySelector('.rep-stock-alert');
        var desarmeBadge = row.querySelector('.rep-desarme-badge');
        var removeBtn = row.querySelector('.rep-remove-btn');
        var toggleCostBtn = row.querySelector('.rep-toggle-cost');
        var costPanel = row.querySelector('.rep-cost-panel');
        var costInput = row.querySelector('.rep-cost-input');
        var costValue = row.querySelector('.rep-cost-value');
        var timer = null;

        function syncOrigenField(explicitOrigin) {
            var piezaDesarmeId = repPiezaDesarmeId && String(repPiezaDesarmeId.value || '').trim();
            var repuestoId = idHidden && String(idHidden.value || '').trim();
            var origin = explicitOrigin || '';

            if (piezaDesarmeId) {
                origin = 'DESARME';
            } else if (origin === 'DESARME') {
                origin = repuestoId ? 'STOCK_BODEGA' : 'EXTERNO';
            } else if (repuestoId) {
                origin = 'STOCK_BODEGA';
            } else {
                origin = 'EXTERNO';
            }

            if (repOrigen) {
                repOrigen.value = origin;
            }
            return origin;
        }

        function clearSelectedPartState() {
            if (idHidden) idHidden.value = '';
            if (repPiezaDesarmeId) repPiezaDesarmeId.value = '';
            if (repStockDisponible) repStockDisponible.value = '';
            if (repStockMinimo) repStockMinimo.value = '';
            syncOrigenField('');
            if (desarmeBadge) {
                desarmeBadge.classList.add('hidden');
            }
            if (stockAlert) {
                stockAlert.className = 'rep-stock-alert hidden mt-2 rounded-md border px-2 py-1 text-xs leading-5';
                stockAlert.textContent = '';
            }
        }

        function hideCostPanel() {
            if (costPanel) {
                costPanel.classList.add('hidden');
            }
            if (toggleCostBtn) {
                toggleCostBtn.setAttribute('aria-expanded', 'false');
            }
        }

        function setStockAlertState(message, tone) {
            if (!stockAlert) {
                return;
            }
            stockAlert.className = 'rep-stock-alert mt-2 rounded-md border px-2 py-1 text-xs leading-5';
            if (!message) {
                stockAlert.classList.add('hidden');
                stockAlert.textContent = '';
                return;
            }

            if (tone === 'danger') {
                stockAlert.classList.add('border-red-400/50', 'bg-red-950/50', 'text-red-200');
            } else if (tone === 'warning') {
                stockAlert.classList.add('border-amber-400/50', 'bg-amber-950/40', 'text-amber-200');
            } else {
                stockAlert.classList.add('border-cyan-400/40', 'bg-cyan-950/30', 'text-cyan-100');
            }
            stockAlert.textContent = message;
        }

        function updateStockAlert() {
            var origin = syncOrigenField(repOrigen && repOrigen.value || '');
            var repuestoId = idHidden && String(idHidden.value || '').trim();
            var stock = Number((repStockDisponible && repStockDisponible.value) || 0) || 0;
            var stockMinimo = Number((repStockMinimo && repStockMinimo.value) || 0) || 0;
            var cantidad = Number((qEl && qEl.value) || 0) || 0;

            if (!repuestoId || origin !== 'STOCK_BODEGA') {
                setStockAlertState('', '');
                return;
            }

            if (stock <= 0) {
                setStockAlertState('Sin stock disponible en bodega.', 'danger');
                return;
            }

            if (cantidad > stock) {
                setStockAlertState('Solicitas ' + cantidad + ' y solo hay ' + stock + ' en stock.', 'danger');
                return;
            }

            if (stockMinimo > 0 && (stock - cantidad) < stockMinimo) {
                setStockAlertState(
                    'Después de esta línea quedarían ' + (stock - cantidad) + ' unidades, bajo el mínimo de ' + stockMinimo + '.',
                    'warning'
                );
                return;
            }

            if (stockMinimo > 0 && stock <= stockMinimo) {
                setStockAlertState('Stock actual en umbral mínimo: ' + stock + ' / ' + stockMinimo + '.', 'warning');
                return;
            }

            setStockAlertState('', '');
        }

        function recalc() {
            var cantidad = Number((qEl && qEl.value) || 0) || 0;
            var precio = EG.utils.parseNumericInput(inpPV && inpPV.value || 0);
            var subtotal = cantidad * precio;
            if (sub) sub.value = subtotal;
            if (view) view.textContent = money(subtotal);
            updateStockAlert();
            if (typeof window.serializeRows === 'function') window.serializeRows();
            if (typeof window.recalcTotales === 'function') window.recalcTotales();
        }

        function syncCostField(rawValue, formatInput) {
            var costo = EG.utils.parseNumericInput(rawValue || 0);
            if (repCostoLinea) {
                repCostoLinea.value = costo > 0 ? costo : '';
            }
            if (costValue) {
                costValue.textContent = money(costo);
            }
            if (costInput) {
                if (formatInput) {
                    costInput.value = costo > 0 ? EG.utils.formatNumberInput(costo) : '';
                } else if (document.activeElement !== costInput) {
                    costInput.value = costo > 0 ? EG.utils.formatNumberInput(costo) : '';
                }
            }
            if (typeof window.serializeRows === 'function') window.serializeRows();
        }

        function applyPartData(item) {
            var part = normalizePartItem(item);
            if (idHidden) idHidden.value = part.id || '';
            if (inpCode) inpCode.value = part.codigo || '';
            if (searchInput) searchInput.value = part.nombre || '';
            if (repNombre) repNombre.value = part.nombre || '';
            if (inpPV) {
                var precio = EG.utils.parseNumericInput(part.precio_venta);
                inpPV.value = precio > 0 ? EG.utils.formatNumberInput(precio) : '';
            }
            if (repPiezaDesarmeId) repPiezaDesarmeId.value = part.pieza_desarme_id || '';
            if (repStockDisponible) repStockDisponible.value = part.stock !== undefined ? part.stock : '';
            if (repStockMinimo) repStockMinimo.value = part.stock_minimo !== undefined ? part.stock_minimo : '';
            syncOrigenField(part.origen_repuesto || '');
            var costoRaw = part.costo_linea !== undefined && part.costo_linea !== ''
                ? part.costo_linea
                : (part.precio_compra || 0);
            syncCostField(costoRaw, true);
            if (desarmeBadge) {
                var isDesarme = part.origen_repuesto === 'DESARME' || !!part.pieza_desarme_id;
                desarmeBadge.classList.toggle('hidden', !isDesarme);
            }
            hideCostPanel();
            recalc();
        }

        row.__applyRepData = function(data) {
            if (!data) return;
            applyPartData(data);
            if (qEl && data.cantidad) {
                qEl.value = data.cantidad;
            }
            recalc();
        };

        async function searchRepuestos(query, activeDrop) {
            if (!activeDrop) {
                return;
            }

            var q = String(query || '').trim();
            if (q.length < 2) {
                activeDrop.classList.add('hidden');
                return;
            }

            var localMatches = EG.utils.filterPrefetchItems(
                (EG.PREFETCH && EG.PREFETCH.repuestos) || [],
                ['codigo', 'nombre', 'part_number', 'proveedor', 'supplier', 'vendor'],
                q,
                15
            );
            if (localMatches.length) {
                renderResultadosRepuestos(localMatches, activeDrop);
            }

            try {
                var response = await EG.utils.egFetch((EG.cfg.URL_REPUESTO_SEARCH || EG.config.buildEndpoint('/api/repuestos/')) + '?q=' + encodeURIComponent(q));
                if (!response.ok) {
                    throw new Error('HTTP ' + response.status);
                }
                var data = await response.json();
                var items = EG.utils.extractResponseItems(data, ['results', 'items', 'repuestos']);
                if (!items.length && Array.isArray(data)) {
                    items = data;
                }
                renderResultadosRepuestos(items, activeDrop);
            } catch (err) {
                console.error('searchRepuestos', err);
                if (!localMatches.length) {
                    activeDrop.innerHTML = '<div class="p-3 text-red-300">' + (EG.I18N.server_error || 'Error') + '</div>';
                    activeDrop.classList.remove('hidden');
                }
            }
        }

        function renderResultadosRepuestos(lista, activeDrop) {
            if (!activeDrop) return;
            activeDrop.innerHTML = '';
            if (!lista || !lista.length) {
                activeDrop.innerHTML = '<div class="p-3 text-gray-300">' + (EG.I18N.no_parts || 'Sin repuestos') + '</div>';
                activeDrop.classList.remove('hidden');
                return;
            }

            lista.forEach(function(rawItem) {
                var item = normalizePartItem(rawItem);
                var div = document.createElement('div');
                div.className = 'srv-item px-3 py-2 hover:bg-cyan-700 cursor-pointer border-b border-cyan-600';
                div.dataset.id = item.id || '';
                div.dataset.codigo = item.codigo || '';
                div.dataset.nombre = item.nombre || '';
                div.dataset.precio = item.precio_venta || 0;
                div.dataset.precioCompra = item.precio_compra || 0;
                div.dataset.proveedor = item.proveedor || '';
                div.dataset.stock = item.stock || 0;
                div.dataset.stockMinimo = item.stock_minimo || 0;
                div.dataset.origen = item.origen_repuesto || 'STOCK_BODEGA';
                div.dataset.piezaDesarmeId = item.pieza_desarme_id || '';
                div.dataset.costoLinea = item.costo_linea || '';
                var stockText = 'Stock: ' + (Number(item.stock || 0) || 0);
                if ((Number(item.stock_minimo || 0) || 0) > 0) {
                    stockText += ' | Min: ' + (Number(item.stock_minimo || 0) || 0);
                }
                div.innerHTML = '<div class="text-cyan-200 font-semibold">'
                    + escapeHtml((item.codigo ? item.codigo + ' - ' : '') + (item.nombre || ''))
                    + '</div><div class="text-xs text-gray-300">'
                    + (item.proveedor ? escapeHtml(item.proveedor) + ' | ' : '')
                    + stockText + ' | '
                    + money(item.precio_venta || 0)
                    + '</div>';
                activeDrop.appendChild(div);
            });
            activeDrop.classList.remove('hidden');
        }

        function seleccionarRepuestoFromElement(el) {
            if (!el) return;
            applyPartData({
                id: el.dataset.id,
                codigo: el.dataset.codigo,
                nombre: el.dataset.nombre,
                precio_venta: el.dataset.precio,
                precio_compra: el.dataset.precioCompra,
                stock: el.dataset.stock,
                stock_minimo: el.dataset.stockMinimo,
                origen_repuesto: el.dataset.origen,
                pieza_desarme_id: el.dataset.piezaDesarmeId,
                costo_linea: el.dataset.costoLinea,
            });
            if (drop) drop.classList.add('hidden');
            if (codeDrop) codeDrop.classList.add('hidden');
            markRowAsActive(row);
        }

        if (toggleCostBtn) {
            toggleCostBtn.addEventListener('click', function(event) {
                event.preventDefault();
                event.stopPropagation();
                if (!costPanel) {
                    return;
                }
                document.querySelectorAll('#repuestos-container .rep-cost-panel').forEach(function(panel) {
                    if (panel !== costPanel) {
                        panel.classList.add('hidden');
                    }
                });
                document.querySelectorAll('#repuestos-container .rep-toggle-cost').forEach(function(button) {
                    if (button !== toggleCostBtn) {
                        button.setAttribute('aria-expanded', 'false');
                    }
                });
                costPanel.classList.toggle('hidden');
                var isOpen = !costPanel.classList.contains('hidden');
                toggleCostBtn.setAttribute('aria-expanded', String(isOpen));
                if (isOpen && costInput) {
                    costInput.focus();
                    costInput.select();
                }
            });
        }

        [row, searchInput, inpCode, inpPV, qEl].forEach(function(node) {
            if (node) {
                node.addEventListener('focus', function() { markRowAsActive(row); }, true);
                node.addEventListener('click', function(event) {
                    markRowAsActive(row);
                    if (!event.target.closest('.rep-cost-panel') && !event.target.closest('.rep-toggle-cost')) {
                        hideCostPanel();
                    }
                });
            }
        });

        if (removeBtn) {
            removeBtn.addEventListener('click', function() {
                removeRow(row);
            });
        }

        if (searchInput) {
            searchInput.addEventListener('input', function(event) {
                
                if (repNombre) repNombre.value = event.target.value || '';
                clearTimeout(timer);
                timer = setTimeout(function() {
                    searchRepuestos(event.target.value.trim(), drop);
                }, 250);
            });
            searchInput.addEventListener('focus', function() {
                if ((searchInput.value || '').trim().length >= 2) {
                    searchRepuestos(searchInput.value.trim(), drop);
                }
            });
        }

        if (inpCode) {
            inpCode.addEventListener('input', function(event) {
                
                clearTimeout(timer);
                timer = setTimeout(function() {
                    searchRepuestos(event.target.value.trim(), codeDrop || drop);
                }, 250);
            });
            inpCode.addEventListener('focus', function() {
                if ((inpCode.value || '').trim().length >= 2) {
                    searchRepuestos(inpCode.value.trim(), codeDrop || drop);
                }
            });
        }

        if (drop) {
            drop.addEventListener('click', function(event) {
                var item = event.target.closest('.srv-item');
                if (item) seleccionarRepuestoFromElement(item);
            });
        }
        if (codeDrop) {
            codeDrop.addEventListener('click', function(event) {
                var item = event.target.closest('.srv-item');
                if (item) seleccionarRepuestoFromElement(item);
            });
        }

        document.addEventListener('click', function(event) {
            if (!row.contains(event.target)) {
                if (drop) drop.classList.add('hidden');
                if (codeDrop) codeDrop.classList.add('hidden');
                if (costPanel) costPanel.classList.add('hidden');
                if (toggleCostBtn) toggleCostBtn.setAttribute('aria-expanded', 'false');
            }
        });

        if (qEl) qEl.addEventListener('input', recalc);
        if (inpPV) {
            inpPV.addEventListener('input', recalc);
            inpPV.addEventListener('change', recalc);
        }
        if (costInput) {
            costInput.addEventListener('input', function() {
                syncCostField(costInput.value, false);
            });
            costInput.addEventListener('change', function() {
                syncCostField(costInput.value, true);
            });
            costInput.addEventListener('blur', function() {
                syncCostField(costInput.value, true);
                window.setTimeout(function() {
                    if (document.activeElement !== toggleCostBtn && !(costPanel && costPanel.contains(document.activeElement))) {
                        hideCostPanel();
                    }
                }, 0);
            });
            costInput.addEventListener('keydown', function(event) {
                if (event.key === 'Enter') {
                    event.preventDefault();
                    syncCostField(costInput.value, true);
                    hideCostPanel();
                    if (inpPV) {
                        inpPV.focus();
                    } else {
                        costInput.blur();
                    }
                }
            });
        }

        syncOrigenField(repOrigen && repOrigen.value || '');
        updateStockAlert();
        toggleRepuestosEmptyHint();
        refreshHeaderLabels();
    }

    function handleCreatedRepuestoFromReturn(context) {
        var repuestoId = context.created_repuesto_id || '';
        if (!repuestoId) {
            return;
        }

        var rowId = resolveTargetRowId(context);
        var row = getRowById(rowId);
        if (!row) {
            row = addRepuestoRow(rowId || null);
        }
        if (!row || !row.__applyRepData) {
            return;
        }

        row.__applyRepData({
            id: repuestoId,
            codigo: context.created_repuesto_codigo || '',
            nombre: context.created_repuesto_nombre || context.created_repuesto_label || '',
            precio_venta: context.created_repuesto_precio_venta || context.created_repuesto_precio_compra || 0,
            cantidad: 1,
        });

        if (EG.utils.clearActiveRowContext) {
            EG.utils.clearActiveRowContext();
        }

        var focusTarget = row.querySelector('.rep-cantidad') || row.querySelector('.rep-search');
        if (focusTarget) {
            focusTarget.focus();
            focusTarget.select && focusTarget.select();
        }
    }

    function openUsedPartsModal() {
        var modal = document.getElementById('modal-used-parts');
        if (modal) modal.classList.remove('hidden');
    }

    function closeUsedPartsModal() {
        var modal = document.getElementById('modal-used-parts');
        if (modal) modal.classList.add('hidden');
    }

    function init() {
        document.querySelectorAll('#repuestos-container .dynamic-element').forEach(setupRepuestoRow);

        var modal = document.getElementById('modal-used-parts');
        if (modal && !modal.dataset.egBound) {
            modal.dataset.egBound = '1';
            var overlay = document.getElementById('used-parts-overlay');
            if (overlay) {
                overlay.addEventListener('click', closeUsedPartsModal);
            }
            var closeBtn = document.getElementById('close-used-parts');
            if (closeBtn) {
                closeBtn.addEventListener('click', closeUsedPartsModal);
            }
        }

        refreshHeaderLabels();
        toggleRepuestosEmptyHint();
    }

    EG.repuestos = {
        addRepuestoRow: addRepuestoRow,
        setupRepuestoRow: setupRepuestoRow,
        openUsedPartsModal: openUsedPartsModal,
        closeUsedPartsModal: closeUsedPartsModal,
        handleCreatedRepuestoFromReturn: handleCreatedRepuestoFromReturn,
        init: init
    };

    window.addRepuestoRow = addRepuestoRow;
    window.openUsedPartsModal = openUsedPartsModal;
})();

