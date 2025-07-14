
window.addEventListener('load', () => {
  console.log("✅ Script cargado y DOM listo");

  const regionSelect = document.getElementById('id_region');
  const ciudadSelect = document.getElementById('id_ciudad');

  if (!regionSelect || !ciudadSelect) {
    console.warn("⚠️ No se encontraron los campos de región o ciudad.");
    return;
  }

  console.log("✅ Campos encontrados:", regionSelect, ciudadSelect);

  regionSelect.addEventListener('change', () => {
    console.log("📌 Cambio detectado en región");
    const regionId = regionSelect.value;
    console.log("➡️ Región seleccionada:", regionId);

    if (!regionId) {
      ciudadSelect.innerHTML = '<option value="">Seleccione una región primero</option>';
      ciudadSelect.disabled = true;
      return;
    }

    ciudadSelect.innerHTML = '<option value="">Cargando ciudades...</option>';
    ciudadSelect.disabled = true;

    const urlCiudades = '/clientes/obtener-ciudades/?region_id=' + regionId;

    console.log("🌐 Haciendo fetch a:", urlCiudades);

    fetch(urlCiudades)
      .then(response => {
        console.log("📥 Respuesta recibida:", response);
        if (!response.ok) throw new Error("Respuesta no válida del servidor");
        return response.json();
      })
      .then(data => {
        console.log("📦 Datos de ciudades:", data);
        ciudadSelect.innerHTML = '<option value="">Seleccione una ciudad</option>';
        data.forEach(ciudad => {
          const option = document.createElement('option');
          option.value = ciudad.id;
          option.textContent = ciudad.nombre;
          ciudadSelect.appendChild(option);
        });
        ciudadSelect.disabled = false;
        console.log("✅ Ciudades cargadas en el select.");
      })
      .catch(err => {
        console.error("❌ Error al cargar ciudades:", err);
        ciudadSelect.innerHTML = '<option value="">Error al cargar</option>';
      });
  });
});
