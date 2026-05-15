document.addEventListener('DOMContentLoaded', () => {
  const estadoSelect = document.getElementById('id_estado');
  const ciudadInput = document.getElementById('id_ciudad');
  const zipInput = document.getElementById('id_zip_code');
  const datalist = document.getElementById('ciudades-list');

  estadoSelect.addEventListener('change', () => {
    const estadoId = estadoSelect.value;
    fetch(`/ubicacion/api/ciudades/${estadoId}/`)
      .then(res => res.json())
      .then(data => {
        datalist.innerHTML = '';
        data.forEach(ciudad => {
          const option = document.createElement('option');
          option.value = ciudad.nombre;
          datalist.appendChild(option);
        });
        // Siempre agregar la opción "Otra" al final
        const otra = document.createElement('option');
        otra.value = "Otra";
        datalist.appendChild(otra);
      });
  });

  ciudadInput.addEventListener('change', () => {
    const ciudadNombre = ciudadInput.value;
    fetch(`/ubicacion/api/zip-code/${ciudadNombre}/`)
      .then(res => res.json())
      .then(data => {
        if (data.zip_code) {
          zipInput.value = data.zip_code;
          zipInput.readOnly = true;
        } else {
          zipInput.value = '';
          zipInput.readOnly = false;
        }
      });
  });
});
