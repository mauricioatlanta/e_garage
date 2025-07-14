document.addEventListener('DOMContentLoaded', function () {
  const regionSelect = document.getElementById('id_region');
  const ciudadSelect = document.getElementById('id_ciudad');
  if (!regionSelect || !ciudadSelect) return;

  function cargarCiudades(regionId, ciudadActual) {
    ciudadSelect.innerHTML = '<option value="">Seleccione ciudad</option>';
    if (!regionId) return;

    fetch(`/clientes/ajax/ciudades/?region_id=${regionId}&_=${Date.now()}`)
      .then(response => response.json())
      .then(data => {
        console.log("👀 Ciudades recibidas:", data);  // depuración
        data.forEach(ciudad => {
          const option = document.createElement('option');
          option.value = ciudad.id;
          option.textContent = ciudad.nombre;
          if (ciudadActual && String(ciudadActual) === String(ciudad.id)) {
            option.selected = true;
          }
          ciudadSelect.appendChild(option);
        });

        // Verifica si realmente se agregaron
        console.log("🧪 Opciones generadas:", ciudadSelect.innerHTML);
      })
      .catch(error => console.error("❌ Error cargando ciudades:", error));
  }

  // Cargar al cambiar la región
  regionSelect.addEventListener('change', function () {
    cargarCiudades(this.value);
  });

  // Si ya hay región seleccionada (modo edición)
  if (regionSelect.value) {
    const ciudadActual = window.CIUDAD_ACTUAL || ciudadSelect.value;
    cargarCiudades(regionSelect.value, ciudadActual);
  } else {
    ciudadSelect.innerHTML = '<option value="">Seleccione ciudad</option>';
  }
});
