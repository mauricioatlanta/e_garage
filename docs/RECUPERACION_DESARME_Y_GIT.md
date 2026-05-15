# Recuperación: Desarme + Git en servidor

## Qué pasó

1. **Git**: `checkout review/templates-auth-core-clean` falló por cambios locales y archivos sin trackear. La rama no llegó a cambiarse.
2. **Django**: En ese árbol (o en el servidor), `taller.models.pieza_desarme` no existe, pero `taller/desarme/views.py` lo importa → `ModuleNotFoundError` al cargar URLs → Gunicorn/Django caen.

## Cambio hecho en este repo (para que no vuelva a pasar)

En **`taller/urls_desarme.py`** las rutas de desarme solo se registran si existe el modelo:

- Si `taller.models.pieza_desarme` existe → se cargan todas las URLs de desarme.
- Si **no** existe (rama sin Desarme) → `urlpatterns = []`, no se importan las vistas y **el sitio arranca igual**. `/desarme/` dará 404 en esa rama.

Así, en ramas donde el módulo Desarme no está, el arranque ya no se rompe.

---

## En el servidor: recuperación en 2 fases

### Fase 1 – Dejar el sitio arriba ya

Si quieres que el sitio responda de inmediato sin tocar Git:

**Opción A – Desactivar solo la URL de desarme (rápido)**

```bash
cd /srv/egarage
source venv/bin/activate
```

Editar `taller/urls.py` y **comentar** la línea de desarme:

```python
# path("desarme/", include(("taller.urls_desarme", "desarme"), namespace="desarme")),
```

Luego:

```bash
python manage.py check
sudo systemctl restart gunicorn
sudo journalctl -u gunicorn -n 50 --no-pager
```

**Opción B – Subir el cambio de `urls_desarme.py` (recomendado)**

Si en el servidor puedes actualizar solo ese archivo (o hacer merge de la rama que ya tiene el fix):

- Copiar el contenido actual de `taller/urls_desarme.py` de este repo (con el `try/except ImportError` y `urlpatterns = []` cuando falla el import). Con eso, aunque no exista `taller.models.pieza_desarme`, el arranque no falla y no hace falta comentar la línea en `taller/urls.py`.

---

### Fase 2 – Ordenar Git sin perder nada

```bash
cd /srv/egarage
source venv/bin/activate

# 1) Ver estado
git branch --show-current
git status

# 2) Respaldo de cambios locales
mkdir -p /root/backups_egarage
git diff > /root/backups_egarage/working_tree_$(date +%F_%H%M%S).patch
git diff --cached > /root/backups_egarage/index_$(date +%F_%H%M%S).patch
git status --short > /root/backups_egarage/status_$(date +%F_%H%M%S).txt

# 3) Guardar todo (incl. no trackeados) en stash
git stash push -u -m "backup antes de review/templates-auth-core-clean"

# 4) Comprobar que quedó limpio
git status

# 5) Cambiar de rama
git fetch --all --prune
git checkout review/templates-auth-core-clean
git pull --rebase origin review/templates-auth-core-clean
```

Si en esa rama **no** existe el modelo Desarme y quieres que el sitio siga arrancando, aplica en el servidor el mismo `urls_desarme.py` con el `try/except` (o comenta la línea de desarme en `taller/urls.py` como en Fase 1).

---

## Comprobar dónde está el modelo (en el servidor)

```bash
cd /srv/egarage
rg -n "class PiezaDesarme|ESTADO_VENDIDA" taller/
```

- Si **no aparece nada**: esa rama no tiene el módulo Desarme; usar `urls_desarme.py` con fallback o comentar la ruta.
- Si **aparece** en otro archivo (p. ej. `taller/models/repuesto.py`): habría que ajustar el import en `taller/desarme/views.py` a ese módulo (y en `taller/urls_desarme.py` el `try/except` debería comprobar ese mismo módulo).
