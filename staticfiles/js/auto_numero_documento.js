document.addEventListener('DOMContentLoaded', function () {
  const tipoSelect = document.querySelector('#id_tipo_documento');
  const numeroInput = document.querySelector('#id_numero');
  const card = document.querySelector('.card.shadow.rounded-xl');

  const siglas = {
    'Presupuesto': 'P',
    'Orden de Trabajo': 'O',
    'Factura': 'F'
  };

  function actualizarEstiloTipo(tipo) {
    if (!card) return;

    card.classList.remove(
      'bg-info-subtle', 'bg-success-subtle', 'bg-warning-subtle',
      'border-info', 'border-success', 'border-warning'
    );

    if (tipo === 'Presupuesto') {
      card.classList.add('bg-info-subtle', 'border-info');
    } else if (tipo === 'Orden de Trabajo') {
      card.classList.add('bg-success-subtle', 'border-success');
    } else if (tipo === 'Factura') {
      card.classList.add('bg-warning-subtle', 'border-warning');
    }
  }

  function obtenerNumeroDesdeServidor(tipoTexto) {
    fetch(`/ajax/obtener-numero-documento/?tipo=${encodeURIComponent(tipoTexto)}`)
      .then(response => response.json())
      .then(data => {
        if (data.numero && numeroInput) {
          numeroInput.value = data.numero;
        }
      })
      .catch(err => {
        console.error("❌ Error al obtener número de documento:", err);
      });
  }

  if (tipoSelect && numeroInput) {
    // Estilo inicial y número inicial
    const tipoInicial = tipoSelect.options[tipoSelect.selectedIndex].text;
    actualizarEstiloTipo(tipoInicial);
    obtenerNumeroDesdeServidor(tipoInicial);

    tipoSelect.addEventListener('change', function () {
      const tipoTexto = tipoSelect.options[tipoSelect.selectedIndex].text;
      actualizarEstiloTipo(tipoTexto);
      obtenerNumeroDesdeServidor(tipoTexto);
    });
  }
});
