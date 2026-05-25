/**
 * state.js - Estado base del formulario de documentos
 */

(function() {
    'use strict';

    var EG = window.EG = window.EG || {};
    var state = EG.state = EG.state || {};
    var bootstrapCache = null;

    function getForm() {
        return document.getElementById('document-form');
    }

    function buildDefaultData() {
        return {
            cliente: null,
            vehiculo: null,
            repuestos: [],
            servicios: [],
            otros: [],
            totales: {
                repuestos: 0,
                servicios: 0,
                otros: 0,
                iva: 0,
                total: 0
            }
        };
    }

    function safeParseBootstrap() {
        try {
            var el = document.getElementById('documentFormBootstrap');
            return el ? JSON.parse(el.textContent || '{}') : {};
        } catch (err) {
            console.warn('No se pudo leer documentFormBootstrap', err);
            return {};
        }
    }

    function normalizeBootstrap(raw) {
        var form = getForm();
        var lineItems = raw && raw.line_items ? raw.line_items : {};
        var repuestos = Array.isArray(lineItems.repuestos)
            ? lineItems.repuestos
            : (Array.isArray(raw && raw.repuestos) ? raw.repuestos : []);
        var servicios = Array.isArray(lineItems.servicios)
            ? lineItems.servicios
            : (Array.isArray(raw && raw.servicios) ? raw.servicios : []);
        var otros = Array.isArray(lineItems.otros)
            ? lineItems.otros
            : (Array.isArray(raw && raw.otros_servicios)
                ? raw.otros_servicios
                : (Array.isArray(raw && raw.otros) ? raw.otros : []));

        return {
            mode: String(
                (raw && raw.mode)
                || (form && form.dataset ? form.dataset.formMode : '')
                || 'clean'
            ).toLowerCase(),
            cliente: raw && raw.cliente ? raw.cliente : null,
            vehiculo_id: String(
                (raw && (raw.vehiculo_id || raw.vehiculoId))
                || ''
            ),
            line_items: {
                repuestos: repuestos,
                servicios: servicios,
                otros: otros
            },
            has_server_line_items: !!(
                raw
                && (
                    raw.has_server_line_items
                    || repuestos.length
                    || servicios.length
                    || otros.length
                )
            )
        };
    }

    function getBootstrap() {
        if (!bootstrapCache) {
            bootstrapCache = normalizeBootstrap(safeParseBootstrap());
        }
        return bootstrapCache;
    }

    function setBootstrap(nextBootstrap) {
        bootstrapCache = normalizeBootstrap(nextBootstrap || {});
        return bootstrapCache;
    }

    function hasServerLineItems() {
        var form = getForm();

        if (window.FORCE_NEW_DOCUMENT) {
            return false;
        }

        if (form && form.dataset && form.dataset.hasServerLineItems) {
            return String(form.dataset.hasServerLineItems) === '1';
        }

        return !!getBootstrap().has_server_line_items;
    }

    function isCleanMode() {
        var form = getForm();
        var formMode = form && form.dataset ? String(form.dataset.formMode || '').toLowerCase() : '';

        return !!window.FORCE_NEW_DOCUMENT || formMode === 'clean';
    }

    function syncDataFromBootstrap() {
        var bootstrap = getBootstrap();
        state.data = buildDefaultData();
        state.data.cliente = bootstrap.cliente || null;
        state.data.vehiculo = bootstrap.vehiculo_id ? { id: bootstrap.vehiculo_id } : null;
        state.data.repuestos = (bootstrap.line_items.repuestos || []).slice();
        state.data.servicios = (bootstrap.line_items.servicios || []).slice();
        state.data.otros = (bootstrap.line_items.otros || []).slice();
    }

    function reset() {
        console.log('Reset completo de state');
        if (window.DESARME_PREFILL) {
            console.log('Saltando reset por DESARME_PREFILL');
            return;
        }
        state.data = buildDefaultData();
        setBootstrap({
            mode: 'clean',
            cliente: null,
            vehiculo_id: '',
            line_items: {
                repuestos: [],
                servicios: [],
                otros: []
            },
            has_server_line_items: false
        });
    }

    function init() {
        syncDataFromBootstrap();

        if (window.FORCE_NEW_DOCUMENT && !window.DESARME_PREFILL) {
            reset();
        }
    }

    state.data = state.data || buildDefaultData();
    state.getBootstrap = getBootstrap;
    state.setBootstrap = setBootstrap;
    state.hasServerLineItems = hasServerLineItems;
    state.isCleanMode = isCleanMode;
    state.reset = reset;
    state.init = init;
})();
