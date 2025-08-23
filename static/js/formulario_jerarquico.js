/**
 * 🎯 JavaScript para formularios jerárquicos
 * Marca → Modelo → Motor/Caja
 */

$(document).ready(function() {
    // Configuración CSRF
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
    
    const csrftoken = getCookie('csrftoken');
    
    // Función para limpiar y deshabilitar select
    function clearAndDisableSelect(selectId, placeholder = 'Seleccione...') {
        const $select = $(selectId);
        $select.empty().append(`<option value="">${placeholder}</option>`);
        $select.prop('disabled', true);
    }
    
    // Función para habilitar y llenar select
    function populateSelect(selectId, data, valueField = 'id', textField = 'nombre') {
        const $select = $(selectId);
        $select.empty().append('<option value="">Seleccione...</option>');
        
        if (data && data.length > 0) {
            data.forEach(item => {
                const value = item[valueField];
                const text = item.display || item[textField];
                $select.append(`<option value="${value}">${text}</option>`);
            });
            $select.prop('disabled', false);
        } else {
            $select.prop('disabled', true);
        }
    }
    
    // Evento: Cambio de Marca (desactivado, DAL/Select2 maneja modelos)
    /*
    $('#id_marca').change(function() {
        const marcaId = $(this).val();
        // Limpiar campos dependientes
        clearAndDisableSelect('#id_modelo', 'Seleccione marca primero');
        clearAndDisableSelect('#id_motor', 'Seleccione modelo primero');
        clearAndDisableSelect('#id_caja', 'Seleccione modelo primero');
        if (!marcaId) return;
        // Cargar modelos via AJAX
        $.get('/ajax/load-modelos/', {marca_id: marcaId})
            .done(function(data) {
                if (data.error) {
                    alert('Error: ' + data.error);
                    return;
                }
                populateSelect('#id_modelo', data.modelos);
                if (data.modelos.length === 0) {
                    $('#id_modelo').append('<option value="">No hay modelos disponibles</option>');
                }
            })
            .fail(function() {
                alert('Error al cargar modelos');
            });
    });
    */
    
    // Evento: Cambio de Modelo
    $('#id_modelo').change(function() {
        const modeloId = $(this).val();
        
        // Limpiar campos dependientes
        clearAndDisableSelect('#id_motor', 'Seleccione modelo primero');
        clearAndDisableSelect('#id_caja', 'Seleccione modelo primero');
        
        if (!modeloId) return;
        
        // Cargar motores y cajas via AJAX combinado
        $.get('/ajax/load-motores-cajas/', {modelo_id: modeloId})
            .done(function(data) {
                if (data.error) {
                    alert('Error: ' + data.error);
                    return;
                }
                
                // Poblar motores
                populateSelect('#id_motor', data.motores);
                if (data.motores.length === 0) {
                    $('#id_motor').append('<option value="">No hay motores disponibles</option>');
                }
                
                // Poblar cajas
                populateSelect('#id_caja', data.cajas);
                if (data.cajas.length === 0) {
                    $('#id_caja').append('<option value="">No hay cajas disponibles</option>');
                }
                
                // Opcional: Mostrar información del modelo
                console.log(`Cargado: ${data.marca} ${data.modelo} (${data.pais})`);
            })
            .fail(function() {
                alert('Error al cargar motores y cajas');
            });
    });
    
    // Inicialización: Deshabilitar campos dependientes
    clearAndDisableSelect('#id_modelo', 'Seleccione marca primero');
    clearAndDisableSelect('#id_motor', 'Seleccione modelo primero');
    clearAndDisableSelect('#id_caja', 'Seleccione modelo primero');
});

/**
 * Función auxiliar para debugging
 */
function debugFormularioJerarquico() {
    console.log('Marca:', $('#id_marca').val());
    console.log('Modelo:', $('#id_modelo').val());
    console.log('Motor:', $('#id_motor').val());
    console.log('Caja:', $('#id_caja').val());
}
