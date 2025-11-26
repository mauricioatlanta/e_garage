# 🚀 Instrucciones para Actualizar el Servidor

## 📋 Resumen Rápido

Este documento contiene las instrucciones paso a paso para actualizar el servidor eGarage con los últimos cambios.

---

## ⚡ Método Rápido (Recomendado)

### Opción 1: Usar el script automático

```bash
# 1. Desde tu máquina local
./ACTUALIZAR_SERVIDOR.sh

# El script generará:
# - actualizar_en_servidor.sh (script para ejecutar en el servidor)
# - COMANDOS_COPIAR_ARCHIVOS.txt (comandos para copiar archivos específicos)
```

### Opción 2: Actualización manual completa

**1. Conectarse al servidor:**
```bash
ssh atlantareciclajes@ssh.pythonanywhere.com
```

**2. Ir al directorio del proyecto:**
```bash
cd /home/atlantareciclajes/apps/egarage/current
```

**3. Activar virtualenv:**
```bash
source ~/.virtualenvs/venv_egarage310/bin/activate
```

**4. Actualizar código:**
```bash
git pull origin main
```

**5. Instalar dependencias (si hay nuevas):**
```bash
pip install -r requirements.txt
```

**6. Ejecutar migraciones:**
```bash
python manage.py migrate
```

**7. Recopilar archivos estáticos:**
```bash
python manage.py collectstatic --noinput
```

**8. Arreglar usuario testuser_usa:**
```bash
python manage.py fix_testuser_usa
```

**9. Reiniciar aplicación:**
```bash
touch /var/www/atlantareciclajes_pythonanywhere_com_wsgi.py
```

**10. Verificar logs:**
```bash
tail -f ~/logs/user/error.log
```

---

## 📝 Cambios Incluidos en Esta Actualización

### 1. **Fix usuario testuser_usa**
- ✅ Comando Django: `python manage.py fix_testuser_usa`
- ✅ Crea/actualiza usuario con credenciales correctas
- ✅ Configura empresa y suscripción automáticamente

**Archivos:**
- `taller/management/commands/fix_testuser_usa.py`

### 2. **Multi-tenant Hardening**
- ✅ Managers personalizados para aislamiento de empresa
- ✅ Mixins para vistas que verifican pertenencia
- ✅ Middleware mejorado de aislamiento

**Archivos:**
- `taller/managers/empresa_aware.py`
- `taller/mixins/empresa_required.py`
- `taller/middleware/tenant_isolation.py`
- `taller/utils/tenant_audit.py`
- `taller/managers/__init__.py`

### 3. **Fix formulario de vehículos**
- ✅ Corrección del campo marca para USA
- ✅ Fallback directo desde la vista si el formulario no tiene choices
- ✅ Mejoras en la detección de país

**Archivos:**
- `taller/vehiculos/forms.py`
- `taller/vehiculos/views_fbv.py`
- `templates/taller/us/en/vehiculos/crear_vehiculo.html`

### 4. **Documentación**
- ✅ Guías de multi-tenant hardening
- ✅ Documentación Alpine.js + HTMX
- ✅ Ejemplos de implementación

**Archivos:**
- `docs/BLINDAJE_MULTITENANT_HARDENING.md`
- `docs/MIGRACION_ALPINE_HTMX.md`
- `docs/GUIA_IMPLEMENTACION_ALPINE_HTMX.md`
- `EJEMPLO_ACTUALIZAR_MODELO_TENANT.md`

---

## 🔍 Verificación Post-Actualización

### 1. Verificar que el servidor funciona:
```bash
curl -I https://www.egarage.cl/
```

### 2. Verificar login con testuser_usa:
- URL: `https://www.egarage.cl/us/accounts/login/`
- Usuario: `testuser_usa`
- Contraseña: `TestUSA2025!`

### 3. Verificar formulario de vehículos:
- URL: `https://www.egarage.cl/us/vehiculos/crear/`
- Verificar que aparecen las marcas (29 marcas)

### 4. Verificar logs:
```bash
# En el servidor
tail -f ~/logs/user/error.log | grep -i error
```

---

## 🛠️ Solución de Problemas

### Error: "No module named 'taller.management.commands.fix_testuser_usa'"

**Solución:**
```bash
# Verificar que el archivo existe
ls -la taller/management/commands/fix_testuser_usa.py

# Si no existe, copiar manualmente:
# Desde tu máquina local:
scp taller/management/commands/fix_testuser_usa.py \
    atlantareciclajes@ssh.pythonanywhere.com:/home/atlantareciclajes/apps/egarage/current/taller/management/commands/
```

### Error: "ModuleNotFoundError: No module named 'taller.managers'"

**Solución:**
```bash
# Crear directorio managers si no existe
mkdir -p taller/managers

# Copiar archivos
scp taller/managers/*.py \
    atlantareciclajes@ssh.pythonanywhere.com:/home/atlantareciclajes/apps/egarage/current/taller/managers/
```

### Error: "No se cargan los archivos estáticos"

**Solución:**
```bash
# Recopilar estáticos de nuevo
python manage.py collectstatic --noinput --clear

# Verificar configuración en dashboard de PythonAnywhere:
# Web → Static files
```

### Error: "Usuario testuser_usa no puede entrar"

**Solución:**
```bash
# Ejecutar comando de fix
python manage.py fix_testuser_usa

# O ejecutar manualmente en shell:
python manage.py shell
# Luego copiar y pegar el código de verificar_testuser_usa_directo.py
```

---

## 📊 Checklist de Actualización

Antes de marcar como completado, verificar:

- [ ] Código actualizado desde Git
- [ ] Migraciones ejecutadas sin errores
- [ ] Archivos estáticos recopilados
- [ ] Usuario testuser_usa funciona correctamente
- [ ] Formulario de vehículos muestra marcas para USA
- [ ] No hay errores en logs
- [ ] Sitio web funciona correctamente
- [ ] Login funciona para ambos países (CL y US)

---

## 🔄 Rollback (Si algo sale mal)

Si necesitas revertir la actualización:

```bash
# 1. Volver a commit anterior
cd /home/atlantareciclajes/apps/egarage/current
git log --oneline -10  # Ver últimos commits
git reset --hard <commit-anterior>

# 2. Recopilar estáticos
python manage.py collectstatic --noinput

# 3. Reiniciar aplicación
touch /var/www/atlantareciclajes_pythonanywhere_com_wsgi.py

# 4. Verificar
curl -I https://www.egarage.cl/
```

---

## 📞 Soporte

Si encuentras problemas:

1. **Revisar logs:**
   ```bash
   tail -f ~/logs/user/error.log
   ```

2. **Verificar configuración:**
   ```bash
   python manage.py check
   ```

3. **Verificar base de datos:**
   ```bash
   python manage.py dbshell
   ```

---

**Fecha:** Noviembre 2025  
**Última actualización:** 19 de Noviembre 2025  
**Versión:** 2.0
