document.addEventListener("DOMContentLoaded", () => {
  const input = document.getElementById("id_part_number");
  if (!input) return;

  input.addEventListener("blur", () => {
    const value = input.value.trim();
    if (value.length < 3) return;

    fetch(`/api/validar_part_number/?pn=${encodeURIComponent(value)}`)
      .then(response => response.json())
      .then(data => {
        if (data.existe) {
          alert("❗ Ya existe un repuesto con este part number.");
        }
      });
  });
});