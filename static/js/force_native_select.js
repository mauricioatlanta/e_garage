// FIX AGREGIVO: Forzar select nativo cuando Select2 falla
(function() {
    console.log('🔧 FORCE NATIVE SELECT: Iniciando...');
    
    function forceNativeSelect() {
        var vehiculoSelect = document.getElementById('id_vehiculo');
        if (!vehiculoSelect) {
            console.error('❌ No se encontró #id_vehiculo');
            return;
        }
        
        console.log('🔍 Analizando select de vehículos:');
        console.log('  - ID:', vehiculoSelect.id);
        console.log('  - Clases:', vehiculoSelect.className);
        console.log('  - Opciones:', vehiculoSelect.options.length);
        console.log('  - Estilo display:', window.getComputedStyle(vehiculoSelect).display);
        console.log('  - Estilo visibility:', window.getComputedStyle(vehiculoSelect).visibility);
        
        // Mostrar TODAS las opciones
        for (var i = 0; i < vehiculoSelect.options.length; i++) {
            console.log('    [' + i + '] ' + vehiculoSelect.options[i].value + ' = ' + vehiculoSelect.options[i].text);
        }
        
        // PASO 1: Remover completamente Select2
        if (window.jQuery) {
            var $vs = jQuery(vehiculoSelect);
            
            // Destruir Select2
            if ($vs.data('select2')) {
                try {
                    $vs.select2('destroy');
                    console.log('✅ Select2 destruido');
                } catch (e) {
                    console.error('❌ Error destruyendo Select2:', e);
                }
            }
            
            // Remover contenedores de Select2
            jQuery('.select2-container').each(function() {
                if (jQuery(this).find('#' + vehiculoSelect.id).length > 0) {
                    jQuery(this).remove();
                    console.log('✅ Contenedor Select2 removido');
                }
            });
        }
        
        // PASO 2: Limpiar completamente el select
        vehiculoSelect.className = 'native-select-vehiculo';
        vehiculoSelect.removeAttribute('data-select2-id');
        vehiculoSelect.removeAttribute('aria-hidden');
        vehiculoSelect.removeAttribute('tabindex');
        
        // PASO 3: Aplicar estilos VISIBLES
        vehiculoSelect.style.cssText = `
            /* FORZAR VISIBILIDAD */
            display: block !important;
            visibility: visible !important;
            opacity: 1 !important;
            position: relative !important;
            z-index: 1000 !important;
            
            /* ESTILOS VISUALES */
            width: 100% !important;
            min-height: 48px !important;
            padding: 12px 16px !important;
            margin: 10px 0 !important;
            
            /* ESTILOS CYBER */
            background: rgba(20, 20, 40, 0.98) !important;
            border: 2px solid #00f2fe !important;
            border-radius: 12px !important;
            color: #ffffff !important;
            font-size: 14px !important;
            font-weight: 500 !important;
            font-family: 'Inter', 'Segoe UI', sans-serif !important;
            
            /* EFECTOS */
            box-shadow: 0 4px 15px rgba(0, 242, 254, 0.3) !important;
            backdrop-filter: blur(10px) !important;
            transition: all 0.3s ease !important;
            
            /* SCROLL */
            overflow-y: auto !important;
            max-height: 200px !important;
        `;
        
        // PASO 4: Agregar hover effect
        vehiculoSelect.onmouseenter = function() {
            this.style.borderColor = '#00ffff';
            this.style.boxShadow = '0 4px 20px rgba(0, 255, 255, 0.4)';
        };
        
        vehiculoSelect.onmouseleave = function() {
            this.style.borderColor = '#00f2fe';
            this.style.boxShadow = '0 4px 15px rgba(0, 242, 254, 0.3)';
        };
        
        // PASO 5: Agregar label informativo
        var existingLabel = document.getElementById('vehiculo-force-label');
        if (!existingLabel) {
            var label = document.createElement('div');
            label.id = 'vehiculo-force-label';
            label.innerHTML = `
                <div style="
                    margin-bottom: 8px;
                    padding: 8px 12px;
                    background: rgba(0, 242, 254, 0.1);
                    border: 1px solid rgba(0, 242, 254, 0.3);
                    border-radius: 6px;
                    color: #00f2fe;
                    font-size: 12px;
                    font-weight: bold;
                ">
                    🚗 <strong>Vehículos disponibles:</strong> ${vehiculoSelect.options.length - 1}
                </div>
            `;
            vehiculoSelect.parentNode.insertBefore(label, vehiculoSelect);
        }
        
        // PASO 6: Crear botón de ayuda
        var helpBtn = document.createElement('button');
        helpBtn.innerHTML = '🔄 Mostrar Opciones';
        helpBtn.style.cssText = `
            display: block;
            width: 100%;
            margin: 10px 0;
            padding: 10px;
            background: linear-gradient(45deg, #00f2fe, #3b82f6);
            color: white;
            border: none;
            border-radius: 8px;
            font-weight: bold;
            cursor: pointer;
            font-size: 14px;
        `;
        helpBtn.onclick = function() {
            var optionsText = '';
            for (var i = 1; i < vehiculoSelect.options.length; i++) {
                optionsText += '• ' + vehiculoSelect.options[i].text + '\n';
            }
            alert('🚗 VEHÍCULOS DISPONIBLES:\n\n' + optionsText);
        };
        
        vehiculoSelect.parentNode.insertBefore(helpBtn, vehiculoSelect.nextSibling);
        
        console.log('✅ Select nativo forzado con ' + (vehiculoSelect.options.length - 1) + ' opciones');
        
        // PASO 7: Si hay menos de 2 opciones, intentar cargar desde prefetch
        if (vehiculoSelect.options.length <= 2 && window.PREFETCH && window.PREFETCH.vehiculos) {
            console.log('🔍 Intentando cargar desde prefetch...');
            
            var clienteSelect = document.getElementById('id_cliente');
            var clienteId = clienteSelect ? clienteSelect.value : null;
            
            if (clienteId) {
                var vehiculosCliente = window.PREFETCH.vehiculos.filter(function(v) {
                    return String(v.cliente_id) === String(clienteId);
                });
                
                if (vehiculosCliente.length > 0) {
                    // Limpiar y agregar
                    vehiculoSelect.innerHTML = '<option value="">Selecciona vehículo...</option>';
                    
                    vehiculosCliente.forEach(function(vehiculo) {
                        var option = document.createElement('option');
                        option.value = vehiculo.id;
                        option.textContent = vehiculo.text || vehiculo.label || 'Vehículo ' + vehiculo.id;
                        vehiculoSelect.appendChild(option);
                    });
                    
                    console.log('✅ ' + vehiculosCliente.length + ' vehículos cargados desde prefetch');
                }
            }
        }
    }
    
    // Ejecutar inmediatamente
    setTimeout(forceNativeSelect, 1000);
    
    // También ejecutar cuando cambie el cliente
    document.addEventListener('change', function(e) {
        if (e.target.id === 'id_cliente' && e.target.value) {
            setTimeout(forceNativeSelect, 500);
        }
    });
    
    // Exponer función globalmente
    window.forceNativeSelect = forceNativeSelect;
    
    console.log('✅ FORCE NATIVE SELECT cargado. Use window.forceNativeSelect()');
})();