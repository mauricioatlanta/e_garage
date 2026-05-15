// Parche para solucionar el problema de vehículos no mostrados en el formulario de documentos
// Este script debe incluirse después de jQuery y Select2

(function() {
    'use strict';
    
    console.log('🔧 Aplicando parche para vehículos y Select2...');
    
    // Esperar a que el DOM esté completamente cargado
    document.addEventListener('DOMContentLoaded', function() {
        // Esperar un poco más para asegurar que todos los scripts se hayan cargado
        setTimeout(applyFix, 500);
    });
    
    function applyFix() {
        console.log('🔧 Aplicando correcciones...');
        
        // 1. Corregir el problema de Select2 para vehículos
        fixVehiculoSelect2();
        
        // 2. Verificar y forzar la carga de vehículos si hay un cliente seleccionado
        checkAndLoadVehicles();
        
        // 3. Parche para el error de JSON en updateDocumentNumber
        patchUpdateDocumentNumber();
        
        // 4. Parche para el error de marketplace_tooltip.js
        patchMarketplaceTooltip();
        
        console.log('✅ Parches aplicados');
    }
    
    function fixVehiculoSelect2() {
        const vehiculoSelect = document.getElementById('id_vehiculo');
        if (!vehiculoSelect) {
            console.warn('⚠️ No se encontró el elemento #id_vehiculo');
            return;
        }
        
        console.log('🔧 Corrigiendo Select2 para vehículos...');
        console.log('   - Opciones disponibles:', vehiculoSelect.options.length);
        console.log('   - Valor actual:', vehiculoSelect.value);
        console.log('   - Data source:', vehiculoSelect.dataset.source);
        
        // Verificar si jQuery y Select2 están disponibles
        if (!window.jQuery) {
            console.error('❌ jQuery no está disponible');
            return;
        }
        
        const $vs = jQuery(vehiculoSelect);
        
        // Destruir Select2 si ya está inicializado
        if ($vs.data('select2')) {
            console.log('   - Select2 ya está inicializado, destruyendo...');
            try {
                $vs.select2('destroy');
                console.log('   - Select2 destruido exitosamente');
            } catch (error) {
                console.error('   - Error al destruir Select2:', error);
            }
        }
        
        // Verificar si hay opciones disponibles
        if (vehiculoSelect.options.length <= 1) {
            console.log('   - Pocas opciones disponibles, verificando prefetch...');
            
            // Intentar cargar vehículos desde prefetch si está disponible
            if (window.PREFETCH && window.PREFETCH.vehiculos) {
                console.log('   - Prefetch disponible con', window.PREFETCH.vehiculos.length, 'vehículos');
                
                // Obtener el ID del cliente seleccionado
                const clienteSelect = document.getElementById('id_cliente');
                const clienteId = clienteSelect ? clienteSelect.value : null;
                
                if (clienteId) {
                    console.log('   - Cliente seleccionado ID:', clienteId);
                    
                    // Filtrar vehículos por cliente
                    const vehiculosCliente = window.PREFETCH.vehiculos.filter(v => 
                        String(v.cliente_id) === String(clienteId)
                    );
                    
                    console.log('   - Vehículos encontrados para cliente:', vehiculosCliente.length);
                    
                    if (vehiculosCliente.length > 0) {
                        // Limpiar opciones actuales
                        vehiculoSelect.innerHTML = '';
                        
                        // Agregar opción por defecto
                        const defaultOption = document.createElement('option');
                        defaultOption.value = '';
                        defaultOption.textContent = 'Selecciona vehículo...';
                        vehiculoSelect.appendChild(defaultOption);
                        
                        // Agregar vehículos
                        vehiculosCliente.forEach(vehiculo => {
                            const option = document.createElement('option');
                            option.value = vehiculo.id;
                            option.textContent = vehiculo.text || vehiculo.label || `Vehículo ${vehiculo.id}`;
                            vehiculoSelect.appendChild(option);
                        });
                        
                        console.log('   - Opciones actualizadas:', vehiculoSelect.options.length);
                    }
                }
            }
        }
        
        // Inicializar Select2 con opciones robustas
        try {
            $vs.select2({
                placeholder: 'Selecciona vehículo...',
                allowClear: true,
                width: '100%',
                dropdownParent: $vs.closest('.modal').length ? $vs.closest('.modal') : document.body,
                language: {
                    noResults: function() {
                        return "No se encontraron vehículos";
                    },
                    searching: function() {
                        return "Buscando...";
                    }
                }
            });
            
            console.log('✅ Select2 inicializado exitosamente');
            
            // Forzar la actualización visual
            $vs.trigger('change.select2');
            
            // Si hay un valor seleccionado, asegurarse de que Select2 lo muestre
            if (vehiculoSelect.value) {
                setTimeout(() => {
                    $vs.val(vehiculoSelect.value).trigger('change');
                    console.log('   - Valor forzado en Select2:', vehiculoSelect.value);
                }, 100);
            }
        } catch (error) {
            console.error('❌ Error al inicializar Select2:', error);
        }
    }
    
    function checkAndLoadVehicles() {
        const clienteSelect = document.getElementById('id_cliente');
        const vehiculoSelect = document.getElementById('id_vehiculo');
        
        if (!clienteSelect || !vehiculoSelect) {
            return;
        }
        
        // Si hay un cliente seleccionado pero pocos vehículos
        if (clienteSelect.value && vehiculoSelect.options.length <= 1) {
            console.log('🔍 Cliente seleccionado pero sin vehículos, intentando cargar...');
            
            // Buscar la función de carga de vehículos
            if (typeof window.cargarVehiculosPorCliente === 'function') {
                console.log('   - Llamando a cargarVehiculosPorCliente...');
                window.cargarVehiculosPorCliente(clienteSelect.value);
            } else {
                console.warn('   - Función cargarVehiculosPorCliente no encontrada');
                
                // Intentar cargar manualmente
                loadVehiclesManually(clienteSelect.value);
            }
        }
    }
    
    function loadVehiclesManually(clienteId) {
        console.log('🔧 Cargando vehículos manualmente para cliente:', clienteId);
        
        // URL para la API de vehículos
        const url = '/ajax/vehiculos-por-cliente/';
        
        fetch(`${url}?cliente_id=${encodeURIComponent(clienteId)}`, {
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('✅ Vehículos cargados:', data);
            
            const vehiculoSelect = document.getElementById('id_vehiculo');
            if (!vehiculoSelect) return;
            
            // Limpiar opciones
            vehiculoSelect.innerHTML = '';
            
            // Agregar opción por defecto
            const defaultOption = document.createElement('option');
            defaultOption.value = '';
            defaultOption.textContent = 'Selecciona vehículo...';
            vehiculoSelect.appendChild(defaultOption);
            
            // Procesar datos
            const items = Array.isArray(data) ? data : (data.results || data.items || []);
            
            items.forEach(item => {
                const option = document.createElement('option');
                option.value = item.id || item.pk;
                option.textContent = item.text || item.label || item.patente || `Vehículo ${item.id}`;
                vehiculoSelect.appendChild(option);
            });
            
            console.log(`✅ ${items.length} vehículos agregados`);
            
            // Reinicializar Select2
            if (window.jQuery) {
                const $vs = jQuery(vehiculoSelect);
                if ($vs.data('select2')) {
                    $vs.select2('destroy');
                }
                $vs.select2({
                    placeholder: 'Selecciona vehículo...',
                    allowClear: true,
                    width: '100%'
                });
            }
        })
        .catch(error => {
            console.error('❌ Error cargando vehículos:', error);
        });
    }
    
    function patchUpdateDocumentNumber() {
        // Parche para el error de JSON en updateDocumentNumber
        if (typeof window.updateDocumentNumber === 'function') {
            const originalUpdateDocumentNumber = window.updateDocumentNumber;
            
            window.updateDocumentNumber = async function() {
                try {
                    return await originalUpdateDocumentNumber.apply(this, arguments);
                } catch (error) {
                    console.warn('⚠️ Error en updateDocumentNumber, usando valor por defecto:', error);
                    
                    // Establecer un valor por defecto
                    const numeroView = document.getElementById('numero-view');
                    const numeroHidden = document.getElementById('id_numero');
                    
                    if (numeroView) {
                        numeroView.textContent = 'Auto-generated';
                    }
                    if (numeroHidden) {
                        numeroHidden.value = '';
                    }
                }
            };
            
            console.log('✅ Parche aplicado a updateDocumentNumber');
        }
    }
    
    function patchMarketplaceTooltip() {
        // Parche para el error de marketplace_tooltip.js
        // El error es de sintaxis en modo estricto, probablemente por una declaración de función
        // en un lugar incorrecto. Este parche intenta evitar que el error bloquee la ejecución.
        
        if (window.MarketplaceTooltip) {
            console.log('✅ MarketplaceTooltip ya está disponible');
        } else {
            console.log('⚠️ MarketplaceTooltip no está disponible, el error podría estar bloqueando la carga');
        }
        
        // Intentar cargar el script de manera segura
        const script = document.querySelector('script[src*="marketplace_tooltip.js"]');
        if (script) {
            console.log('🔧 Script marketplace_tooltip.js encontrado, verificando...');
            
            // Agregar un manejador de errores global para capturar errores de sintaxis
            window.addEventListener('error', function(event) {
                if (event.filename && event.filename.includes('marketplace_tooltip.js')) {
                    console.warn('⚠️ Error capturado en marketplace_tooltip.js:', event.message);
                    event.preventDefault(); // Prevenir que el error se propague
                }
            });
        }
    }
    
    // También exponer funciones útiles globalmente
    window.repararSelect2Vehiculos = fixVehiculoSelect2;
    window.forzarCargaVehiculos = function(clienteId) {
        if (clienteId) {
            loadVehiclesManually(clienteId);
        } else {
            const clienteSelect = document.getElementById('id_cliente');
            if (clienteSelect && clienteSelect.value) {
                loadVehiclesManually(clienteSelect.value);
            }
        }
    };
    
    console.log('🔧 Parche listo. Use window.repararSelect2Vehiculos() o window.forzarCargaVehiculos() manualmente si es necesario.');
})();