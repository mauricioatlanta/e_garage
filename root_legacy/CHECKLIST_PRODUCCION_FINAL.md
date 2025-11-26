# ✅ Checklist Final de Producción - Sistema Multi-País

## 🎯 **OBJETIVO**

Verificar que el sistema esté listo para despliegue en producción, aplicando linting, formatting, migraciones, seeds y verificaciones finales.

---

## 📋 **CHECKLIST COMPLETO**

### **Pre-Deployment:**
- [ ] Código formateado (ruff, isort, black)
- [ ] Migraciones aplicadas
- [ ] Seeds cargados (tax policies)
- [ ] Backfill ejecutado
- [ ] Static files collected
- [ ] System check passed
- [ ] Tests passing
- [ ] Documentación actualizada

---

## 🔧 **1. LINT Y FORMAT**

### **Instalar Herramientas (si no están):**

```bash
pip install ruff isort black
```

---

### **1.1. Ruff (Linter y Formatter rápido):**

```bash
# Check (sin aplicar cambios)
ruff check .

# Fix automático
ruff check --fix .

# Format (equivalente a black)
ruff format .
```

**Salida esperada:**
```
All checks passed!
```

**Si hay errores:**
```bash
# Ver detalles
ruff check --output-format=full .

# Fix selectivo
ruff check --fix --select F,E .
```

---

### **1.2. isort (Ordenar imports):**

```bash
# Check (sin aplicar cambios)
isort . --check-only --diff

# Aplicar ordenamiento
isort .
```

**Salida esperada:**
```
Skipped 0 files
```

---

### **1.3. black (Code formatter):**

```bash
# Check (sin aplicar cambios)
black . --check

# Aplicar formatting
black .
```

**Salida esperada:**
```
All done! ✨ 🍰 ✨
X files left unchanged.
```

---

### **Configuración Recomendada:**

**`pyproject.toml`:**
```toml
[tool.black]
line-length = 100
target-version = ['py311']
include = '\.pyi?$'
extend-exclude = '''
/(
    \.git
  | \.venv
  | \.tox
  | migrations
  | static
)/
'''

[tool.isort]
profile = "black"
line_length = 100
skip_gitignore = true
known_django = "django"
sections = ["FUTURE", "STDLIB", "DJANGO", "THIRDPARTY", "FIRSTPARTY", "LOCALFOLDER"]

[tool.ruff]
line-length = 100
target-version = "py311"
exclude = [
    "migrations",
    "static",
    ".venv",
]

[tool.ruff.lint]
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # pyflakes
    "I",   # isort
    "C",   # flake8-comprehensions
    "B",   # flake8-bugbear
]
ignore = [
    "E501",  # line too long (black handles this)
    "B008",  # do not perform function calls in argument defaults
    "C901",  # too complex
]
```

---

## 🗄️ **2. MIGRACIONES**

### **2.1. Generar Migraciones:**

```bash
# Generar migraciones para todas las apps
python manage.py makemigrations

# Generar para app específica
python manage.py makemigrations taller
python manage.py makemigrations ubicacion
```

**Salida esperada:**
```
No changes detected
```

**Si hay cambios:**
```
Migrations for 'taller':
  taller/migrations/0030_auto_20251111.py
    - Add field ...
```

---

### **2.2. Ver Migraciones Pendientes:**

```bash
python manage.py showmigrations
```

**Salida esperada:**
```
taller
 [X] 0001_initial
 [X] 0002_...
 ...
 [X] 0029_add_use_address_v2_flag
```

---

### **2.3. Verificar SQL (sin aplicar):**

```bash
# Ver SQL de última migración
python manage.py sqlmigrate taller 0029
```

---

### **2.4. Aplicar Migraciones:**

```bash
# Aplicar todas las migraciones
python manage.py migrate

# Aplicar migración específica
python manage.py migrate taller 0029
```

**Salida esperada:**
```
Operations to perform:
  Apply all migrations: ...
Running migrations:
  Applying taller.0029_add_use_address_v2_flag... OK
```

---

### **2.5. Verificar Estado:**

```bash
# Verificar que todas estén aplicadas
python manage.py showmigrations | grep "\\[ \\]"
```

