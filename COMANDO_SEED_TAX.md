# 💰 Comando seed_tax - Políticas de Impuestos Base

## 🎯 **PROPÓSITO**

El comando `seed_tax` crea las políticas de impuestos mínimas necesarias para que el sistema funcione correctamente en los 5 países soportados.

---

## 🚀 **USO**

### **Básico:**
```bash
python manage.py seed_tax
```

### **Con actualización (forzar):**
```bash
python manage.py seed_tax --force
```

---

## 📋 **POLÍTICAS CREADAS**

### **🇨🇱 Chile (CL)**
- ✅ **Repuestos:** IVA 19% (solo repuestos)
- ✅ **Servicios:** 0% (sin política = sin impuesto)

**CONVENCIÓN CRÍTICA:** Chile aplica IVA 19% SOLO a repuestos, NO a servicios.

---

### **🇺🇸 USA (US)**
- ✅ **Georgia (GA):** 4% ambos
- ✅ **California (CA):** 7.25% ambos
- ✅ **New York (NY):** 4% ambos
- ✅ **Florida (FL):** 6% ambos
- ✅ **Texas (TX):** 6.25% ambos

**Sales tax por ubicación** (estado/ciudad).

---

### **🇧🇷 Brasil (BR)**
- ✅ **Repuestos:** ICMS 18%
- ✅ **Servicios:** Sin impuesto específico

---

### **🇵🇪 Perú (PE)**
- ✅ **Ambos:** IGV 18% (repuestos y servicios)

---

### **🇻🇪 Venezuela (VE)**
- ✅ **Ambos:** IVA 16% (repuestos y servicios)

---

## 📊 **OUTPUT ESPERADO**

```
================================================================================
[SEED] Creando políticas de impuestos base
================================================================================
  [CREADO] CL -> parts 19.00%
  [CREADO] US-GA -> both 4.00%
  [CREADO] US-CA -> both 7.25%
  [CREADO] US-NY -> both 4.00%
  [CREADO] US-FL -> both 6.00%
  [CREADO] US-TX -> both 6.25%
  [CREADO] BR -> parts 18.00%
  [CREADO] PE -> both 18.00%
  [CREADO] VE -> both 16.00%

================================================================================
[RESUMEN] Seed TaxPolicy completado
================================================================================

  Políticas creadas: 9
  Políticas actualizadas: 0
  Políticas ya existentes: 0
  Total procesadas: 9

[EXITO] Seed TaxPolicy OK

================================================================================
[CONVENCIONES] Verificación
================================================================================
  [OK] Chile: IVA 19% repuestos
  [OK] Chile: Sin IVA en servicios (correcto)
  [OK] Peru: IGV 18% ambos
  [OK] Venezuela: IVA 16% ambos
  [OK] Brasil: ICMS 18% repuestos
  [OK] USA: 5 estados configurados

================================================================================
```

---

## ✅ **VERIFICAR POLÍTICAS**

### **En Django Shell:**
```python
from taller.models import TaxPolicy

# Ver todas las políticas
for p in TaxPolicy.objects.all():
    print(f"{p.country}-{p.state_code or 'nacional'}: {p.rate*100:.2f}% ({p.applies_to})")

# Verificar Chile
cl_parts = TaxPolicy.objects.filter(country='CL', applies_to='parts').first()
print(f"Chile repuestos: {cl_parts.rate * 100}%")  # Debe ser 19.0

# Verificar que Chile NO tiene política para servicios
cl_services = TaxPolicy.objects.filter(country='CL', applies_to='services').exists()
print(f"Chile servicios: {cl_services}")  # Debe ser False
```

---

## 🔄 **CUÁNDO EJECUTAR**

### **Obligatorio:**
- ✅ Setup inicial (primera vez)
- ✅ Después de `python manage.py migrate`
- ✅ En cada nuevo entorno (desarrollo, staging, producción)

### **Opcional:**
- Después de borrar la base de datos
- Si se agregaron nuevos países (ejecutar con `--force`)

---

## 🎯 **INTEGRACIÓN CON MOTOR DE IMPUESTOS**

Las políticas creadas por `seed_tax` son utilizadas automáticamente por:

```python
from taller.impuestos.engine import resolve_tax_rate

# Automáticamente busca en TaxPolicy
rate, inclusive = resolve_tax_rate(
    empresa_chile,  # Empresa de Chile
    None,           # Sin ciudad específica
    'parts'         # Tipo: repuestos
)
# rate = 0.19 (19%)

# Para servicios en Chile
rate, inclusive = resolve_tax_rate(
    empresa_chile,
    None,
    'services'
)
# rate = 0.00 (0%) ✅ Correcto según convención
```

---

## 🆕 **AGREGAR MÁS ESTADOS USA**

Para agregar más estados de USA, editar `seed_tax.py`:

```python
# Agregar en la lista de policies:
{
    'country': 'US',
    'state_code': 'WA',  # Washington
    'city_name': '',
    'applies_to': 'both',
    'defaults': {
        'rate': Decimal('0.065'),  # 6.5%
        'inclusive': False,
        'active': True,
    }
},
```

---

## 📚 **ARCHIVOS RELACIONADOS**

- **Comando:** `taller/management/commands/seed_tax.py`
- **Motor:** `taller/impuestos/engine.py`
- **Modelo:** `taller/models/catalogo_repuestos.py` (TaxPolicy)
- **Docs:** `MOTOR_IMPUESTOS_IMPLEMENTADO.md`

---

## ⚠️ **ADVERTENCIAS**

### **NO modificar manualmente:**
- NO cambiar `CL` repuestos de 19%
- NO crear política para `CL` servicios
- NO cambiar `applies_to` sin revisar motor de impuestos

### **Actualizar políticas existentes:**
```bash
python manage.py seed_tax --force
```

---

## 🧪 **TESTING**

### **Probar en shell:**
```python
from taller.models import TaxPolicy, Empresa
from taller.impuestos.engine import resolve_tax_rate

# Empresa de Chile
empresa_cl = Empresa.objects.filter(pais='CL').first()

# Repuestos: debe dar 19%
rate_parts, _ = resolve_tax_rate(empresa_cl, None, 'parts')
assert rate_parts == Decimal('0.19'), "Chile repuestos debe ser 19%"

# Servicios: debe dar 0%
rate_services, _ = resolve_tax_rate(empresa_cl, None, 'services')
assert rate_services == Decimal('0.00'), "Chile servicios debe ser 0%"

print("✅ Todas las pruebas pasaron")
```

---

## 📊 **ESTADÍSTICAS**

```
Total políticas: 9
  CL: 1 (solo repuestos)
  US: 5 (5 estados)
  BR: 1 (solo repuestos)
  PE: 1 (ambos)
  VE: 1 (ambos)
```

---

## 🎊 **RESUMEN**

✅ **Comando creado:** `seed_tax.py`  
✅ **Políticas:** 9 base (ampliable)  
✅ **Convenciones:** 100% respetadas  
✅ **Chile:** IVA 19% solo repuestos ✅  
✅ **USA:** Sales tax por estado ✅  
✅ **Testing:** Verificado  

---

**Siguiente:** Ejecutar `python manage.py seed_tax` en tu entorno.

