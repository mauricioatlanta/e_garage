# 📧 Instrucciones Corregidas: Configuración de Correo Electrónico - eGarage

## ⚠️ Problemas Identificados en la Instrucción Original

La instrucción original contenía varios errores que han sido corregidos:

1. ❌ **Servidor SMTP incorrecto**: Mencionaba `smtp.mailtrap.io` (servicio de prueba) en lugar del servidor real
2. ❌ **Puerto y protocolo incorrectos**: Mencionaba puerto 587 con TLS, pero la configuración usa 465 con SSL
3. ❌ **Cuenta de correo incorrecta**: Mencionaba `support@egarage.cl`, pero la configuración actual usa `subscription@egarage.cl`
4. ❌ **Contraseña expuesta**: Incluía una contraseña en texto plano (riesgo de seguridad)
5. ❌ **Información confusa**: Mezclaba referencias a Cloudflare, Gmail y Mailtrap sin claridad
6. ❌ **Comando inexistente**: Mencionaba `python manage.py send_test_email` que no existe en el proyecto

---

## ✅ Instrucciones Corregidas

### 1. Actualizar los Detalles de Correo en settings.py

**⚠️ IMPORTANTE**: El proyecto ya tiene una configuración de correo configurada. Si necesitas cambiarla, edita el archivo `gestion_taller/settings/base.py` o usa variables de entorno.

#### Configuración Actual del Proyecto:

```python
# Email backend - Usando backend personalizado para evitar errores SMTP
EMAIL_BACKEND = "taller.backends.egarage_email.EgarageEmailBackend"
EMAIL_HOST = "srv24.cpanelhost.cl"  # Servidor SMTP de cPanel
EMAIL_PORT = 465  # Puerto SSL (NO 587)
EMAIL_USE_SSL = True  # Usar SSL (NO TLS)
EMAIL_USE_TLS = False  # TLS deshabilitado cuando se usa SSL
EMAIL_HOST_USER = "subscription@egarage.cl"  # Cuenta de correo actual
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_PASSWORD", "laila2013-")  # Desde variable de entorno
DEFAULT_FROM_EMAIL = "eGarage <subscription@egarage.cl>"
```

#### Si Necesitas Cambiar a `support@egarage.cl`:

**Nota**: Según la documentación del proyecto, `support@egarage.cl` NO está configurado actualmente. Si deseas usarlo:

1. **Crear la cuenta de correo** `support@egarage.cl` en tu panel de cPanel
2. **Obtener la contraseña** de esa cuenta
3. **Actualizar la configuración** usando variables de entorno (recomendado):

```bash
# En tu archivo .env o variables de entorno del servidor
EMAIL_HOST_USER=support@egarage.cl
EMAIL_PASSWORD=tu-contraseña-segura-aqui
DEFAULT_FROM_EMAIL=eGarage <support@egarage.cl>
```

4. **O editar directamente** en `gestion_taller/settings/base.py`:

```python
EMAIL_HOST_USER = "support@egarage.cl"
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_PASSWORD", "tu-contraseña-aqui")
DEFAULT_FROM_EMAIL = "eGarage <support@egarage.cl>"
```

**⚠️ SEGURIDAD**: NUNCA expongas contraseñas en el código. Siempre usa variables de entorno.

---

### 2. Configurar Variables de Entorno (Recomendado)

El proyecto está configurado para usar variables de entorno. Crea o actualiza tu archivo `.env`:

```env
# Email Configuration
EMAIL_HOST=srv24.cpanelhost.cl
EMAIL_PORT=465
EMAIL_USE_SSL=True
EMAIL_USE_TLS=False
EMAIL_HOST_USER=support@egarage.cl  # O subscription@egarage.cl
EMAIL_PASSWORD=tu-contraseña-segura-aqui
DEFAULT_FROM_EMAIL=eGarage <support@egarage.cl>
EMAIL_TIMEOUT=30
```

**Importante**: 
- El archivo `.env` debe estar en `.gitignore` (ya está configurado)
- En producción, configura estas variables en el panel de tu servidor/hosting

---

### 3. Configuración de DNS y Registros MX

**Nota sobre Cloudflare**: Si estás usando Cloudflare para el DNS del dominio `egarage.cl`, pero el correo se gestiona a través de cPanel (`srv24.cpanelhost.cl`), necesitas:

1. **Registros MX en Cloudflare**:
   - Entra a tu cuenta de Cloudflare
   - Ve a DNS → Registros
   - Asegúrate de que los registros MX apunten al servidor de correo correcto (probablemente algo como `mail.egarage.cl` o el servidor de cPanel)

2. **Registros SPF** (para evitar spam):
   ```
   v=spf1 include:srv24.cpanelhost.cl ~all
   ```

3. **Registros DKIM** (si están disponibles en cPanel):
   - Configura DKIM desde el panel de cPanel
   - Agrega el registro TXT en Cloudflare

**⚠️ Importante**: Si Cloudflare está en modo "Proxy" (nube naranja) para los registros MX, cámbialo a "DNS only" (nube gris), ya que los registros MX no funcionan con proxy.

---

### 4. Verificar la Configuración

#### Opción A: Usar el Shell de Django (Recomendado)

```bash
python manage.py shell
```

Luego en el shell:

