# 🚀 ACTUALIZACIÓN DEL SERVIDOR - FIX SERVICIOS

**Fecha:** 2025-12-23  
**Cambios:** Corrección de búsqueda de servicios y migraciones

---

## 📋 ARCHIVOS MODIFICADOS

### 1. Backend - Lógica de Búsqueda
- **`taller/servicios/views.py`**
  - Corregida lógica de búsqueda para respetar TenantScoped
  - Agregado filtro por país
  - Búsqueda ampliada en `nombre` y `names__label`

### 2. API - Corrección de Imports
- **`taller/servicios/api_servicios_moderno.py`**
  - Eliminadas referencias a `ServicioBase` (modelo inexistente)
  - Eliminado `servicio_base` del `select_related`
  - Eliminado `servicio_base_id` de la respuesta JSON

### 3. Comandos de Management (NUEVOS)
- **`taller/management/commands/clonar_servicios_base.py`** ⭐ NUEVO
  - Comando para clonar servicios de una empresa maestra a otras
  - Uso: `python manage.py clonar_servicios_base --empresa-maestra 1`

- **`taller/management/commands/listar_empresas_servicios.py`** ⭐ NUEVO
  - Comando para listar empresas y cantidad de servicios
  - Uso: `python manage.py listar_empresas_servicios`

### 4. Comandos Existentes - Correcciones
- **`taller/management/commands/cargar_servicios_produccion.py`**
  - Corregidas referencias `empresa.nombre` → `empresa.nombre_taller`
  - Eliminados emojis que causaban errores de encoding en Windows

### 5. Migraciones (NUEVA)
- **`taller/migrations/0054_remove_serviciobase_subcategoria_and_more.py`** ⭐ NUEVA
  - Elimina campo `activo` de `CategoriaServicio`, `Servicio`, `SubcategoriaServicio`
  - Elimina modelo `ServicioBase` y campos obsoletos
  - **IMPORTANTE:** Esta migración debe aplicarse en el servidor

### 6. Script Standalone (OPCIONAL)
- **`reparar_servicios.py`** ⭐ NUEVO
  - Script independiente para clonar servicios (alternativa al comando Django)

---

## 📤 PASOS PARA ACTUALIZAR EL SERVIDOR

### Opción A: Usando el Script PowerShell (Recomendado)

```powershell
# Desde la raíz del proyecto
cd E:\projecto\e_garage
.\actualizar_app_completa_servidor.ps1
```

Este script:
1. ✅ Subirá todos los archivos modificados
2. ✅ Ejecutará las migraciones
3. ✅ Actualizará archivos estáticos
4. ✅ Reiniciará la aplicación

---

### Opción B: Manual (Paso a Paso)

#### 1. Subir Archivos Modificados

**Archivos a subir:**
```
taller/servicios/views.py
taller/servicios/api_servicios_moderno.py
taller/management/commands/clonar_servicios_base.py
taller/management/commands/listar_empresas_servicios.py
taller/management/commands/cargar_servicios_produccion.py
taller/migrations/0054_remove_serviciobase_subcategoria_and_more.py
```

**Método de subida:**
- **FileZilla/WinSCP:** Subir archivos manteniendo la estructura de carpetas
- **SCP desde PowerShell:**
  ```powershell
  scp taller/servicios/views.py usuario@servidor:/ruta/a/egarage/taller/servicios/
  scp taller/servicios/api_servicios_moderno.py usuario@servidor:/ruta/a/egarage/taller/servicios/
  scp taller/management/commands/clonar_servicios_base.py usuario@servidor:/ruta/a/egarage/taller/management/commands/
  scp taller/management/commands/listar_empresas_servicios.py usuario@servidor:/ruta/a/egarage/taller/management/commands/
  scp taller/management/commands/cargar_servicios_produccion.py usuario@servidor:/ruta/a/egarage/taller/management/commands/
  scp taller/migrations/0054_remove_serviciobase_subcategoria_and_more.py usuario@servidor:/ruta/a/egarage/taller/migrations/
  ```

#### 2. En el Servidor (SSH/Console)

```bash
# 1. Ir al directorio del proyecto
cd /ruta/a/egarage

# 2. Activar virtual environment (si aplica)
source venv/bin/activate  # o el nombre de tu venv

# 3. Crear backup de la base de datos (IMPORTANTE)
mkdir -p backups/deployments
cp db.sqlite3 backups/deployments/db_backup_$(date +%Y%m%d_%H%M%S).sqlite3

# 4. Aplicar migraciones
python manage.py migrate taller

# 5. Verificar que la migración 0054 se aplicó
python manage.py showmigrations taller | grep 0054

# 6. Actualizar archivos estáticos (si hay cambios)
python manage.py collectstatic --noinput

# 7. Reiniciar aplicación (depende de tu servidor)
# PythonAnywhere: tocar el archivo WSGI
touch /var/www/www_tudominio_com_wsgi.py

# O si usas systemd/supervisor:
sudo systemctl restart egarage
# o
supervisorctl restart egarage
```

#### 3. Verificar en el Servidor

```bash
# Verificar que los comandos nuevos funcionan
python manage.py listar_empresas_servicios

# Verificar migraciones aplicadas
python manage.py showmigrations taller | tail -5
```

---

## ⚠️ IMPORTANTE: Migración 0054

Esta migración **elimina campos** de la base de datos:
- Campo `activo` de `CategoriaServicio`
- Campo `activo` de `Servicio`
- Campo `activo` de `SubcategoriaServicio`
- Modelo `ServicioBase` completo
- Varios campos obsoletos

**Esto es seguro** porque:
- ✅ Los campos ya no se usan en el código
- ✅ No hay datos críticos en esos campos
- ✅ La migración fue probada localmente

**Antes de aplicar:**
1. ✅ Crear backup de la base de datos
2. ✅ Verificar que no hay dependencias en esos campos
3. ✅ Aplicar en horario de bajo tráfico (si aplica)

---

## 🧪 VERIFICACIÓN POST-DEPLOYMENT

### 1. Verificar Búsqueda de Servicios
- Ir a: `/us/documentos/form/`
- Intentar buscar un servicio (ej: "oil")
- Debe encontrar servicios en tiempo real

### 2. Verificar Comandos Nuevos
```bash
# Listar empresas y servicios
python manage.py listar_empresas_servicios

# Clonar servicios (si es necesario)
python manage.py clonar_servicios_base --dry-run
```

### 3. Verificar Migraciones
```bash
python manage.py showmigrations taller | grep 0054
# Debe mostrar: [X] 0054_remove_serviciobase_subcategoria_and_more
```

---

## 🆘 ROLLBACK (Si algo falla)

Si necesitas revertir los cambios:

```bash
# 1. Restaurar backup de base de datos
cp backups/deployments/db_backup_YYYYMMDD_HHMMSS.sqlite3 db.sqlite3

# 2. Revertir migración (si se aplicó)
python manage.py migrate taller 0053

# 3. Restaurar archivos anteriores desde backup
```

---

## ✅ CHECKLIST FINAL

- [ ] Archivos subidos al servidor
- [ ] Backup de base de datos creado
- [ ] Migración 0054 aplicada
- [ ] Archivos estáticos actualizados
- [ ] Aplicación reiniciada
- [ ] Búsqueda de servicios funciona
- [ ] Comandos nuevos funcionan
- [ ] Sin errores en logs

---

## 📞 SOPORTE

Si encuentras problemas:
1. Revisar logs del servidor
2. Verificar que todas las migraciones se aplicaron
3. Verificar permisos de archivos
4. Revisar que el virtual environment esté activo

---

**Última actualización:** 2025-12-23

