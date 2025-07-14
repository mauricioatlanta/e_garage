document.addEventListener('DOMContentLoaded', function () {
  const input = document.getElementById('busqueda-repuesto');
  const tabla = document.getElementById('tabla-repuestos');

  input.addEventListener('input', function () {
    const query = this.value;

    fetch(`/api/repuestos/?q=${encodeURIComponent(query)}`)
      .then(response => response.json())
      .then(data => {
        tabla.innerHTML = '';
        data.forEach(r => {
          const row = document.createElement('tr');
          row.className = 'hover:bg-gray-200';
          row.innerHTML = `
            <td class="px-4 py-2">${r.id}</td>
            <td class="px-4 py-2">${r.nombre_repuesto}</td>
            <td class="px-4 py-2">${r.part_number}</td>
            <td class="px-4 py-2">${r.tienda}</td>
            <td class="px-4 py-2">$${r.precio_compra}</td>
            <td class="px-4 py-2">$${r.precio_venta}</td>
            <td class="px-4 py-2">${r.stock}</td>
            <td class="px-4 py-2 space-x-2">
              <a href="/repuestos/editar/${r.id}/" class="text-yellow-500 hover:underline">Editar</a>
              <a href="/repuestos/eliminar/${r.id}/" class="text-red-600 hover:underline">Eliminar</a>
            </td>
          `;
          tabla.appendChild(row);
        });
      });
  });
});
