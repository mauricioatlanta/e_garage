# 📘 Guía de Migraciones y Backfill - Sistema Multi-País

## 🎯 **OBJETIVO**

Migrar el sistema de desarrollo a producción (PythonAnywhere) aplicando:

1. ✅ Migraciones de base de datos (4 migraciones)
2. ✅ Backfill de datos legacy → Address
3. ✅ Backfill de tax_id → tax_id_type
4. ✅ Cargar datos de ubicaciones (Brasil, Venezuela, Perú)
5. ✅ Cargar catálogo demo

---

## 📋 **CHECKLIST PRE-MIGRACIÓN**

### **Antes de Ejecutar:**

- [ ] Backup de base de datos
  ```bash
  python manage.py dumpdata > backup_pre_migracion.json
  ```

- [ ] Verificar archivos en servidor
  ```bash
  ls -la taller/models/
  ls -la ubicacion/
  ls -la taller/impuestos/
  ```

- [ ] Verificar que git esté actualizado
  ```bash
  git status
  git pull origin main
  ```

- [ ] Activar virtualenv
  ```bash
  workon venv_egarage310
  cd ~/apps/egarage/current
  ```

---

## 🚀 **PASO 1: APLICAR MIGRACIONES**

### **En PythonAnywhere (Producción):**

```bash
# Activar entorno
workon venv_egarage310
cd ~/apps/egarage/current

# Verificar migraciones pendientes
python manage.py showmigrations

# Generar migraciones (si no están en git)
python manage.py makemigrations ubicacion
python manage.py makemigrations taller

# Aplicar migraciones
python manage.py migrate ubicacion
python manage.py migrate taller

# Verificar que se aplicaron
python manage.py showmigrations
```

### **Output Esperado:**

```
Running migrations:
  Applying ubicacion.0004_agregar_modelo_address... OK
  Applying taller.0026_agregar_modelo_address... OK
  Applying taller.0027_agregar_tax_id_type... OK
  Applying taller.0028_catalogo_i18n_precios... OK
```

---

## 📦 **PASO 2: CARGAR DATOS DE UBICACIONES**

### **Estados y Ciudades por País:**

```bash
# Brasil (27 estados, 22 ciudades)
python manage.py cargar_estados_brasil

# Venezuela (24 estados, 20 ciudades)
python manage.py cargar_estados_venezuela

# Perú (25 departamentos, 19 ciudades)
python manage.py cargar_estados_peru

# Políticas de impuestos base (5 países)
python manage.py seed_tax
```

### **Verificar Datos Cargados:**

```bash
python manage.py shell
```

```python
from taller.models import Estado, Ciudad

# Verificar estados por país
for pais in ['BR', 'PE', 'VE']:
    count = Estado.objects.filter(pais=pais).count()
    print(f"{pais}: {count} estados")

# Verificar ciudades
for pais in ['BR', 'PE', 'VE']:
    count = Ciudad.objects.filter(estado__pais=pais).count()
    print(f"{pais}: {count} ciudades")

# Verificar políticas de impuestos
from taller.models import TaxPolicy
print(f"\nTaxPolicies: {TaxPolicy.objects.count()}")
for country in ['CL', 'US', 'BR', 'PE', 'VE']:
    count = TaxPolicy.objects.filter(country=country).count()
    print(f"  {country}: {count} políticas")

exit()
```

---

## 🔄 **PASO 3: BACKFILL DE ADDRESSES**

### **3.1 Simular (Dry Run):**

```bash
# Ver qué se haría sin aplicar cambios
python manage.py backfill_addresses --dry-run
```

**Output Esperado:**
```
[DRY RUN] Simulación - no se guardarán cambios
[BACKFILL] Migrando direcciones legacy a Address
[INFO] Total de clientes a procesar: 150
[OK] 100 direcciones migradas...
[RESUMEN] Backfill completado
  Total clientes procesados: 150
  Addresses creadas: 120
  Clientes ya con Address: 15
  Clientes sin ciudad: 15
[DRY RUN] Ejecuta sin --dry-run para aplicar
```

---

### **3.2 Ejecutar Backfill:**

