# Instrucciones para Consolidar e Importar Suscriptores

Este proceso te permite extraer TODOS los suscriptores de TODOS los backups y consolidarlos en una sola lista antes de importarlos al nuevo servidor.

## Paso 1: Consolidar suscriptores en PythonAnywhere

**Ejecuta en la consola Bash de PythonAnywhere:**

```bash
cd /home/atlantareciclajes/apps/egarage/current
python tools/consolidar_suscriptores_todos_backups.py > suscripciones_consolidadas.json 2>&1
```

Este script:
- ✅ Revisa TODOS los backups disponibles
- ✅ Extrae todas las suscripciones de cada backup
- ✅ Consolida por email (evita duplicados)
- ✅ Mantiene la suscripción más reciente o activa si hay duplicados
- ✅ Incluye información de empresas relacionadas
- ✅ Genera estadísticas por país

**Verifica el resultado:**
```bash
# Ver el resumen (los mensajes van a stderr, así que se muestran en pantalla)
# El JSON va a stdout y se guarda en el archivo

# Ver tamaño del archivo
ls -lh suscripciones_consolidadas.json

# Ver primeras líneas (resumen)
head -n 50 suscripciones_consolidadas.json

# Ver estadísticas en el JSON
python -c "import json; data=json.load(open('suscripciones_consolidadas.json')); print(f\"Total: {data['total_suscriptores_unicos']}\"); print('Por país:', data['por_pais'])"
```

## Paso 2: Descargar el archivo JSON

Descarga `suscripciones_consolidadas.json` desde PythonAnywhere a tu PC usando:
- La interfaz de archivos de PythonAnywhere
- O `scp` si tienes acceso SSH

## Paso 3: Subir al nuevo servidor (OceanDigital)

**Sube el archivo `suscripciones_consolidadas.json` al servidor OceanDigital:**
- Ubicación recomendada: `/srv/egarage/app/suscripciones_consolidadas.json`

## Paso 4: Importar en OceanDigital

**Ejecuta en la consola SSH de OceanDigital:**

```bash
cd /srv/egarage/app
python tools/importar_suscripciones.py suscripciones_consolidadas.json
```

Este script:
- ✅ Busca usuarios por email o username
- ✅ Crea o actualiza suscripciones
- ✅ Muestra un resumen detallado
- ✅ Lista errores si los hay

## Paso 5: Verificar la importación

**Ejecuta en OceanDigital:**

```bash
cd /srv/egarage/app
python tools/verificar_suscripciones_migradas.py
```

Este script te mostrará:
- Total de usuarios y suscripciones
- Usuarios con/sin suscripción
- Suscripciones activas/expiradas
- Detalles de las primeras suscripciones

## Formato del archivo consolidado

El archivo JSON generado tiene esta estructura:

```json
{
  "total_suscriptores_unicos": 15,
  "fecha_consolidacion": "2026-01-13",
  "estadisticas_backups": {
    "backup_db.sqlite3": 3,
    "backup_otro.sqlite3": 2
  },
  "por_pais": {
    "CL": 8,
    "US": 5,
    "SIN_PAIS": 2
  },
  "suscripciones": [
    {
      "user_email": "usuario@ejemplo.com",
      "user_username": "usuario",
      "user_id_original": 40,
      "tipo": "trial",
      "fecha_inicio": "2025-12-01",
      "fecha_fin": "2026-01-01",
      "activa": true,
      "empresa": {
        "id": 10,
        "nombre_taller": "Mi Taller",
        "pais": "CL",
        "telefono": "+56912345678",
        "email": "taller@ejemplo.com"
      },
      "backup_origen": "db.sqlite3"
    }
  ]
}
```

## Notas importantes

1. **Duplicados**: El script consolida automáticamente por email. Si un usuario aparece en múltiples backups, se mantiene la suscripción más reciente o activa.

2. **Usuarios no encontrados**: Si un usuario del backup no existe en OceanDigital, se mostrará un error pero el proceso continuará con los demás.

3. **Empresas**: La información de empresas se incluye para referencia, pero las empresas deben estar ya migradas o crearse por separado.

4. **Backups procesados**: El script procesa estos backups en orden:
   - `/home/atlantareciclajes/apps/egarage/shared/db/db.sqlite3`
   - `/home/atlantareciclajes/apps/egarage/current/data/root_data/db.sqlite3`
   - `/home/atlantareciclajes/apps/egarage/current/backups/deployments/db_backup_20251215_154133.sqlite3`
   - Y otros backups disponibles

## Solución de problemas

**Si el script no encuentra backups:**
- Verifica las rutas en el script
- Asegúrate de estar en el directorio correcto

**Si hay errores de importación:**
- Verifica que los usuarios existan en OceanDigital
- Revisa los logs de errores que muestra el script

**Si faltan suscripciones:**
- Verifica que los backups tengan la tabla `taller_suscripcion`
- Revisa las estadísticas mostradas por el script de consolidación
