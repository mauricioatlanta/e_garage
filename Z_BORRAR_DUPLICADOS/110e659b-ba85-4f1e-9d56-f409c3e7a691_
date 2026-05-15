/*! Select2 Spanish translation (no AMD, compatible con DAL) */
(function($){
  if($.fn.select2){
    $.fn.select2.defaults.set('language', {
      errorLoading: function () { return "No se pudieron cargar los resultados."; },
      inputTooLong: function (args) { var overChars = args.input.length - args.maximum; return "Por favor, elimine " + overChars + " car" + (overChars == 1 ? "ácter" : "acteres"); },
      inputTooShort: function (args) { var remainingChars = args.minimum - args.input.length; return "Por favor, introduzca " + remainingChars + " car" + (remainingChars == 1 ? "ácter" : "acteres"); },
      loadingMore: function () { return "Cargando más resultados…"; },
      maximumSelected: function (args) { return "Sólo puede seleccionar " + args.maximum + " elemento" + (args.maximum == 1 ? "" : "s"); },
      noResults: function () { return "No se encontraron resultados"; },
      searching: function () { return "Buscando…"; },
      removeAllItems: function () { return "Eliminar todos los elementos"; }
    });
  }
})(window.jQuery);