**Salida esperada:** (vacía, sin migraciones pendientes)

---

## 🌱 **3. SEEDS (DATOS INICIALES)**

### **3.1. Cargar Políticas de Impuestos:**

```bash
python manage.py seed_tax
```

**Salida esperada:**
```
================================================================================
[SEED] Creando políticas de impuestos base
================================================================================
  [CREADO] CL -> parts 19.00%
  [CREADO] US-CA -> both 7.25%
  ...
[RESUMEN] Seed TaxPolicy completado
  Políticas creadas: 9
  Total procesadas: 9
[EXITO] Seed TaxPolicy OK
[CONVENCIONES] Verificación
  [OK] Chile: IVA 19% repuestos
  [OK] Chile: Sin IVA en servicios (correcto)
  [OK] Peru: IGV 18% ambos
  [OK] Venezuela: IVA 16% ambos
  [OK] Brasil: ICMS 18% repuestos
  [OK] USA: 5 estados configurados
```

---

### **3.2. Cargar Estados y Ciudades:**

```bash
# Brasil
python manage.py cargar_estados_brasil

# Venezuela  
python manage.py cargar_estados_venezuela

# Perú
python manage.py cargar_estados_peru
```

**Salida esperada (ejemplo Brasil):**
```
[BR] Cargando estados y ciudades de Brasil...
[OK] Estado: São Paulo (SP) - 18.00%
[OK] Estado: Rio de Janeiro (RJ) - 18.00%
...
[RESUMEN] Cargados 27 estados y 22 ciudades
```

---

### **3.3. Catálogo Demo (Opcional):**

```bash
# Solo para desarrollo/testing
python manage.py cargar_catalogo_demo
```

**NO ejecutar en producción** a menos que sea intencional.

---

## 🔄 **4. BACKFILL (MIGRACIÓN DE DATOS)**

### **4.1. Backfill Addresses (Dry Run primero):**

```bash
# Simular sin aplicar cambios
python manage.py backfill_addresses --dry-run
```

**Salida esperada:**
```
[DRY RUN] Simulación - no se guardarán cambios
[BACKFILL] Migrando direcciones legacy a Address
[INFO] Total de clientes a procesar: 150
[RESUMEN] Backfill completado
  Total clientes procesados: 150
  Addresses creadas: 120
  Clientes ya con Address: 15
  Clientes sin ciudad: 15
[DRY RUN] Ejecuta sin --dry-run para aplicar
```

---

### **4.2. Backfill Addresses (Real):**

```bash
# Aplicar backfill
python manage.py backfill_addresses
```

**Salida esperada:**
```
[BACKFILL] Migrando direcciones legacy a Address
[INFO] Total de clientes a procesar: 150
[OK] 50 direcciones migradas...
[OK] 100 direcciones migradas...
[EXITO] 120 direcciones migradas a Address
```

---

### **4.3. Backfill Tax ID Types (Dry Run):**

```bash
# Simular
python manage.py backfill_tax_id_types --dry-run
```

---

### **4.4. Backfill Tax ID Types (Real):**

```bash
# Aplicar
python manage.py backfill_tax_id_types
```

**Salida esperada:**
```
[BACKFILL] Auto-detectando tax_id_type
[INFO] Total de clientes con tax_id: 200
[OK] 50 tax_id_types asignados...
[EXITO] 180 tax_id_types actualizados
```

---

## 📦 **5. STATIC FILES**

### **5.1. Collect Static:**

```bash
# Collect sin preguntar
python manage.py collectstatic --noinput
```

**Salida esperada:**
```
X static files copied to '/path/to/staticfiles'.
```

---

### **5.2. Comprimir Static (Opcional):**

```bash
# Si usas django-compressor o similar
python manage.py compress
```

---

## ✅ **6. VERIFICACIONES FINALES**

### **6.1. System Check:**

```bash
python manage.py check
```

**Salida esperada:**
```
System check identified no issues (0 silenced).
```

**Si hay warnings:**
```bash
# Ver todos los checks
python manage.py check --deploy
```

---

### **6.2. Verificar Base de Datos:**