```python
from django.core.mail import send_mail

# Enviar correo de prueba
result = send_mail(
    'Test Email - eGarage',
    'Este es un correo de prueba para verificar la configuración SMTP.',
    'support@egarage.cl',  # O subscription@egarage.cl
    ['tu-email@ejemplo.com'],  # Tu email para recibir la prueba
    fail_silently=False,
)

print(f"Resultado: {result}")  # Debe ser 1 si se envió correctamente
```

#### Opción B: Crear un Comando de Management Personalizado

Si prefieres un comando dedicado, puedes crear `gestion_taller/management/commands/send_test_email.py`:

```python
from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings

class Command(BaseCommand):
    help = 'Envía un correo de prueba para verificar la configuración SMTP'

    def add_arguments(self, parser):
        parser.add_argument(
            '--to',
            type=str,
            required=True,
            help='Email destino para la prueba',
        )

    def handle(self, *args, **options):
        to_email = options['to']
        
        try:
            result = send_mail(
                'Test Email - eGarage',
                'Este es un correo de prueba para verificar la configuración SMTP.',
                settings.DEFAULT_FROM_EMAIL,
                [to_email],
                fail_silently=False,
            )
            
            if result == 1:
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Correo enviado exitosamente a {to_email}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'⚠️ El correo no se pudo enviar (resultado: {result})')
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error al enviar correo: {e}')
            )
```

Luego ejecuta:

```bash
python manage.py send_test_email --to tu-email@ejemplo.com
```

---

### 5. Revisar los Logs de Errores

El proyecto tiene un backend personalizado (`EgarageEmailBackend`) que registra errores. Revisa los logs:

```bash
# Si estás en desarrollo
python manage.py runserver
# Los errores aparecerán en la consola

# Si estás en producción
tail -f /ruta/a/logs/django.log
# O revisa los logs de tu servidor/hosting
```

**Errores comunes y soluciones**:

- **`SMTPAuthenticationError`**: Credenciales incorrectas o cuenta no existe
- **`SMTPConnectError`**: No se puede conectar al servidor SMTP (verifica EMAIL_HOST y EMAIL_PORT)
- **`SMTPServerDisconnected`**: El servidor cerró la conexión (verifica SSL/TLS)
- **Timeout**: Aumenta `EMAIL_TIMEOUT` en settings (por defecto 30 segundos)

---

### 6. Diferencias Clave: SSL vs TLS

**Configuración Actual (SSL en puerto 465)**:
```python
EMAIL_PORT = 465
EMAIL_USE_SSL = True
EMAIL_USE_TLS = False
```

**Si necesitas usar TLS (puerto 587)**:
```python
EMAIL_PORT = 587
EMAIL_USE_SSL = False
EMAIL_USE_TLS = True
```

**⚠️ Importante**: No uses ambos `EMAIL_USE_SSL = True` y `EMAIL_USE_TLS = True` al mismo tiempo. El proyecto actual usa SSL en puerto 465, que es la configuración correcta para cPanel.

---

## 📋 Checklist de Verificación

- [ ] Variables de entorno configuradas (`.env` o en el servidor)
- [ ] `EMAIL_HOST` apunta al servidor correcto (`srv24.cpanelhost.cl`)
- [ ] `EMAIL_PORT` es 465 (SSL) o 587 (TLS) según corresponda
- [ ] `EMAIL_USE_SSL` o `EMAIL_USE_TLS` configurado correctamente (NO ambos)
- [ ] `EMAIL_HOST_USER` tiene el email correcto (`subscription@egarage.cl` o `support@egarage.cl`)
- [ ] `EMAIL_PASSWORD` está configurado (preferiblemente en variables de entorno)
- [ ] `DEFAULT_FROM_EMAIL` tiene el formato correcto
- [ ] Registros MX configurados en DNS (Cloudflare o donde corresponda)
- [ ] Prueba de envío de correo exitosa
- [ ] Logs revisados para verificar que no hay errores

---

## 🔒 Consideraciones de Seguridad

1. **NUNCA** expongas contraseñas en el código fuente
2. **SIEMPRE** usa variables de entorno para credenciales sensibles
3. **Verifica** que el archivo `.env` esté en `.gitignore`
4. **Usa** contraseñas fuertes para las cuentas de correo
5. **Habilita** autenticación de dos factores si está disponible en cPanel

---

## 📚 Referencias del Proyecto

- Configuración actual: `gestion_taller/settings/base.py` (líneas 209-217)
- Backend personalizado: `taller/backends/egarage_email.py`
- Ejemplo de variables: `env.example`
- Documentación adicional: `docs/GUIA_CONFIGURACION_EMAILS.md`

---

## ❓ Preguntas Frecuentes

**P: ¿Puedo usar `support@egarage.cl` en lugar de `subscription@egarage.cl`?**  
R: Sí, pero primero debes crear la cuenta en cPanel y luego actualizar la configuración.

**P: ¿Por qué no funciona con Cloudflare Email Routing?**  
R: Cloudflare Email Routing es un servicio diferente. Si usas cPanel para correo, necesitas configurar los registros MX para apuntar al servidor de cPanel, no a Cloudflare.

**P: ¿El comando `send_test_email` existe?**  
R: No existe por defecto. Usa el shell de Django o crea el comando personalizado como se muestra arriba.

**P: ¿Qué hacer si el correo va a spam?**  
R: Configura registros SPF, DKIM y DMARC en tu DNS. Revisa `docs/GUIA_CONFIGURACION_EMAILS.md` para más detalles.

---

**Última actualización**: Diciembre 2024  
**Versión del proyecto**: Basado en configuración actual de eGarage
