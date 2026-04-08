/**
 * ui.js - Módulo de temas y modos de la UI
 * 
 * Extraído del código embebido en document_form.html
 */

(function() {
    'use strict';

    const EG = window.EG = window.EG || {};

    var shell = null;
    var selTipo = null;
    var selMode = null;
    var numeroView = null;
    var numeroHidden = null;

    /**
     * Aplica tema según tipo de documento
     */
    function applyTheme(tipo) {
        if (!shell) return;
        shell.classList.remove('theme-ot', 'theme-fac', 'theme-pres', 'theme-pts');
        var themeClass = 'theme-ot';
        if (tipo === 'FAC') themeClass = 'theme-fac';
        else if (tipo === 'PRES') themeClass = 'theme-pres';
        else if (tipo === 'PTS') themeClass = 'theme-pts';
        shell.classList.add(themeClass);
    }

    /**
     * Aplica UI según modo de operación
     */
    function applyModeDependentUI() {
        if (!selMode) return;
        var mode = selMode.value;
        var isParts = mode === 'parts';

        var vehicleSection = document.getElementById('vehicle-section');
        var milesSection = document.getElementById('miles-section');
        var tecnicoLabel = document.getElementById('tecnico-label');

        if (vehicleSection) vehicleSection.style.display = isParts ? 'none' : '';
        if (milesSection) milesSection.style.display = isParts ? 'none' : '';

        if (tecnicoLabel) {
            tecnicoLabel.textContent = isParts
                ? (tecnicoLabel.dataset.labelPts || 'Salesperson')
                : (tecnicoLabel.dataset.labelDefault || '');
        }
    }

    /**
     * Actualiza número de documento
     */
    async function updateDocumentNumber() {
        if (!selTipo) return;
        var tipo = selTipo.value;
        if (!tipo) return;
        try {
            var r = await EG.utils.egFetch(EG.cfg.URL_NEXT_NUMBER + '?tipo=' + encodeURIComponent(tipo));
            if (!r.ok) throw new Error('HTTP ' + r.status);
            var data = await r.json();
            var next = data.number || data.numero || data.next || 'Auto-generated';
            setText(numeroView, next);
            if (numeroHidden) numeroHidden.value = next;
        } catch (err) {
            console.error('Error next-number:', err);
            setText(numeroView, '— error —');
            if (numeroHidden) numeroHidden.value = '';
        }
    }

    function setText(selOrEl, txt) {
        var el = typeof selOrEl === 'string' ? document.querySelector(selOrEl) : selOrEl;
        if (el) el.textContent = txt;
    }

    function bindDetailToolbar() {
        document.querySelectorAll('[data-doc-add-target]').forEach(function(btn) {
            if (btn.dataset.egToolbarBound) return;
            btn.dataset.egToolbarBound = '1';
            btn.addEventListener('click', function() {
                var targetId = btn.getAttribute('data-doc-add-target');
                var target = targetId ? document.getElementById(targetId) : null;
                if (target) target.click();
            });
        });
    }

    function updateVehicleCardState() {
        var vehicleSection = document.getElementById('vehicle-section');
        var clienteSelect = document.getElementById('id_cliente');
        if (!vehicleSection || !clienteSelect) return;
        vehicleSection.classList.toggle('is-disabled', !clienteSelect.value);
    }

    /**
     * Actualiza badge de estado de pago
     */
    function updatePaymentStatusBadge() {
        var sel = document.getElementById('id_payment_status');
        var badge = document.getElementById('payment-status-badge');
        if (!badge || !sel) return;
        badge.classList.remove('doc-console-payment-paid', 'doc-console-payment-pending', 'doc-console-payment-partial');
        var v = (sel.value || '').toUpperCase();
        if (v === 'PAGADO' || v === 'PAID') badge.classList.add('doc-console-payment-paid');
        else if (v === 'PARCIAL' || v === 'PARTIAL') badge.classList.add('doc-console-payment-partial');
        else badge.classList.add('doc-console-payment-pending');
    }

    function bindSubmitState() {
        var form = document.getElementById('document-form');
        var saveBtn = document.querySelector('.doc-save-btn');
        if (!form || !saveBtn || saveBtn.dataset.egSubmitBound) return;
        saveBtn.dataset.egSubmitBound = '1';

        function resetSubmitState() {
            saveBtn.disabled = false;
            saveBtn.classList.remove('is-loading');
            saveBtn.textContent = saveBtn.dataset.defaultLabel || 'Save Document';
        }

        form.addEventListener('submit', function(event) {
            if (event.defaultPrevented) return;
            saveBtn.disabled = true;
            saveBtn.classList.add('is-loading');
            saveBtn.textContent = saveBtn.dataset.loadingLabel || 'Saving...';
            window.setTimeout(function() {
                if (window.__EG_INVALID_SERVICE_ROWS__ && window.__EG_INVALID_SERVICE_ROWS__.length) {
                    resetSubmitState();
                }
            }, 0);
        });
    }

    function getSpreadsheetCellTargets(cell) {
        if (!cell) return [];
        return Array.from(cell.querySelectorAll('input:not([type="hidden"]):not([disabled]):not([readonly]), select:not([disabled]), textarea:not([disabled]):not([readonly])'));
    }

    function focusSpreadsheetTarget(cell, direction) {
        var targets = getSpreadsheetCellTargets(cell);
        if (!targets.length) return false;
        var target = direction === 'last' ? targets[targets.length - 1] : targets[0];
        target.focus();
        if (typeof target.select === 'function' && target.tagName !== 'SELECT') target.select();
        return true;
    }

    function moveSpreadsheetHorizontal(input, step) {
        var cell = input && input.closest('td');
        var row = input && input.closest('tr.dynamic-element');
        if (!cell || !row) return false;
        var sibling = step > 0 ? cell.nextElementSibling : cell.previousElementSibling;
        while (sibling) {
            if (focusSpreadsheetTarget(sibling, step > 0 ? 'first' : 'last')) return true;
            sibling = step > 0 ? sibling.nextElementSibling : sibling.previousElementSibling;
        }
        return false;
    }

    function moveSpreadsheetVertical(input, step) {
        var cell = input && input.closest('td');
        var row = input && input.closest('tr.dynamic-element');
        var tbody = row && row.parentElement;
        if (!cell || !row || !tbody) return false;
        var columnIndex = cell.cellIndex;
        var rows = Array.from(tbody.querySelectorAll('tr.dynamic-element'));
        var rowIndex = rows.indexOf(row);
        if (rowIndex === -1) return false;

        for (var i = rowIndex + step; i >= 0 && i < rows.length; i += step) {
            var targetCell = rows[i].cells[columnIndex];
            if (targetCell && focusSpreadsheetTarget(targetCell, 'first')) return true;
        }
        return false;
    }

    function bindSpreadsheetNavigation() {
        if (document.body.dataset.egSpreadsheetNavBound) return;
        document.body.dataset.egSpreadsheetNavBound = '1';

        document.addEventListener('focusin', function(event) {
            var target = event.target;
            var cell = target && target.closest ? target.closest('.doc-sheet-cell') : null;
            var row = target && target.closest ? target.closest('tr.dynamic-element') : null;
            document.querySelectorAll('.doc-sheet-cell.is-focus-cell').forEach(function(el) {
                if (el !== cell) el.classList.remove('is-focus-cell');
            });
            document.querySelectorAll('tr.dynamic-element.is-focus-row').forEach(function(el) {
                if (el !== row) el.classList.remove('is-focus-row');
            });
            if (cell) cell.classList.add('is-focus-cell');
            if (row) row.classList.add('is-focus-row');
        });

        document.addEventListener('focusout', function(event) {
            var cell = event.target && event.target.closest ? event.target.closest('.doc-sheet-cell') : null;
            var row = event.target && event.target.closest ? event.target.closest('tr.dynamic-element') : null;
            window.setTimeout(function() {
                if (cell && !cell.contains(document.activeElement)) cell.classList.remove('is-focus-cell');
                if (row && !row.contains(document.activeElement)) row.classList.remove('is-focus-row');
            }, 0);
        });

        document.addEventListener('keydown', function(event) {
            var target = event.target;
            if (!target || !target.closest || !target.closest('.doc-sheet-table')) return;
            if (target.tagName === 'TEXTAREA') return;

            if (event.key === 'Enter') {
                event.preventDefault();
                moveSpreadsheetHorizontal(target, 1);
                return;
            }
            var canUseCaret = typeof target.selectionStart === 'number' && typeof target.selectionEnd === 'number' && typeof target.value === 'string';
            if (event.key === 'ArrowRight' && canUseCaret && (target.selectionStart === target.selectionEnd) && target.selectionEnd === target.value.length) {
                if (moveSpreadsheetHorizontal(target, 1)) event.preventDefault();
                return;
            }
            if (event.key === 'ArrowLeft' && canUseCaret && (target.selectionStart === target.selectionEnd) && target.selectionStart === 0) {
                if (moveSpreadsheetHorizontal(target, -1)) event.preventDefault();
                return;
            }
            if (event.key === 'ArrowDown') {
                if (moveSpreadsheetVertical(target, 1)) event.preventDefault();
                return;
            }
            if (event.key === 'ArrowUp') {
                if (moveSpreadsheetVertical(target, -1)) event.preventDefault();
            }
        });
    }

    function bindCostToggles() {
        function toggleSection(buttonId, tableSelector) {
            var btn = document.getElementById(buttonId);
            var table = document.querySelector(tableSelector);
            if (!btn || !table || btn.dataset.egBound) return;
            btn.dataset.egBound = '1';
            btn.addEventListener('click', function() {
                table.classList.toggle('cost-visible');
            });
        }

        toggleSection('toggle-repuesto-cost', '.doc-sheet-table-repuestos');
        toggleSection('toggle-otro-cost', '.doc-sheet-table-otros');
    }

    /**
     * Inicializar eventos de UI
     */
    function init() {
        shell = document.getElementById('doc-shell');
        selTipo = document.getElementById('id_tipo');
        selMode = document.getElementById('doc_mode');
        numeroView = document.getElementById('id_numero');

        // Crear input oculto para número
        if (numeroView && !document.querySelector('input[name="numero_documento"]')) {
            numeroHidden = document.createElement('input');
            numeroHidden.type = 'hidden';
            numeroHidden.name = 'numero_documento';
            var form = document.getElementById('document-form');
            if (form) form.appendChild(numeroHidden);
        }

        // Badge estado de pago
        updatePaymentStatusBadge();
        var selPay = document.getElementById('id_payment_status');
        if (selPay) selPay.addEventListener('change', updatePaymentStatusBadge);

        // Tema según tipo
        if (selTipo) {
            selTipo.addEventListener('change', function() {
                var t = selTipo.value;
                applyTheme(t);
                updateDocumentNumber();
            });
            // Aplicar tema inicial
            var t0 = selTipo.value || 'OT';
            applyTheme(t0);
        }

        // Modo según operación
        if (selMode) {
            selMode.addEventListener('change', applyModeDependentUI);
            applyModeDependentUI();
        }

        bindDetailToolbar();
        updateVehicleCardState();
        bindSubmitState();
        bindSpreadsheetNavigation();
        bindCostToggles();
        document.addEventListener('cliente:seleccionado', updateVehicleCardState);
        var clienteSelect = document.getElementById('id_cliente');
        if (clienteSelect) clienteSelect.addEventListener('change', updateVehicleCardState);

        console.log('UI module initialized');
    }

    // Exports
    EG.ui = {
        applyTheme: applyTheme,
        applyModeDependentUI: applyModeDependentUI,
        updateDocumentNumber: updateDocumentNumber,
        updatePaymentStatusBadge: updatePaymentStatusBadge,
        init: init
    };

})();
