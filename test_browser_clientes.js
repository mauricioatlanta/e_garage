// Test para verificar la búsqueda de clientes en el navegador
// Ejecutar este código en la consola del navegador (F12 -> Console)

console.log('🧪 Iniciando test de búsqueda de clientes...');

// 1. Verificar que los elementos existen
const clienteSearch = document.getElementById('cliente-search');
const clienteSelect = document.getElementById('cliente');
const vehiculoSelect = document.getElementById('vehiculo');

console.log('🔍 Elementos encontrados:', {
    'cliente-search': !!clienteSearch,
    'cliente': !!clienteSelect,
    'vehiculo': !!vehiculoSelect
});

if (!clienteSearch) {
    console.error('❌ Elemento cliente-search no encontrado');
    console.log('📝 Elementos input disponibles:', Array.from(document.querySelectorAll('input')).map(i => i.id || i.name).filter(Boolean));
    return;
}

if (!clienteSelect) {
    console.error('❌ Elemento cliente (select) no encontrado');
    console.log('📝 Elementos select disponibles:', Array.from(document.querySelectorAll('select')).map(s => s.id || s.name).filter(Boolean));
    return;
}

// 2. Verificar que el JavaScript se cargó
if (typeof searchClientes === 'function') {
    console.log('✅ Función searchClientes está disponible');
} else {
    console.error('❌ Función searchClientes no encontrada');
    console.log('🔍 Funciones globales disponibles:', Object.getOwnPropertyNames(window).filter(name => typeof window[name] === 'function' && name.includes('client')));
}

// 3. Test manual de la API
async function testAPI() {
    console.log('📡 Probando API directamente...');
    try {
        const response = await fetch('/api/v1/clientes/?q=juan');
        console.log('📥 Status:', response.status);
        const data = await response.json();
        console.log('✅ Datos recibidos:', data);
        
        if (data.results && data.results.length > 0) {
            console.log('🎉 Se encontraron clientes:', data.results.length);
            data.results.forEach((cliente, index) => {
                console.log(`   ${index + 1}. ${cliente.nombre} (${cliente.identificador})`);
            });
        } else {
            console.log('😔 No se encontraron clientes');
        }
    } catch (error) {
        console.error('❌ Error en API:', error);
    }
}

// 4. Test de event listener
function testEventListener() {
    console.log('⌨️ Probando event listener...');
    
    // Simular input
    clienteSearch.value = 'juan';
    clienteSearch.dispatchEvent(new Event('input', { bubbles: true }));
    
    console.log('⏰ Event disparado, esperando resultados...');
    
    setTimeout(() => {
        console.log('📋 Opciones en select:', clienteSelect.innerHTML);
        console.log('🔢 Número de opciones:', clienteSelect.options.length);
    }, 500);
}

// Ejecutar tests
console.log('🚀 Ejecutando tests...');
testAPI();
setTimeout(testEventListener, 1000);

console.log('📖 Para probar manualmente:');
console.log('   1. Escribir en el campo de búsqueda');
console.log('   2. Verificar la consola para logs');
console.log('   3. Verificar que aparezcan opciones en el select');
