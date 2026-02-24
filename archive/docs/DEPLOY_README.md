# 🚀 Guía de Deploy - Registro Simplificado

## 📦 Resumen

**Total de archivos a actualizar:** 12
- **1 archivo NUEVO** (crear)
- **11 archivos MODIFICADOS** (reemplazar)

---

## ⚡ Deploy Rápido (Automático)

### Windows (PowerShell)

```powershell
# Desde la raíz del proyecto
.\scripts\deploy_signup_simplificado.ps1 -Server "tu_usuario@tu_servidor.com" -ServerPath "/ruta/a/egarage"
```

### Linux/Mac (Bash)

```bash
# Desde la raíz del proyecto
chmod +x scripts/deploy_signup_simplificado.sh
./scripts/deploy_signup_simplificado.sh usuario@servidor.com /ruta/a/egarage
```

---

## 📋 Lista Completa de Archivos

### 1️⃣ Archivo NUEVO
```
taller/views_extra/signup_redirects.py
```

### 2️⃣ Archivos MODIFICADOS
```
taller/forms/custom_signup.py
templates/account/signup.html
taller/views_extra/custom_signup.py
gestion_taller/urls.py
gestion_taller/settings.py
taller/urls_extra/brasil.py
taller/urls_extra/colombia.py
taller/urls_extra/ecuador.py
taller/urls_extra/mexico.py
taller/urls_extra/peru.py
taller/urls_extra/venezuela.py
```

---

## 🔧 Scripts Disponibles

### 1. `scripts/deploy_signup_simplificado.ps1`
**Descripción:** Script PowerShell para Windows que copia todos los archivos al servidor
**Uso:**
```powershell
.\scripts\deploy_signup_simplificado.ps1 -Server "admin@servidor.com" -ServerPath "/var/www/egarage"
```

### 2. `scripts/deploy_signup_simplificado.sh`
**Descripción:** Script Bash para Linux/Mac que copia todos los archivos al servidor
**Uso:**
```bash
chmod +x scripts/deploy_signup_simplificado.sh
./scripts/deploy_signup_simplificado.sh admin@servidor.com /var/www/egarage
```

### 3. `scripts/verificar_deploy.sh`
**Descripción:** Script de verificación post-deploy (ejecutar en el servidor)
**Uso:**
```bash
# En el servidor
cd /ruta/a/egarage
chmod +x scripts/verificar_deploy.sh
./scripts/verificar_deploy.sh
```

### 4. `scripts/deploy_instrucciones.md`
**Descripción:** Documentación completa de deploy manual y troubleshooting

---

## ✅ Checklist Post-Deploy

Después de ejecutar el deploy, verificar:

- [ ] Todos los archivos fueron copiados correctamente
- [ ] `python manage.py check` pasa sin errores
- [ ] Aplicación Django reiniciada
- [ ] Test: `/accounts/signup/?from=cl` retorna 200 OK
- [ ] Test: `/cl/accounts/signup/` redirige a `/accounts/signup/?from=cl` (302)
- [ ] Test: Registro completo funciona (muestra "¡Ya casi llegamos!")
- [ ] Test: Teléfono se normaliza correctamente (+56912345678)

---

## 🐛 Troubleshooting Rápido

### Error: "ModuleNotFoundError: No module named 'taller.views_extra.signup_redirects'"
```bash
# En servidor: Verificar que el archivo existe
ls -la taller/views_extra/signup_redirects.py
```

### Error: "ACCOUNT_USERNAME_REQUIRED is not defined"
```bash
# En servidor: Verificar settings.py
grep "ACCOUNT_USERNAME_REQUIRED" gestion_taller/settings.py
# Si no está, agregar: ACCOUNT_USERNAME_REQUIRED = False
```

### Error: El registro falla con "teléfono es obligatorio"
```bash
# Verificar que telefono tiene required=True
grep "required=True" taller/forms/custom_signup.py | grep telefono
```

---

## 📞 Comandos Útiles Post-Deploy

### Verificar logs de Django:
```bash
tail -f /var/log/gunicorn/error.log
# O
tail -f logs/django.log
```

### Test rápido de importación:
```bash
python manage.py shell
>>> from taller.views_extra.signup_redirects import signup_redirect
>>> from taller.forms.custom_signup import CustomSignupForm
>>> exit()
```

### Test de URLs:
```bash
python manage.py shell -c "from django.test import Client; c=Client(); print('CL:', c.get('/cl/accounts/signup/', follow=False).status_code); print('US:', c.get('/us/accounts/signup/', follow=False).status_code)"
```

---

## 🎯 Resultado Esperado

Después del deploy exitoso:

✅ Registro simplificado: Solo 4 campos (email, telefono, password1, password2)  
✅ Teléfono normalizado: E.164 para WhatsApp (+56912345678)  
✅ País automático: Detectado desde `?from=xx`  
✅ URLs por país redirigen correctamente  
✅ Registro exitoso muestra "¡Ya casi llegamos!"

---

## 📚 Documentación Adicional

- Ver `scripts/deploy_instrucciones.md` para instrucciones detalladas
- Ver `ARCHIVOS_SUBIR_SERVIDOR_SIGNUP_SIMPLIFICADO.md` para lista detallada de archivos
