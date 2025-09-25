# Sistema de Idiomas por País - eGarage

## Objetivo
- **USA**: Idioma predeterminado inglés, con opción a español por usuario
- **Chile**: Solo español (forzado)

## Implementación

### 1. Configuración en settings.py
```python
LANGUAGE_CODE = "es"  # fallback global
LANGUAGES = [("en", "English"), ("es", "Español")]
USE_I18N = True
```

### 2. Middleware LanguagePolicyMiddleware
**Ubicación**: `taller/middleware/lang_policy.py`

**Reglas**:
- Si `empresa.pais == CL`: forzar 'es'
- Si `empresa.pais == US`: usar sesión/usuario si está permitido (en/es), si no usar default 'en'
- Cualquier otro país: caer a LANGUAGE_CODE global

**Orden en MIDDLEWARE**:
```python
MIDDLEWARE = [
    # ... otros middlewares ...
    "taller.middleware.empresa_middleware.EmpresaMiddleware",
    "taller.middleware.simple_country_redirect.SimpleCountryRedirectMiddleware",
    "taller.middleware.lang_policy.LanguagePolicyMiddleware",  # ← NUEVO
    # ... resto de middlewares ...
]
```

### 3. Vista de Cambio de Idioma
**Ubicación**: `taller/views_extra/lang_switch.py`
**URL**: `/lang/set/`
**Restricciones**: Solo para usuarios de USA

### 4. Templates de Switcher
**Bootstrap**: `templates/taller/includes/lang_switcher.html`
**Tailwind**: `templates/taller/includes/lang_switcher_tailwind.html`

**Uso en templates**:
```html
{% include 'taller/includes/lang_switcher_tailwind.html' %}
```

### 5. Lógica de Detección

#### Chile (CL):
- `request.LANGUAGE_CODE` siempre será `'es'`
- No se muestra switcher de idioma
- Usuario no puede cambiar idioma

#### USA (US):
- `request.LANGUAGE_CODE` por defecto es `'en'`
- Usuario puede cambiar a `'es'` mediante switcher
- Preferencia se guarda en `session['preferred_lang']`
- Si no hay preferencia, usa perfil de usuario (opcional)

### 6. Variables de Entorno

#### Desarrollo:
```bash
# No se requieren variables adicionales
# El sistema funciona con configuración por defecto
```

#### Producción:
```bash
# Configurar idiomas por país si es necesario
# El sistema detecta automáticamente el país de la empresa
```

### 7. Pruebas Manuales

#### Usuario Chile:
1. Visitar `/cl/es/...`
2. Verificar que `request.LANGUAGE_CODE == 'es'`
3. Verificar que NO se muestra switcher de idioma

#### Usuario USA nuevo:
1. Entrar a `/us/...`
2. Verificar que `request.LANGUAGE_CODE == 'en'`
3. Verificar que SÍ se muestra switcher de idioma

#### USA cambia idioma:
1. Cambiar a español con el switcher
2. Recargar página
3. Verificar que `request.LANGUAGE_CODE == 'es'`

#### Seguridad:
1. Usuario USA intenta forzar idioma no permitido por POST
2. Verificar que se rechaza y se mantiene idioma anterior

### 8. Estructura de Archivos

```
taller/
├── middleware/
│   └── lang_policy.py              # Middleware principal
├── views_extra/
│   └── lang_switch.py              # Vista de cambio de idioma
templates/
└── taller/
    └── includes/
        ├── lang_switcher.html      # Switcher Bootstrap
        └── lang_switcher_tailwind.html  # Switcher Tailwind
```

### 9. Notas Técnicas

- **No se usa `Accept-Language`** del navegador para evitar sorpresas
- **Sesión persistente**: La preferencia se mantiene entre sesiones
- **Seguridad**: Solo usuarios de USA pueden cambiar idioma
- **Fallback robusto**: Si no se puede determinar idioma, usa español
- **Compatibilidad**: Mantiene configuración existente de Django i18n

### 10. Troubleshooting

#### Problema: Idioma no cambia
- Verificar que el usuario es de USA (`request.empresa.pais == "US"`)
- Verificar que el middleware está en el orden correcto
- Verificar que no hay cache de sesión

#### Problema: Switcher no aparece
- Verificar que `request.empresa.pais == "US"`
- Verificar que el template incluye el switcher
- Verificar que el usuario está autenticado

#### Problema: Error 500 en cambio de idioma
- Verificar que `EMAIL_PASSWORD` está configurado (para mensajes)
- Verificar que CSRF está habilitado
- Verificar logs de Django para más detalles
