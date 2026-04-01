/**
 * repuestos.js - Módulo de gestión de repuestos
 * 
 * Extraído del código embebido en document_form.html
 */

(function() {
    'use strict';

    const EG = window.EG = window.EG || {};

    let currentRepuestoRow = null;

    /**
     * Agrega una nueva fila de repuesto al contenedor
     */
    function addRepuestoRow(presetRowId) {
        var container = document.getElementById('repuestos-container');
        if (!container) {
            console.error('Contenedor de repuestos no encontrado');
            return null;
        }

        var isFirstRow = !container.querySelector('.dynamic-element');
        var row = document.createElement('div');
        row.className = 'dynamic-element';

        var rowId = (presetRowId && String(presetRowId).trim())
            ? String(presetRowId).trim()
            : 'rep_' + Date.now() + '_' + Math.floor(Math.random() * 1000);

        row.dataset.rowId = rowId;
        row.innerHTML = buildRepuestoRowHTML(rowId, isFirstRow);

        container.appendChild(row);
        setupRepuestoRow(row);
        return row;
    }

    function buildRepuestoRowHTML(rowId, isFirstRow) {
        var lbl = isFirstRow ? '<label class="block text-cyan-200 text-sm mb-1">' : '<label class="hidden">';
        var lblEnd = isFirstRow ? '</label>' : '</label>';
        return '<div class="doc-row-grid grid grid-cols-12 gap-2 items-center border border-cyan-400/30 rounded-lg p-2 sm:p-3 bg-black/20" data-row-id="' + rowId + '">' +
            '<div class="col-span-2 sm:col-span-2 relative min-w-0">' +
            lbl + (EG.I18N.code || 'Code') + lblEnd +
            '<input type="text" class="rep-codigo form-control w-full h-10 text-sm" placeholder="' + (EG.I18N.code || 'Code') + '">' +
            '<div class="rep-codigo-dropdown absolute z-50 w-full bg-gray-800 border border-cyan-400 rounded-lg shadow-lg hidden max-h-60 overflow-y-auto"></div>' +
            '<input type="hidden" class="rep-id"><input type="hidden" class="rep-origen" value="STOCK_BODEGA">' +
            '<input type="hidden" class="rep-pieza-desarme-id"><input type="hidden" class="rep-costo-linea"></div>' +
            '<div class="col-span-4 sm:col-span-4 description-field rep-search-container relative min-w-0">' +
            '<div class="flex items-center justify-between gap-2 mb-1"><span>' + (isFirstRow ? (EG.I18N.name || 'Name') : '') + '</span>' +
            '<span class="rep-desarme-badge hidden text-[10px] font-semibold px-2 py-0.5 rounded-full bg-amber-900/60 border border-amber-400/70 text-amber-200 uppercase">Usado</span></div>' +
            '<div class="flex gap-1">' +
            '<input type="text" class="rep-search form-control w-full h-10 text-sm flex-1" placeholder="' + (EG.I18N.type_to_search_parts || 'Buscar...') + '">' +
            '<button type="button" class="rep-create-btn btn-add flex-shrink-0 h-10 px-2">+</button></div>' +
            '<div class="rep-dropdown absolute z-50 w-full bg-gray-800 border border-cyan-400 rounded-lg shadow-lg hidden max-h-60 overflow-y-auto"></div>' +
            '<input type="hidden" class="rep-nombre"></div>' +
            '<div class="col-span-1 sm:col-span-1 min-w-0">' + lbl + (EG.I18N.qty || 'Qty') + lblEnd +
            '<input type="number" class="rep-cantidad form-control w-full h-10 text-sm" min="1" value="1"></div>' +
            '<div class="col-span-2 sm:col-span-2 min-w-0">' + lbl + (EG.I18N.sale_price || 'Price') + lblEnd +
            '<div class="relative"><span class="absolute left-2 top-1/2 -translate-y-1/2 text-cyan-300">$</span>' +
            '<input type="text" class="rep-precio-venta form-control w-full h-10 text-sm pl-6" placeholder="0"></div></div>' +
            '<div class="col-span-1 sm:col-span-1 min-w-0"><label class="block text-cyan-200 text-sm mb-1">' + (EG.I18N.subtotal || 'Subtotal') + '</label>' +
            '<input type="hidden" class="rep-subtotal" value="0">' +
            '<div class="rep-subtotal-view subtotal-field w-full h-10 text-right font-bold form-control text-sm flex items-center justify-end">$0</div></div>' +
            '<div class="col-span-1 sm:col-span-1"><button type="button" class="btn-add w-full h-10" onclick="var r=this.closest(\'.dynamic-element\');r.remove();if(typeof window.recalcTotales===\'function\')window.recalcTotales();">X</button></div></div>';
    }

    function setupRepuestoRow(row) {
        var searchInput = row.querySelector('.rep-search');
        var drop = row.querySelector('.rep-dropdown');
        var idHidden = row.querySelector('.rep-id');
        var inpCode = row.querySelector('.rep-codigo');
        var inpPV = row.querySelector('.rep-precio-venta');
        var qEl = row.querySelector('.rep-cantidad');
        var sub = row.querySelector('.rep-subtotal');
        var view = row.querySelector('.rep-subtotal-view');
        var repOrigen = row.querySelector('.rep-origen');
        var repPiezaDesarmeId = row.querySelector('.rep-pieza-desarme-id');
        var repCostoLinea = row.querySelector('.rep-costo-linea');
        var desarmeBadge = row.querySelector('.rep-desarme-badge');

        var timer = null;

        // Botón crear repuesto
        var btnCreate = row.querySelector('.rep-create-btn');
        if (btnCreate) {
            btnCreate.addEventListener('click', function() {
                currentRepuestoRow = row;
                var nombre = (searchInput && searchInput.value || '').split('|')[0].trim();
                var codigo = (inpCode && inpCode.value || '').trim();
                var rowId = row.dataset.rowId || '';
                if (!EG.cfg.URL_REPUESTO_CREATE_WINDOW) {
                    console.error('URL_REPUESTO_CREATE_WINDOW no configurada');
                    return;
                }
                var next = window.location.pathname + window.location.search;
                var createUrl = new URL(EG.cfg.URL_REPUESTO_CREATE_WINDOW, window.location.origin);
                createUrl.searchParams.set('next', next);
                createUrl.searchParams.set('target_row', rowId);
                if (nombre) createUrl.searchParams.set('prefill_nombre', nombre);
                if (codigo) createUrl.searchParams.set('prefill_code', codigo);
                window.location.href = createUrl.toString();
            });
        }

        // Aplica datos de repuesto a la fila
        function applyPartData(item) {
            if (!item) return;
            if (idHidden) idHidden.value = item.id || '';
            if (inpCode) inpCode.value = item.codigo || '';
            if (searchInput) searchInput.value = item.nombre || '';
            if (inpPV && item.precio_venta !== undefined) {
                var precio = EG.utils.parseNumericInput(item.precio_venta);
                inpPV.value = precio > 0 ? EG.utils.formatNumberInput(precio) : '';
            }
            if (repOrigen) repOrigen.value = item.origen_repuesto || 'STOCK_BODEGA';
            if (repPiezaDesarmeId) repPiezaDesarmeId.value = item.pieza_desarme_id || '';
            if (repCostoLinea) repCostoLinea.value = item.costo_linea || '';
            if (desarmeBadge) {
                var isDesarme = item.origen_repuesto === 'DESARME' || item.pieza_desarme_id;
                desarmeBadge.classList.toggle('hidden', !isDesarme);
            }
            recalc();
        }

        row.__applyRepData = function(data) {
            if (!data) return;
            applyPartData({
                id: data.id || '',
                codigo: data.codigo || '',
                nombre: data.nombre || '',
                precio_venta: data.precio_venta !== undefined ? data.precio_venta : (data.precio || 0),
                precio_compra: data.precio_compra,
                origen_repuesto: data.origen_repuesto,
                pieza_desarme_id: data.pieza_desarme_id,
                costo_linea: data.costo_linea
            });
            if (qEl && data.cantidad) {
                qEl.value = data.cantidad;
                qEl.dispatchEvent(new Event('input'));
            }
            recalc();
        };

        // Busca repuestos
        async function searchRepuestos(q) {
            if (!drop || !q || q.length < 2) {
                if (drop) drop.classList.add('hidden');
                return;
            }
            var localMatches = EG.utils.filterPrefetchItems(EG.PREFETCH.repuestos, ['codigo', 'nombre'], q, 15);
            if (localMatches.length) renderResultadosRepuestos(localMatches);
            try {
                var url = EG.cfg.URL_REPUESTO_SEARCH || '/cl/api/repuestos/';
                var r = await EG.utils.egFetch(url + '?q=' + encodeURIComponent(q));
                if (!r.ok) throw new Error('HTTP ' + r.status);
                var data = await r.json();
                var items = Array.isArray(data) ? data : (data.results || data.items || []);
                if (items.length) renderResultadosRepuestos(items);
            } catch (err) {
                console.error('buscarRepuestos', err);
                if (!localMatches.length && drop) {
                    drop.innerHTML = '<div class="p-3 text-red-300">' + (EG.I18N.server_error || 'Error') + '</div>';
                    drop.classList.remove('hidden');
                }
            }
        }

        function renderResultadosRepuestos(lista) {
            if (!drop) return;
            drop.innerHTML = '';
            if (!lista.length) {
                drop.innerHTML = '<div class="p-3 text-gray-300">' + (EG.I18N.no_parts || 'Sin repuestos') + '</div>';
                drop.classList.remove('hidden');
                return;
            }
            lista.forEach(function(item) {
                var div = document.createElement('div');
                div.className = 'srv-item px-3 py-2 hover:bg-cyan-700 cursor-pointer border-b border-cyan-600';
                div.dataset.id = item.id || '';
                div.dataset.codigo = item.codigo || '';
                div.dataset.nombre = item.nombre || '';
                div.dataset.precio = item.precio_venta_sugerido || item.precio_venta || item.precio || 0;
                div.innerHTML = '<div class="text-cyan-200 font-semibold">' + (item.codigo ? item.codigo + ' - ' : '') + item.nombre + '</div>' +
                    '<div class="text-xs text-gray-300">' + EG.utils.money(div.dataset.precio) + '</div>';
                div.addEventListener('click', function() {
                    seleccionarRepuesto(div);
                });
                drop.appendChild(div);
            });
            drop.setAttribute('role', 'listbox');
            drop.classList.remove('hidden');
        }

        function seleccionarRepuesto(el) {
            if (!el) return;
            applyPartData({
                id: el.dataset.id,
                codigo: el.dataset.codigo,
                nombre: el.dataset.nombre,
                precio_venta: EG.utils.parseNumericInput(el.dataset.precio)
            });
            if (drop) drop.classList.add('hidden');
        }

        function recalc() {
            var q = Number(qEl && qEl.value || 0);
            var p = EG.utils.parseNumericInput(inpPV && inpPV.value || 0);
            var subtotal = q * p;
            if (sub) sub.value = subtotal;
            if (view) view.textContent = EG.utils.money(subtotal);
            if (typeof window.recalcTotales === 'function') window.recalcTotales();
        }

        // Eventos
        if (searchInput) {
            searchInput.addEventListener('input', function(e) {
                clearTimeout(timer);
                timer = setTimeout(function() { searchRepuestos(e.target.value.trim()); }, 250);
            });
            searchInput.addEventListener('focus', function() {
                if (searchInput.value.trim().length >= 2) searchRepuestos(searchInput.value.trim());
            });
        }
        if (drop) {
            drop.addEventListener('click', function(e) {
                var item = e.target.closest('.srv-item');
                if (item) seleccionarRepuesto(item);
            });
        }
        document.addEventListener('click', function(e) {
            if (!row.contains(e.target) && drop) drop.classList.add('hidden');
        });
        if (qEl) qEl.addEventListener('input', recalc);
        if (inpPV) inpPV.addEventListener('input', recalc);
    }

    // Modal piezas usadas (desarme)
    function openUsedPartsModal() {
        var modal = document.getElementById('modal-used-parts');
        if (modal) modal.classList.remove('hidden');
    }

    function closeUsedPartsModal() {
        var modal = document.getElementById('modal-used-parts');
        if (modal) modal.classList.add('hidden');
    }

    // Exports
    EG.repuestos = {
        addRepuestoRow: addRepuestoRow,
        setupRepuestoRow: setupRepuestoRow,
        openUsedPartsModal: openUsedPartsModal,
        closeUsedPartsModal: closeUsedPartsModal
    };
    window.addRepuestoRow = addRepuestoRow;
    window.openUsedPartsModal = openUsedPartsModal;

})();
