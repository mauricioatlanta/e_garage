# Archivos para Actualizar en el Servidor - Fix Migraciones y URLs

## 📋 Resumen de Cambios

Esta actualización corrige:
1. Error de migración `numero_documento_db` (KeyError)
2. Error de migración `LogAuditoria` (tabla no existe)
3. Error de columna `terms_and_conditions` faltante
4. URLs faltantes en namespace `chile`

---

## 📁 Archivos a Subir al Servidor

### 1. Migraciones Modificadas

```
taller/migrations/0014_remove_duplicate_fields.py
```
**Cambio:** Comentada la eliminación de `numero_documento_db` que nunca existió.

---

### 2. Migraciones Modificadas

```
taller/migrations/0055_remove_logauditoria_empresa_and_more.py
```
**Cambio:** Usa `SeparateDatabaseAndState` para LogAuditoria e is_trial (tablas que no existen en BD).

---

### 3. Migración Nueva (IMPORTANTE)

```
taller/migrations/0056_add_company_settings_fields.py
```
**Cambio:** Nueva migración que agrega los campos faltantes de CompanySettings:
- `terms_and_conditions`
- `apply_tax_by_default`
- `separate_by_technician`
- `tax_rate`

---

### 4. URLs Modificadas

```
taller/urls_extra/chile.py
```
**Cambio:** Agregadas las URLs:
- `configuracion/` → `configuracion_empresa`
- `configuracion/tecnicos/` → `configuracion_tecnicos`

---

## 🚀 Pasos para Actualizar el Servidor

### Paso 1: Hacer Backup de la Base de Datos

```bash
# En el servidor, hacer backup antes de aplicar migraciones
python manage.py dumpdata > backup_antes_migraciones_$(date +%Y%m%d_%H%M%S).json
```

---

### Paso 2: Subir los Archivos

Subir los siguientes archivos al servidor:

```bash
# Opción 1: Usando git (recomendado)
git add taller/migrations/0014_remove_duplicate_fields.py
git add taller/migrations/0055_remove_logauditoria_empresa_and_more.py
git add taller/migrations/0056_add_company_settings_fields.py
git add taller/urls_extra/chile.py
git commit -m "Fix: Corregir migraciones y agregar URLs faltantes en Chile"
git push origin main  # o la rama que uses

# En el servidor:
git pull origin main
```

**O manualmente usando FTP/SCP:**

1. `taller/migrations/0014_remove_duplicate_fields.py`
2. `taller/migrations/0055_remove_logauditoria_empresa_and_more.py`
3. `taller/migrations/0056_add_company_settings_fields.py` ⚠️ **NUEVO**
4. `taller/urls_extra/chile.py`

---

### Paso 3: Verificar Estado de Migraciones

```bash
# Ver qué migraciones están aplicadas
python manage.py showmigrations taller | grep -E "0014|0055|0056"
```

**Estado esperado:**
- `[X] 0014_remove_duplicate_fields` - Ya aplicada
- `[X] 0055_remove_logauditoria_empresa_and_more` - Aplicada con --fake
- `[ ] 0056_add_company_settings_fields` - Pendiente

---

### Paso 4: Aplicar la Nueva Migración

```bash
# Aplicar la migración 0056 que agrega los campos faltantes
python manage.py migrate taller 0056
```

**Salida esperada:**
```
Operations to perform:
  Target specific migration: 0056_add_company_settings_fields, from taller
Running migrations:
  Applying taller.0056_add_company_settings_fields... OK
```

---

### Paso 5: Verificar que Todo Funciona

```bash
# Verificar que todas las migraciones están aplicadas
python manage.py showmigrations taller | tail -5

# Debería mostrar:
# [X] 0054_merge_20260101_2354
# [X] 0055_remove_logauditoria_empresa_and_more
# [X] 0056_add_company_settings_fields
```

---

### Paso 6: Reiniciar el Servidor

```bash
# Si usas Gunicorn
touch /ruta/a/tu/proyecto/gestion_taller/wsgi.py

# O reiniciar el servicio
sudo systemctl restart gunicorn
# O el método que uses en tu servidor
```

---

### Paso 7: Probar las URLs

Verificar que funcionan:
- ✅ `/cl/es/configuracion/` - Debe cargar sin errores
- ✅ `/cl/es/configuracion/tecnicos/` - Debe funcionar el enlace

---

## ⚠️ Notas Importantes

1. **Migración 0055:** Ya está aplicada con `--fake` en el servidor, solo necesitas el archivo actualizado para mantener consistencia.

2. **Migración 0056:** Es nueva y DEBE aplicarse en el servidor para agregar las columnas faltantes.

3. **URLs:** Los cambios en `chile.py` son inmediatos, no requieren migraciones.

4. **Backup:** Siempre hacer backup antes de aplicar migraciones en producción.

---

## 🔍 Verificación Post-Deploy

Después de actualizar, verificar:

1. ✅ La página `/cl/es/configuracion/` carga sin errores
2. ✅ No hay errores de `NoReverseMatch` para `configuracion_tecnicos`
3. ✅ No hay errores de columna faltante `terms_and_conditions`
4. ✅ Las migraciones están todas aplicadas

---

## 📝 Comandos de Diagnóstico

Si algo falla, usar estos comandos:

```bash
# Ver estado de migraciones
python manage.py showmigrations taller

# Ver SQL que se ejecutará
python manage.py sqlmigrate taller 0056

# Verificar que las columnas existen
python manage.py dbshell
# Luego en SQLite:
.schema taller_companysettings
# Debe mostrar: terms_and_conditions, apply_tax_by_default, etc.
```

---

## ✅ Checklist Final

- [ ] Backup de base de datos realizado
- [ ] Archivos subidos al servidor
- [ ] Migración 0056 aplicada exitosamente
- [ ] Servidor reiniciado
- [ ] URLs funcionando correctamente
- [ ] Sin errores en logs

---

**Fecha de creación:** 2026-01-02  
**Última actualización:** 2026-01-02