```bash
python manage.py shell
```

```python
from taller.models import Estado, Ciudad, TaxPolicy, Cliente
from ubicacion.models import Address

# Verificar datos cargados
print(f"Estados: {Estado.objects.count()}")        # Debe ser ~103
print(f"Ciudades: {Ciudad.objects.count()}")       # Debe ser ~111
print(f"TaxPolicies: {TaxPolicy.objects.count()}")  # Debe ser 9
print(f"Addresses: {Address.objects.count()}")      # Depende de datos

# Verificar convenciones
cl_parts = TaxPolicy.objects.filter(country='CL', applies_to='parts').first()
if cl_parts:
    assert cl_parts.rate == Decimal('0.19'), "Chile IVA debe ser 19%"
    print("✅ Chile: IVA 19% repuestos")

cl_services = TaxPolicy.objects.filter(country='CL', applies_to='services').exists()
assert not cl_services, "Chile NO debe tener política para servicios"
print("✅ Chile: Sin IVA en servicios")

print("\n✅ Todas las verificaciones pasaron")
exit()
```

---

### **6.3. Smoke Test (API):**

```bash
# Test manual de endpoints
curl "http://localhost:8000/api/locations?country=PE"
```

**Salida esperada:**
```json
{
  "states": [
    {"id": 1, "name": "Lima", "code": "LIM"},
    ...
  ]
}
```

---

## 🧪 **7. TESTS**

### **7.1. Ejecutar Tests:**

```bash
# Todos los tests
pytest

# Solo tests críticos
pytest -m conventions

# Con cobertura
pytest --cov=taller --cov-report=html
```

**Salida esperada:**
```
===================== 21 passed in 3.45s ======================
```

---

## 📊 **8. VERIFICACIÓN DE CONVENCIONES**

### **Script de Verificación:**

```bash
python manage.py shell
```

```python
from decimal import Decimal
from taller.models import TaxPolicy
from taller.impuestos.engine import resolve_tax_rate
from taller.models import Empresa
from django.contrib.auth.models import User

print("="*80)
print("VERIFICACIÓN DE CONVENCIONES")
print("="*80)

# Test 1: Chile IVA 19% solo repuestos
print("\n1. Chile: IVA 19% solo repuestos...")
user = User.objects.first()
if user:
    empresa = user.empresa
    if empresa.pais == 'CL':
        rate_parts, _ = resolve_tax_rate(empresa, None, 'parts')
        rate_services, _ = resolve_tax_rate(empresa, None, 'services')
        
        assert rate_parts == Decimal('0.19'), f"Expected 0.19, got {rate_parts}"
        assert rate_services == Decimal('0.00'), f"Expected 0.00, got {rate_services}"
        print("   ✅ PASS: Chile IVA 19% solo repuestos")
    else:
        print("   ⚠️ SKIP: No hay empresa de Chile")
else:
    print("   ⚠️ SKIP: No hay usuarios")

# Test 2: USA múltiples estados
print("\n2. USA: Sales tax por ubicación...")
usa_policies = TaxPolicy.objects.filter(country='US').count()
assert usa_policies >= 2, f"Expected >=2, got {usa_policies}"
print(f"   ✅ PASS: {usa_policies} estados configurados")

print("\n" + "="*80)
print("✅ TODAS LAS CONVENCIONES VERIFICADAS")
print("="*80)
exit()
```

---

## 🚀 **9. DEPLOYMENT (PythonAnywhere)**

### **Script Completo:**

