# 📧 Instrucciones para Configurar Gmail en el Servidor (PythonAnywhere)

## ✅ Prueba Local Exitosa

Las pruebas locales fueron exitosas:
- ✅ Correo de prueba enviado correctamente
- ✅ Registro de usuario funciona
- ✅ Correo de bienvenida se envía correctamente

---

## 🔧 Configuración en PythonAnywhere

### Paso 1: Configurar Variables de Entorno

1. **Ir al panel de PythonAnywhere**
   - Accede a: https://www.pythonanywhere.com
   - Ve a la pestaña **Web**

2. **Agregar Variables de Entorno**
   - Busca la sección **"Environment variables"**
   - Haz clic en **"Add a new environment variable"**
   - Agrega cada una de estas variables:

```
EMAIL_HOST = smtp.gmail.com
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_USE_SSL = False
EMAIL_HOST_USER = mauricioatlanta@gmail.com
EMAIL_PASSWORD = aohulwlfwzfvqajz
DEFAULT_FROM_EMAIL = eGarage <mauricioatlanta@gmail.com>
```

**⚠️ IMPORTANTE**: 
- `EMAIL_PASSWORD` debe ser la App Password: `aohulwlfwzfvqajz` (sin espacios)
- NO uses tu contraseña normal de Gmail

### Paso 2: Subir Archivos Modificados

Sube estos archivos al servidor:

1. **`gestion_taller/settings/base.py`**
   - Este archivo ahora soporta Gmail vía variables de entorno
   - Ruta en servidor: `/home/tu_usuario/e_garage/gestion_taller/settings/base.py`

2. **Archivos de prueba (opcionales, para testing)**
   - `test_email_gmail.py`
   - `test_email_registro.py`

### Paso 3: Reiniciar la Aplicación

1. En el panel de PythonAnywhere, ve a la pestaña **Web**
2. Haz clic en el botón **"Reload"** o **"Restart"** de tu aplicación web
3. Espera unos segundos a que se reinicie

---

## 🧪 Probar en el Servidor

### Opción A: Usar Django Shell

1. En PythonAnywhere, ve a la pestaña **Consoles**
2. Abre una consola de Bash
3. Ejecuta:

```bash
cd ~/e_garage  # Ajusta la ruta según tu configuración
python3.10 manage.py shell
```

4. En el shell de Django:

```python
from django.core.mail import send_mail
from django.conf import settings

# Verificar configuración
print(f"EMAIL_HOST: {settings.EMAIL_HOST}")
print(f"EMAIL_PORT: {settings.EMAIL_PORT}")
print(f"EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
print(f"EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")

# Enviar correo de prueba
send_mail(
    'Test Gmail - eGarage',
    'Este es un correo de prueba desde el servidor.',
    settings.DEFAULT_FROM_EMAIL,
    ['mauricioatlanta@gmail.com'],
    fail_silently=False,
)
```

### Opción B: Usar el Script de Prueba

Si subiste los scripts de prueba:

```bash
cd ~/e_garage
python3.10 test_email_gmail.py 1
```

---

## ✅ Verificación

Después de configurar:

1. **Verifica que las variables de entorno estén configuradas**
   - En Django shell: `from django.conf import settings; print(settings.EMAIL_HOST)`
   - Debe mostrar: `smtp.gmail.com`

2. **Envía un correo de prueba**
   - Usa el método de prueba arriba
   - Revisa tu bandeja de entrada en `mauricioatlanta@gmail.com`

3. **Prueba el registro de un nuevo usuario**
   - Ve a la página de registro de tu aplicación
   - Registra un nuevo usuario
   - Verifica que reciba el correo de bienvenida

---

## 🔍 Solución de Problemas

### Error: "Username and Password not accepted"

**Causa**: La App Password no está configurada correctamente.

**Solución**:
1. Verifica que `EMAIL_PASSWORD` tenga el valor: `aohulwlfwzfvqajz` (sin espacios)
2. Verifica que las variables de entorno estén guardadas
3. Reinicia la aplicación web

### Error: Variables de entorno no se leen

**Causa**: Django no está leyendo las variables de entorno.

**Solución**:
1. Verifica que las variables estén en la sección "Environment variables" del panel Web
2. Reinicia la aplicación web después de agregar las variables
3. Verifica en Django shell: `import os; print(os.environ.get('EMAIL_HOST'))`

### El correo no llega

**Causa**: Puede estar en spam o hay un problema de configuración.

**Solución**:
1. Revisa la carpeta de spam en Gmail
2. Verifica los logs del servidor en PythonAnywhere
3. Prueba enviar un correo simple desde Django shell

---

## 📋 Checklist Final

- [ ] Variables de entorno configuradas en PythonAnywhere
- [ ] Archivo `gestion_taller/settings/base.py` subido al servidor
- [ ] Aplicación web reiniciada
- [ ] Prueba de correo exitosa desde Django shell
- [ ] Correo de bienvenida llega al registrar nuevo usuario
- [ ] Correos no van a spam (verificar configuración SPF/DKIM si es necesario)

---

## 📝 Notas Importantes

1. **Seguridad de la App Password**:
   - La App Password `aohulwlfwzfvqajz` es específica para esta aplicación
   - No la compartas ni la expongas en código público
   - Si la comprometes, puedes revocarla y generar una nueva en https://myaccount.google.com/apppasswords

2. **Límites de Gmail**:
   - Gmail tiene límites de envío: 500 correos/día para cuentas gratuitas
   - Para producción con muchos correos, considera usar un servicio profesional (SendGrid, Mailgun, etc.)

3. **Alternativa Futura**:
   - Una vez que funcione con Gmail, puedes considerar:
     - Configurar el servidor SMTP original (`srv24.cpanelhost.cl`) con la contraseña correcta
     - Usar un servicio de email transaccional profesional

---

## 🎉 ¡Listo!

Si todo está configurado correctamente, los nuevos usuarios que se registren recibirán automáticamente el correo de bienvenida con las instrucciones para iniciar sesión.

**Última actualización**: Diciembre 2024
