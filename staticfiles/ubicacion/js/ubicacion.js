// ubicacion/static/ubicacion/js/ubicacion.js

document.addEventListener("DOMContentLoaded", function () {
  const estadoSelect = document.getElementById("id_estado");
  const ciudadSelect = document.getElementById("id_ciudad");

  // 👀 Si no estamos en un formulario con estado/ciudad, salir sin romper nada
  if (!estadoSelect || !ciudadSelect) {
    // console.debug("[ubicacion] No hay id_estado o id_ciudad en esta página, se omite.");
    return;
  }

  // Idealmente definimos esta URL en el HTML con data-ciudades-url
  // <select id="id_estado" data-ciudades-url="/cl/es/ubicacion/ajax/ciudades-por-estado/">
  const ciudadesUrlAttr =
    estadoSelect.dataset.ciudadesUrl || estadoSelect.getAttribute("data-ciudades-url");

  // Fallback si no tienes data-ciudades-url configurado (ajusta a tu vista real)
  const ciudadesUrl = ciudadesUrlAttr || "/taller/clientes/ajax/ciudades/";

  function resetCiudades() {
    ciudadSelect.innerHTML = "";
    const opt = document.createElement("option");
    opt.value = "";
    opt.textContent = "Selecciona una ciudad";
    ciudadSelect.appendChild(opt);
    ciudadSelect.disabled = true;
  }

  function cargarCiudades(estadoId) {
    if (!estadoId) {
      resetCiudades();
      return;
    }

    // Por si acaso, deshabilitar mientras carga
    ciudadSelect.disabled = true;
    ciudadSelect.innerHTML = "";
    const cargandoOpt = document.createElement("option");
    cargandoOpt.value = "";
    cargandoOpt.textContent = "Cargando ciudades...";
    ciudadSelect.appendChild(cargandoOpt);

    // Usar region_id para Chile (ya que el modelo usa Región, no Estado para CL)
    const paramName = estadoSelect.dataset.paramName || "region_id";
    const url = `${ciudadesUrl}?${paramName}=${encodeURIComponent(estadoId)}`;

    console.log("[ubicacion] Cargando ciudades desde:", url);

    fetch(url, {
      headers: {
        "X-Requested-With": "XMLHttpRequest",
      },
    })
      .then((response) => {
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }
        return response.json();
      })
      .then((data) => {
        console.log("[ubicacion] Ciudades recibidas:", data);
        
        // Limpiar select
        ciudadSelect.innerHTML = "";
        const optDefault = document.createElement("option");
        optDefault.value = "";
        optDefault.textContent = "Selecciona una ciudad";
        ciudadSelect.appendChild(optDefault);

        // Manejar diferentes formatos de respuesta
        // Puede ser un array directo o un objeto con propiedad 'ciudades'
        let ciudades = [];
        if (Array.isArray(data)) {
          ciudades = data;
        } else if (data.ciudades && Array.isArray(data.ciudades)) {
          ciudades = data.ciudades;
        }

        if (ciudades.length) {
          ciudades.forEach((c) => {
            const opt = document.createElement("option");
            opt.value = c.id;
            opt.textContent = c.nombre;
            ciudadSelect.appendChild(opt);
          });
          ciudadSelect.disabled = false;
          console.log(`[ubicacion] ${ciudades.length} ciudades cargadas exitosamente`);
        } else {
          ciudadSelect.disabled = true;
          console.warn("[ubicacion] No hay ciudades disponibles para este estado/región");
        }
      })
      .catch((err) => {
        console.error("[ubicacion] Error cargando ciudades:", err);
        resetCiudades();
        // Opcional: mostrar mensaje al usuario
        alert("Error al cargar las ciudades. Por favor, intenta de nuevo.");
      });
  }

  // 🔑 Este evento funciona igual en PC y en celular, con o sin Select2
  estadoSelect.addEventListener("change", function () {
    const estadoId = this.value;
    console.log("[ubicacion] Estado/región cambiado:", estadoId);
    cargarCiudades(estadoId);
  });

  // Si ya viene un estado seleccionado (editar cliente), cargamos de una
  if (estadoSelect.value) {
    console.log("[ubicacion] Estado/región pre-seleccionado detectado, cargando ciudades...");
    cargarCiudades(estadoSelect.value);
  } else {
    resetCiudades();
  }
});
