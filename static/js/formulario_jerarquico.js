/**
 * 🎯 VehiculoForm dinámico (Chile/USA)
 * Endpoints usados:
 *   - /vehiculos/ajax/modelos-por-marca-anio/?marca_id=...&anio=...
 *   - /vehiculos/ajax/motores-por-modelo/?modelo_id=...
 *   - /vehiculos/ajax/cajas-por-modelo/?modelo_id=...
 *
 * Sentinel para "Agregar nuevo": "__nuevo__"
 */
$(function () {
  const NEW_SENTINEL = "__nuevo__";

  function clearAndDisable($el, placeholder) {
    $el.empty().append($("<option>").val("").text(placeholder)).prop("disabled", true);
  }
  function enable($el) {
    $el.prop("disabled", false);
  }

  const $marca = $("#id_marca");
  const $anio = $("#id_anio");
  const $modelo = $("#id_modelo");
  const $motor = $("#id_motor");
  const $caja = $("#id_caja");

  const endpointsTag = document.getElementById("vehiculos-endpoints");
  const endpoints = endpointsTag ? endpointsTag.dataset || {} : {};

  function getDatasetValue(...keys) {
    for (const key of keys) {
      if (key && endpoints[key]) {
        return endpoints[key];
      }
    }
    return undefined;
  }

  function detectBasePrefix() {
    const path = window.location.pathname || "";
    if (path.includes("/us/en/")) return "/us/en/vehiculos/";
    if (path.startsWith("/us/")) return "/us/vehiculos/";
    if (path.includes("/cl/es/")) return "/cl/es/vehiculos/";
    if (path.startsWith("/cl/")) return "/cl/es/vehiculos/";
    if (path.includes("/mx/")) return "/mx/vehiculos/";
    if (path.includes("/compat/")) return "/cl/es/vehiculos/";
    return "/cl/es/vehiculos/";
  }

  const basePrefix = detectBasePrefix();
  const modelosUrl = getDatasetValue("epModelos", "modelosUrl") || (console.warn("[formulario_jerarquico] ⚠️ data-ep-modelos faltante. Agregar #vehiculos-endpoints con data-ep-modelos desde country_url."), basePrefix + "ajax/modelos-por-marca-anio/");
  const motoresUrl = getDatasetValue("epMotores", "motoresUrl") || basePrefix + "ajax/motores-por-modelo/";
  const cajasUrl = getDatasetValue("epCajas", "cajasUrl") || basePrefix + "ajax/cajas-por-modelo/";

  // Cuando cambia marca o año → cargar modelos
  $marca.add($anio).on("change", function () {
    const marcaId = $marca.val();
    const year = $anio.val();
    if (!marcaId || !year) {
      clearAndDisable($modelo, "Selecciona marca y año primero");
      clearAndDisable($motor, "Selecciona un modelo primero");
      clearAndDisable($caja, "Selecciona un modelo primero");
      return;
    }
    $.getJSON(modelosUrl, { marca_id: marcaId, anio: year }, function (data) {
      console.log("📦 Respuesta modelos:", data);
      $modelo.empty().append($("<option>").val("").text("Seleccione un modelo"));
      const modelos = Array.isArray(data)
        ? data
        : Array.isArray(data.results)
          ? data.results
          : [];
      console.log("📋 Modelos normalizados:", modelos.length);
      $.each(modelos, function (_, item) {
        const text = item.text || item.nombre || item.label || item.value || "";
        $modelo.append($("<option>").val(item.id).text(text));
      });
      enable($modelo);
    });
  });

  // Cuando cambia modelo → cargar motores y cajas
  $modelo.on("change", function () {
    const modeloId = $modelo.val();
    if (!modeloId) {
      clearAndDisable($motor, "Selecciona un modelo primero");
      clearAndDisable($caja, "Selecciona un modelo primero");
      return;
    }

    // Motores
    $.getJSON(motoresUrl, { modelo_id: modeloId }, function (data) {
      $motor.empty().append($("<option>").val("").text("Seleccione un motor"));
      const motores = Array.isArray(data)
        ? data
        : Array.isArray(data.results)
          ? data.results
          : Array.isArray(data.motores)
            ? data.motores
            : [];
      $.each(motores, function (_, item) {
        const text = item.text || item.nombre || item.label || item.value || "";
        $motor.append($("<option>").val(item.id).text(text));
      });
      $motor.append($("<option>").val(NEW_SENTINEL).text("➕ Agregar nuevo motor..."));
      enable($motor);
    });

    // Cajas
    $.getJSON(cajasUrl, { modelo_id: modeloId }, function (data) {
      $caja.empty().append($("<option>").val("").text("Seleccione una caja"));
      const cajas = Array.isArray(data)
        ? data
        : Array.isArray(data.results)
          ? data.results
          : Array.isArray(data.cajas)
            ? data.cajas
            : [];
      $.each(cajas, function (_, item) {
        const text = item.text || item.nombre || item.label || item.value || "";
        $caja.append($("<option>").val(item.id).text(text));
      });
      $caja.append($("<option>").val(NEW_SENTINEL).text("➕ Agregar nueva caja..."));
      enable($caja);
    });
  });

  // Detectar selección de "nuevo" motor/caja → abrir input extra
  $motor.on("change", function () {
    if ($motor.val() === NEW_SENTINEL) {
      $("#motor-nuevo-container").show();
    } else {
      $("#motor-nuevo-container").hide();
    }
  });

  $caja.on("change", function () {
    if ($caja.val() === NEW_SENTINEL) {
      $("#caja-nueva-container").show();
    } else {
      $("#caja-nueva-container").hide();
    }
  });
});
