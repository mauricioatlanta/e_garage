// FIX DE EMERGENCIA para vehículos no mostrados
// Este script se ejecuta inmediatamente y fuerza la visualización de vehículos

(function() {
    console.log('🚨 EMERGENCY FIX: Iniciando fix de emergencia para vehículos...');
    
    // Función para forzar la visualización de vehículos
    function emergencyFixVehiculos() {
        console.log('🔧 EMERGENCY FIX: Ejecutando...');
        
        // 1. Buscar el select de vehículos
        var vehiculoSelect = document.getElementById('id_vehiculo');
        if (!vehiculoSelect) {
            console.error('🚨 No se encontró #id_vehiculo');
            return;
        }
        
        console.log('📊 Estado actual del select:');
        console.log('  - Opciones:', vehiculoSelect.options.length);
        console.log('  - Valor:', vehiculoSelect.value);
        console.log('  - HTML interno:', vehiculoSelect.innerHTML.substring(0, 200) + '...');
        
        // 2. Verificar si hay opciones ocultas
        if (vehiculoSelect.options.length > 1) {
            console.log('✅ Hay opciones en el select, pero no se ven');
            
            // Forzar la visualización cambiando estilos
            vehiculoSelect.style.display = 'block';
            vehiculoSelect.style.visibility = 'visible';
            vehiculoSelect.style.opacity = '1';
            vehiculoSelect.style.height = 'auto';
            
            // 3. Si jQuery está disponible, destruir y recrear Select2
            if (window.jQuery) {
                console.log('🔄 Recreando Select2...');
                var $vs = jQuery(vehiculoSelect);
                
                // Destruir Select2 si existe
                if ($vs.data('select2')) {
                    try {
                        $vs.select2('destroy');
                        console.log('✅ Select2 destruido');
                    } catch (e) {
                        console.error('❌ Error destruyendo Select2:', e);
                    }
                }
                
                // Crear un select simple temporalmente
                vehiculoSelect.style.display = 'block';
                vehiculoSelect.style.width = '100%';
                vehiculoSelect.style.padding = '10px';
                vehiculoSelect.style.border = '2px solid #00f2fe';
                vehiculoSelect.style.borderRadius = '6px';
                vehiculoSelect.style.background = 'rgba(20, 20, 40, 0.95)';
                vehiculoSelect.style.color = 'white';
                
                // Mostrar mensaje
                alert('🚗 VEHÍCULOS CARGADOS: ' + (vehiculoSelect.options.length - 1) + ' vehículos disponibles.\n\nSi no ve el dropdown, use el select nativo arriba.');
            }
        } else {
            console.log('⚠️ Pocas opciones en el select');
            
            // 4. Intentar cargar desde prefetch manualmente
            if (window.PREFETCH && window.PREFETCH.vehiculos) {
                console.log('🔍 Buscando vehículos en prefetch...');
                
                // Obtener cliente seleccionado
                var clienteSelect = document.getElementById('id_cliente');
                var clienteId = clienteSelect ? clienteSelect.value : null;
                
                if (clienteId) {
                    console.log('👤 Cliente ID:', clienteId);
                    
                    // Filtrar vehículos
                    var vehiculosCliente = window.PREFETCH.vehiculos.filter(function(v) {
                        return String(v.cliente_id) === String(clienteId);
                    });
                    
                    console.log('🚗 Vehículos encontrados:', vehiculosCliente.length);
                    
                    if (vehiculosCliente.length > 0) {
                        // Limpiar y agregar opciones
                        vehiculoSelect.innerHTML = '<option value="">Selecciona vehículo...</option>';
                        
                        vehiculosCliente.forEach(function(vehiculo) {
                            var option = document.createElement('option');
                            option.value = vehiculo.id;
                            option.textContent = vehiculo.text || vehiculo.label || 'Vehículo ' + vehiculo.id;
                            vehiculoSelect.appendChild(option);
                        });
                        
                        console.log('✅ ' + vehiculosCliente.length + ' vehículos agregados al select');
                        
                        // Forzar cambio visual
                        vehiculoSelect.style.display = 'block';
                        vehiculoSelect.style.visibility = 'visible';
                    }
                }
            }
        }
        
        // 5. Crear un visualizador de opciones
        createOptionsViewer(vehiculoSelect);
    }
    
    // Crear un visualizador de opciones para debug
    function createOptionsViewer(selectElement) {
        var viewer = document.createElement('div');
        viewer.id = 'debug-vehiculos-viewer';
        viewer.style.cssText = [
            'position: fixed',
            'top: 10px',
            'right: 10px',
            'background: rgba(0,0,0,0.9)',
            'color: #00ff00',
            'padding: 15px',
            'border: 2px solid #00ff00',
            'border-radius: 5px',
            'z-index: 99999',
            'font-family: monospace',
            'font-size: 12px',
            'max-width: 300px',
            'max-height: 400px',
            'overflow: auto'
        ].join(';');
        
        var html = '<strong>🚗 DEBUG VEHÍCULOS</strong><br>';
        html += 'Opciones: ' + selectElement.options.length + '<br>';
        html += 'Valor: ' + (selectElement.value || '(ninguno)') + '<br><br>';
        
        if (selectElement.options.length > 0) {
            html += '<strong>Opciones disponibles:</strong><br>';
            for (var i = 0; i < selectElement.options.length; i++) {
                var opt = selectElement.options[i];
                html += i + '. ' + opt.value + ' = ' + opt.text + '<br>';
            }
        }
        
        html += '<br><button onclick="document.getElementById(\'debug-vehiculos-viewer\').remove()" style="padding:5px 10px;background:#ff4444;color:white;border:none;border-radius:3px;cursor:pointer">Cerrar</button>';
        
        viewer.innerHTML = html;
        document.body.appendChild(viewer);
    }
    
    // 6. Función para probar APIs
    function testAPIs() {
        console.log('🔧 Testeando APIs...');
        
        var apis = [
            '/cl/es/documentos/api/obtener-numero-documento/',
            '/cl/es/ajax/clientes/buscar/',
            '/cl/es/ajax/vehiculos-por-cliente/'
        ];
        
        apis.forEach(function(api) {
            fetch(api + '?test=1')
                .then(function(response) {
                    console.log('🌐 ' + api + ' → Status: ' + response.status + ' ' + response.statusText);
                    return response.text();
                })
                .then(function(text) {
                    if (text.includes('<!DOCTYPE') || text.includes('<html')) {
                        console.error('❌ ' + api + ' devuelve HTML (probable error 404/500)');
                    } else {
                        console.log('✅ ' + api + ' parece funcionar');
                    }
                })
                .catch(function(error) {
                    console.error('❌ Error en ' + api + ':', error);
                });
        });
    }
    
    // 7. Exponer funciones globalmente
    window.emergencyFixVehiculos = emergencyFixVehiculos;
    window.testAPIs = testAPIs;
    window.showVehiculosDebug = function() {
        var select = document.getElementById('id_vehiculo');
        if (select) createOptionsViewer(select);
    };
    
    // 8. Ejecutar automáticamente después de un delay
    setTimeout(function() {
        console.log('⏰ Ejecutando emergency fix después de delay...');
        emergencyFixVehiculos();
        testAPIs();
    }, 2000);
    
    // 9. También ejecutar cuando se seleccione un cliente
    document.addEventListener('change', function(e) {
        if (e.target.id === 'id_cliente' && e.target.value) {
            console.log('👤 Cliente cambiado, ejecutando emergency fix...');
            setTimeout(emergencyFixVehiculos, 500);
        }
    });
    
    console.log('✅ EMERGENCY FIX cargado. Use:');
    console.log('   - window.emergencyFixVehiculos()');
    console.log('   - window.testAPIs()');
    console.log('   - window.showVehiculosDebug()');
})();