```bash
# Aplicar backfill
python manage.py backfill_addresses
```

**Output Esperado:**
```
[BACKFILL] Migrando direcciones legacy a Address
[INFO] Total de clientes a procesar: 150
[OK] 50 direcciones migradas...
[OK] 100 direcciones migradas...
[EXITO] 120 direcciones migradas a Address
```

---

### **3.3 Backfill por País (Opcional):**

```bash
# Solo migrar USA
python manage.py backfill_addresses --pais=US

# Solo migrar Perú
python manage.py backfill_addresses --pais=PE

# Solo migrar Brasil
python manage.py backfill_addresses --pais=BR
```

---

### **3.4 Verificar:**

```bash
python manage.py shell
```

```python
from taller.models import Cliente
from ubicacion.models import Address

# Clientes con billing_address
con_address = Cliente.objects.filter(billing_address__isnull=False).count()
print(f"Clientes con Address: {con_address}")

# Total de addresses
total_addr = Address.objects.count()
print(f"Total Addresses: {total_addr}")

# Ver ejemplo
cliente = Cliente.objects.filter(billing_address__isnull=False).first()
if cliente:
    print(f"\nEjemplo:")
    print(f"  Cliente: {cliente.nombre}")
    print(f"  Address: {cliente.billing_address.line1}")
    print(f"  Ciudad: {cliente.billing_address.city}")
    print(f"  País: {cliente.billing_address.country_code}")
    print(f"  Sales Tax: {cliente.billing_address.sales_tax}%")

exit()
```

---

## 🆔 **PASO 4: BACKFILL DE TAX ID TYPES**

### **4.1 Simular:**

```bash
python manage.py backfill_tax_id_types --dry-run
```

---

### **4.2 Ejecutar:**

```bash
python manage.py backfill_tax_id_types
```

**Output Esperado:**
```
[BACKFILL] Auto-detectando tax_id_type
[INFO] Total de clientes con tax_id: 200
[OK] 50 tax_id_types asignados...
[OK] 100 tax_id_types asignados...
[EXITO] 180 tax_id_types actualizados
```

---

### **4.3 Verificar:**

```bash
python manage.py shell
```

```python
from taller.models import Cliente

# Ver distribución de tax_id_types
for tipo_code, tipo_label in Cliente.TAX_ID_TYPES:
    count = Cliente.objects.filter(tax_id_type=tipo_code).count()
    print(f"{tipo_code}: {count} clientes")

# Ver ejemplos por país
for pais in ['CL', 'US', 'BR', 'PE', 'VE']:
    cliente = Cliente.objects.filter(
        empresa__pais=pais,
        tax_id__isnull=False
    ).exclude(tax_id='').first()
    
    if cliente:
        print(f"\n{pais}:")
        print(f"  Tax ID Type: {cliente.tax_id_type}")
        print(f"  Tax ID: {cliente.tax_id}")

exit()
```

---

## 📊 **PASO 5: CARGAR CATÁLOGO DEMO (OPCIONAL)**

### **Solo para Desarrollo/Testing:**

```bash
python manage.py cargar_catalogo_demo
```

**Carga:**
- 5 políticas de impuestos
- 3 repuestos con I18N (5 idiomas)
- 3 servicios con I18N (5 idiomas)

**⚠️ NOTA:** En producción, probablemente querrás crear tu propio catálogo.

---

## 🔍 **PASO 6: VERIFICACIÓN FINAL**

### **6.1 Verificar Migraciones:**

```bash
python manage.py showmigrations ubicacion taller
```

**Debe mostrar:**
```
ubicacion
 [X] 0001_initial
 [X] 0002_alter_ciudad_estado
 [X] 0003_alter_ciudad_estado
 [X] 0004_agregar_modelo_address

taller
 ... (migraciones anteriores)
 [X] 0026_agregar_modelo_address
 [X] 0027_agregar_tax_id_type
 [X] 0028_catalogo_i18n_precios
```

---

### **6.2 Verificar Modelos:**

```bash
python manage.py shell
```

