/**
 * utils.js - Utilidades reutilizables del formulario de documentos
 * 
 * ExtraÃ­do del cÃ³digo embebido en document_form.html
 */

(function() {
    'use strict';

    const EG = window.EG = window.EG || {};
    const ACTIVE_ROW_CONTEXT_KEY = 'eg.documentForm.activeRowContext';
    const RETURN_CONTEXT_KEYS = [
        'cliente_id',
        'vehiculo_id',
        'created_cliente_id',
        'created_cliente_label',
        'created_vehiculo_id',
        'created_vehiculo_label',
        'created_repuesto_id',
        'created_repuesto_label',
        'created_repuesto_nombre',
        'created_repuesto_codigo',
        'created_repuesto_precio_venta',
        'created_repuesto_precio_compra',
        'created_repuesto_costo_linea',
        'created_servicio_id',
        'created_servicio_label',
        'created_servicio_precio',
        'target_row',
    ];

    // ==================== CSRF & FETCH ====================

    /**
     * Obtiene el token CSRF de las cookies
     */
    function getCookie(name) {
        const m = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
        return m ? m.pop() : '';
    }

    /**
     * Wrapper fetch con CSRF y headers por defecto
     */
    async function egFetch(url, opts = {}) {
        const CSRF = getCookie('csrftoken') || (document.querySelector('[name=csrfmiddlewaretoken]') || {}).value || '';
        const defaults = {
            credentials: 'same-origin',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': CSRF,
            }
        };
        const cfg = {
            ...defaults,
            ...opts,
            headers: { ...(defaults.headers || {}), ...((opts || {}).headers || {}) }
        };
        return fetch(url, cfg);
    }

    // ==================== PREFETCH ====================

    /**
     * Carga datos prefetch desde scripts JSON del DOM
     */
    function safeJSON(id) {
        try {
            const el = document.getElementById(id);
            return el ? JSON.parse(el.textContent) : [];
        } catch (err) {
            console.warn('âš ï¸ PREFETCH invÃ¡lido para', id, err);
            return [];
        }
    }

    function loadPrefetch() {
        EG.PREFETCH = EG.PREFETCH || {
            clientes: safeJSON('prefetchClientes'),
            vehiculos: safeJSON('prefetchVehiculos'),
            repuestos: safeJSON('prefetchRepuestos'),
            servicios: safeJSON('prefetchServicios'),
            otros: safeJSON('prefetchOtrosServicios'),
        };
        return EG.PREFETCH;
    }

    /**
     * Filtra items del prefetch por campos
     */
    function filterPrefetchItems(list, fields, query, limit = 15) {
        if (!Array.isArray(list) || !fields?.length) return [];
        
        const normalize = (value) => (value ?? '')
            .toString()
            .toLowerCase()
            .normalize('NFD')
            .replace(/\p{Diacritic}/gu, '');
        
        const needle = normalize(query);
        if (!needle) return [];

        const results = [];
        for (const item of list) {
            for (const field of fields) {
                if (normalize(item?.[field]).includes(needle)) {
                    results.push(item);
                    break;
                }
            }
            if (results.length >= limit) break;
        }
        return results;
    }

    // ==================== MONEY FORMATTING ====================

    let MONEY_FORMATTER = null;

    function buildMoneyFormatter(country) {
        const MONEY_FORMATS = {
            US: { locale: 'en-US', currency: 'USD', min: 2, max: 2 },
            CL: { locale: 'es-CL', currency: 'CLP', min: 0, max: 0 },
            MX: { locale: 'es-MX', currency: 'MXN', min: 2, max: 2 },
            PE: { locale: 'es-PE', currency: 'PEN', min: 2, max: 2 },
            VE: { locale: 'es-VE', currency: 'VES', min: 2, max: 2 },
            BR: { locale: 'pt-BR', currency: 'BRL', min: 2, max: 2 },
        };
        const cfg = MONEY_FORMATS[country] || MONEY_FORMATS.CL;
        return new Intl.NumberFormat(cfg.locale, {
            style: 'currency',
            currency: cfg.currency,
            minimumFractionDigits: cfg.min ?? 2,
            maximumFractionDigits: cfg.max ?? 2,
        });
    }

    function money(n) {
        if (!MONEY_FORMATTER) {
            const country = EG.cfg?.country || 'CL';
            MONEY_FORMATTER = buildMoneyFormatter(country);
        }
        const value = Number(n) || 0;
        return MONEY_FORMATTER.format(value);
    }

    function formatNumberInput(value) {
        const num = Number(value);
        if (!Number.isFinite(num)) return '';
        return String(Math.round(num));
    }

    const MILEAGE_LOCALES = {
        US: 'en-US', CL: 'es-CL', MX: 'es-MX', AR: 'es-AR',
        UY: 'es-UY', PE: 'es-PE', VE: 'es-VE', CO: 'es-CO',
        EC: 'es-EC', BR: 'pt-BR',
    };
    const MILEAGE_UNIT = { US: 'mi' };

    function formatMileage(value) {
        const num = parseInt(value, 10);
        if (!Number.isFinite(num) || isNaN(num)) return String(value || '');
        const country = (EG.cfg && EG.cfg.country) || 'CL';
        const locale = MILEAGE_LOCALES[country] || 'es-CL';
        const unit = MILEAGE_UNIT[country] || 'km';
        return new Intl.NumberFormat(locale, { maximumFractionDigits: 0 }).format(num) + ' ' + unit;
    }

    function parseNumericInput(value) {
        if (value === undefined || value === null) return 0;
        const num = Number(value.toString().replace(/[^0-9.-]/g, ''));
        return Number.isFinite(num) ? num : 0;
    }

    // ==================== DOM HELPERS ====================

    const $ = (sel, ctx = document) => ctx.querySelector(sel);
    const $$ = (sel, ctx = document) => Array.from(ctx.querySelectorAll(sel));

    function setText(selOrEl, txt) {
        const el = typeof selOrEl === 'string' ? $(selOrEl) : selOrEl;
        if (el) el.textContent = txt;
    }

    function showFieldError(el, msg) {
        const hint = document.createElement('div');
        hint.className = 'mt-1 text-red-300 text-sm eg-hint';
        hint.textContent = msg;
        el.closest('div')?.appendChild(hint);
        el.classList.add('ring-2', 'ring-red-500');
    }

    // ==================== NORMALIZERS ====================

    /**
     * Normaliza servicio para asegurar que siempre tenga 'id' y 'pk'
     */
    function normalizeServicio(servicio) {
        if (!servicio || typeof servicio !== 'object') return servicio;
        return {
            ...servicio,
            id: servicio.id || servicio.pk || '',
            pk: servicio.pk || servicio.id || '',
        };
    }

    

function extractResponseItems(data, preferredKeys = ['results', 'items']) {
    if (Array.isArray(data)) return data;

    for (const key of preferredKeys) {
        if (Array.isArray(data?.[key])) {
            return data[key];
        }
    }

    return [];
}
function getDocumentReturnTo() {
        return window.location.pathname + (window.location.search || '');
    }

    function buildContextualCreateUrl(baseUrl, params = {}) {
        const url = new URL(baseUrl, window.location.origin);
        Object.entries(params).forEach(([key, value]) => {
            if (value === undefined || value === null || value === '') {
                return;
            }
            url.searchParams.set(key, String(value));
        });
        return url.toString();
    }

    function getReturnContextParams() {
        const search = new URLSearchParams(window.location.search || '');
        const context = {};

        RETURN_CONTEXT_KEYS.forEach((key) => {
            const value = search.get(key);
            if (value !== null) {
                context[key] = value;
            }
        });

        context.hasAny = RETURN_CONTEXT_KEYS.some((key) => search.has(key));
        return context;
    }

    function cleanReturnContextParamsFromUrl() {
        const url = new URL(window.location.href);
        let changed = false;

        RETURN_CONTEXT_KEYS.forEach((key) => {
            if (url.searchParams.has(key)) {
                url.searchParams.delete(key);
                changed = true;
            }
        });

        if (changed) {
            window.history.replaceState({}, '', url.toString());
        }
    }

    function saveActiveRowContext(type, rowId) {
        if (!type || !rowId) return;
        try {
            sessionStorage.setItem(
                ACTIVE_ROW_CONTEXT_KEY,
                JSON.stringify({ type: String(type), rowId: String(rowId), savedAt: Date.now() })
            );
        } catch (err) {
            console.warn('No se pudo guardar el contexto de fila activa', err);
        }
    }

    function restoreActiveRowContext() {
        try {
            const raw = sessionStorage.getItem(ACTIVE_ROW_CONTEXT_KEY);
            return raw ? JSON.parse(raw) : null;
        } catch (err) {
            console.warn('No se pudo leer el contexto de fila activa', err);
            return null;
        }
    }

    function clearActiveRowContext() {
        try {
            sessionStorage.removeItem(ACTIVE_ROW_CONTEXT_KEY);
        } catch (err) {
            console.warn('No se pudo limpiar el contexto de fila activa', err);
        }
    }

    // ==================== INIT ====================

    function init() {
        loadPrefetch();
        const country = EG.cfg?.country || 'CL';
        MONEY_FORMATTER = buildMoneyFormatter(country);
        console.log('ðŸ”§ Utils initialized');
    }

    // Exports
    EG.fetch = egFetch;
    EG.utils = {
        getCookie,
        egFetch,
        safeJSON,
        loadPrefetch,
        filterPrefetchItems,
        money,
        formatMileage,
        formatNumberInput,
        parseNumericInput,
        buildMoneyFormatter,
        $,
        $$,
        setText,
        showFieldError,
        normalizeServicio,
        extractResponseItems,
        getDocumentReturnTo,
        buildContextualCreateUrl,
        getReturnContextParams,
        cleanReturnContextParamsFromUrl,
        saveActiveRowContext,
        restoreActiveRowContext,
        clearActiveRowContext,
        init
    };

})();





