#!/usr/bin/env python3
"""
Script para arreglar los problemas con Select2 en templates:
1. Título roto en base.html (YA CORREGIDO)
2. Conflicto DAL + CDN Select2 (YA CORREGIDO)
3. JavaScript robusto para autocompletado de clientes
"""

import os
import re
from pathlib import Path

# JavaScript robusto para Select2
ROBUST_SELECT2_JS = """
<script>
(function() {
  const base = window.location.pathname.startsWith('/us/') ? '/us' : '/cl';
  const origin = window.location.origin;

  const $ = window.jQuery;
  if (!$ || !$.fn || !$.fn.select2) {
    console.warn("Select2/jQuery no están cargados.");
    return;
  }

  const dropdownParent = document.getElementById('eg-portal') || document.body;
  const $cliente = $('#id_cliente');

  function normalizeClientResults(data) {
    const raw = Array.isArray(data) ? data : (data.results || data.items || []);
    return raw.map(it => {
      const text = it.text ??
                   [it.nombre, it.apellido].filter(Boolean).join(' ') ||
                   it.nombre || it.name || it.email || it.telefono || String(it.id);
      const subtitle = it.subtitle || it.email || it.telefono || '';
      return { id: it.id, text, subtitle };
    });
  }

  $cliente.select2({
    theme: 'bootstrap-5',
    placeholder: 'Buscar cliente…',
    allowClear: true,
    minimumInputLength: 1,
    width: '100%',
    dropdownParent: $(dropdownParent),
    ajax: {
      url: origin + base + "/ajax/clientes/buscar/",
      dataType: 'json',
      delay: 250,
      cache: true,
      data: function(params) {
        return { q: params.term || '', page: params.page || 1 };
      },
      beforeSend: function(xhr) {
        xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');
      },
      processResults: function(data, params) {
        params.page = params.page || 1;
        const results = normalizeClientResults(data);
        return { results, pagination: { more: !!(data && data.more) } };
      },
      transport: function (params, success, failure) {
        const req = $.ajax(params);
        req.then(success).fail(function(xhr){
          console.error("❌ AJAX clientes:", xhr.status, xhr.responseText);
          failure(xhr);
        });
        return req;
      }
    },
    templateResult: function(item) {
      if (!item.id) return item.text;
      const sub = item.subtitle ? `<div class="text-muted small">${item.subtitle}</div>` : '';
      return $(`<div><div><strong>${item.text}</strong></div>${sub}</div>`);
    },
    templateSelection: function(item) { return item.text || item.id; }
  });

  const vehiculoSelect = document.querySelector('select[name="vehiculo"]');
  function cargarVehiculos(clienteId) {
    if (!vehiculoSelect) return;
    if (!clienteId) {
      vehiculoSelect.innerHTML = '<option value="">-- Seleccionar Vehículo --</option>';
      return;
    }
    vehiculoSelect.innerHTML = '<option value="">-- Cargando vehículos... --</option>';

    const urlA = `${origin + base}/ajax/vehiculos-por-cliente/?cliente=${encodeURIComponent(clienteId)}`;
    const urlB = `${origin + base}/ajax/vehiculos-por-cliente/?cliente_id=${encodeURIComponent(clienteId)}`;

    fetch(urlA, { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
      .then(r => r.ok ? r.json() : Promise.reject())
      .then(renderVehiculos)
      .catch(() => {
        fetch(urlB, { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
          .then(r => r.json())
          .then(renderVehiculos)
          .catch(err => {
            console.error("❌ AJAX vehículos:", err);
            vehiculoSelect.innerHTML = '<option value="">-- Error al cargar vehículos --</option>';
          });
      });
  }
  function renderVehiculos(data) {
    const raw = Array.isArray(data) ? data : (data.results || []);
    const opts = ['<option value="">-- Seleccionar Vehículo --</option>']
      .concat(raw.map(v => {
        const label = v.text || [v.patente, v.marca, v.modelo].filter(Boolean).join(' ') || `Vehículo #${v.id}`;
        return `<option value="${v.id}">${label}</option>`;
      }));
    vehiculoSelect.innerHTML = opts.join('');
  }

  $cliente.on('select2:select', e => cargarVehiculos(e.params.data.id))
          .on('select2:clear', () => cargarVehiculos(''));
})();
</script>
"""


def find_templates_with_select2():
    """Buscar templates que usan Select2 y necesitan corrección."""
    templates = []
    base_dir = Path(".")

    # Buscar en los directorios de templates
    for template_dir in ["templates", "templates_new", "templates_canonical"]:
        if (base_dir / template_dir).exists():
            for file_path in (base_dir / template_dir).rglob("*.html"):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                        if "select2" in content.lower() and "id_cliente" in content:
                            templates.append(file_path)
                except:
                    pass

    return templates


def update_template_with_robust_js(template_path):
    """Actualizar template con JavaScript robusto."""
    try:
        with open(template_path, "r", encoding="utf-8") as f:
            content = f.read()

        print(f"🔧 Actualizando: {template_path}")

        # Buscar y reemplazar JavaScript Select2 existente
        # Patrón para detectar configuración de Select2 existente
        select2_pattern = r"\$cliente\.select2\({[^}]*ajax:\s*{[^}]*}[^}]*}\);"

        if re.search(select2_pattern, content):
            print(f"  ✅ Encontrado Select2 existente, reemplazando...")

            # Buscar el bloque de script completo donde está Select2
            script_start = content.find("<script>")
            script_end = content.find("</script>", script_start)

            if script_start != -1 and script_end != -1:
                # Extraer el contenido antes y después del script
                before_script = content[:script_start]
                after_script = content[script_end + 9 :]  # 9 = len('</script>')

                # Agregar el nuevo script robusto
                new_content = before_script + ROBUST_SELECT2_JS + after_script

                # Backup del archivo original
                backup_path = str(template_path) + ".backup"
                with open(backup_path, "w", encoding="utf-8") as f:
                    f.write(content)

                # Escribir el archivo actualizado
                with open(template_path, "w", encoding="utf-8") as f:
                    f.write(new_content)

                print(f"  ✅ Actualizado exitosamente")
                return True

        return False

    except Exception as e:
        print(f"  ❌ Error actualizando {template_path}: {e}")
        return False


def main():
    """Función principal."""
    print("🚀 Iniciando corrección de problemas Select2...")
    print("=" * 60)

    # Buscar templates con Select2
    templates = find_templates_with_select2()

    if not templates:
        print("❌ No se encontraron templates con Select2")
        return

    print(f"📋 Encontrados {len(templates)} templates con Select2:")
    for t in templates:
        print(f"  - {t}")

    print("\n" + "=" * 60)

    # Actualizar cada template
    updated_count = 0
    for template_path in templates:
        if update_template_with_robust_js(template_path):
            updated_count += 1

    print("\n" + "=" * 60)
    print(f"✅ Proceso completado:")
    print(f"   - {updated_count} templates actualizados")
    print(f"   - {len(templates) - updated_count} templates sin cambios")
    print(f"   - Backups creados con extensión .backup")

    print("\n🔍 Sanity checks recomendados:")
    print("1. Abrir /cl/ajax/clientes/buscar/?q=a en navegador")
    print(
        '2. Verificar que devuelve JSON con estructura {"results":[...],"more":false}'
    )
    print("3. En consola del navegador, no debe haber errores de Select2")
    print("4. En Network, peticiones AJAX deben tener status 200")


if __name__ == "__main__":
    main()
