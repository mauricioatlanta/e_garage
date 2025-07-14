
document.addEventListener("DOMContentLoaded", () => {
  const tabla = document.getElementById("tabla-items");
  const agregarBtn = document.getElementById("agregar-item");

  function agregarFila() {
    const fila = document.createElement("tr");
    fila.innerHTML = `
      <td class="p-2">
        <select class="tipo w-full bg-white border border-gray-300 rounded">
          <option value="repuesto">Repuesto</option>
          <option value="servicio">Servicio</option>
        </select>
      </td>
      <td class="p-2">
        <input type="text" class="nombre w-full bg-white border border-gray-300 rounded" placeholder="Nombre" />
      </td>
      <td class="p-2">
        <input type="number" class="precio w-full bg-white border border-gray-300 rounded" min="0" value="0" />
      </td>
      <td class="p-2 text-center">
        <button type="button" class="eliminar text-red-600 hover:text-red-800 font-bold">✕</button>
      </td>
    `;
    tabla.appendChild(fila);
    actualizarTotales();
  }

  function actualizarTotales() {
    let subtotal = 0;
    document.querySelectorAll("#tabla-items .precio").forEach(input => {
      subtotal += parseFloat(input.value) || 0;
    });
    const iva = subtotal * 0.19;
    const total = subtotal + iva;

    document.getElementById("subtotal").textContent = subtotal.toLocaleString();
    document.getElementById("iva").textContent = iva.toLocaleString();
    document.getElementById("total").textContent = total.toLocaleString();
  }

  agregarBtn.addEventListener("click", agregarFila);

  tabla.addEventListener("input", e => {
    if (e.target.classList.contains("precio")) actualizarTotales();
  });

  tabla.addEventListener("click", e => {
    if (e.target.classList.contains("eliminar")) {
      e.target.closest("tr").remove();
      actualizarTotales();
    }
  });

  document.querySelector("form").addEventListener("submit", e => {
    const items = [];
    document.querySelectorAll("#tabla-items tr").forEach(tr => {
      items.push({
        tipo: tr.querySelector(".tipo").value,
        nombre: tr.querySelector(".nombre").value,
        precio: parseFloat(tr.querySelector(".precio").value) || 0
      });
    });
    document.getElementById("json_items").value = JSON.stringify(items);
  });
});