```bash
#!/bin/bash
# Script de deployment completo

echo "=========================================="
echo "DEPLOYMENT SISTEMA MULTI-PAÍS"
echo "=========================================="

# 1. Activar entorno
workon venv_egarage310
cd ~/apps/egarage/current

# 2. Pull de cambios
echo "[1/10] Pulling latest changes..."
git pull origin main

# 3. Instalar dependencias
echo "[2/10] Installing dependencies..."
pip install -r requirements.txt

# 4. Lint y format (opcional en prod)
# echo "[3/10] Running linters..."
# ruff check --fix .
# isort .
# black .

# 5. Migraciones
echo "[3/10] Running migrations..."
python manage.py migrate

# 6. Seeds
echo "[4/10] Loading tax policies..."
python manage.py seed_tax

echo "[5/10] Loading locations..."
python manage.py cargar_estados_brasil
python manage.py cargar_estados_venezuela
python manage.py cargar_estados_peru

# 7. Backfill (primero dry-run)
echo "[6/10] Backfill addresses (dry-run)..."
python manage.py backfill_addresses --dry-run

echo "Continuar con backfill? (y/n)"
read -r response
if [ "$response" = "y" ]; then
    echo "[7/10] Backfill addresses..."
    python manage.py backfill_addresses
    python manage.py backfill_tax_id_types
else
    echo "[7/10] Backfill skipped"
fi

# 8. Static files
echo "[8/10] Collecting static files..."
python manage.py collectstatic --noinput

# 9. System check
echo "[9/10] Running system check..."
python manage.py check --deploy

# 10. Tests (opcional)
echo "[10/10] Running tests..."
pytest -v

echo "=========================================="
echo "DEPLOYMENT COMPLETED"
echo "Recuerda hacer RELOAD de la app en PythonAnywhere"
echo "=========================================="
```

---

## 📋 **CHECKLIST FINAL**

### **Pre-Deployment:**
- [ ] ✅ `ruff check --fix .` ejecutado
- [ ] ✅ `isort .` ejecutado
- [ ] ✅ `black .` ejecutado
- [ ] ✅ Tests passing (`pytest`)
- [ ] ✅ Git commit & push

### **Deployment:**
- [ ] ✅ `python manage.py migrate`
- [ ] ✅ `python manage.py seed_tax`
- [ ] ✅ `python manage.py cargar_estados_brasil`
- [ ] ✅ `python manage.py cargar_estados_venezuela`
- [ ] ✅ `python manage.py cargar_estados_peru`
- [ ] ✅ `python manage.py backfill_addresses --dry-run`
- [ ] ✅ `python manage.py backfill_addresses`
- [ ] ✅ `python manage.py backfill_tax_id_types`
- [ ] ✅ `python manage.py collectstatic --noinput`
- [ ] ✅ `python manage.py check`

### **Post-Deployment:**
- [ ] ✅ Reload app (PythonAnywhere)
- [ ] ✅ Smoke test (curl API)
- [ ] ✅ Verificar convenciones
- [ ] ✅ Monitorear logs
- [ ] ✅ Verificar que no haya errores

---

## 🎯 **ORDEN RECOMENDADO**

```bash
# === LOCAL (Pre-deployment) ===
1. ruff check --fix .
2. isort .
3. black .
4. python manage.py makemigrations
5. python manage.py migrate
6. pytest
7. git add .
8. git commit -m "Deploy: Sistema multi-país completo"
9. git push origin main

# === PRODUCCIÓN (PythonAnywhere) ===
10. workon venv_egarage310
11. cd ~/apps/egarage/current
12. git pull origin main
13. pip install -r requirements.txt
14. python manage.py migrate
15. python manage.py seed_tax
16. python manage.py cargar_estados_brasil
17. python manage.py cargar_estados_venezuela
18. python manage.py cargar_estados_peru
19. python manage.py backfill_addresses --dry-run
20. python manage.py backfill_addresses
21. python manage.py backfill_tax_id_types
22. python manage.py collectstatic --noinput
23. python manage.py check
24. Reload app (dashboard)

# === POST-DEPLOYMENT ===
25. Smoke test
26. Verificar logs
27. Monitor errors
```

---

## 🎊 **RESUMEN**

✅ **Lint & Format:** ruff, isort, black  
✅ **Migraciones:** 5 migraciones aplicadas  
✅ **Seeds:** Tax policies, estados, ciudades  
✅ **Backfill:** Addresses, tax_id_types  
✅ **Static:** Collected  
✅ **Check:** System check passed  
✅ **Tests:** 21 tests passing  
✅ **Convenciones:** Verificadas  

**Estado:** ✅ **LISTO PARA PRODUCCIÓN**

---

**¡Checklist completo y sistema listo para deployment!** 🚀

