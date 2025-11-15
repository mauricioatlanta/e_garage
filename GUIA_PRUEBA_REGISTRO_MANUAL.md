# Guía de Prueba Manual: Sistema de Registro por País

Esta guía te permitirá verificar manualmente que el sistema de registro funciona correctamente según el país.

---

## 🧪 Pruebas Manuales Rápidas

### 1️⃣ Prueba Registro USA (Inglés con opción a Español)

#### 🔗 URL de prueba:
```
http://localhost:8000/accounts/signup/?from=us
```

#### ✅ Lo que DEBES ver:

**Idioma predeterminado: INGLÉS**
- Título: "Create Account" o "Create Your Account"
- Secciones: "Personal Information", "Business Information"
- Campos: "First Name", "Last Name", "Email", "Company Name", "Phone", "Country"
- Planes: "Monthly", "Semi-Annual", "Annual"
- Botón: "CREATE ACCOUNT"
- Link inferior: "Already have an account? Sign in"

#### 🔄 Cambio a español (solo USA):

**Opción 1: Cambiar idioma en la sesión**
1. Iniciar sesión con una cuenta USA
2. Buscar el selector de idioma en el menú
3. Cambiar a "Español"
4. Volver a la página de registro

**Opción 2: URL directa con parámetro de idioma**
```
http://localhost:8000/accounts/signup/?from=us&lang=es
```

**Lo que DEBES ver en español**:
- Título: "Crear Cuenta" o "Crea Tu Cuenta"
- Secciones: "Información Personal", "Información de la Empresa"
- Campos: "Nombre", "Apellido", "Email", "Nombre de Empresa", "Teléfono", "País"
- Planes: "Mensual", "Semestral", "Anual"
- Botón: "CREAR CUENTA"

---

### 2️⃣ Prueba Registro Chile (Solo Español)

#### 🔗 URL de prueba:
```
http://localhost:8000/accounts/signup/?from=cl
```

#### ✅ Lo que DEBES ver:

**Idioma FORZADO: ESPAÑOL**
- Título: "Crear Cuenta" o "Crea Tu Cuenta"
- Secciones: "Información Personal", "Información de la Empresa"
- Todo el contenido en español
- **NO debe haber selector de idioma**
- País pre-seleccionado: Chile (CL)

#### ❌ Lo que NO debe pasar:
- NO debe aparecer contenido en inglés
- NO debe haber opción de cambiar a inglés
- NO debe responder a `?lang=en` (debe ignorarlo)

**Prueba de bloqueo de inglés**:
```
http://localhost:8000/accounts/signup/?from=cl&lang=en
# ← Debe seguir mostrando todo en español
```

---

## 🌐 Prueba de Páginas de Bienvenida

### 🇨🇱 Bienvenida Chile

#### 🔗 URL:
```
http://localhost:8000/bienvenida/cl/
```

#### ✅ Lo que DEBES ver:
- Todo en ESPAÑOL
- `<html lang="es">`
- Contenido específico de Chile
- Terminología chilena (pesos, RUT, etc.)
- Título: "eGarage Chile - La Plataforma N°1 para Digitalizar tu Taller"

---

### 🇺🇸 Bienvenida USA

#### 🔗 URLs:
```
# Inglés (default)
http://localhost:8000/us/

# Español
http://localhost:8000/us/?lang=es
```

#### ✅ Lo que DEBES ver (inglés):
- `<html lang="en">`
- Título: "Welcome to eGarage USA" o similar
- Contenido en inglés
- Terminología USA (ZIP Code, State, USD)

#### ✅ Lo que DEBES ver (español):
- `<html lang="es">`
- Contenido en español
- Mantiene formatos USA pero en español

---

## 🧩 Prueba de Middleware de Idiomas

### Test con Python Shell

```bash
python manage.py shell
```

```python
# Verificar configuración de idiomas por país
from taller.middleware.lang_policy import ALLOWED_BY_COUNTRY, DEFAULT_BY_COUNTRY

print("Idiomas permitidos por país:")
print(ALLOWED_BY_COUNTRY)
# Debe mostrar: {'US': ('en', 'es'), 'CL': ('es',)}

print("\nIdiomas predeterminados:")
print(DEFAULT_BY_COUNTRY)
# Debe mostrar: {'US': 'en', 'CL': 'es'}

# Verificar que el middleware está cargado
from django.conf import settings
middlewares = [m for m in settings.MIDDLEWARE if 'lang' in m.lower() or 'country' in m.lower()]
print("\nMiddlewares de idioma/país:")
for m in middlewares:
    print(f"  - {m}")
```

---

## 📝 Checklist de Verificación

### ✅ Registro USA

