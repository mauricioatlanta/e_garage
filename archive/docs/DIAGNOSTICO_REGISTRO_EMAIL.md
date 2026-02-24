# 🔍 Diagnóstico: Problema de Registro y Envío de Correos

## 📋 Resumen del Problema

El registro de usuarios no se completa correctamente y no se envían correos de confirmación.

---

## 🔎 Análisis de la Configuración Actual

### 1. Configuración de Email en `settings.py`

```python
# Línea 217-233
EMAIL_BACKEND = "taller.backends.egarage_email.EgarageEmailBackend"
EMAIL_HOST = os.getenv("EMAIL_HOST", "srv24.cpanelhost.cl")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "465"))
EMAIL_USE_SSL = env_bool("EMAIL_USE_SSL", True)
EMAIL_USE_TLS = env_bool("EMAIL_USE_TLS", False)
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "subscription@egarage.cl")
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "eGarage <subscription@egarage.cl>")
EMAIL_TIMEOUT = int(os.getenv("EMAIL_TIMEOUT", "30"))

_email_pwd = os.getenv("EMAIL_PASSWORD")
if _email_pwd:
    EMAIL_HOST_PASSWORD = _email_pwd
elif DEBUG:
    EMAIL_HOST_PASSWORD = ""
else:
    raise RuntimeError("EMAIL_PASSWORD must be set in production")
```

**⚠️ Puntos Críticos:**
- Si `EMAIL_PASSWORD` no está configurado en `.env` y `DEBUG=False`, el sistema fallará
- Si `EMAIL_PASSWORD` está vacío en desarrollo, el envío de correos fallará

### 2. Configuración de Allauth

```python
# Línea 69
ACCOUNT_EMAIL_VERIFICATION = os.getenv("ACCOUNT_EMAIL_VERIFICATION", "mandatory")
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_CONFIRM_EMAIL_ON_GET = True
ACCOUNT_EMAIL_CONFIRMATION_EXPIRE_DAYS = 2
```

**⚠️ Punto Crítico:**
- `ACCOUNT_EMAIL_VERIFICATION = "mandatory"` significa que Allauth **requiere** enviar el correo de confirmación
- Si el envío de correo falla, el proceso podría no completarse

### 3. Backend de Email Personalizado

El `EgarageEmailBackend` lanza `EmailBackendError` cuando falla el envío:

```python
# taller/backends/egarage_email.py
class EgarageEmailBackend(DjangoSMTPBackend):
    def send_messages(self, email_messages):
        try:
            result = super().send_messages(email_messages)
            if result == 0:
                logger.warning("[EgarageEmailBackend] send_messages retornó 0")
            return result
        except (smtplib.SMTPAuthenticationError, smtplib.SMTPException, OSError) as e:
            raise EmailBackendError(f"Error SMTP al enviar correo: {e}") from e
```

**⚠️ Problema Potencial:**
- Si Allauth no captura `EmailBackendError`, el proceso de signup podría fallar completamente
- El usuario no se crearía si el email falla

---

## 🐛 Posibles Causas del Problema

### Causa 1: Email Password no Configurado

**Síntoma:** El backend no puede autenticarse con el servidor SMTP

**Solución:**
```bash
# Verificar que EMAIL_PASSWORD esté en .env
EMAIL_PASSWORD=tu-password-aqui
```

### Causa 2: Allauth no Captura EmailBackendError

**Síntoma:** El signup falla cuando intenta enviar el correo

**Ubicación del problema:** `taller/views_extra/custom_signup.py` línea 93

```python
# Guardar el usuario (Allauth maneja el envío de email si ACCOUNT_EMAIL_VERIFICATION = "mandatory")
user = form.save(self.request)  # ⚠️ Si Allauth falla aquí, no hay manejo de error
```

### Causa 3: El EmailAddress no se Crea Correctamente

**Síntoma:** El usuario se crea pero no se envía el correo porque Allauth no crea el `EmailAddress`

**Verificación:**
```python
from allauth.account.models import EmailAddress
from django.contrib.auth import get_user_model

User = get_user_model()
user = User.objects.get(email='usuario@ejemplo.com')
email_address = EmailAddress.objects.filter(user=user).first()
print(f"EmailAddress existe: {email_address}")
print(f"Verified: {email_address.verified if email_address else 'No existe'}")
```

---

## 🔧 Soluciones Recomendadas

### Solución 1: Agregar Manejo de Errores en CustomSignupView

Modificar `taller/views_extra/custom_signup.py` para capturar errores de email:

