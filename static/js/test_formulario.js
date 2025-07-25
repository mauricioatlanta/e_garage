// Test para verificar que el JavaScript funciona correctamente
console.log('=== TEST FORMULARIO DOCUMENTO ===');

// Simular DOMContentLoaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('✅ DOMContentLoaded ejecutado');
    
    // Verificar elementos críticos
    const elementos = {
        tipoDoc: document.getElementById('id_tipo_documento'),
        numeroDoc: document.getElementById('id_numero_documento'),
        formContainer: document.getElementById('form-doc-container'),
        tablaRepuestos: document.getElementById('tabla-repuestos'),
        tablaServicios: document.getElementById('tabla-servicios'),
        checkboxIva: document.getElementById('lleva_iva')
    };
    
    console.log('🔍 Elementos encontrados:', elementos);
    
    // Verificar que el script principal se carga
    setTimeout(() => {
        if (window.agregarRepuesto) {
            console.log('✅ Función agregarRepuesto disponible');
        } else {
            console.warn('❌ Función agregarRepuesto NO disponible');
        }
        
        if (window.agregarServicio) {
            console.log('✅ Función agregarServicio disponible');
        } else {
            console.warn('❌ Función agregarServicio NO disponible');
        }
    }, 1000);
});
