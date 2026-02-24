
/*! Dummy autocomplete_light.js */
window.dal = window.dal || {};
dal.widgets = {
  init: function () {
    console.log("📦 DAL inicializado");
    const widgets = document.querySelectorAll('[data-autocomplete-light-function]');
    widgets.forEach(w => {
      const $ = window.jQuery;
      if ($(w).select2) {
        $(w).select2();
      } else {
        console.warn("⚠️ select2 no está disponible para", w);
      }
    });
  }
};
