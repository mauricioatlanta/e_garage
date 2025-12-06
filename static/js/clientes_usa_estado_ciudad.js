/**
 * Script robusto para cargar ciudades según estado seleccionado (USA)
 * Compatible con PC y móviles - Sin duplicados
 * 
 * Funciona con:
 * - id_estado_usa (select de estados)
 * - id_ciudad_usa (select de ciudades)
 */

(function() {
    'use strict';

    document.addEventListener("DOMContentLoaded", function() {
        const estadoSelect = document.getElementById("id_estado_usa");
        const ciudadSelect = document.getElementById("id_ciudad_usa");

        // Si no están ambos elementos, esta vista no los necesita
        if (!estadoSelect || !ciudadSelect) {
            console.log("[Estado→Ciudad USA] No se encontraron los selectores necesarios en esta vista");
            return;
        }

        console.log("✅ [Estado→Ciudad USA] Inicializando...");

        // Obtener URL del data-attribute o usar default
        const baseUrl = estadoSelect.dataset.citiesUrl || 
                       estadoSelect.getAttribute('data-cities-url') ||
                       '/taller/clientes/ajax/ciudades_usa/';

        /**
         * Actualiza las opciones del select de ciudades
         */
        function setCiudadesOptions(options, placeholder) {
            ciudadSelect.innerHTML = "";

            const defaultOption = document.createElement("option");
            defaultOption.value = "";
            defaultOption.textContent = placeholder || "Selecciona ciudad";
            ciudadSelect.appendChild(defaultOption);

            if (options && options.length > 0) {
                options.forEach(function(ciudad) {
                    const opt = document.createElement("option");
                    opt.value = ciudad.id;
                    opt.textContent = ciudad.nombre;
                    ciudadSelect.appendChild(opt);
                });
                ciudadSelect.disabled = false;
            } else {
                ciudadSelect.disabled = true;
            }
        }

        /**
         * Carga las ciudades para un estado dado
         */
        function loadCiudades(estadoId) {
            if (!estadoId) {
                setCiudadesOptions([], "Selecciona un estado primero");
                return;
            }

            console.log("🔄 [Estado→Ciudad USA] Cargando ciudades para estado:", estadoId);

            // Mostrar estado de carga
            setCiudadesOptions([], "Cargando ciudades...");

            // Construir URL con parámetro
            const url = baseUrl + "?estado_id=" + encodeURIComponent(estadoId);

            fetch(url, {
                method: 'GET',
                headers: {
                    "X-Requested-With": "XMLHttpRequest",
                    "Accept": "application/json"
                },
                credentials: 'same-origin'
            })
            .then(function(response) {
                if (!response.ok) {
                    throw new Error("Error HTTP " + response.status);
                }
                return response.json();
            })
            .then(function(data) {
                // Manejar diferentes formatos de respuesta
                const ciudades = data.ciudades || data;
                
                if (Array.isArray(ciudades) && ciudades.length > 0) {
                    console.log("✅ [Estado→Ciudad USA]", ciudades.length, "ciudades cargadas");
                    setCiudadesOptions(ciudades, "Selecciona ciudad");
                } else {
                    console.warn("⚠️ [Estado→Ciudad USA] No hay ciudades para este estado");
                    setCiudadesOptions([], "No hay ciudades disponibles");
                }
            })
            .catch(function(error) {
                console.error("❌ [Estado→Ciudad USA] Error al cargar ciudades:", error);
                setCiudadesOptions([], "Error al cargar ciudades");
                
                // Mostrar alerta al usuario
                if (window.alert) {
                    alert("No se pudieron cargar las ciudades. Por favor, intenta de nuevo.");
                }
            });
        }

        /**
         * Event listener principal: funciona igual en PC y móvil
         */
        estadoSelect.addEventListener("change", function(e) {
            loadCiudades(e.target.value);
        });

        // IMPORTANTE PARA MÓVILES: También escuchar 'input' como backup
        estadoSelect.addEventListener("input", function(e) {
            loadCiudades(e.target.value);
        });

        // Si el estado ya viene seleccionado (editar cliente, etc.)
        if (estadoSelect.value) {
            console.log("🔄 [Estado→Ciudad USA] Estado pre-seleccionado detectado");
            loadCiudades(estadoSelect.value);
        } else {
            setCiudadesOptions([], "Selecciona un estado primero");
        }

        console.log("✅ [Estado→Ciudad USA] Handler configurado correctamente");
    });
})();






