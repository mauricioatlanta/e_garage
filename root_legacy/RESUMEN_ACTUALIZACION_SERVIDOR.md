# 📋 RESUMEN DE ACTUALIZACIÓN DEL SERVIDOR

## 🚀 Cambios Incluidos en Esta Actualización

### 1. **Fix Usuario testuser_usa** ⭐ CRÍTICO
- ✅ Comando Django: `python manage.py fix_testuser_usa`
- ✅ Crea/actualiza usuario automáticamente
- ✅ Configura empresa y suscripción

**Archivos nuevos:**
- `taller/management/commands/fix_testuser_usa.py`

**Archivos relacionados:**
- `verificar_testuser_usa_directo.py` (para ejecutar manualmente si es necesario)
- `COMANDO_VERIFICAR_TESTUSER_USA.txt` (instrucciones)

---

### 2. **Multi-Tenant Hardening** 🔒 SEGURIDAD
- ✅ Managers personalizados para aislamiento de empresa
- ✅ Mixins para vistas que verifican pertenencia
- ✅ Middleware mejorado de aislamiento
- ✅ Utilidades de auditoría

**Archivos nuevos:**
- `taller/managers/empresa_aware.py`
- `taller/managers/__init__.py`
- `taller/mixins/empresa_required.py`
- `taller/middleware/tenant_isolation.py`
- `taller/utils/tenant_audit.py`
- `docs/BLINDAJE_MULTITENANT_HARDENING.md`
- `EJEMPLO_ACTUALIZAR_MODELO_TENANT.md`

---

### 3. **Fix Formulario de Vehículos USA** 🚗
- ✅ Corrección del campo marca para USA
- ✅ Fallback directo desde la vista si formulario no tiene choices
- ✅ Mejoras en detección de país
- ✅ Debug mejorado en template

**Archivos modificados:**
- `taller/vehiculos/forms.py`
- `taller/vehiculos/views_fbv.py`
- `templates/taller/us/en/vehiculos/crear_vehiculo.html`

---

### 4. **Documentación Alpine.js + HTMX** 📚
- ✅ Guías de migración completa
- ✅ Ejemplos de código
- ✅ Templates de ejemplo

**Archivos nuevos:**
- `docs/MIGRACION_ALPINE_HTMX.md`
- `docs/GUIA_IMPLEMENTACION_ALPINE_HTMX.md`
- `templates/base_alpine_htmx.html`
- `ejemplos_alpine/documento_form_example.html`
- `ejemplos_alpine/ejemplo_htmx_agregar_fila.html`

---

### 5. **Credenciales de Prueba** 🔑
- ✅ Documento con todas las credenciales organizadas por país

**Archivos nuevos:**
- `CREDENCIALES_PRUEBA_SERVIDOR.md`

---

## 🚀 Pasos para Actualizar el Servidor

### Opción 1: Script Automático (Recomendado)

**1. Desde tu máquina local:**
```bash
# Ejecutar script que genera el script para el servidor
./ACTUALIZAR_SERVIDOR.sh
```

**2. Copiar script al servidor:**
```bash
scp actualizar_en_servidor.sh atlantareciclajes@ssh.pythonanywhere.com:~/
```

**3. Ejecutar en el servidor:**
```bash
ssh atlantareciclajes@ssh.pythonanywhere.com
bash ~/actualizar_en_servidor.sh
```

---

### Opción 2: Actualización Manual (Paso a Paso)

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

**5. Instalar dependencias:**
```bash
pip install -r requirements.txt --upgrade
```

**6. Ejecutar migraciones:**
```bash
python manage.py migrate
```

**7. Recopilar estáticos:**
```bash
python manage.py collectstatic --noinput
```

**8. Arreglar testuser_usa:**
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

### Opción 3: Copiar Archivos Específicos

Si solo necesitas actualizar archivos específicos:

