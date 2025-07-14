document.addEventListener("DOMContentLoaded", function () {
  const buscador = document.getElementById("buscador");

  buscador.addEventListener("input", function () {
    const filtro = buscador.value.toLowerCase();
    const filas = document.querySelectorAll("#tabla-clientes tr.fila-cliente");

    filas.forEach((fila) => {
      const textoFila = fila.textContent.toLowerCase();
      fila.style.display = textoFila.includes(filtro) ? "" : "none";
    });
  });
});
