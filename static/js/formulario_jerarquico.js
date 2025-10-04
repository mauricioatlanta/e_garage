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
    // Construir URL basada en la ruta actual
    const baseUrl = window.location.pathname.includes('/us/') ? '/us/vehiculos/ajax/modelos-por-marca-anio/' : '/cl/vehiculos/ajax/modelos-por-marca-anio/';
    
    $.getJSON(baseUrl, { marca_id: marcaId, anio: year }, function (data) {
      $modelo.empty().append($("<option>").val("").text("Seleccione un modelo"));
      $.each(data.results || data, function (_, item) {
        $modelo.append($("<option>").val(item.id).text(item.text || item.nombre));
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

    // Construir URLs basadas en la ruta actual
    const motoresUrl = window.location.pathname.includes('/us/') ? '/us/vehiculos/ajax/motores-por-modelo/' : '/cl/vehiculos/ajax/motores-por-modelo/';
    const cajasUrl = window.location.pathname.includes('/us/') ? '/us/vehiculos/ajax/cajas-por-modelo/' : '/cl/vehiculos/ajax/cajas-por-modelo/';

    // Motores
    $.getJSON(motoresUrl, { modelo_id: modeloId }, function (data) {
      $motor.empty().append($("<option>").val("").text("Seleccione un motor"));
      $.each(data.results || data, function (_, item) {
        $motor.append($("<option>").val(item.id).text(item.text || item.nombre));
      });
      $motor.append($("<option>").val(NEW_SENTINEL).text("➕ Agregar nuevo motor..."));
      enable($motor);
    });

    // Cajas
    $.getJSON(cajasUrl, { modelo_id: modeloId }, function (data) {
      $caja.empty().append($("<option>").val("").text("Seleccione una caja"));
      $.each(data.results || data, function (_, item) {
        $caja.append($("<option>").val(item.id).text(item.text || item.nombre));
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