/**
 * config.js - Configuración global del formulario de documentos
 * 
 * Extraído del código embebido en document_form.html
 * Mantiene backward compatibility con window.EG.cfg
 */

(function() {
    'use strict';

    const EG = window.EG = window.EG || {};
    EG.cfg = EG.cfg || {};

    /**
     * Detecta el país desde el path o formulario
     */
    function detectCountry() {
        const formEl = document.getElementById('document-form');
        if (formEl && formEl.dataset.countryCode) {
            return String(formEl.dataset.countryCode).toUpperCase();
        }
        const path = (window.location.pathname || '').toLowerCase();
        if (path.startsWith('/us/')) return 'US';
        if (path.startsWith('/cl/')) return 'CL';
        if (path.startsWith('/mx/')) return 'MX';
        if (path.startsWith('/pe/')) return 'PE';
        if (path.startsWith('/br/')) return 'BR';
        return 'CL'; // Default
    }

    /**
     * Lee endpoints desde data-* attributes del formulario
     */
    function loadEndpointsFromForm() {
        const form = document.getElementById('document-form');
        if (!form) return;

        EG.cfg.URL_NEXT_NUMBER = EG.cfg.URL_NEXT_NUMBER || form.dataset.urlNextNumber;
        EG.cfg.URL_CLIENT_SEARCH = EG.cfg.URL_CLIENT_SEARCH || form.dataset.urlClientSearch;
        EG.cfg.URL_VEHICULOS_BY_CLI = EG.cfg.URL_VEHICULOS_BY_CLI || form.dataset.urlVehiculosByCli;
        EG.cfg.URL_REPUESTO_BY_CODE = EG.cfg.URL_REPUESTO_BY_CODE || form.dataset.urlRepuestoByCode;
        EG.cfg.URL_REPUESTO_SEARCH = EG.cfg.URL_REPUESTO_SEARCH || form.dataset.urlRepuestoSearch;
        EG.cfg.URL_REPUESTO_CREATE = EG.cfg.URL_REPUESTO_CREATE || form.dataset.urlRepuestoCreate;
        EG.cfg.URL_REPUESTO_CREATE_WINDOW = EG.cfg.URL_REPUESTO_CREATE_WINDOW || form.dataset.urlRepuestoCreatePage;
        EG.cfg.URL_SERVICE_SEARCH = EG.cfg.URL_SERVICE_SEARCH || form.dataset.urlServiceSearch;
        EG.cfg.URL_SERVICE_CREATE = EG.cfg.URL_SERVICE_CREATE || form.dataset.urlServiceCreate;
        EG.cfg.URL_OUTSOURCED_SERVICES = EG.cfg.URL_OUTSOURCED_SERVICES || form.dataset.urlOutsourcedServices;
        EG.cfg.URL_USED_PARTS = EG.cfg.URL_USED_PARTS || form.dataset.urlUsedParts;
    }

    /**
     * Construye endpoint absoluto desde relativo
     */
    function buildEndpoint(url) {
        if (!url) return '';
        if (/^https?:\/\//i.test(url)) return url;
        if (url.startsWith('/')) return url;
        const path = window.location.pathname || '/';
        const parts = path.split('/').filter(Boolean);
        if (!parts.length) return `/${url.replace(/^\//, '')}`;
        const countrySegment = parts[0];
        return `/${countrySegment}/${url.replace(/^\//, '')}`;
    }

    /**
     * Configuración de formato de moneda por país
     */
    const MONEY_FORMATS = {
        US: { locale: 'en-US', currency: 'USD', min: 2, max: 2 },
        CL: { locale: 'es-CL', currency: 'CLP', min: 0, max: 0 },
        MX: { locale: 'es-MX', currency: 'MXN', min: 2, max: 2 },
        PE: { locale: 'es-PE', currency: 'PEN', min: 2, max: 2 },
        VE: { locale: 'es-VE', currency: 'VES', min: 2, max: 2 },
        BR: { locale: 'pt-BR', currency: 'BRL', min: 2, max: 2 },
    };

    /**
     * Inicializar configuración completa
     */
    function init() {
        // País
        if (!EG.cfg.country) {
            EG.cfg.country = detectCountry();
        }
        EG.COUNTRY = EG.COUNTRY || EG.cfg.country;

        // Cargar endpoints desde formulario
        loadEndpointsFromForm();

        // Tax lines desde ui_config
        const taxLinesScript = document.getElementById('uiConfigTaxLines');
        if (taxLinesScript) {
            try {
                EG.cfg.taxLines = JSON.parse(taxLinesScript.textContent);
            } catch (e) {
                console.error('Error parsing taxLines:', e);
                EG.cfg.taxLines = [];
            }
        } else {
            EG.cfg.taxLines = [];
        }

        // Sales tax legacy
        if (typeof EG.cfg.salesTax !== 'number') {
            EG.cfg.salesTax = 0.08;
        }

        console.log('📋 Document Form Config initialized:', {
            country: EG.cfg.country,
            endpoints: Object.keys(EG.cfg).filter(k => k.startsWith('URL_')).length
        });
    }

    // Exports
    EG.config = {
        init,
        detectCountry,
        loadEndpointsFromForm,
        buildEndpoint,
        MONEY_FORMATS
    };

})();
