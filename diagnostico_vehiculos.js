// Script de diagnóstico para el problema de vehículos no mostrados

document.addEventListener('DOMContentLoaded', function() {
    console.log('🔍 DIAGNÓSTICO: Iniciando análisis del problema de vehículos...');
    
    // 1. Verificar si el elemento select de vehículos existe
    const vehiculoSelect = document.getElementById('id_vehiculo');
    console.log('1. Elemento #id_vehiculo encontrado:', !!vehiculoSelect);
    
    if (vehiculoSelect) {
        console.log('   - ID:', vehiculoSelect.id);
        console.log('   - Clases:', vehiculoSelect.className);
        console.log('   - Número de opciones:', vehiculoSelect.options.length);
        console.log('   - Valor seleccionado:', vehiculoSelect.value);
        console.log('   - Atributo data-source:', vehiculoSelect.dataset.source);
        console.log('   - Deshabilitado:', vehiculoSelect.disabled);
        
        // Mostrar todas las opciones
        console.log('   - Opciones disponibles:');
        for (let i = 0; i < vehiculoSelect.options.length; i++) {
            const option = vehiculoSelect.options[i];
            console.log(`     [${i}] value="${option.value}", text="${option.text}"`);
        }
    }
    
    // 2. Verificar si jQuery está cargado
    console.log('2. jQuery disponible:', !!window.jQuery);
    
    // 3. Verificar si Select2 está inicializado en el elemento
    if (vehiculoSelect && window.jQuery) {
        const $vs = jQuery(vehiculoSelect);
        const hasSelect2 = !!$vs.data('select2');
        console.log('3. Select2 inicializado en #id_vehiculo:', hasSelect2);
        
        if (hasSelect2) {
            console.log('   - Datos Select2:', $vs.data('select2'));
        }
    }
    
    // 4. Verificar si hay elementos de prefetch de vehículos
    console.log('4. Prefetch de vehículos disponible:', !!window.PREFETCH);
    if (window.PREFETCH && window.PREFETCH.vehiculos) {
        console.log('   - Número de vehículos en prefetch:', window.PREFETCH.vehiculos.length);
        console.log('   - Primeros 3 vehículos:', window.PREFETCH.vehiculos.slice(0, 3));
    }
    
    // 5. Verificar si hay errores en la consola relacionados
    console.log('5. Errores en consola relacionados:');
    console.log('   - Error de marketplace_tooltip.js: Este es un error de sintaxis que podría estar bloqueando la ejecución');
    console.log('   - Error de JSON en updateDocumentNumber: La API está devolviendo HTML en lugar de JSON');
    
    // 6. Verificar el estado del cliente seleccionado
    const clienteSelect = document.getElementById('id_cliente');
    console.log('6. Cliente seleccionado:');
    console.log('   - Elemento encontrado:', !!clienteSelect);
    if (clienteSelect) {
        console.log('   - ID del cliente:', clienteSelect.value);
    }
    
    // 7. Intentar forzar la reinicialización de Select2
    console.log('7. Intentando reinicializar Select2 manualmente...');
    if (vehiculoSelect && window.jQuery) {
        try {
            const $vs = jQuery(vehiculoSelect);
            // Destruir Select2 si existe
            if ($vs.data('select2')) {
                $vs.select2('destroy');
                console.log('   - Select2 destruido');
            }
            
            // Recrear Select2
            $vs.select2({
                placeholder: 'Selecciona vehículo...',
                allowClear: true,
                width: '100%'
            });
            console.log('   - Select2 reinicializado exitosamente');
            
            // Forzar la actualización visual
            $vs.trigger('change.select2');
            console.log('   - Cambio forzado en Select2');
        } catch (error) {
            console.error('   - Error al reinicializar Select2:', error);
        }
    }
    
    // 8. Verificar si hay estilos CSS que oculten el select
    console.log('8. Estilos CSS aplicados a #id_vehiculo:');
    if (vehiculoSelect) {
        const styles = window.getComputedStyle(vehiculoSelect);
        console.log('   - display:', styles.display);
        console.log('   - visibility:', styles.visibility);
        console.log('   - opacity:', styles.opacity);
        console.log('   - width:', styles.width);
        console.log('   - height:', styles.height);
    }
    
    console.log('✅ DIAGNÓSTICO COMPLETADO');
    
    // Recomendaciones
    console.log('\n🔧 RECOMENDACIONES:');
    console.log('1. Corregir el error de sintaxis en marketplace_tooltip.js:361');
    console.log('2. Verificar la API /cl/documentos/api/obtener-numero-documento/');
    console.log('3. Asegurar que Select2 se inicialice después de cargar las opciones');
    console.log('4. Verificar que el prefetch de vehículos tenga datos correctos');
});

// Función para forzar la carga de vehículos de un cliente específico
function diagnosticarCargaVehiculos(clienteId) {
    console.log(`🔍 DIAGNÓSTICO: Forzando carga de vehículos para cliente ${clienteId}...`);
    
    // Buscar la función cargarVehiculosPorCliente en el scope global
    if (typeof window.cargarVehiculosPorCliente === 'function') {
        window.cargarVehiculosPorCliente(clienteId);
        console.log('✅ Función cargarVehiculosPorCliente llamada');
    } else {
        console.error('❌ Función cargarVehiculosPorCliente no encontrada');
        
        // Intentar encontrar la función de otra manera
        console.log('Buscando funciones relacionadas con vehículos...');
        const funciones = Object.keys(window).filter(key => 
            typeof window[key] === 'function' && 
            key.toLowerCase().includes('vehiculo')
        );
        console.log('Funciones encontradas:', funciones);
    }
}