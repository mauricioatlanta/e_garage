# 🚨 Error de Password de Email con Caracteres Especiales

## Problema

Al intentar enviar emails (como reset de contraseña), se produce el error:

```
UnicodeEncodeError: 'ascii' codec can't encode character '\xf1' in position 35: ordinal not in range(128)
```

## Causa

La contraseña de la cuenta de email `subscription@egarage.cl` contiene caracteres especiales (como **ñ**, **á**, **é**, etc.) que no son compatibles con el protocolo SMTP AUTH PLAIN que usa Python's `smtplib`.

El error específico indica que el carácter `\xf1` (la letra **ñ**) en la posición 35 de la contraseña no puede ser codificado en ASCII puro.

## Solución

**Debes cambiar la contraseña de la cuenta de email en cPanel para usar SOLO caracteres ASCII:**

### ✅ Caracteres Permitidos:
- Letras: `a-z`, `A-Z`
- Números: `0-9`
- Símbolos básicos: `!@#$%^&*-_=+()[]{}<>?/\|;:,.'"`

### ❌ Caracteres NO Permitidos:
- Letras con tildes: `á`, `é`, `í`, `ó`, `ú`
- Letra ñ: `ñ`, `Ñ`
- Caracteres especiales UTF-8: `¿`, `¡`, `€`, etc.

## Pasos para Resolver

1. **Acceder a cPanel:**
   - URL: https://srv24.cpanelhost.cl:2083
   - Usuario: tu usuario de cPanel

2. **Ir a "Email Accounts" (Cuentas de Email)**

3. **Encontrar la cuenta:** `subscription@egarage.cl`

4. **Click en "Change Password" (Cambiar Contraseña)**

5. **Generar una nueva contraseña segura SIN caracteres especiales:**
   - Ejemplo válido: `MyStr0ngP@ssw0rd2024!`
   - Ejemplo válido: `eG@rage_Secure_2025`
   - ❌ NO válido: `MiContraseña2024` (tiene ñ)
   - ❌ NO válido: `Contraseña_Ségura` (tiene ñ y é)

6. **Actualizar la variable de entorno en tu servidor:**
   ```bash
   # En tu archivo .env o configuración del servidor
   EMAIL_PASSWORD=TuNuevaContraseñaSinCaracteresEspeciales
   ```

7. **Reiniciar el servidor Django:**
   ```bash
   # Si usas systemctl
   sudo systemctl restart gunicorn

   # O simplemente detener y volver a iniciar el servidor de desarrollo
   python manage.py runserver
   ```

## Workaround Temporal (NO RECOMENDADO)

Si no puedes cambiar el password inmediatamente, puedes desactivar temporalmente el envío de emails:

```python
# En settings.py
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

Esto imprimirá los emails en la consola en lugar de enviarlos.

## Verificación

Después de cambiar el password, prueba el envío de email:

```bash
python manage.py shell
```

```python
from django.core.mail import send_mail

send_mail(
    'Test Email',
    'This is a test message.',
    'subscription@egarage.cl',
    ['tu_email@test.com'],
    fail_silently=False,
)
```

Si no hay errores, el problema está resuelto! ✅

## Prevención Futura

Al crear cuentas de email para aplicaciones Django/Python:
- Siempre usar solo caracteres ASCII en las contraseñas
- Usar un generador de contraseñas que excluya caracteres especiales
- Documentar este requisito en la documentación del proyecto

---

**Nota:** Este es un problema conocido de Python's `smtplib` que no soporta autenticación con passwords UTF-8. No es un bug de Django ni de eGarage, sino una limitación del protocolo SMTP AUTH PLAIN.



