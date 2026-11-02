# Fix Crítico: Configuración Híbrida DEV/PROD

## 🚨 PROBLEMA IDENTIFICADO

El sistema estaba corriendo con **configuración híbrida** (DEV + PROD) en producción, causando comportamiento no determinístico.

---

## 🔥 CAUSA RAÍZ

### Conflicto de Configuración

| Componente | Configuración | Estado |
|------------|---------------|--------|
| systemd (gunicorn.service) | `DJANGO_SETTINGS_MODULE=gestion_taller.settings_prod` | ✅ Correcto |
| wsgi.py | `os.environ.setdefault(..., "gestion_taller.settings")` | ❌ DEV |
| manage.py | `os.environ.setdefault(..., "gestion_taller.settings")` | ❌ DEV |

### El Problema con `setdefault()`

```python
# ❌ PROBLEMA
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")

# Si systemd ya definió la variable, setdefault() la respeta
# PERO si Gunicorn no inyecta la variable ANTES de que wsgi.py se ejecute,
# wsgi.py usa el valor por defecto (settings de DEV)
```

---

## 💥 SÍNTOMAS DEL PROBLEMA

Todos estos bugs eran causados por la configuración híbrida:

- ❌ Login inconsistente
- ❌ Emails con templates incorrectos
- ❌ `SECRET_KEY` inconsistente entre requests
- ❌ Sesiones inválidas aleatoriamente
- ❌ Password reset fallando
- ❌ Comportamiento "fantasma" (funciona/no funciona)
- ❌ Warning: "Modo de desarrollo activado" en producción

### Evidencia del Problema

```bash
# Logs de producción mostraban:
WARNING:root:Modo de desarrollo activado. Asegúrate de no usar esto en producción.

# Esto SOLO aparece si se carga settings (DEV), no settings_prod
```

---

## ✅ SOLUCIÓN IMPLEMENTADA

### 1. Forzar `settings_prod` en `wsgi.py`

**Archivo:** `gestion_taller/wsgi.py`

**Cambio:**
```python
# ❌ ANTES (permitía override accidental)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")

# ✅ DESPUÉS (fuerza producción)
os.environ["DJANGO_SETTINGS_MODULE"] = "gestion_taller.settings_prod"
```

**Razón:** Usar asignación directa (`=`) en vez de `setdefault()` garantiza que siempre se use `settings_prod`, sin importar el orden de carga.

---

### 2. Actualizar `manage.py` para usar `settings_prod` por defecto

**Archivo:** `manage.py`

**Cambio:**
```python
# ❌ ANTES
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")

# ✅ DESPUÉS
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings_prod")
```

**Razón:** Permite override para desarrollo local con variable de entorno, pero usa producción por defecto.

---

### 3. Cargar `.env.prod` explícitamente en `settings_prod.py`

**Archivo:** `gestion_taller/settings/prod.py`

**Agregado al inicio:**
```python
from pathlib import Path
from dotenv import load_dotenv

# Cargar .env.prod explícitamente para producción
_env_prod_path = Path(__file__).resolve().parent.parent.parent / ".env.prod"
if _env_prod_path.exists():
    load_dotenv(_env_prod_path, override=True)

from .base import *
```

**Razón:** Garantiza que las variables de entorno de producción se carguen correctamente, incluso si `.env` también existe.

---

## 🚀 DEPLOYMENT EN PRODUCCIÓN

### Pasos para aplicar el fix:

```bash
# 1. Hacer pull de los cambios
cd /srv/egarage
git pull origin main

# 2. Reload daemon (si modificaste gunicorn.service)
sudo systemctl daemon-reload

# 3. Restart Gunicorn
sudo systemctl restart gunicorn

# 4. Verificar logs
sudo journalctl -u gunicorn -f
```

---

## 🧪 VALIDACIÓN POST-FIX

### Verificar que se usa configuración de producción:

