
document.addEventListener('DOMContentLoaded', () => {
  const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

  const regionInput = document.getElementById('nueva-region');
  const ciudadInput = document.getElementById('nueva-ciudad');
  const botonAgregarRegion = document.getElementById('btn-agregar-region');
  const botonAgregarCiudad = document.getElementById('btn-agregar-ciudad');
  const listaRegiones = document.getElementById('lista-regiones');
  const selectRegionCiudad = document.getElementById('region-para-ciudad');

  botonAgregarRegion.addEventListener('click', () => {
    const nombreRegion = regionInput.value.trim();
    if (!nombreRegion) return alert('Ingresa un nombre de región.');

    fetch('/api/region/agregar/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken,
      },
      body: JSON.stringify({ nombre: nombreRegion }),
    })
    .then(res => res.json())
    .then(data => {
      if (data.ok) {
        regionInput.value = '';
        actualizarListaRegiones(data.region);
        alert('✅ Región agregada con éxito.');
      } else {
        alert(data.error || 'Error al agregar región.');
      }
    });
  });

  botonAgregarCiudad.addEventListener('click', () => {
    const nombreCiudad = ciudadInput.value.trim();
    const regionId = selectRegionCiudad.value;

    if (!nombreCiudad || !regionId) return alert('Completa todos los campos.');

    fetch('/api/ciudad/agregar/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken,
      },
      body: JSON.stringify({ nombre: nombreCiudad, region_id: regionId }),
    })
    .then(res => res.json())
    .then(data => {
      if (data.ok) {
        ciudadInput.value = '';
        alert('🏙️ Ciudad agregada correctamente.');
      } else {
        alert(data.error || 'Error al agregar ciudad.');
      }
    });
  });

  function actualizarListaRegiones(region) {
    const option = document.createElement('option');
    option.value = region.id;
    option.textContent = region.nombre;
    selectRegionCiudad.appendChild(option);

    const li = document.createElement('li');
    li.textContent = `🧭 ${region.nombre}`;
    listaRegiones.appendChild(li);
  }
});
