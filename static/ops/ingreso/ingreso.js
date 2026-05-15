/**
 * Centro de Ingreso Pro - JS para home (OCR patente), checklist (SVG daños), repuestos (búsqueda/add).
 */
(function() {
  'use strict';

  var IngresoHome = {
    init: function(opts) {
      this.opts = opts || {};
      var btnManual = document.getElementById('btn-manual-patente');
      var inputManual = document.getElementById('patente-manual');
      var form = document.getElementById('form-patente-manual');
      var inputHidden = document.getElementById('input-patente-manual');
      if (btnManual && form && inputHidden) {
        btnManual.addEventListener('click', function() {
          var val = (inputManual && inputManual.value || '').trim().toUpperCase().replace(/[\s\-]/g, '');
          if (!val) return;
          inputHidden.value = val;
          form.submit();
        });
      }
      if (this.opts.ocrAvailable) {
        var btnOcr = document.getElementById('btn-ocr-patente');
        var inputFile = document.getElementById('input-ocr-patente');
        if (btnOcr && inputFile) {
          btnOcr.addEventListener('click', function() { inputFile.click(); });
          inputFile.addEventListener('change', function() {
            if (!inputFile.files.length) return;
            var fd = new FormData();
            fd.append('image', inputFile.files[0]);
            var csrf = (document.querySelector('[name=csrfmiddlewaretoken]') && document.querySelector('[name=csrfmiddlewaretoken]').value) || (document.getElementById('csrf-token') && document.getElementById('csrf-token').value) || '';
            fd.append('csrfmiddlewaretoken', csrf);
            var xhr = new XMLHttpRequest();
            xhr.open('POST', window.INGRESO_OCR_PATENTE_URL || '/cl/es/ops/api/ocr/patente/');
            xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');
            xhr.onload = function() {
              var res = JSON.parse(xhr.responseText || '{}');
              var container = document.getElementById('ocr-candidates');
              if (!container) return;
              if (!res.success || !res.candidates || !res.candidates.length) {
                container.innerHTML = '<p class="text-warning">No se detectaron candidatos. Use ingreso manual.</p>';
                return;
              }
              container.innerHTML = res.candidates.map(function(c) {
                return '<button type="button" class="btn btn-outline-cyan me-2 mb-2" data-patente="' + (c.text || '') + '">' + (c.text || '') + ' (' + (c.score || 0) + ')</button>';
              }).join('');
              container.querySelectorAll('button').forEach(function(btn) {
                btn.addEventListener('click', function() {
                  var p = this.getAttribute('data-patente');
                  if (p && form && inputHidden) {
                    inputHidden.value = p;
                    form.action = (window.INGRESO_PATENTE_URL || '/cl/es/ops/ingreso/patente/') + '?patente=' + encodeURIComponent(p);
                    form.submit();
                  }
                });
              });
            };
            xhr.send(fd);
            inputFile.value = '';
          });
        }
      }
    }
  };

  var ChecklistIngreso = {
    marks: [],
    init: function(opts) {
      this.opts = opts || {};
      this.documentoId = opts.documentoId;
      this.saveUrl = opts.saveUrl;
      this.csrfToken = opts.csrfToken;
      if (opts.danosJson && typeof opts.danosJson === 'object' && opts.danosJson.marks) {
        this.marks = opts.danosJson.marks.slice();
      }
      var self = this;
      document.querySelectorAll('.damage-zone').forEach(function(el) {
        el.addEventListener('click', function() {
          var zone = this.getAttribute('data-zone');
          document.getElementById('dano-zone-current').value = zone;
          var modal = new (window.bootstrap && window.bootstrap.Modal)(document.getElementById('modal-dano'));
          modal.show();
        });
      });
      var btnSave = document.getElementById('btn-dano-save');
      if (btnSave) {
        btnSave.addEventListener('click', function() {
          var zone = document.getElementById('dano-zone-current').value;
          var type = document.getElementById('dano-type').value;
          var note = document.getElementById('dano-note').value;
          var severity = parseInt(document.getElementById('dano-severity').value, 10) || 1;
          self.marks.push({ zone: zone, type: type, note: note, severity: severity });
          self.saveDanos();
          if (window.bootstrap) { var m = document.getElementById('modal-dano'); if (m) window.bootstrap.Modal.getInstance(m).hide(); }
        });
      }
      this.renderMarks();
    },
    saveDanos: function() {
      var self = this;
      var payload = JSON.stringify({ danos: { marks: this.marks }, documento_id: this.documentoId });
      var xhr = new XMLHttpRequest();
      xhr.open('POST', this.saveUrl);
      xhr.setRequestHeader('Content-Type', 'application/json');
      xhr.setRequestHeader('X-CSRFToken', this.csrfToken);
      xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');
      xhr.onload = function() { self.renderMarks(); };
      xhr.send(payload);
    },
    renderMarks: function() {
      var container = document.getElementById('danos-marks');
      if (!container) return;
      container.innerHTML = this.marks.map(function(m, i) {
        return '<span class="badge bg-cyan me-1" title="' + (m.note || m.type) + '">' + m.zone + '</span>';
      }).join('');
    }
  };

  var RepuestosIngreso = {
    init: function(opts) {
      this.opts = opts || {};
      this.documentoId = opts.documentoId;
      this.addRepuestoUrl = opts.addRepuestoUrl;
      this.buscarRepuestoUrl = opts.buscarRepuestoUrl;
      this.ocrRepuestoUrl = opts.ocrRepuestoUrl;
      this.csrfToken = opts.csrfToken;
      var self = this;

      var btnBuscar = document.getElementById('btn-buscar-repuesto');
      var inputQ = document.getElementById('repuesto-q');
      if (btnBuscar && inputQ) {
        btnBuscar.addEventListener('click', function() { self.buscarRepuesto(inputQ.value.trim()); });
        inputQ.addEventListener('keydown', function(e) { if (e.key === 'Enter') { e.preventDefault(); self.buscarRepuesto(inputQ.value.trim()); } });
      }

      document.getElementById('btn-add-repuesto-libre') && document.getElementById('btn-add-repuesto-libre').addEventListener('click', function() {
        var codigo = (document.getElementById('repuesto-codigo') && document.getElementById('repuesto-codigo').value) || '';
        var nombre = (document.getElementById('repuesto-nombre') && document.getElementById('repuesto-nombre').value) || codigo || 'Repuesto';
        var cantidad = parseInt((document.getElementById('repuesto-cantidad') && document.getElementById('repuesto-cantidad').value), 10) || 1;
        var precio = parseFloat((document.getElementById('repuesto-precio') && document.getElementById('repuesto-precio').value), 10) || 0;
        self.addRepuesto({ codigo: codigo, nombre: nombre, cantidad: cantidad, precio_unitario: precio });
      });

      var btnOcr = document.getElementById('btn-ocr-repuesto');
      var inputOcr = document.getElementById('input-ocr-repuesto');
      if (btnOcr && inputOcr) {
        btnOcr.addEventListener('click', function() {
          if (!inputOcr.files.length) return;
          var fd = new FormData();
          fd.append('image', inputOcr.files[0]);
          fd.append('csrfmiddlewaretoken', self.csrfToken);
          var xhr = new XMLHttpRequest();
          xhr.open('POST', self.ocrRepuestoUrl);
          xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');
          xhr.onload = function() {
            var res = JSON.parse(xhr.responseText || '{}');
            var container = document.getElementById('ocr-repuesto-candidates');
            if (!container) return;
            if (!res.success || !res.candidates || !res.candidates.length) {
              container.innerHTML = '<p class="text-warning">No se detectaron códigos. Use manual.</p>';
              return;
            }
            container.innerHTML = res.candidates.map(function(c) {
              return '<button type="button" class="btn btn-outline-cyan me-2 mb-2 btn-sm" data-codigo="' + c + '">' + c + '</button>';
            }).join('');
            container.querySelectorAll('button').forEach(function(btn) {
              btn.addEventListener('click', function() {
                inputQ.value = this.getAttribute('data-codigo');
                self.buscarRepuesto(inputQ.value);
              });
            });
          };
          xhr.send(fd);
        });
      }
    },
    buscarRepuesto: function(q) {
      if (!q) return;
      var self = this;
      var xhr = new XMLHttpRequest();
      xhr.open('GET', this.buscarRepuestoUrl + '?q=' + encodeURIComponent(q));
      xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');
      xhr.onload = function() {
        var res = JSON.parse(xhr.responseText || '{}');
        var container = document.getElementById('repuesto-results');
        if (!container) return;
        if (!res.success || !res.items || !res.items.length) {
          container.innerHTML = '<p class="text-white-50">Sin resultados. Agregue como línea libre.</p>';
          return;
        }
        container.innerHTML = res.items.map(function(it) {
          return '<button type="button" class="list-group-item list-group-item-action list-group-item-dark" data-id="' + it.id + '" data-codigo="' + (it.codigo || '') + '" data-nombre="' + (it.nombre || '') + '" data-precio="' + (it.precio_venta || 0) + '">' + (it.codigo || '') + ' - ' + (it.nombre || '') + '</button>';
        }).join('');
        container.querySelectorAll('button').forEach(function(btn) {
          btn.addEventListener('click', function() {
            self.addRepuesto({
              repuesto_id: this.getAttribute('data-id'),
              codigo: this.getAttribute('data-codigo'),
              nombre: this.getAttribute('data-nombre'),
              cantidad: 1,
              precio_unitario: this.getAttribute('data-precio')
            });
          });
        });
      };
      xhr.send();
    },
    addRepuesto: function(data) {
      var self = this;
      var fd = new FormData();
      fd.append('csrfmiddlewaretoken', this.csrfToken);
      fd.append('cantidad', data.cantidad || 1);
      fd.append('precio_unitario', data.precio_unitario || '0');
      if (data.repuesto_id) fd.append('repuesto_id', data.repuesto_id);
      if (data.codigo) fd.append('codigo', data.codigo);
      if (data.nombre) fd.append('nombre', data.nombre);
      var xhr = new XMLHttpRequest();
      xhr.open('POST', this.addRepuestoUrl);
      xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');
      xhr.setRequestHeader('X-CSRFToken', this.csrfToken);
      xhr.onload = function() {
        if (xhr.status >= 200 && xhr.status < 300) window.location.reload();
      };
      xhr.send(fd);
    }
  };

  window.IngresoHome = IngresoHome;
  window.ChecklistIngreso = ChecklistIngreso;
  window.RepuestosIngreso = RepuestosIngreso;
})();
