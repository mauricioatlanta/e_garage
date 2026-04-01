/**
 * utils.js - Utilidades reutilizables del formulario de documentos
 * 
 * Extraído del código embebido en document_form.html
 */

(function() {
    'use strict';

    const EG = window.EG = window.EG || {};

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
        const CSRF = getCookie('csrftoken');
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
            console.warn('⚠️ PREFETCH inválido para', id, err);
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
        const digits = EG.config?.MONEY_FORMATS?.[EG.cfg?.country]?.max ?? 2;
        return num.toFixed(digits);
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

    // ==================== INIT ====================

    function init() {
        loadPrefetch();
        const country = EG.cfg?.country || 'CL';
        MONEY_FORMATTER = buildMoneyFormatter(country);
        console.log('🔧 Utils initialized');
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
        formatNumberInput,
        parseNumericInput,
        buildMoneyFormatter,
        $,
        $$,
        setText,
        showFieldError,
        normalizeServicio,
        init
    };

})();