- [ ] URL `/accounts/signup/?from=us` funciona
- [ ] Página carga en INGLÉS por defecto
- [ ] Todos los textos en inglés (Create Account, Monthly, etc.)
- [ ] País pre-seleccionado: United States (US)
- [ ] Puede cambiar a español (si hay selector)
- [ ] Template usa i18n (`{% trans %}`)
- [ ] Precios se actualizan al cambiar país

### ✅ Registro Chile

- [ ] URL `/accounts/signup/?from=cl` funciona
- [ ] Página carga en ESPAÑOL forzado
- [ ] Todos los textos en español (Crear Cuenta, Mensual, etc.)
- [ ] País pre-seleccionado: Chile (CL)
- [ ] NO hay selector de idioma
- [ ] `?lang=en` NO cambia el idioma (sigue en español)
- [ ] Precios en pesos chilenos

### ✅ Templates

- [ ] `templates/account/signup.html` existe
- [ ] `templates/auth/signup.html` existe
- [ ] `templates/taller/bienvenida_chile.html` existe (español)
- [ ] `templates/onboarding/bienvenida_usa.html` existe (multiidioma)

### ✅ Middleware

- [ ] `LanguagePolicyMiddleware` está activo
- [ ] USA permite `('en', 'es')`
- [ ] Chile solo permite `('es',)`
- [ ] Default USA es `en`
- [ ] Default Chile es `es`

---

## 🐛 Problemas Comunes y Soluciones

### Problema: Todo aparece en español incluso en USA

**Solución**:
```python
# Verificar configuración en settings
from django.conf import settings
print(settings.LANGUAGE_CODE)  # Debe ser 'es' (fallback global)
print(settings.LANGUAGES)       # Debe incluir ('en', 'English') y ('es', 'Español')
```

**Compilar traducciones**:
```bash
python manage.py compilemessages
```

---

### Problema: Chile muestra inglés

**Solución**:
Verificar que el middleware está aplicando la regla correcta:

```python
# En lang_policy.py línea 62
else:
    lang = DEFAULT_BY_COUNTRY.get(pais, "es")  # Chile debe forzar 'es'
```

---

### Problema: El parámetro `?from=us/cl` no hace nada

**Solución**:
Verificar la vista `signup_complete` en `taller/views_extra/signup_complete.py`:

```python
# Línea 26
from_country = request.GET.get('from', 'us').lower()

# Línea 29-36
if from_country == 'cl':
    activate('es')
    initial_country = 'CL'
else:
    activate('en')
    initial_country = 'US'
```

---

## 🔍 Debugging Tips

### Ver el idioma activo en tiempo real

Agregar en cualquier template:
```django
<p>Idioma actual: {{ LANGUAGE_CODE }}</p>
<p>País: {{ request.country|default:"No detectado" }}</p>
```

### Log del middleware

El middleware `LanguagePolicyMiddleware` tiene prints de debug. Para verlos:

```bash
# En desarrollo con runserver
python manage.py runserver
```

Buscar en la consola:
```
[DEBUG] ===== LanguagePolicyMiddleware =====
[DEBUG] País: US
[DEBUG] Idioma aplicado: en
[DEBUG] URL: /accounts/signup/
[DEBUG] ===========================================
```

---

## 📊 Matriz de Tests

| Escenario | URL | País | Idioma Esperado | Puede Cambiar |
|-----------|-----|------|-----------------|---------------|
| Registro USA default | `/accounts/signup/?from=us` | US | Inglés | Sí (a español) |
| Registro USA español | `/accounts/signup/?from=us&lang=es` | US | Español | Sí (a inglés) |
| Registro Chile | `/accounts/signup/?from=cl` | CL | Español | NO |
| Registro Chile + lang=en | `/accounts/signup/?from=cl&lang=en` | CL | Español | NO (ignora param) |
| Bienvenida Chile | `/bienvenida/cl/` | CL | Español | NO |
| Bienvenida USA | `/us/` | US | Inglés | Sí |

---

## ✅ Resultado Esperado

Si todo funciona correctamente, deberías poder:

1. ✅ Acceder a registro USA en inglés
2. ✅ Cambiar a español en USA (si hay selector)
3. ✅ Acceder a registro Chile solo en español
4. ✅ Chile NO permite cambio a inglés
5. ✅ Templates de bienvenida en idiomas correctos
6. ✅ Middleware aplica reglas correctamente

---

## 📞 Contacto

Si encuentras algún problema:
1. Revisa el archivo `test_registro_idiomas.py`
2. Ejecuta: `python test_registro_idiomas.py`
3. Revisa el reporte: `REPORTE_VERIFICACION_REGISTRO_IDIOMAS.md`

---

> **Última actualización**: 7 de Noviembre, 2025
> **Versión**: 1.0
> **Sistema**: eGarage