```python
def form_valid(self, form):
    try:
        # ... código existente ...
        user = form.save(self.request)
        
        # Verificar si se requiere verificación de email
        requires_email_verification = (
            getattr(settings, "ACCOUNT_EMAIL_VERIFICATION", "mandatory") == "mandatory"
        )

        if requires_email_verification:
            # Verificar que EmailAddress se creó y correo se envió
            try:
                from allauth.account.models import EmailAddress
                email_address = EmailAddress.objects.filter(user=user, email=user.email).first()
                
                if not email_address:
                    # Si no existe, crearlo manualmente
                    EmailAddress.objects.create(
                        user=user,
                        email=user.email,
                        verified=False,
                        primary=True
                    )
                    # Intentar enviar correo
                    from allauth.account.utils import send_email_confirmation
                    send_email_confirmation(self.request, user, email=user.email)
            except Exception as e:
                # Log el error pero no bloquear el registro
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error enviando correo de confirmación: {e}", exc_info=True)
                messages.warning(
                    self.request,
                    "Tu cuenta fue creada exitosamente, pero hubo un problema al enviar el correo de confirmación. "
                    "Puedes solicitar un nuevo correo desde la página de inicio de sesión."
                )
            
            # Redirigir a página de registro exitoso
            registro_exitoso_url = CountrySettings.build_url(
                country_code, "auth/registro-exitoso/", request=self.request
            )
            self.request.session["registro_email"] = user.email
            return redirect(registro_exitoso_url)
        else:
            # ... resto del código ...
            
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error en form_valid: {e}", exc_info=True)
        messages.error(
            self.request,
            "Hubo un error al crear tu cuenta. Por favor, intenta nuevamente."
        )
        return self.form_invalid(form)
```

### Solución 2: Verificar Configuración de Email

**✅ Ya existe un comando de diagnóstico creado:**

```bash
# Ejecutar el comando de diagnóstico de email
python manage.py test_email_config

# Especificar un destinatario diferente
python manage.py test_email_config --recipient tu-email@ejemplo.com
```

Este comando:
- Muestra toda la configuración de email actual
- Muestra la configuración de Allauth
- Intenta enviar un correo de prueba
- Muestra errores detallados si algo falla

### Solución 3: Temporalmente Deshabilitar Verificación Obligatoria

Para debugging, cambiar temporalmente en `.env`:

```env
ACCOUNT_EMAIL_VERIFICATION=none
```

Esto permite que el registro se complete sin requerir verificación de email, ayudando a identificar si el problema es específicamente con el envío de correos.

---

## 📝 Checklist de Verificación

- [ ] Verificar que `EMAIL_PASSWORD` esté configurado en `.env`
- [ ] Ejecutar `python manage.py test_email_config` para probar el envío
- [ ] Verificar logs del servidor para errores SMTP
- [ ] Verificar que el usuario se crea en la base de datos
- [ ] Verificar que `EmailAddress` se crea para el usuario
- [ ] Verificar que no haya errores en los logs cuando se intenta registrar

---

## 🔍 Comandos de Diagnóstico

```bash
# 1. Verificar que el usuario se crea
python manage.py shell
>>> from django.contrib.auth import get_user_model
>>> User = get_user_model()
>>> User.objects.filter(email='test@ejemplo.com').exists()

# 2. Verificar EmailAddress
>>> from allauth.account.models import EmailAddress
>>> EmailAddress.objects.filter(email='test@ejemplo.com').first()

# 3. Verificar logs
# Buscar en los logs del servidor por:
# - "[EgarageEmailBackend]"
# - "Error SMTP"
# - "EmailBackendError"
```

---

## 📚 Archivos Clave para Revisar

1. **`gestion_taller/settings.py`** (líneas 217-233) - Configuración de email
2. **`taller/backends/egarage_email.py`** - Backend de email personalizado
3. **`taller/views_extra/custom_signup.py`** - Vista de registro con Allauth
4. **`taller/forms/custom_signup.py`** - Formulario de registro
5. **`.env`** - Variables de entorno (EMAIL_PASSWORD, ACCOUNT_EMAIL_VERIFICATION)

---

## 🚀 Próximos Pasos

1. **Ejecutar diagnóstico:** Crear y ejecutar el comando `test_email_config`
2. **Revisar logs:** Buscar errores relacionados con SMTP o EmailBackendError
3. **Implementar manejo de errores:** Agregar try-except en `CustomSignupView.form_valid()`
4. **Probar registro:** Intentar registrar un usuario y monitorear logs en tiempo real
5. **Verificar base de datos:** Confirmar que el usuario y EmailAddress se crean correctamente

