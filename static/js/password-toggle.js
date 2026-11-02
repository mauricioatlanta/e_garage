/* Toggle visibilidad de contraseñas — añade ícono de ojo a todos los input[type=password] */
(function () {
  'use strict';

  var EYE = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>';
  var EYE_OFF = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/></svg>';

  function setIcon(btn, svg) {
    btn.innerHTML = svg;
    var s = btn.querySelector('svg');
    if (s) { s.setAttribute('width', '20'); s.setAttribute('height', '20'); }
  }

  function init() {
    document.querySelectorAll('input[type="password"]').forEach(function (inp) {
      if (inp.dataset.egPwToggle) return;
      inp.dataset.egPwToggle = '1';

      var wrap = document.createElement('span');
      wrap.style.cssText = 'position:relative;display:block;';
      inp.parentNode.insertBefore(wrap, inp);
      wrap.appendChild(inp);
      inp.style.paddingRight = '2.7rem';

      var btn = document.createElement('button');
      btn.type = 'button';
      btn.setAttribute('aria-label', 'Mostrar contraseña');
      btn.style.cssText = [
        'position:absolute',
        'right:.55rem',
        'top:50%',
        'transform:translateY(-50%)',
        'background:transparent',
        'border:0',
        'cursor:pointer',
        'padding:.2rem',
        'color:#64748b',
        'line-height:0',
        'z-index:2',
        'width:1.4rem',
        'height:1.4rem',
      ].join(';');

      setIcon(btn, EYE);

      btn.addEventListener('click', function () {
        var show = inp.type === 'password';
        inp.type = show ? 'text' : 'password';
        setIcon(btn, show ? EYE_OFF : EYE);
        btn.setAttribute('aria-label', show ? 'Ocultar contraseña' : 'Mostrar contraseña');
        inp.focus();
      });

      wrap.appendChild(btn);
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
