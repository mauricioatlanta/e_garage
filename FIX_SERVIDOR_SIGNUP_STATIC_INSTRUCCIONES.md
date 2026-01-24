# Fix Servidor: ModuleNotFoundError y collectstatic

## Problemas identificados

1. **ModuleNotFoundError**: Existe el `.pyc` pero no el `.py` de `signup_redirects.py`
2. **collectstatic error**: Falta `STATIC_URL` en settings (aunque está en el código, puede que no se esté cargando)

## Solución

### Opción 1: Ejecutar script automático (recomendado)

```bash
sudo -u egarage -H bash -lc '/srv/egarage/FIX_SERVIDOR_SIGNUP_STATIC.sh'
```

### Opción 2: Ejecutar manualmente

#### 1. Crear signup_redirects.py

```bash
sudo -u egarage -H bash -lc '
cd /srv/egarage
cat > taller/views_extra/signup_redirects.py << "EOF"
"""
Redirect universal para signup por país.
"""

from django.shortcuts import redirect


def signup_redirect(request, country_code: str):
    """
    Redirige a /accounts/signup/ con el parámetro from=country_code.
    """
    country_code_lower = country_code.lower()
    return redirect(f"/accounts/signup/?from={country_code_lower}")
EOF
'
```

#### 2. Validar import

```bash
sudo -u egarage -H bash -lc '
cd /srv/egarage
set -a; source /srv/egarage/.env; set +a
source venv/bin/activate
python -c "from taller.views_extra.signup_redirects import signup_redirect; print(\"OK\", signup_redirect)"
'
```

#### 3. Verificar STATIC_URL

```bash
sudo -u egarage -H bash -lc '
cd /srv/egarage
set -a; source /srv/egarage/.env; set +a
source venv/bin/activate
python -c "import os; print(os.environ.get(\"DJANGO_SETTINGS_MODULE\"))"
python -c "from django.conf import settings; print(\"STATIC_URL=\", getattr(settings,\"STATIC_URL\", None))"
'
```

**Si STATIC_URL es None**, necesitas agregarlo al archivo de settings que está usando. Por ejemplo, si usa `gestion_taller.settings_prod`, edita `/srv/egarage/gestion_taller/settings_prod.py` y asegúrate de que tenga:

```python
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"  # o la ruta que uses
```

#### 4. Limpiar .pyc fantasma (opcional)

```bash
rm -f /srv/egarage/taller/views_extra/__pycache__/signup_redirects*.pyc
```

#### 5. Re-ejecutar deploy

```bash
sudo -u egarage -H bash -lc '
cd /srv/egarage
set -a; source /srv/egarage/.env; set +a
source venv/bin/activate

python manage.py check
python manage.py migrate --noinput
python manage.py collectstatic --noinput
'
```

## Verificación

Después de aplicar los fixes, verifica que todo funciona:

```bash
sudo -u egarage -H bash -lc '
cd /srv/egarage
set -a; source /srv/egarage/.env; set +a
source venv/bin/activate

# Verificar que el import funciona
python -c "from taller.views_extra.signup_redirects import signup_redirect; print(\"✅ Import OK\")"

# Verificar STATIC_URL
python -c "from django.conf import settings; print(\"STATIC_URL:\", getattr(settings, \"STATIC_URL\", \"NO DEFINIDO\"))"

# Verificar que collectstatic funciona
python manage.py collectstatic --noinput --dry-run
'
```

## Notas

- El archivo `signup_redirects.py` ya existe en el repositorio local, pero puede que no se haya subido al servidor
- `STATIC_URL` está definido en `gestion_taller/settings.py` y `gestion_taller/settings_prod.py`, pero puede que el servidor esté usando otro archivo de settings
- El `.pyc` fantasma no es crítico, pero es bueno limpiarlo para evitar confusión