```python
# Verificar que los modelos existan
from ubicacion.models import Address
from taller.models import (
    Part, PartI18N, PartPrice,
    Service, ServiceI18N, ServicePrice,
    TaxPolicy, Cliente
)

print("Modelos importados correctamente ✅")

# Verificar Address
print(f"Total Addresses: {Address.objects.count()}")

# Verificar Catálogo
print(f"Total Parts: {Part.objects.count()}")
print(f"Total Services: {Service.objects.count()}")
print(f"Total TaxPolicies: {TaxPolicy.objects.count()}")

# Verificar Cliente actualizado
cliente = Cliente.objects.first()
if cliente:
    print(f"\nCampos de Cliente:")
    print(f"  billing_address: {hasattr(cliente, 'billing_address')}")
    print(f"  shipping_address: {hasattr(cliente, 'shipping_address')}")
    print(f"  tax_id_type: {hasattr(cliente, 'tax_id_type')}")

exit()
```

---

### **6.3 Probar API:**

```bash
# En navegador o curl
curl "http://tu-dominio.pythonanywhere.com/api/locations?country=PE"
```

**Debe retornar:**
```json
{
  "states": [
    {"id": 77, "name": "Lima", "code": "LIM"},
    {"id": 78, "name": "Arequipa", "code": "ARE"},
    ...
  ]
}
```

---

### **6.4 Probar Admin:**

```
http://tu-dominio.pythonanywhere.com/admin/

Verificar que aparezcan:
  ✅ Addresses
  ✅ Parts
  ✅ Services
  ✅ Tax Policies
```

---

## 🔄 **PASO 7: RELOAD DE APLICACIÓN**

### **En PythonAnywhere:**

```bash
# Reload de la aplicación web
# Ir a: Web tab → Reload button
# O usar API:
curl -X POST https://www.pythonanywhere.com/api/v0/user/{username}/webapps/{domain}/reload/ \
  -H "Authorization: Token {api_token}"
```

---

## 📊 **RESUMEN DE MIGRACIONES**

### **Migraciones a Aplicar:**

| App | Migración | Descripción |
|-----|-----------|-------------|
| ubicacion | 0004 | Create Address |
| taller | 0026 | Add address fields to Cliente/Config |
| taller | 0027 | Add tax_id_type to Cliente |
| taller | 0028 | Create Part/Service/TaxPolicy models |

### **Comandos de Backfill:**

| Comando | Propósito | Orden |
|---------|-----------|-------|
| `cargar_estados_brasil` | Cargar estados de Brasil | 1 |
| `cargar_estados_venezuela` | Cargar estados de Venezuela | 2 |
| `cargar_estados_peru` | Cargar estados de Perú | 3 |
| `backfill_addresses` | Migrar direcciones legacy | 4 |
| `backfill_tax_id_types` | Auto-asignar tax_id_type | 5 |
| `cargar_catalogo_demo` | Cargar catálogo demo (opcional) | 6 |

---

## 🚨 **TROUBLESHOOTING**

### **Error: "Table already exists"**

```bash
# Si la migración ya se aplicó parcialmente
python manage.py migrate --fake ubicacion 0004
python manage.py migrate --fake taller 0028
```

---

### **Error: "No module named 'taller.impuestos'"**

```bash
# Verificar que el directorio exista
ls -la taller/impuestos/
# Debe contener: __init__.py, engine.py

# Si no existe, crear
mkdir -p taller/impuestos
touch taller/impuestos/__init__.py
```

---

### **Error: "Cannot import name 'TaxPolicy'"**

```bash
# Verificar imports en __init__.py
cat taller/models/__init__.py | grep TaxPolicy

# Debe incluir:
# from .catalogo_repuestos import Part, PartI18N, PartPrice, TaxPolicy
```

---

### **Backfill no migra clientes de Chile:**

**Causa:** Chile usa modelo legacy `TallerCiudad` que es diferente a `taller.Ciudad`.

**Solución:** Migración manual o script específico:

```python
# Script para Chile (si es necesario)
from taller.models import Cliente, Ciudad, Estado
from taller.models.region_ciudad import TallerCiudad, TallerRegion
from ubicacion.models import Address

# Mapear TallerCiudad → taller.Ciudad (requiere mapeo manual)
# Por ahora, Chile puede seguir usando campos legacy
```

