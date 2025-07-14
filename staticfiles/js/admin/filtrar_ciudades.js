(function($) {
    'use strict';
    $(document).ready(function() {
        // Solo ejecutar si estamos en la página de agregar/editar cliente
        if ($('#id_region').length) {
            const regionSelect = $('#id_region');
            const ciudadSelect = $('#id_ciudad');
            const currentCiudadId = ciudadSelect.val();
            
            function cargarCiudades(regionId) {
                if (!regionId) {
                    ciudadSelect.html('<option value="">---------</option>');
                    ciudadSelect.prop('disabled', true);
                    return;
                }

                ciudadSelect.prop('disabled', true);
                ciudadSelect.html('<option value="">Cargando ciudades...</option>');

                const currentUrl = window.location.pathname;
                const baseUrl = currentUrl.includes('/add/') ? '../' : './';
                
                $.ajax({
                    url: baseUrl + 'ciudades-por-region/',
                    data: { region: regionId },
                    method: 'GET',
                    dataType: 'json',
                    success: function(response) {
                        ciudadSelect.html('<option value="">---------</option>');
                        
                        if (Array.isArray(response) && response.length > 0) {
                            response.forEach(function(ciudad) {
                                const option = new Option(ciudad.nombre, ciudad.id);
                                ciudadSelect.append(option);
                            });
                            
                            // Restaurar la ciudad seleccionada si existe
                            if (currentCiudadId) {
                                ciudadSelect.val(currentCiudadId);
                            }
                            
                            ciudadSelect.prop('disabled', false);
                        } else {
                            ciudadSelect.html('<option value="">No hay ciudades disponibles</option>');
                        }
                    },
                    error: function(xhr, status, error) {
                        console.error('Error al cargar ciudades:', error);
                        ciudadSelect.html('<option value="">Error al cargar ciudades</option>');
                        ciudadSelect.prop('disabled', true);
                    }
                });
            }

            // Evento cuando cambia la región
            regionSelect.on('change', function() {
                cargarCiudades($(this).val());
            });

            // Cargar ciudades si hay una región seleccionada inicialmente
            if (regionSelect.val()) {
                cargarCiudades(regionSelect.val());
            } else {
                ciudadSelect.html('<option value="">Seleccione una región primero</option>');
                ciudadSelect.prop('disabled', true);
            }
        }
    });
})(django.jQuery);
