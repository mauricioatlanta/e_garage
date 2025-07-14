document.addEventListener("DOMContentLoaded", function () {
  // Este objeto debe mapear el ID de la región a un objeto {nombre, ciudades: [{id, nombre}]}
  const regiones = window.regionesChileConIds || {};

  const regionSelect = document.getElementById("id_region");
  const ciudadSelect = document.getElementById("id_ciudad");

  if (!regionSelect || !ciudadSelect) return;

  // Cargar regiones
  regionSelect.innerHTML = '<option value="">Selecciona región</option>';
  for (const regionId in regiones) {
    const option = document.createElement("option");
    option.value = regionId; // Usar el ID de la región
    option.textContent = regiones[regionId].nombre;
    regionSelect.appendChild(option);
  }

  // Cargar ciudades cuando se elige una región
  regionSelect.addEventListener("change", function () {
    const regionId = this.value;
    const ciudades = (regiones[regionId] && regiones[regionId].ciudades) || [];
    ciudadSelect.innerHTML = '<option value="">Selecciona ciudad</option>';

    ciudades.forEach(function (ciudad) {
      const option = document.createElement("option");
      option.value = ciudad.id; // Usar el ID de la ciudad
      option.textContent = ciudad.nombre;
      ciudadSelect.appendChild(option);
    });

    // Opción extra
    const optionOtra = document.createElement("option");
    optionOtra.value = "otra_ciudad";
    optionOtra.textContent = "Otra ciudad...";
    ciudadSelect.appendChild(optionOtra);
  });

  // Manejar opción "Otra ciudad"
  ciudadSelect.addEventListener("change", function () {
    if (this.value === "otra_ciudad") {
      const nuevaCiudad = prompt("Ingrese el nombre de su ciudad:");
      const regionSeleccionada = regionSelect.value;

      if (nuevaCiudad && regionSeleccionada) {
        fetch("/ajax/guardar_ciudad/", {
          method: "POST",
          headers: {
            "Content-Type": "application/x-www-form-urlencoded",
            "X-CSRFToken": getCookie("csrftoken"),
          },
          body: `ciudad=${encodeURIComponent(nuevaCiudad)}&region=${encodeURIComponent(regionSeleccionada)}`
        })
        .then(res => res.json())
        .then(data => {
          if (data.success) {
            const option = document.createElement("option");
            option.value = nuevaCiudad;
            option.textContent = nuevaCiudad;
            option.selected = true;
            ciudadSelect.appendChild(option);
          } else {
            alert("Error al guardar ciudad: " + (data.error || "desconocido"));
            ciudadSelect.selectedIndex = 0;
          }
        });
      } else {
        this.selectedIndex = 0;
      }
    }
  });

  function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
      const cookies = document.cookie.split(";");
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === name + "=") {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }
});