---

## ⏱️ **TIEMPO ESTIMADO**

| Paso | Tiempo | Downtime |
|------|--------|----------|
| Aplicar migraciones | 1-2 min | ❌ No* |
| Cargar ubicaciones (3 países) | 3-5 min | ❌ No |
| Backfill addresses | 2-10 min** | ❌ No |
| Backfill tax_id_types | 1-5 min** | ❌ No |
| Reload aplicación | 30 seg | ✅ Sí |
| **TOTAL** | **8-23 min** | **30 seg** |

*Las migraciones de Django son atómicas  
**Depende de cantidad de registros  

---

## 📝 **SCRIPT COMPLETO DE MIGRACIÓN**

### **Para copiar/pegar en terminal:**

```bash
#!/bin/bash
# Script de migración completo

echo "=========================================="
echo "MIGRACION SISTEMA MULTI-PAIS"
echo "=========================================="

# 1. Activar entorno
workon venv_egarage310
cd ~/apps/egarage/current

# 2. Backup
echo "[1/7] Creando backup..."
python manage.py dumpdata > backup_$(date +%Y%m%d_%H%M%S).json

# 3. Aplicar migraciones
echo "[2/7] Aplicando migraciones..."
python manage.py migrate ubicacion
python manage.py migrate taller

# 4. Cargar ubicaciones
echo "[3/8] Cargando estados de Brasil..."
python manage.py cargar_estados_brasil

echo "[4/8] Cargando estados de Venezuela..."
python manage.py cargar_estados_venezuela

echo "[5/8] Cargando estados de Perú..."
python manage.py cargar_estados_peru

echo "[6/8] Cargando políticas de impuestos..."
python manage.py seed_tax

# 5. Backfill
echo "[7/8] Migrando direcciones a Address..."
python manage.py backfill_addresses

echo "[8/8] Auto-detectando tax_id_types..."
python manage.py backfill_tax_id_types

# 6. Verificación
echo "=========================================="
echo "VERIFICACION"
echo "=========================================="

python manage.py shell <<EOF
from taller.models import Estado, Ciudad, Part, Service, TaxPolicy
from ubicacion.models import Address

print(f"Estados: {Estado.objects.count()}")
print(f"Ciudades: {Ciudad.objects.count()}")
print(f"Addresses: {Address.objects.count()}")
print(f"Parts: {Part.objects.count()}")
print(f"Services: {Service.objects.count()}")
print(f"TaxPolicies: {TaxPolicy.objects.count()}")
EOF

echo "=========================================="
echo "MIGRACION COMPLETADA"
echo "Recuerda hacer RELOAD de la app en PythonAnywhere"
echo "=========================================="
```

---

## 📋 **PASO A PASO DETALLADO (PythonAnywhere)**

### **1. Conectar por SSH:**

```bash
ssh username@ssh.pythonanywhere.com
```

---

### **2. Navegar al directorio:**

```bash
cd ~/apps/egarage/current
```

---

### **3. Activar virtualenv:**

```bash
workon venv_egarage310
# O si usas otro método:
source ~/venvs/egarage/bin/activate
```

---

### **4. Hacer backup:**

```bash
# Backup de DB
python manage.py dumpdata > backup_pre_multi_pais_$(date +%Y%m%d).json

# Backup de archivos (opcional)
tar -czf backup_code_$(date +%Y%m%d).tar.gz taller/ ubicacion/ templates/
```

---

### **5. Aplicar migraciones:**

```bash
python manage.py migrate
```

---

### **6. Cargar datos:**

```bash
python manage.py cargar_estados_brasil
python manage.py cargar_estados_venezuela
python manage.py cargar_estados_peru
```

---

### **7. Backfill (dry-run primero):**

```bash
# Simular
python manage.py backfill_addresses --dry-run
python manage.py backfill_tax_id_types --dry-run

# Si todo OK, aplicar
python manage.py backfill_addresses
python manage.py backfill_tax_id_types
```

---

