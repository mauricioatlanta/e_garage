/**
 * ui_enhancements.js - Mejoras de UI inspiradas en documento_form_futurista.js
 * 
 * Incorpora funcionalidades útiles:
 * 1. Toast notifications
 * 2. Command palette (Ctrl+K)
 * 3. Mejoras visuales
 */

(function() {
    'use strict';

    const EG = window.EG = window.EG || {};

    // ==================== TOAST NOTIFICATIONS ====================
    function showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.textContent = message;
        toast.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: ${type === 'error' ? '#ef4444' : type === 'success' ? '#10b981' : '#3b82f6'};
            color: white;
            padding: 12px 16px;
            border-radius: 6px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            z-index: 9999;
            transform: translateX(120%);
            transition: transform 0.3s ease;
            max-width: 300px;
            word-wrap: break-word;
        `;
        
        document.body.appendChild(toast);

        // Animación de entrada
        setTimeout(() => toast.style.transform = 'translateX(0)', 10);

        // Remover después de 3 segundos
        setTimeout(() => {
            toast.style.transform = 'translateX(120%)';
            setTimeout(() => {
                if (toast.parentNode) {
                    toast.parentNode.removeChild(toast);
                }
            }, 300);
        }, 3000);
    }

    // ==================== COMMAND PALETTE ====================
    function createCommandPalette() {
        // Verificar si ya existe
        if (document.getElementById('command-palette')) {
            return;
        }

        const palette = document.createElement('div');
        palette.id = 'command-palette';
        palette.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0,0,0,0.8);
            z-index: 10000;
            display: none;
            align-items: flex-start;
            justify-content: center;
            padding-top: 100px;
        `;

        palette.innerHTML = `
            <div style="background: #1e293b; border: 1px solid #475569; border-radius: 8px; width: 90%; max-width: 600px; padding: 20px; box-shadow: 0 10px 25px rgba(0,0,0,0.5);">
                <div style="display: flex; align-items: center; margin-bottom: 16px;">
                    <input type="search" id="palette-search" placeholder="Buscar comando..." 
                           style="flex: 1; padding: 12px; background: #0f172a; border: 1px solid #475569; border-radius: 6px; color: white; font-size: 16px;">
                    <span style="margin-left: 8px; padding: 4px 8px; background: #475569; border-radius: 4px; font-size: 12px; color: #cbd5e1;">Ctrl+K</span>
                </div>
                <div id="palette-results" style="max-height: 400px; overflow-y: auto;"></div>
                <div style="margin-top: 16px; padding-top: 16px; border-top: 1px solid #475569; color: #94a3b8; font-size: 12px;">
                    <div style="display: flex; justify-content: space-between;">
                        <span>↑↓ para navegar</span>
                        <span>Enter para seleccionar</span>
                        <span>Esc para cerrar</span>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(palette);

        // Configurar eventos
        const searchInput = document.getElementById('palette-search');
        const resultsContainer = document.getElementById('palette-results');

        if (searchInput) {
            searchInput.addEventListener('input', function(e) {
                updateCommandResults(e.target.value);
            });

            searchInput.addEventListener('keydown', function(e) {
                if (e.key === 'Escape') {
                    closeCommandPalette();
                }
            });
        }

        // Comandos disponibles
        const commands = [
            { id: 'add-part', label: '➕ Agregar repuesto', action: () => EG.repuestos?.addRepuestoRow?.() },
            { id: 'add-service', label: '🔧 Agregar servicio', action: () => EG.servicios?.addServicioRow?.() },
            { id: 'add-other', label: '🏢 Agregar otro servicio', action: () => EG.otros?.addOtroRow?.() },
            { id: 'save-draft', label: '💾 Guardar borrador', action: () => EG.borrador?.saveDraft?.() },
            { id: 'calc-totals', label: '🧮 Recalcular totales', action: () => window.recalcTotales?.() },
            { id: 'new-client', label: '👤 Nuevo cliente', action: () => document.getElementById('btn-nuevo-cliente')?.click() },
            { id: 'new-vehicle', label: '🚗 Nuevo vehículo', action: () => document.getElementById('btn-nuevo-vehiculo')?.click() },
        ];

        function updateCommandResults(query = '') {
            if (!resultsContainer) return;

            const filtered = commands.filter(cmd => 
                cmd.label.toLowerCase().includes(query.toLowerCase())
            );

            resultsContainer.innerHTML = '';

            if (filtered.length === 0) {
                resultsContainer.innerHTML = '<div style="padding: 16px; text-align: center; color: #94a3b8;">No se encontraron comandos</div>';
                return;
            }

            filtered.forEach((cmd, index) => {
                const div = document.createElement('div');
                div.className = 'command-item';
                div.style.cssText = `
                    padding: 12px;
                    margin: 4px 0;
                    background: ${index === 0 ? '#334155' : 'transparent'};
                    border-radius: 6px;
                    cursor: pointer;
                    color: #e2e8f0;
                    display: flex;
                    align-items: center;
                    gap: 8px;
                `;
                div.innerHTML = `<span>${cmd.label}</span>`;
                
                div.addEventListener('click', () => {
                    cmd.action();
                    closeCommandPalette();
                });

                div.addEventListener('mouseenter', () => {
                    div.style.background = '#334155';
                });

                div.addEventListener('mouseleave', () => {
                    div.style.background = index === 0 ? '#334155' : 'transparent';
                });

                resultsContainer.appendChild(div);
            });
        }

        // Inicializar con todos los comandos
        updateCommandResults();
    }

    function openCommandPalette() {
        const palette = document.getElementById('command-palette');
        if (palette) {
            palette.style.display = 'flex';
            const search = document.getElementById('palette-search');
            if (search) {
                search.value = '';
                search.focus();
            }
            updateCommandResults('');
        }
    }

    function closeCommandPalette() {
        const palette = document.getElementById('command-palette');
        if (palette) {
            palette.style.display = 'none';
        }
    }

    // ==================== KEYBOARD SHORTCUTS ====================
    function initKeyboardShortcuts() {
        document.addEventListener('keydown', function(e) {
            // Ctrl+K: Abrir command palette
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                e.preventDefault();
                openCommandPalette();
                return;
            }

            // Alt+R: Agregar repuesto
            if (e.altKey && e.key === 'r') {
                e.preventDefault();
                if (EG.repuestos?.addRepuestoRow) {
                    EG.repuestos.addRepuestoRow();
                    showToast('Repuesto agregado', 'success');
                }
                return;
            }

            // Alt+S: Agregar servicio
            if (e.altKey && e.key === 's') {
                e.preventDefault();
                if (EG.servicios?.addServicioRow) {
                    EG.servicios.addServicioRow();
                    showToast('Servicio agregado', 'success');
                }
                return;
            }

            // Escape: Cerrar command palette
            if (e.key === 'Escape') {
                closeCommandPalette();
            }
        });
    }

    // ==================== INITIALIZATION ====================
    function init() {
        // Crear command palette
        createCommandPalette();
        
        // Inicializar shortcuts
        initKeyboardShortcuts();
        
        // Agregar estilos CSS para toast
        const style = document.createElement('style');
        style.textContent = `
            .toast {
                position: fixed;
                top: 20px;
                right: 20px;
                padding: 12px 16px;
                border-radius: 6px;
                color: white;
                z-index: 9999;
                transform: translateX(120%);
                transition: transform 0.3s ease;
                max-width: 300px;
                word-wrap: break-word;
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            }
            .toast.info { background: #3b82f6; }
            .toast.success { background: #10b981; }
            .toast.error { background: #ef4444; }
            .toast.warning { background: #f59e0b; }
            
            .command-item:hover {
                background: #334155 !important;
            }
        `;
        document.head.appendChild(style);

        console.log('🎨 UI Enhancements module initialized');
    }

    // ==================== EXPORTS ====================
    EG.ui_enhancements = {
        showToast,
        openCommandPalette,
        closeCommandPalette,
        init
    };

    // Hacer funciones disponibles globalmente
    window.showToast = showToast;
    window.openCommandPalette = openCommandPalette;
    window.closeCommandPalette = closeCommandPalette;

})();