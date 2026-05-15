/**
 * document_engine.js
 * 
 * "Capa de Inteligencia" - UX Móvil y Blindaje de Campos Calculados
 * 
 * Este script implementa:
 * 1. Forzar teclado numérico en móviles para campos de medida
 * 2. Blindar campos calculados (readonly) para que el usuario no los edite manualmente
 * 3. Mejoras de UX para mecánicos en el taller
 */

(function() {
    'use strict';

    /**
     * Inicializa cuando el DOM está listo
     */
    document.addEventListener('DOMContentLoaded', function() {
        console.log('🚀 Document Engine: Inicializando capa de inteligencia...');

        // ==================== 1. FORZAR TECLADO NUMÉRICO EN MÓVILES ====================
        initializeNumericInputs();

        // ==================== 2. BLINDAR CAMPOS CALCULADOS ====================
        protectCalculatedFields();

        // ==================== 3. MEJORAS ADICIONALES DE UX ====================
        enhanceMobileUX();

        console.log('✅ Document Engine: Inicialización completa');
    });

    /**
     * Forzar teclado numérico en móviles para campos de medida
     * Esto mejora drásticamente la experiencia del mecánico en el taller
     */
    function initializeNumericInputs() {
        // Campos de kilometraje
        const kmInputs = document.querySelectorAll('input[name="kilometraje"], input[name="kilometraje_ingreso"]');
        kmInputs.forEach(function(input) {
            input.setAttribute('inputmode', 'numeric');
            input.setAttribute('pattern', '[0-9]*');
            input.setAttribute('type', 'number');
            
            // Prevenir entrada de caracteres no numéricos
            input.addEventListener('keypress', function(e) {
                // Permitir: números, punto, coma, backspace, delete, tab, escape, enter
                const allowedKeys = /[0-9.,\b\s\t\e]/;
                const char = String.fromCharCode(e.which || e.keyCode);
                
                if (!allowedKeys.test(char) && !e.ctrlKey && !e.metaKey) {
                    e.preventDefault();
                }
            });
        });

        // Campos de precio/cantidad (repuestos, servicios)
        const priceInputs = document.querySelectorAll(
            'input[name*="precio"], input[name*="price"], ' +
            'input[name*="cantidad"], input[name*="quantity"], ' +
            'input[name*="subtotal"], input[name*="total"]'
        );
        priceInputs.forEach(function(input) {
            if (input.type === 'number' || input.type === 'text') {
                input.setAttribute('inputmode', 'decimal');
                input.setAttribute('pattern', '[0-9.,]*');
            }
        });

        console.log('✅ Teclados numéricos configurados para', kmInputs.length + priceInputs.length, 'campos');
    }

    /**
     * Blindar campos calculados para que el usuario no los edite manualmente
     * Los subtotales y totales son sagrados - solo se calculan, nunca se editan
     */
    function protectCalculatedFields() {
        // Identificar campos calculados por clase o ID
        const calculatedSelectors = [
            '.readonly-total',
            '.subtotal-field',
            '#t_repuestos',
            '#t_servicios',
            '#t_otros',
            '#t_iva',
            '#t_total',
            '[id^="t_"]',  // Todos los campos que empiezan con "t_"
            '.calculated-field'
        ];

        calculatedSelectors.forEach(function(selector) {
            const fields = document.querySelectorAll(selector);
            fields.forEach(function(field) {
                // Si es un input, hacerlo readonly
                if (field.tagName === 'INPUT') {
                    field.setAttribute('readonly', true);
                    field.setAttribute('tabindex', '-1');  // No permitir tabulación
                    
                    // Prevenir edición incluso si se quita el readonly
                    field.addEventListener('focus', function(e) {
                        e.target.blur();
                    });
                    
                    // Estilo visual para indicar que es readonly
                    field.style.cursor = 'not-allowed';
                    field.style.backgroundColor = 'rgba(40, 40, 60, 0.6)';
                }
                
                // Si es un span o div, prevenir edición de contenido
                if (field.tagName === 'SPAN' || field.tagName === 'DIV') {
                    field.setAttribute('contenteditable', 'false');
                    field.style.userSelect = 'none';
                }
            });
        });

        // Proteger campos de totales específicos
        const totalFields = [
            't_repuestos',
            't_servicios',
            't_otros',
            't_iva',
            't_total'
        ];

        totalFields.forEach(function(id) {
            const field = document.getElementById(id);
            if (field) {
                field.setAttribute('data-calculated', 'true');
                field.setAttribute('contenteditable', 'false');
                field.style.userSelect = 'none';
                
                // Prevenir edición accidental
                field.addEventListener('dblclick', function(e) {
                    e.preventDefault();
                    console.warn('⚠️ Este campo es calculado automáticamente y no puede editarse');
                });
            }
        });

        console.log('✅ Campos calculados protegidos');
    }

    /**
     * Mejoras adicionales de UX para móviles
     */
    function enhanceMobileUX() {
        // Detectar si es móvil
        const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
        
        if (!isMobile) {
            return;  // Solo aplicar mejoras en móviles
        }

        // Auto-enfocar el primer campo editable al cargar
        const firstEditableInput = document.querySelector(
            'input:not([readonly]):not([disabled]), ' +
            'textarea:not([readonly]):not([disabled]), ' +
            'select:not([disabled])'
        );
        
        if (firstEditableInput && !document.querySelector('.modal, .modal-open')) {
            // Pequeño delay para asegurar que el teclado no aparezca inmediatamente
            setTimeout(function() {
                // No auto-enfocar automáticamente (puede ser molesto)
                // firstEditableInput.focus();
            }, 500);
        }

        // Mejorar scroll en campos numéricos
        const numberInputs = document.querySelectorAll('input[type="number"]');
        numberInputs.forEach(function(input) {
            // Prevenir zoom en iOS al hacer doble tap
            input.addEventListener('touchstart', function(e) {
                if (e.touches.length > 1) {
                    e.preventDefault();
                }
            }, { passive: false });

            // Asegurar que el inputmode esté configurado
            if (!input.getAttribute('inputmode')) {
                input.setAttribute('inputmode', 'numeric');
            }
        });

        // Mejorar visibilidad de errores en móviles
        const errorMessages = document.querySelectorAll('.error, .text-red-400, [class*="error"]');
        errorMessages.forEach(function(error) {
            error.style.fontSize = '14px';  // Más grande en móviles
            error.style.padding = '8px';
            error.style.marginTop = '4px';
        });

        console.log('✅ Mejoras de UX móvil aplicadas');
    }

    /**
     * Función auxiliar para verificar si un campo es calculado
     */
    window.isCalculatedField = function(element) {
        return element.hasAttribute('data-calculated') ||
               element.classList.contains('readonly-total') ||
               element.classList.contains('calculated-field') ||
               element.id && element.id.startsWith('t_');
    };

    /**
     * Función auxiliar para proteger un campo dinámicamente creado
     */
    window.protectField = function(element) {
        if (element.tagName === 'INPUT') {
            element.setAttribute('readonly', true);
            element.setAttribute('tabindex', '-1');
            element.style.cursor = 'not-allowed';
        } else {
            element.setAttribute('contenteditable', 'false');
            element.setAttribute('data-calculated', 'true');
        }
    };

    // Exportar funciones para uso global
    window.DocumentEngine = {
        initializeNumericInputs: initializeNumericInputs,
        protectCalculatedFields: protectCalculatedFields,
        enhanceMobileUX: enhanceMobileUX,
        isCalculatedField: window.isCalculatedField,
        protectField: window.protectField
    };

})();


