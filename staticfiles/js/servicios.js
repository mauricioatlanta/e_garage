document.addEventListener("DOMContentLoaded", () => {
  const input = document.getElementById("busqueda-servicio");
  if (!input) return;

  input.addEventListener("input", () => {
    const query = input.value.toLowerCase();
    document.querySelectorAll(".servicio-item").forEach(item => {
      const text = item.textContent.toLowerCase();
      item.style.display = text.includes(query) ? "" : "none";
    });
  });
});