
document.addEventListener('DOMContentLoaded', function () {
  // Función auxiliar para saber si un select usa DAL
  const isDAL = (select) => select.hasAttribute('data-autocomplete-light-url');

  // Cliente: búsqueda en vivo solo si NO usa DAL
  const inputCliente = document.getElementById('busqueda-cliente');
  const selectCliente = document.getElementById('id_cliente');
  if (inputCliente && selectCliente && !isDAL(selectCliente)) {
    inputCliente.addEventListener('input', function () {
      const filtro = this.value.toLowerCase();
      Array.from(selectCliente.options).forEach(option => {
        const texto = option.text.toLowerCase();
        option.style.display = texto.includes(filtro) ? '' : 'none';
      });
    });
  }

  // Marca: búsqueda en vivo
  const inputMarca = document.getElementById('busqueda-marca');
  const selectMarca = document.getElementById('id_marca');
  if (inputMarca && selectMarca && !isDAL(selectMarca)) {
    inputMarca.addEventListener('input', function () {
      const filtro = this.value.toLowerCase();
      Array.from(selectMarca.options).forEach(option => {
        const texto = option.text.toLowerCase();
        option.style.display = texto.includes(filtro) ? '' : 'none';
      });
    });
  }

  // --- Eliminado: búsqueda y filtrado manual de modelos, ahora DAL maneja el filtrado por marca ---
});
