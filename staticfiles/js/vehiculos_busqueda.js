
document.addEventListener("DOMContentLoaded", function () {
  const buscador = document.getElementById("buscarVehiculo");
  const filas = document.querySelectorAll("#vehiculos-table-body tr");

  buscador.addEventListener("keyup", function () {
    const filtro = buscador.value.toLowerCase();
    filas.forEach(fila => {
      const texto = fila.textContent.toLowerCase();
      fila.style.display = texto.includes(filtro) ? "" : "none";
    });
  });
});
