# 📧 Configuración de Gmail para eGarage

## ⚠️ Importante: Requisitos de Gmail

Gmail tiene medidas de seguridad que requieren configuración adicional:

1. **Si tienes 2FA (Autenticación de dos factores) habilitado** (recomendado):
   - Necesitas crear una **"App Password"** (Contraseña de aplicación)
   - NO uses tu contraseña normal de Gmail

2. **Si NO tienes 2FA**:
   - Necesitas habilitar "Acceso de aplicaciones menos seguras" (no recomendado por Google)

---

## 🔐 Opción 1: Usar App Password (Recomendado)

### Paso 1: Habilitar 2FA en tu cuenta de Gmail

1. Ve a: https://myaccount.google.com/security
2. En "Iniciar sesión en Google", haz clic en "Verificación en dos pasos"
3. Sigue las instrucciones para habilitar 2FA

### Paso 2: Crear App Password

1. Ve a: https://myaccount.google.com/apppasswords
2. Selecciona "Correo" como aplicación
3. Selecciona "Otro (nombre personalizado)" como dispositivo
4. Escribe: "eGarage Django"
5. Haz clic en "Generar"
6. **Copia la contraseña de 16 caracteres** (sin espacios)
   - Ejemplo: `abcd efgh ijkl mnop` → usa `abcdefghijklmnop`

### Paso 3: Configurar en Django

Usa la **App Password** (no tu contraseña normal) en la configuración:

```python
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_USE_SSL = False
EMAIL_HOST_USER = 'mauricioatlanta@gmail.com'
EMAIL_HOST_PASSWORD = 'abcdefghijklmnop'  # ← App Password de 16 caracteres
DEFAULT_FROM_EMAIL = 'eGarage <mauricioatlanta@gmail.com>'
```

---

## 🔓 Opción 2: Acceso de aplicaciones menos seguras (No recomendado)

**⚠️ ADVERTENCIA**: Google desaconseja esta opción. Solo úsala si no puedes usar App Passwords.

1. Ve a: https://myaccount.google.com/lesssecureapps
2. Habilita "Permitir aplicaciones menos seguras"
3. Usa tu contraseña normal de Gmail

---

## 📝 Configuración para PythonAnywhere

### Variables de Entorno en PythonAnywhere

En el panel de PythonAnywhere, ve a **Web** → **Environment variables** y agrega:

```
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
EMAIL_HOST_USER=mauricioatlanta@gmail.com
EMAIL_PASSWORD=tu-app-password-aqui
DEFAULT_FROM_EMAIL=eGarage <mauricioatlanta@gmail.com>
```

### O editar directamente en settings.py

Si prefieres editar directamente, busca el archivo de configuración de producción y actualiza:

```python
# Email backend - Gmail
EMAIL_BACKEND = "taller.backends.egarage_email.EgarageEmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_USE_SSL = False
EMAIL_HOST_USER = "mauricioatlanta@gmail.com"
EMAIL_HOST_PASSWORD = "tu-app-password-aqui"  # ← App Password, NO contraseña normal
DEFAULT_FROM_EMAIL = "eGarage <mauricioatlanta@gmail.com>"
```

---

## 🧪 Probar la Configuración

### Opción A: Usar el script de prueba

```bash
python test_email_gmail.py 1
```

### Opción B: Usar Django shell

```bash
python manage.py shell
```

```python
from django.core.mail import send_mail
from django.conf import settings

# Verificar configuración
print(f"EMAIL_HOST: {settings.EMAIL_HOST}")
print(f"EMAIL_PORT: {settings.EMAIL_PORT}")
print(f"EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")

# Enviar correo de prueba
send_mail(
    'Test Gmail - eGarage',
    'Este es un correo de prueba.',
    settings.DEFAULT_FROM_EMAIL,
    ['mauricioatlanta@gmail.com'],
    fail_silently=False,
)
```

---

## ❌ Errores Comunes

### Error: "Username and Password not accepted"

**Causa**: Estás usando la contraseña normal en lugar de App Password.

**Solución**: 
1. Crea una App Password en https://myaccount.google.com/apppasswords
2. Usa esa contraseña de 16 caracteres (sin espacios)

### Error: "Application-specific password required"

**Causa**: Tienes 2FA habilitado pero estás usando contraseña normal.

**Solución**: Usa App Password (ver arriba).

### Error: "Please log in via your web browser"

**Causa**: Gmail bloqueó el acceso por seguridad.

**Solución**: 
1. Ve a: https://accounts.google.com/DisplayUnlockCaptcha
2. Haz clic en "Continuar"
3. Intenta enviar el correo de nuevo

---

## ✅ Checklist

- [ ] 2FA habilitado en Gmail (recomendado)
- [ ] App Password creada en https://myaccount.google.com/apppasswords
- [ ] Variables de entorno configuradas en PythonAnywhere
- [ ] Prueba de envío de correo exitosa
- [ ] Correo de bienvenida llega correctamente

---

## 📚 Referencias

- [App Passwords de Google](https://support.google.com/accounts/answer/185833)
- [Configuración SMTP de Gmail](https://support.google.com/mail/answer/7126229)
- [Solución de problemas de Gmail](https://support.google.com/mail/?p=BadCredentials)

---

**Última actualización**: Diciembre 2024
