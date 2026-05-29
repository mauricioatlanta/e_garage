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

    /**
     * Inicializar eventos de UI
     */
    function init() {
        shell = document.getElementById('doc-shell');
        selTipo = document.getElementById('id_tipo');
        selMode = document.getElementById('doc_mode');
        numeroView = document.getElementById('id_numero');
        numeroHidden = document.querySelector('input[name="numero"]');

        // Crear input oculto para número
        if (!numeroHidden && numeroView && !document.querySelector('input[name="numero_documento"]')) {
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
