// SCRIPT DE TEST PARA CREAR MECÁNICOS
// Pegar este código en la consola del navegador en la página /documentos/nuevo/

console.log('🧪 INICIANDO TEST DE MECÁNICOS');

// Función para obtener CSRF token
function getCSRFToken() {
    const token = document.querySelector('[name=csrfmiddlewaretoken]')?.value ||
                  document.querySelector('meta[name=csrf-token]')?.getAttribute('content') ||
                  getCookie('csrftoken');
    console.log('🔑 CSRF Token:', token ? token.substring(0, 10) + '...' : 'NO ENCONTRADO');
    return token;
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Test crear mecánico
function testCrearMecanico() {
    const nombreMecanico = 'Test Mecánico ' + new Date().getTime();
    const csrfToken = getCSRFToken();
    
    console.log('📤 Enviando petición para crear mecánico:', nombreMecanico);
    
    // Usar fetch para la petición
    fetch('/documentos/api/crear_mecanico/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': csrfToken
        },
        body: `nombre=${encodeURIComponent(nombreMecanico)}&csrfmiddlewaretoken=${encodeURIComponent(csrfToken)}`
    })
    .then(response => {
        console.log('📊 Status:', response.status);
        return response.json();
    })
    .then(data => {
        console.log('✅ Respuesta exitosa:', data);
        if (data.id) {
            console.log(`🎉 Mecánico creado: ID ${data.id}, Nombre: ${data.nombre}`);
            
            // Verificar que aparece en el select
            const selectMecanico = document.querySelector('#id_mecanico');
            if (selectMecanico) {
                const option = document.createElement('option');
                option.value = data.id;
                option.textContent = data.nombre;
                option.selected = true;
                selectMecanico.appendChild(option);
                console.log('✅ Mecánico agregado al select');
            }
        }
    })
    .catch(error => {
        console.error('❌ Error:', error);
    });
}

// Test con jQuery si está disponible
function testConJQuery() {
    if (typeof $ !== 'undefined') {
        console.log('🔧 Testing con jQuery...');
        const nombreMecanico = 'Test jQuery ' + new Date().getTime();
        
        $.post('/documentos/api/crear_mecanico/', {
            'nombre': nombreMecanico,
            'csrfmiddlewaretoken': getCSRFToken()
        })
        .done(function(data) {
            console.log('✅ jQuery Success:', data);
        })
        .fail(function(xhr) {
            console.log('❌ jQuery Error:', xhr.status, xhr.responseText);
        });
    } else {
        console.log('❌ jQuery no disponible');
    }
}

// Ejecutar tests
console.log('🚀 Ejecutando tests...');
testCrearMecanico();
setTimeout(testConJQuery, 2000);

console.log('📋 Tests programados. Revisa la consola para los resultados.');
console.log('💡 Si quieres ejecutar manualmente: testCrearMecanico()');
