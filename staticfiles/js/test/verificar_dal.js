
document.addEventListener("DOMContentLoaded", function () {
  console.log("✅ Verificando estado de Django Autocomplete Light...");
  
  if (typeof autocomplete_light === "undefined") {
    console.error("❌ DAL no está definido. Verifica si los scripts fueron cargados.");
    return;
  }

  console.log("✅ DAL está cargado.");
  console.log("📦 Widgets registrados:", Object.keys(autocomplete_light.widgets));

  const selects = document.querySelectorAll("select[data-autocomplete-light-function]");
  if (selects.length === 0) {
    console.warn("⚠️ No se encontraron campos con autocompletado activo en esta vista.");
  } else {
    console.log("✅ Campos DAL detectados:", selects.length);
    selects.forEach(select => {
      console.log("➡️ Campo:", select.name, "| Widget:", select.getAttribute("data-autocomplete-light-function"));
    });
  }
});