### **8. Reload aplicación:**

```
PythonAnywhere Dashboard → Web → Reload (botón verde)
```

---

### **9. Probar:**

```
https://tu-dominio.pythonanywhere.com/
https://tu-dominio.pythonanywhere.com/pe/
https://tu-dominio.pythonanywhere.com/api/locations?country=PE
```

---

## ✅ **VERIFICACIÓN POST-MIGRACIÓN**

### **Checklist:**

- [ ] Migraciones aplicadas (showmigrations)
- [ ] Estados cargados (103+ total)
- [ ] Ciudades cargadas (111+ total)
- [ ] Addresses creadas (backfill)
- [ ] Tax ID types asignados (backfill)
- [ ] API funcionando (/api/locations)
- [ ] Admin accesible (/admin/)
- [ ] Páginas de países cargando (/pe/, /br/, /ve/)
- [ ] Sin errores en logs

---

## 🔙 **ROLLBACK (Si es necesario)**

### **Revertir Migraciones:**

```bash
# Volver a migración anterior
python manage.py migrate taller 0025
python manage.py migrate ubicacion 0003

# Restaurar backup
python manage.py flush --no-input
python manage.py loaddata backup_pre_multi_pais_YYYYMMDD.json
```

---

## 📊 **DATOS ESPERADOS POST-MIGRACIÓN**

```
✅ Estados: ~103 (US:25, BR:27, PE:27, VE:24, CL:0*)
✅ Ciudades: ~111 (distribuidas por país)
✅ Addresses: Depende de clientes existentes
✅ TaxPolicies: 5 (una por país)
✅ Parts: 0-3 (si se carga demo)
✅ Services: 0-3 (si se carga demo)
✅ PartI18N: 0-15 (si se carga demo)
✅ ServiceI18N: 0-15 (si se carga demo)
```

*Chile usa modelo legacy TallerRegion/TallerCiudad

---

## 📚 **COMANDOS DE REFERENCIA**

### **Management Commands Disponibles:**

```bash
# Ubicaciones
python manage.py cargar_estados_brasil
python manage.py cargar_estados_venezuela
python manage.py cargar_estados_peru

# Backfill
python manage.py backfill_addresses [--dry-run] [--pais=XX]
python manage.py backfill_tax_id_types [--dry-run] [--force]

# Catálogo (opcional)
python manage.py cargar_catalogo_demo

# Verificación
python manage.py showmigrations
python manage.py check
python manage.py migrate --plan
```

---

## 🎯 **ORDEN RECOMENDADO DE EJECUCIÓN**

```
1. Backup ✅
2. Migrate ✅
3. Cargar ubicaciones (BR, VE, PE) ✅
4. Backfill addresses ✅
5. Backfill tax_id_types ✅
6. Cargar catálogo demo (opcional)
7. Reload app ✅
8. Verificar ✅
```

---

## 📖 **DOCUMENTACIÓN ADICIONAL**

- **Arquitectura:** `SISTEMA_MULTI_PAIS_COMPLETO_FINAL.md`
- **API:** `API_UBICACIONES_UNIFICADA.md`
- **Formularios:** `FORMULARIOS_UNIFICADOS_IMPLEMENTADOS.md`
- **Motor Impuestos:** `MOTOR_IMPUESTOS_IMPLEMENTADO.md`

---

## ✅ **CHECKLIST FINAL**

- [✅] Script de backfill_addresses.py creado
- [✅] Script de backfill_tax_id_types.py creado
- [✅] Documentación de migración creada
- [✅] Comandos de verificación incluidos
- [✅] Troubleshooting incluido
- [✅] Script bash completo incluido
- [✅] Orden de ejecución documentado

---

## 🎉 **RESUMEN**

✅ **Guía completa de migración** a producción  
✅ **Scripts de backfill** con dry-run  
✅ **Verificación paso a paso**  
✅ **Troubleshooting** incluido  
✅ **Rollback plan** documentado  

**Estado:** ✅ **LISTO PARA PRODUCCIÓN**

**Siguiente paso:** Ejecutar en PythonAnywhere siguiendo esta guía.

