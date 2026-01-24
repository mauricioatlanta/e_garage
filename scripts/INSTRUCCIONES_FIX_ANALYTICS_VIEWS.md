# 🔧 Fix: Stubs para analytics/views.py

## Problema
El archivo `/srv/egarage/taller/analytics/views.py` está dañado/truncado, causando errores de importación en `urls.py` y errores 502.

## Solución Rápida: Agregar Stubs

### Opción 1: Usar el script automático (Recomendado)

```bash
# Subir el script al servidor
scp scripts/fix_analytics_views_stubs.sh usuario@servidor:/tmp/

# Ejecutar en el servidor
ssh usuario@servidor
sudo bash /tmp/fix_analytics_views_stubs.sh
```

### Opción 2: Manual con nano

1. Abrir el archivo:
```bash
sudo nano /srv/egarage/taller/analytics/views.py
```

2. Ir al final del archivo (Ctrl+End o `G` en nano)

3. Pegar este bloque:

```python
# --- HOTFIX: stubs para compatibilidad con urls.py ---
from django.http import JsonResponse, HttpResponse
from django.views import View
from django.views.decorators.http import require_GET


def dashboard_ai_view(request, *args, **kwargs):
    return HttpResponse("Dashboard AI (stub).", status=200)


@require_GET
def revenue_analytics_api(request, *args, **kwargs):
    return JsonResponse({"ok": False, "stub": "revenue_analytics_api"}, status=200)


@require_GET
def vehicle_analytics_api(request, *args, **kwargs):
    return JsonResponse({"ok": False, "stub": "vehicle_analytics_api"}, status=200)


@require_GET
def clientes_analytics_api(request, *args, **kwargs):
    return JsonResponse({"ok": False, "stub": "clientes_analytics_api"}, status=200)


@require_GET
def predictive_analytics_api(request, *args, **kwargs):
    return JsonResponse({"ok": False, "stub": "predictive_analytics_api"}, status=200)


@require_GET
def real_time_metrics_api(request, *args, **kwargs):
    return JsonResponse({"ok": False, "stub": "real_time_metrics_api"}, status=200)


class AIInsightView(View):
    def get(self, request, *args, **kwargs):
        return JsonResponse({"ok": False, "stub": "AIInsightView"}, status=200)


def export_report_view(request, *args, **kwargs):
    return JsonResponse({"ok": False, "stub": "export_report_view"}, status=200)
```

4. Guardar (Ctrl+O, Enter, Ctrl+X)

### Opción 3: Copiar archivo completo

También puedes copiar el archivo completo desde tu repo local:

```bash
# Desde tu máquina local
scp taller/analytics/views.py usuario@servidor:/tmp/views.py

# En el servidor
sudo cp /tmp/views.py /srv/egarage/taller/analytics/views.py
sudo chown egarage:egarage /srv/egarage/taller/analytics/views.py
```

## 2. Reiniciar y Verificar

```bash
# Reiniciar Gunicorn
sudo systemctl restart egarage-gunicorn

# Verificar que Django carga sin errores
sudo -u egarage -H bash -lc '
cd /srv/egarage
/srv/egarage/venv/bin/python manage.py check
'
```

**Resultado esperado:** `System check identified no issues (0 silenced).`

## 3. Si check sigue fallando: Verificar otros módulos

Si `manage.py check` sigue fallando, puede ser que otros módulos también estén dañados:

```bash
# Usar el script de verificación
scp scripts/verificar_modulos_analytics.sh usuario@servidor:/tmp/
sudo bash /tmp/verificar_modulos_analytics.sh
```

O manualmente:

```bash
sudo -u egarage -H bash -lc '
cd /srv/egarage
/srv/egarage/venv/bin/python - <<PY
import importlib
mods = [
  "taller.analytics.views",
  "taller.analytics.admin_views",
  "taller.analytics.funcionalidades_adicionales",
  "taller.analytics.apis_avanzadas",
]
for m in mods:
    try:
        importlib.import_module(m)
        print("OK:", m)
    except Exception as e:
        print("FAIL:", m, "=>", e)
PY
'
```

Esto te dirá exactamente qué módulo está fallando.

## 4. Verificar URLs se resuelven correctamente

```bash
sudo -u egarage -H bash -lc '
cd /srv/egarage
/srv/egarage/venv/bin/python manage.py shell - <<PY
from django.urls import resolve
try:
    result = resolve("/analytics/")
    print("✅ URL resuelta:", result.view_name)
except Exception as e:
    print("❌ Error:", e)
PY
'
```

## Checklist

- [ ] Stubs agregados a `/srv/egarage/taller/analytics/views.py`
- [ ] `sudo systemctl restart egarage-gunicorn` ejecutado
- [ ] `manage.py check` pasa sin errores
- [ ] `resolve()` funciona correctamente
- [ ] No hay errores 502 en los logs

## Notas

- Estos stubs son temporales para que Django pueda cargar las URLs
- Una vez que el servidor esté estable, deberías restaurar el archivo completo desde tu repo/backup
- O reducir `analytics/urls.py` para que solo apunte a endpoints reales

## Archivos de referencia

- `scripts/STUBS_ANALYTICS_VIEWS.py` - Contiene solo los stubs para copiar/pegar
- `scripts/fix_analytics_views_stubs.sh` - Script automático para agregar stubs
- `scripts/verificar_modulos_analytics.sh` - Script para verificar todos los módulos
