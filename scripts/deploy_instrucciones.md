# 📋 Instrucciones de Deploy - Registro Simplificado

## 🚀 Opción 1: Deploy Automatizado (Recomendado)

### Windows (PowerShell)

```powershell
# 1. Editar los parámetros en el script si es necesario
#    Abrir: scripts/deploy_signup_simplificado.ps1
#    Cambiar: -Server "tu_usuario@tu_servidor.com" -ServerPath "/ruta/a/egarage"

# 2. Ejecutar desde la raíz del proyecto
.\scripts\deploy_signup_simplificado.ps1 -Server "usuario@servidor.com" -ServerPath "/ruta/a/egarage"

# O con parámetros personalizados:
.\scripts\deploy_signup_simplificado.ps1 -Server "admin@egarage.com" -ServerPath "/var/www/egarage"
```

### Linux/Mac (Bash)

```bash
# 1. Dar permisos de ejecución
chmod +x scripts/deploy_signup_simplificado.sh

# 2. Editar el script si es necesario (cambiar variables SERVER y SERVER_PATH)
#    O pasar parámetros al ejecutar

# 3. Ejecutar desde la raíz del proyecto
./scripts/deploy_signup_simplificado.sh usuario@servidor.com /ruta/a/egarage
```

---

## 📤 Opción 2: Deploy Manual (Paso a Paso)

### Paso 1: Copiar Archivos al Servidor

#### Desde Windows (PowerShell):

```powershell
# Definir variables
$Server = "usuario@servidor.com"
$ServerPath = "/ruta/a/egarage"

# Nuevo archivo (crear)
scp taller/views_extra/signup_redirects.py ${Server}:${ServerPath}/taller/views_extra/

# Archivos modificados
scp taller/forms/custom_signup.py ${Server}:${ServerPath}/taller/forms/
scp templates/account/signup.html ${Server}:${ServerPath}/templates/account/
scp taller/views_extra/custom_signup.py ${Server}:${ServerPath}/taller/views_extra/
scp gestion_taller/urls.py ${Server}:${ServerPath}/gestion_taller/
scp gestion_taller/settings.py ${Server}:${ServerPath}/gestion_taller/

# URLs por país
scp taller/urls_extra/brasil.py ${Server}:${ServerPath}/taller/urls_extra/
scp taller/urls_extra/colombia.py ${Server}:${ServerPath}/taller/urls_extra/
scp taller/urls_extra/ecuador.py ${Server}:${ServerPath}/taller/urls_extra/
scp taller/urls_extra/mexico.py ${Server}:${ServerPath}/taller/urls_extra/
scp taller/urls_extra/peru.py ${Server}:${ServerPath}/taller/urls_extra/
scp taller/urls_extra/venezuela.py ${Server}:${ServerPath}/taller/urls_extra/
```

#### Desde Linux/Mac:

```bash
# Definir variables
SERVER="usuario@servidor.com"
SERVER_PATH="/ruta/a/egarage"

# Nuevo archivo
scp taller/views_extra/signup_redirects.py ${SERVER}:${SERVER_PATH}/taller/views_extra/

# Archivos modificados
scp taller/forms/custom_signup.py ${SERVER}:${SERVER_PATH}/taller/forms/
scp templates/account/signup.html ${SERVER}:${SERVER_PATH}/templates/account/
scp taller/views_extra/custom_signup.py ${SERVER}:${SERVER_PATH}/taller/views_extra/
scp gestion_taller/urls.py ${SERVER}:${SERVER_PATH}/gestion_taller/
scp gestion_taller/settings.py ${SERVER}:${SERVER_PATH}/gestion_taller/

# URLs por país
scp taller/urls_extra/brasil.py ${SERVER}:${SERVER_PATH}/taller/urls_extra/
scp taller/urls_extra/colombia.py ${SERVER}:${SERVER_PATH}/taller/urls_extra/
scp taller/urls_extra/ecuador.py ${SERVER}:${SERVER_PATH}/taller/urls_extra/
scp taller/urls_extra/mexico.py ${SERVER}:${SERVER_PATH}/taller/urls_extra/
scp taller/urls_extra/peru.py ${SERVER}:${SERVER_PATH}/taller/urls_extra/
scp taller/urls_extra/venezuela.py ${SERVER}:${SERVER_PATH}/taller/urls_extra/
```