```bash
# Desde tu máquina local, copiar archivos críticos:

# 1. Comando fix_testuser_usa
scp taller/management/commands/fix_testuser_usa.py \
    atlantareciclajes@ssh.pythonanywhere.com:/home/atlantareciclajes/apps/egarage/current/taller/management/commands/

# 2. Multi-tenant hardening
scp -r taller/managers \
    atlantareciclajes@ssh.pythonanywhere.com:/home/atlantareciclajes/apps/egarage/current/taller/

scp -r taller/mixins \
    atlantareciclajes@ssh.pythonanywhere.com:/home/atlantareciclajes/apps/egarage/current/taller/

scp taller/middleware/tenant_isolation.py \
    atlantareciclajes@ssh.pythonanywhere.com:/home/atlantareciclajes/apps/egarage/current/taller/middleware/

scp taller/utils/tenant_audit.py \
    atlantareciclajes@ssh.pythonanywhere.com:/home/atlantareciclajes/apps/egarage/current/taller/utils/

# 3. Forms y vistas actualizados
scp taller/vehiculos/forms.py \
    atlantareciclajes@ssh.pythonanywhere.com:/home/atlantareciclajes/apps/egarage/current/taller/vehiculos/

scp taller/vehiculos/views_fbv.py \
    atlantareciclajes@ssh.pythonanywhere.com:/home/atlantareciclajes/apps/egarage/current/taller/vehiculos/

# 4. Templates actualizados
scp templates/taller/us/en/vehiculos/crear_vehiculo.html \
    atlantareciclajes@ssh.pythonanywhere.com:/home/atlantareciclajes/apps/egarage/current/templates/taller/us/en/vehiculos/

# Luego en el servidor:
cd /home/atlantareciclajes/apps/egarage/current
source ~/.virtualenvs/venv_egarage310/bin/activate
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py fix_testuser_usa
touch /var/www/atlantareciclajes_pythonanywhere_com_wsgi.py
```

---

## ✅ Verificación Post-Actualización

### 1. Verificar que el servidor funciona:
```bash
curl -I https://www.egarage.cl/
```

### 2. Verificar login con testuser_usa:
- URL: `https://www.egarage.cl/us/accounts/login/`
- Usuario: `testuser_usa`
- Contraseña: `TestUSA2025!`
- Debe entrar correctamente ✅

### 3. Verificar formulario de vehículos:
- URL: `https://www.egarage.cl/us/vehiculos/crear/`
- Verificar que aparecen las marcas (29 marcas) ✅
- No debe mostrar solo "Select a brand" ✅

### 4. Verificar logs:
```bash
tail -f ~/logs/user/error.log | grep -i error
```

---

## 📋 Checklist de Actualización

Antes de marcar como completado:

- [ ] Código actualizado desde Git (`git pull`)
- [ ] Dependencias instaladas/actualizadas (`pip install -r requirements.txt`)
- [ ] Migraciones ejecutadas (`python manage.py migrate`)
- [ ] Archivos estáticos recopilados (`python manage.py collectstatic`)
- [ ] Usuario testuser_usa actualizado (`python manage.py fix_testuser_usa`)
- [ ] Aplicación reiniciada (`touch WSGI file`)
- [ ] Login testuser_usa funciona correctamente
- [ ] Formulario de vehículos muestra marcas para USA
- [ ] No hay errores en logs
- [ ] Sitio web funciona correctamente

---

## 🆘 Solución de Problemas

### Error: "No module named 'taller.management.commands.fix_testuser_usa'"

**Solución:**
```bash
# Verificar que el archivo existe
ls -la taller/management/commands/fix_testuser_usa.py

# Si no existe, crear directorio y copiar archivo
mkdir -p taller/management/commands
# Copiar archivo desde local (ver Opción 3 arriba)
```

### Error: "No module named 'taller.managers'"

**Solución:**
```bash
# Crear directorio
mkdir -p taller/managers

# Copiar archivos (ver Opción 3 arriba)
```

### Error: Usuario testuser_usa sigue sin funcionar

**Solución:**
Ejecutar manualmente en shell de Django:
```bash
python manage.py shell
# Luego copiar y pegar el código de verificar_testuser_usa_directo.py
```

---

## 📊 Archivos Críticos a Actualizar

### Prioridad ALTA:
1. `taller/management/commands/fix_testuser_usa.py` - Fix usuario
2. `taller/vehiculos/forms.py` - Fix formulario
3. `taller/vehiculos/views_fbv.py` - Fix vista
4. `templates/taller/us/en/vehiculos/crear_vehiculo.html` - Fix template

### Prioridad MEDIA:
5. `taller/managers/empresa_aware.py` - Multi-tenant
6. `taller/mixins/empresa_required.py` - Multi-tenant
7. `taller/middleware/tenant_isolation.py` - Multi-tenant

### Prioridad BAJA (Documentación):
8. `docs/BLINDAJE_MULTITENANT_HARDENING.md`
9. `docs/MIGRACION_ALPINE_HTMX.md`
10. `CREDENCIALES_PRUEBA_SERVIDOR.md`

---

**Fecha:** Noviembre 2025  
**Versión:** 2.1  
**Estado:** ✅ Listo para actualización