```bash
# En el servidor
python manage.py shell -c "from django.conf import settings; print(f'DEBUG={settings.DEBUG}'); print(f'SECRET_KEY={settings.SECRET_KEY[:10]}...')"

# Resultado esperado:
# DEBUG=False
# SECRET_KEY=<tu_clave_real>...
```

### Verificar que NO aparece el warning de desarrollo:

```bash
# Ejecutar cualquier comando de manage.py
python manage.py check

# NO debe aparecer:
# WARNING:root:Modo de desarrollo activado...
```

---

## 📊 IMPACTO DEL FIX

### Antes (Configuración Híbrida)

```
┌─────────────┐
│  systemd    │ → settings_prod ✅
└─────────────┘
       ↓
┌─────────────┐
│  gunicorn   │ → puede no inyectar variable a tiempo
└─────────────┘
       ↓
┌─────────────┐
│   wsgi.py   │ → setdefault(..., "settings") ❌
└─────────────┘
       ↓
    HÍBRIDO (DEV + PROD) 💥
```

### Después (Configuración Consistente)

```
┌─────────────┐
│  systemd    │ → settings_prod ✅
└─────────────┘
       ↓
┌─────────────┐
│  gunicorn   │
└─────────────┘
       ↓
┌─────────────┐
│   wsgi.py   │ → FUERZA settings_prod ✅
└─────────────┘
       ↓
    PRODUCCIÓN 100% ✅
```

---

## 🎯 RESULTADOS ESPERADOS

Después de aplicar este fix:

| Aspecto | Estado |
|---------|--------|
| `SECRET_KEY` | ✅ Consistente en todos los requests |
| Sesiones | ✅ Válidas y persistentes |
| Login | ✅ Estable y predecible |
| Password Reset | ✅ Funciona correctamente |
| Emails | ✅ Templates correctos |
| Comportamiento | ✅ 100% producción, sin híbridos |
| Logs | ✅ Sin warnings de desarrollo |

---

## 🔍 DESARROLLO LOCAL

### Para desarrollo local, puedes usar:

**Opción A:** Variable de entorno
```bash
export DJANGO_SETTINGS_MODULE=gestion_taller.settings
python manage.py runserver
```

**Opción B:** Crear archivo `.env` local
```bash
# .env (local)
DJANGO_SETTINGS_MODULE=gestion_taller.settings
DEBUG=True
```

**Opción C:** Usar `settings/__init__.py` con lógica condicional
```python
# gestion_taller/settings/__init__.py
import os

if os.getenv("EGARAGE_ENV") == "prod":
    from .prod import *
else:
    from .dev import *
```

---

## 📝 LECCIONES APRENDIDAS

### 1. Nunca confiar en `setdefault()` para producción

`setdefault()` es útil para desarrollo, pero en producción puede causar inconsistencias si el orden de carga de variables no está garantizado.

### 2. Siempre validar configuración en runtime

Agregar checks de validación en `settings_prod.py`:

```python
# Al final de settings_prod.py
if DEBUG:
    raise RuntimeError("DEBUG=True en settings_prod.py - esto NO debería pasar")
```

### 3. Cargar `.env.prod` explícitamente

No asumir que `load_dotenv()` en `base.py` cargará el archivo correcto. Ser explícito en `settings_prod.py`.

---

## 🔗 ARCHIVOS MODIFICADOS

1. `gestion_taller/wsgi.py` - Forzar `settings_prod`
2. `manage.py` - Usar `settings_prod` por defecto
3. `gestion_taller/settings/prod.py` - Cargar `.env.prod` explícitamente

---

## ⚠️ NOTAS IMPORTANTES

- Este fix es **crítico** y debe aplicarse en producción lo antes posible
- Después del fix, reiniciar Gunicorn es **obligatorio**
- Validar que el sistema funcione correctamente después del restart
- Monitorear logs por 24-48 horas para detectar cualquier regresión

---

**Fecha del fix:** 2026-03-29  
**Severidad:** CRÍTICA  
**Estado:** ✅ Implementado y documentado  
**Requiere restart:** Sí (Gunicorn)
