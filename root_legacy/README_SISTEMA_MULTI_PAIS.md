# 🌎 eGarage - Sistema Multi-País

## 🚀 **INICIO RÁPIDO**

### **Aplicar Migraciones:**
```bash
python manage.py migrate
```

### **Cargar Datos:**
```bash
# Ubicaciones
python manage.py cargar_estados_brasil
python manage.py cargar_estados_venezuela
python manage.py cargar_estados_peru

# Catálogo demo
python manage.py cargar_catalogo_demo
```

### **URLs de Prueba:**
```
http://127.0.0.1:8000/              → Selector de países
http://127.0.0.1:8000/pe/           → Perú
http://127.0.0.1:8000/br/           → Brasil
http://127.0.0.1:8000/ve/           → Venezuela
http://127.0.0.1:8000/api/locations?country=PE → API
```

---

## 🌍 **PAÍSES SOPORTADOS**

| País | Moneda | Impuesto | URL |
|------|--------|----------|-----|
| 🇨🇱 Chile | CLP ($) | IVA 19% solo repuestos | `/cl/` |
| 🇺🇸 USA | USD ($) | Sales tax por estado | `/us/` |
| 🇧🇷 Brasil | BRL (R$) | ICMS 18% | `/br/` |
| 🇵🇪 Perú | PEN (S/) | IGV 18% | `/pe/` |
| 🇻🇪 Venezuela | VES (Bs.) | IVA 16% | `/ve/` |

---

## 📦 **COMPONENTES PRINCIPALES**

### **1. Direcciones (Address):**
```python
from ubicacion.models import Address

address = Address.objects.create(
    line1="Av. Arequipa 123",
    city=ciudad_lima,
    postal_code="15001"
)

address.country_code  # "PE"
address.sales_tax     # 18.00 (IGV automático)
```

### **2. Tax ID (7 tipos):**
```python
cliente = Cliente.objects.create(
    nombre="Comercial ABC",
    tax_id_type='PE_RUC',
    tax_id='20123456789'
)
```

### **3. Catálogo I18N:**
```python
oil = Part.objects.get(sku='OIL-5W30-4L')
oil.get_display_name('es-PE')  # "Aceite para Motor 5W30"
oil.get_display_name('en-US')  # "Engine Oil 5W30"
```

### **4. API Unificada:**
```javascript
fetch('/api/locations?country=PE')
  .then(r => r.json())
  .then(data => console.log(data.states));
```

### **5. JavaScript Reutilizable:**
```html
<script type="module">
  import { bindCountryStateCity } from "{% static 'js/locations.js' %}";
  bindCountryStateCity('#id_country', '#id_state', '#id_city');
</script>
```

---

## 📚 **DOCUMENTACIÓN**

| Documento | Descripción |
|-----------|-------------|
| `SISTEMA_MULTI_PAIS_COMPLETO_FINAL.md` | **Inicio aquí** - Arquitectura completa |
| `API_UBICACIONES_UNIFICADA.md` | Documentación API |
| `EJEMPLOS_USO_LOCATIONS_JS.md` | Guía JavaScript |
| `FORMULARIOS_UNIFICADOS_IMPLEMENTADOS.md` | Formularios Customer/Company |

---

## ✅ **CHECKLIST DE IMPLEMENTACIÓN**

### **Backend:**
- [✅] Modelo Address
- [✅] Tax ID Type (7 tipos)
- [✅] Catálogo I18N (Part/Service)
- [✅] Políticas de impuestos (TaxPolicy)
- [✅] API unificada

### **Frontend:**
- [✅] JavaScript reutilizable (locations.js)
- [✅] Formularios unificados (Customer/Company)
- [✅] Templates de ejemplo

### **Datos:**
- [✅] 103 Estados
- [✅] 111 Ciudades
- [✅] 5 Políticas impuestos
- [✅] Demo catálogo

### **Testing:**
- [✅] API probada
- [✅] Migraciones aplicadas
- [✅] Catálogo cargado

---

## 🎯 **CONVENCIONES**

✅ FKs como string ('app.Model')  
✅ AuditMixin respetado  
✅ KPIs: solo fecha_emision  
✅ Chile: IVA 19% solo repuestos  
✅ USA: sales tax por ubicación  

---

## 🎉 **RESUMEN**

**5 países completos** | **9 modelos nuevos** | **1 API unificada** | **1 JS reutilizable** | **Production Ready** ✅

---

**¿Preguntas?** Ver documentación completa en archivos `.md`

