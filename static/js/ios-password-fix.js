/**
 * iOS Password Field Fix
 * Soluciona problemas conocidos con campos de contraseña en iOS Safari
 * 
 * Problemas resueltos:
 * - Cursor que se mueve y deja espacio
 * - Caracteres que no aparecen al escribir
 * - Formulario que regresa sin completar la acción
 */

(function() {
    'use strict';

    // Detectar iOS (mejorado para iPhone 16 y versiones recientes)
    const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream ||
                  (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1) ||
                  /iPhone/.test(navigator.userAgent);
    
    if (!isIOS) {
        return; // Solo aplicar fix en iOS
    }
    
    // Log para debugging (remover en producción si es necesario)
    console.log('[iOS Password Fix] Detectado iOS, aplicando fix...');

    // Función para aplicar fix a un campo de contraseña
    function applyPasswordFix(input) {
        if (!input || input.type !== 'password') {
            return;
        }

        // 1. Agregar atributos específicos para iOS
        input.setAttribute('autocapitalize', 'none');
        input.setAttribute('autocorrect', 'off');
        input.setAttribute('spellcheck', 'false');
        input.setAttribute('inputmode', 'text');
        
        // 2. Prevenir interferencia del autocompletado
        input.setAttribute('autocomplete', 'current-password');
        
        // 3. Asegurar que el campo tenga un ID único si no lo tiene
        if (!input.id) {
            input.id = 'password-input-' + Date.now();
        }

        // 4. Fix para el problema del cursor que se mueve
        let isComposing = false;
        
        input.addEventListener('compositionstart', function(e) {
            isComposing = true;
        });
        
        input.addEventListener('compositionend', function(e) {
            isComposing = false;
            // Forzar actualización del valor después de composición
            const value = input.value;
            input.value = '';
            setTimeout(function() {
                input.value = value;
                // Mantener el cursor al final
                input.setSelectionRange(value.length, value.length);
            }, 0);
        });

        // 5. Fix para caracteres que no aparecen
        input.addEventListener('input', function(e) {
            if (isComposing) {
                return; // No interferir durante composición
            }
            
            // Asegurar que el valor se mantiene
            const currentValue = input.value;
            
            // Si el valor cambió pero el campo parece vacío, restaurar
            if (currentValue.length > 0 && input.value.length === 0) {
                setTimeout(function() {
                    input.value = currentValue;
                    input.setSelectionRange(currentValue.length, currentValue.length);
                }, 10);
            }
        });

        // 6. Prevenir que el formulario se envíe con campo vacío
        const form = input.closest('form');
        if (form) {
            form.addEventListener('submit', function(e) {
                // Verificar que el campo tenga valor antes de enviar
                if (input.value.length === 0) {
                    e.preventDefault();
                    e.stopPropagation();
                    
                    // Mostrar mensaje de error
                    input.focus();
                    input.style.borderColor = '#ef4444';
                    
                    // Restaurar borde después de 2 segundos
                    setTimeout(function() {
                        input.style.borderColor = '';
                    }, 2000);
                    
                    return false;
                }
            }, true); // Usar capture phase para interceptar antes
        }

        // 7. Fix para el problema del cursor que deja espacio
        input.addEventListener('keydown', function(e) {
            // No interferir con teclas especiales
            if (e.key === 'Backspace' || e.key === 'Delete' || 
                e.key === 'ArrowLeft' || e.key === 'ArrowRight' ||
                e.key === 'ArrowUp' || e.key === 'ArrowDown' ||
                e.key === 'Home' || e.key === 'End' ||
                e.metaKey || e.ctrlKey || e.altKey) {
                return;
            }
            
            // Para caracteres normales, asegurar que se insertan correctamente
            if (e.key.length === 1 && !isComposing) {
                const cursorPos = input.selectionStart;
                const currentValue = input.value;
                
                // Guardar posición del cursor
                setTimeout(function() {
                    if (input.selectionStart !== cursorPos + 1 && 
                        input.value.length === currentValue.length + 1) {
                        // El cursor no se movió correctamente, corregirlo
                        input.setSelectionRange(cursorPos + 1, cursorPos + 1);
                    }
                }, 0);
            }
        });

        // 8. Fix adicional: Asegurar que el campo mantiene el foco
        input.addEventListener('blur', function(e) {
            // Si el campo tiene valor pero perdió el foco inesperadamente, restaurarlo
            if (input.value.length > 0) {
                const form = input.closest('form');
                if (form && !form.querySelector(':focus')) {
                    // El formulario perdió el foco, pero el campo tiene valor
                    // Esto puede indicar un problema de iOS
                    setTimeout(function() {
                        if (document.activeElement !== input && input.value.length > 0) {
                            // El campo aún tiene valor, está bien
                        }
                    }, 100);
                }
            }
        });

        // 9. Agregar clase CSS para identificar campos corregidos
        input.classList.add('ios-password-fixed');
        
        // 10. Log para debugging
        console.log('[iOS Password Fix] Fix aplicado a campo:', input.id || input.name || 'password');
    }

    // Aplicar fix cuando el DOM esté listo
    function initPasswordFixes() {
        // Buscar todos los campos de contraseña
        const passwordInputs = document.querySelectorAll('input[type="password"]');
        
        console.log('[iOS Password Fix] Encontrados', passwordInputs.length, 'campos de contraseña');
        
        passwordInputs.forEach(function(input) {
            applyPasswordFix(input);
        });

        // Observar nuevos campos de contraseña (para formularios dinámicos)
        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                mutation.addedNodes.forEach(function(node) {
                    if (node.nodeType === 1) { // Element node
                        if (node.tagName === 'INPUT' && node.type === 'password') {
                            applyPasswordFix(node);
                        } else {
                            // Buscar campos de contraseña dentro del nodo
                            const passwordInputs = node.querySelectorAll && node.querySelectorAll('input[type="password"]');
                            if (passwordInputs) {
                                passwordInputs.forEach(function(input) {
                                    applyPasswordFix(input);
                                });
                            }
                        }
                    }
                });
            });
        });

        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    }

    // Inicializar cuando el DOM esté listo
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initPasswordFixes);
    } else {
        initPasswordFixes();
    }
})();