---

### Paso 2: En el Servidor - Verificar y Configurar

```bash
# SSH al servidor
ssh usuario@servidor.com
cd /ruta/a/egarage

# Ejecutar script de verificación
chmod +x scripts/verificar_deploy.sh
./scripts/verificar_deploy.sh

# O verificar manualmente:
python manage.py check
python -c "from taller.views_extra.signup_redirects import signup_redirect"
python -c "from taller.forms.custom_signup import CustomSignupForm"
```

---

### Paso 3: Reiniciar Aplicación

#### Si usas Gunicorn:

```bash
sudo systemctl restart gunicorn
sudo systemctl status gunicorn
```

#### Si usas uWSGI:

```bash
sudo systemctl restart uwsgi
sudo systemctl status uwsgi
```

#### Si usas DigitalOcean:

```bash
# Tocar el archivo WSGI para forzar reload
touch /var/www/egarage_digitalocean_com_wsgi.py
```

#### Si usas otros métodos:

```bash
# Supervisor
sudo supervisorctl restart egarage

# Docker
docker-compose restart web

# O el método que uses normalmente
```

---

## ✅ Verificación Post-Deploy

### Test 1: Verificar que el registro funciona

```bash
# En el servidor o desde tu PC
curl -I https://tudominio.com/accounts/signup/?from=cl
# Debe retornar: HTTP/1.1 200 OK
```

### Test 2: Verificar redirects por país

```bash
# Chile
curl -I https://tudominio.com/cl/accounts/signup/
# Debe retornar: HTTP/1.1 302 Found
# Location: /accounts/signup/?from=cl

# USA
curl -I https://tudominio.com/us/accounts/signup/
# Debe retornar: HTTP/1.1 302 Found
# Location: /accounts/signup/?from=us

# Brasil
curl -I https://tudominio.com/br/es/accounts/signup/
# Debe retornar: HTTP/1.1 302 Found
# Location: /accounts/signup/?from=br
```

### Test 3: Registro completo (desde navegador)

1. Ir a: `https://tudominio.com/accounts/signup/?from=cl`
2. Completar solo: email, telefono, password1, password2
3. Enviar formulario
4. Debe mostrar: "¡Ya casi llegamos!"
5. Verificar en BD que teléfono sea: `+56912345678`

---

## 🐛 Troubleshooting

### Error: "No module named 'taller.views_extra.signup_redirects'"

**Solución:** Verificar que el archivo existe y tiene permisos correctos:
```bash
ls -la taller/views_extra/signup_redirects.py
chmod 644 taller/views_extra/signup_redirects.py
```

### Error: "ACCOUNT_USERNAME_REQUIRED is not defined"

**Solución:** Verificar que está en settings.py:
```bash
grep "ACCOUNT_USERNAME_REQUIRED" gestion_taller/settings.py
# Si no está, agregarlo después de ACCOUNT_AUTHENTICATION_METHOD
```

### Error: "Form validation failed"

**Solución:** Verificar que telefono es obligatorio:
```bash
grep "required=True" taller/forms/custom_signup.py | grep telefono
```

### El registro no muestra "¡Ya casi llegamos!"

**Solución:** Verificar que CustomSignupView renderiza registro_exitoso.html:
```bash
grep "registro_exitoso.html" taller/views_extra/custom_signup.py
```

---

## 📝 Checklist Final

- [ ] Todos los archivos copiados correctamente
- [ ] Permisos verificados (644 para archivos .py y .html)
- [ ] Django check pasa sin errores
- [ ] Aplicación reiniciada
- [ ] Test de registro funciona (200 OK)
- [ ] Redirects funcionan (302 Found)
- [ ] Teléfono se normaliza correctamente (+56912345678)
- [ ] Registro exitoso muestra "¡Ya casi llegamos!"

---

## 📞 Si necesitas ayuda

Revisar logs de Django:
```bash
tail -f /var/log/gunicorn/error.log
# O
tail -f logs/django.log
```

Verificar errores en consola:
```bash
python manage.py shell
>>> from taller.views_extra.signup_redirects import signup_redirect
>>> from taller.forms.custom_signup import CustomSignupForm
```
