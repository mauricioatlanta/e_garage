/* Modal de detalle de pieza para el storefront público (tienda.html / kiosko.html).
   Vanilla JS — el storefront público no carga Alpine ni ningún framework.
   Las cards marcan su contenido con data-pieza-modal + data-* (ver _card_pieza.html
   y el bloque de card inline en tienda.html); el modal es un único nodo por página
   (_modal_pieza.html) que se rellena al vuelo con esos data-* al hacer click. */
(function () {
  "use strict";

  function getModal() {
    return document.getElementById("pieza-modal");
  }

  function fillText(modal, selector, value) {
    var el = modal.querySelector(selector);
    if (el) el.textContent = value || "";
  }

  function toggleWrap(modal, wrapSelector, hasValue) {
    var wrap = modal.querySelector(wrapSelector);
    if (wrap) wrap.style.display = hasValue ? "" : "none";
  }

  function openModal(trigger) {
    var modal = getModal();
    if (!modal) return;

    var d = trigger.dataset;

    fillText(modal, "[data-modal-nombre]", d.nombre);
    fillText(modal, "[data-modal-condicion]", d.condicion);
    fillText(modal, "[data-modal-codigo]", d.codigo);
    fillText(modal, "[data-modal-vehiculo]", d.vehiculo);
    fillText(modal, "[data-modal-zona]", d.zona);
    fillText(modal, "[data-modal-observaciones]", d.observaciones);
    fillText(modal, "[data-modal-precio]", d.precio);

    toggleWrap(modal, "[data-modal-codigo-wrap]", !!d.codigo);
    toggleWrap(modal, "[data-modal-vehiculo-wrap]", !!d.vehiculo);
    toggleWrap(modal, "[data-modal-zona-wrap]", !!d.zona);

    var obsEl = modal.querySelector("[data-modal-observaciones]");
    if (obsEl) obsEl.style.display = d.observaciones ? "" : "none";

    var waBtn = modal.querySelector("[data-modal-wa]");
    if (waBtn) {
      if (d.waUrl) {
        waBtn.href = d.waUrl;
        waBtn.style.display = "";
      } else {
        waBtn.style.display = "none";
      }
    }

    var telBtn = modal.querySelector("[data-modal-tel]");
    if (telBtn) {
      if (d.telUrl) {
        telBtn.href = d.telUrl;
        telBtn.style.display = "";
      } else {
        telBtn.style.display = "none";
      }
    }

    modal.classList.add("is-open");
    document.body.style.overflow = "hidden";
  }

  function closeModal() {
    var modal = getModal();
    if (!modal) return;
    modal.classList.remove("is-open");
    document.body.style.overflow = "";
  }

  document.addEventListener("click", function (e) {
    if (e.target.closest("[data-stop-modal]")) return;

    var closeTrigger = e.target.closest("[data-modal-close]");
    if (closeTrigger) {
      closeModal();
      return;
    }

    var backdrop = e.target.closest("[data-modal-backdrop]");
    if (backdrop && e.target === backdrop) {
      closeModal();
      return;
    }

    var trigger = e.target.closest("[data-pieza-modal]");
    if (trigger) {
      openModal(trigger);
    }
  });

  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") {
      closeModal();
      return;
    }
    if (e.key !== "Enter" && e.key !== " ") return;
    var trigger = e.target.closest && e.target.closest("[data-pieza-modal]");
    if (!trigger) return;
    e.preventDefault();
    openModal(trigger);
  });
})();
