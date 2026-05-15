# 📦 Archivos a Subir al Servidor - Registro Simplificado

## 📅 Fecha: 2025-01-XX
## 🎯 Objetivo: Simplificar registro - Solo campos obligatorios (email, telefono, password)

---

## ✅ NUEVO ARCHIVO (CREAR EN SERVIDOR)

### 1. `taller/views_extra/signup_redirects.py`
**Acción:** CREAR archivo nuevo
**Descripción:** Función universal de redirect para signup por país

---

## 🔄 ARCHIVOS MODIFICADOS (REEMPLAZAR EN SERVIDOR)

### 2. `taller/forms/custom_signup.py`
**Acción:** REEMPLAZAR
**Cambios:**
- Teléfono ahora es OBLIGATORIO (required=True)
- Normalización E.164 para WhatsApp
- Campos opcionales: first_name, last_name, nombre_taller, country
- Método clean_username() para generar username automáticamente
- Método clean() para garantizar país válido siempre

### 3. `templates/account/signup.html`
**Acción:** REEMPLAZAR
**Cambios:**
- Eliminados campos: first_name, last_name, nombre_taller, selector de país
- Solo muestra: email, telefono, password1, password2
- Campo oculto country con valor desde ?from=xx

### 4. `taller/views_extra/custom_signup.py`
**Acción:** REEMPLAZAR
**Cambios:**
- get_form_kwargs() actualizado para detectar país desde ?from=xx
- form_valid() actualizado para detectar país correctamente

### 5. `gestion_taller/urls.py`
**Acción:** REEMPLAZAR
**Cambios:**
- Import de signup_redirect agregado
- Rutas /cl/accounts/signup/ y /us/accounts/signup/ actualizadas para usar redirect

### 6. `gestion_taller/settings.py`
**Acción:** REEMPLAZAR (o agregar línea si no existe)
**Cambios:**
- Agregado: `ACCOUNT_USERNAME_REQUIRED = False`
- Ubicación: Después de `ACCOUNT_AUTHENTICATION_METHOD = "email"`

### 7. `taller/urls_extra/brasil.py`
**Acción:** REEMPLAZAR
**Cambios:**
- Import de signup_redirect agregado
- Ruta accounts/signup/ ahora usa redirect en lugar de TemplateView

### 8. `taller/urls_extra/colombia.py`
**Acción:** REEMPLAZAR
**Cambios:**
- Import de signup_redirect agregado
- Ruta accounts/signup/ ahora usa redirect en lugar de TemplateView

### 9. `taller/urls_extra/ecuador.py`
**Acción:** REEMPLAZAR
**Cambios:**
- Import de signup_redirect agregado
- Ruta accounts/signup/ ahora usa redirect en lugar de TemplateView

### 10. `taller/urls_extra/mexico.py`
**Acción:** REEMPLAZAR
**Cambios:**
- Import de signup_redirect agregado
- Ruta accounts/signup/ ahora usa redirect en lugar de TemplateView

### 11. `taller/urls_extra/peru.py`
**Acción:** REEMPLAZAR
**Cambios:**
- Import de signup_redirect agregado
- Ruta accounts/signup/ ahora usa redirect en lugar de TemplateView

### 12. `taller/urls_extra/venezuela.py`
**Acción:** REEMPLAZAR
**Cambios:**
- Import de signup_redirect agregado
- Ruta accounts/signup/ ahora usa redirect en lugar de TemplateView

---

## 📋 RESUMEN

### Total de archivos:
- **1 archivo NUEVO** (crear en servidor)
- **11 archivos MODIFICADOS** (reemplazar en servidor)

### Comandos rápidos (desde PC):

```bash
# NUEVO archivo (crear directorio si no existe)
scp taller/views_extra/signup_redirects.py usuario@servidor:/ruta/a/egarage/taller/views_extra/

# ARCHIVOS MODIFICADOS
scp taller/forms/custom_signup.py usuario@servidor:/ruta/a/egarage/taller/forms/
scp templates/account/signup.html usuario@servidor:/ruta/a/egarage/templates/account/
scp taller/views_extra/custom_signup.py usuario@servidor:/ruta/a/egarage/taller/views_extra/
scp gestion_taller/urls.py usuario@servidor:/ruta/a/egarage/gestion_taller/
scp gestion_taller/settings.py usuario@servidor:/ruta/a/egarage/gestion_taller/

# URLs por país
scp taller/urls_extra/brasil.py usuario@servidor:/ruta/a/egarage/taller/urls_extra/
scp taller/urls_extra/colombia.py usuario@servidor:/ruta/a/egarage/taller/urls_extra/
scp taller/urls_extra/ecuador.py usuario@servidor:/ruta/a/egarage/taller/urls_extra/
scp taller/urls_extra/mexico.py usuario@servidor:/ruta/a/egarage/taller/urls_extra/
scp taller/urls_extra/peru.py usuario@servidor:/ruta/a/egarage/taller/urls_extra/
scp taller/urls_extra/venezuela.py usuario@servidor:/ruta/a/egarage/taller/urls_extra/
```

---

## ⚠️ IMPORTANTE: Después de subir

1. **Verificar permisos:**
   ```bash
   chmod 644 taller/views_extra/signup_redirects.py
   chmod 644 taller/forms/custom_signup.py
   chmod 644 templates/account/signup.html
   # ... etc para todos los archivos
   ```

2. **Restart de la aplicación Django:**
   ```bash
   # Si usas gunicorn/uwsgi
   sudo systemctl restart gunicorn
   # O
   sudo systemctl restart uwsgi
   
   # Si usas PythonAnywhere
   touch /var/www/egarage_pythonanywhere_com_wsgi.py
   
   # Si usas otro método, usar el comando correspondiente
   ```

3. **Verificar que funciona:**
   - Test: `/accounts/signup/?from=cl`
   - Verificar redirect: `/cl/accounts/signup/` → `/accounts/signup/?from=cl`
   - Verificar registro exitoso: debe mostrar "¡Ya casi llegamos!"

---

## ✅ Checklist Pre-Deploy

- [ ] Todos los archivos copiados correctamente
- [ ] Permisos verificados
- [ ] Settings.py actualizado (ACCOUNT_USERNAME_REQUIRED = False)
- [ ] Aplicación reiniciada
- [ ] Test de registro funcionando
- [ ] Verificar que teléfono se normaliza correctamente (+56912345678)
- [ ] Verificar que país se detecta desde ?from=xx

---

## 🐛 Si algo falla

1. Revisar logs de Django:
   ```bash
   tail -f /var/log/gunicorn/error.log
   # O
   tail -f /ruta/a/logs/django.log
   ```

2. Verificar que todos los imports están correctos:
   ```bash
   python manage.py check
   ```

3. Verificar sintaxis Python:
   ```bash
   python -m py_compile taller/views_extra/signup_redirects.py
   python -m py_compile taller/forms/custom_signup.py
   ```
