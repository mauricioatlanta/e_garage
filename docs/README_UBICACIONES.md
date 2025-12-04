# 🌎 Sistema de Ubicaciones Multi-País

> **Un sistema completo para manejar ubicaciones geográficas en 8 países de LATAM y USA**

---

## 🎯 ¿Qué es esto?

Un sistema de **ubicaciones geográficas normalizado** que permite:

- ✅ Gestionar **países, estados/regiones, y ciudades** de forma unificada
- ✅ Soportar **8 países** (Chile, USA, Brasil, México, Perú, Venezuela, Colombia, Ecuador)
- ✅ Pre-cargar **~800 ciudades** principales de cada país
- ✅ Agregar ubicaciones nuevas desde formularios
- ✅ Usar estándares internacionales (**ISO 3166-1 alpha-2**)

---

## 🗺️ ARQUITECTURA VISUAL

```
                    🌎 MULTI-PAÍS
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
    🇨🇱 Chile        🇺🇸 USA           🇧🇷 Brasil
    🇲🇽 México       🇵🇪 Perú          🇻🇪 Venezuela
    🇨🇴 Colombia     🇪🇨 Ecuador


┌─────────────────────────────────────────────────────────────┐
│                     PAÍS (ISO 3166-1)                        │
│  CL • US • BR • MX • PE • VE • CO • EC                       │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              ESTADO / REGIÓN / DEPARTAMENTO                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │ 🇨🇱 RM        │  │ 🇺🇸 CA        │  │ 🇧🇷 SP        │       │
│  │ Región        │  │ California   │  │ São Paulo    │       │
│  │ Metropolitana │  │              │  │              │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
│                                                               │
│  Propiedades: codigo, nombre, pais, sales_tax, timezone      │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                        CIUDAD                                │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐             │
│  │ Santiago   │  │ Los Angeles│  │ São Paulo  │             │
│  │ (RM, CL)   │  │ (CA, US)   │  │ (SP, BR)   │             │
│  └────────────┘  └────────────┘  └────────────┘             │
│                                                               │
│  Propiedades: nombre, estado_fk, población, coordenadas      │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                    ADDRESS (Dirección)                       │
│  ┌───────────────────────────────────────────────────┐       │
│  │  line1: "Av. Providencia 123"                     │       │
│  │  line2: "Oficina 456"                             │       │
│  │  city: Santiago (RM, CL)                          │       │
│  │  postal_code: "7500000"                           │       │
│  └───────────────────────────────────────────────────┘       │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                      CLIENTE                                 │
│  ┌───────────────────────────────────────────────────┐       │
│  │  nombre: "Juan Pérez"                             │       │
│  │  billing_address: ───→ Address                    │       │
│  │  shipping_address: ──→ Address (opcional)         │       │
│  └───────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────┘
```

---

## 📊 COBERTURA DE PAÍSES

| Bandera | País | ISO | División L1 | Cantidad | Ciudades | IVA/Tax |
|---------|------|-----|-------------|----------|----------|---------|
| 🇨🇱 | Chile | CL | Regiones | 16 | ~100 | 19% |
| 🇺🇸 | USA | US | States | 51 | ~300 | Varía |
| 🇧🇷 | Brasil | BR | Estados | 27 | ~100 | ICMS/ISS |
| 🇲🇽 | México | MX | Estados | 32 | ~60 | 16% |
| 🇵🇪 | Perú | PE | Departamentos | 25 | ~50 | 18% |
| 🇻🇪 | Venezuela | VE | Estados | 24 | ~40 | 16% |
| 🇨🇴 | Colombia | CO | Departamentos | 33 | ~60 | 19% |
| 🇪🇨 | Ecuador | EC | Provincias | 24 | ~40 | 12% |

**📈 Totales:** 208 divisiones administrativas • ~800+ ciudades principales

---

## 🚀 INICIO RÁPIDO (3 comandos)

```bash
# 1️⃣ Cargar todas las ubicaciones
python manage.py cargar_todas_ubicaciones

# 2️⃣ Verificar que todo está bien
python manage.py verificar_ubicaciones

# 3️⃣ Migrar datos legacy (si aplica)
python manage.py backfill_addresses
```

**⏱️ Tiempo total:** 2-5 minutos

---

## 📚 DOCUMENTACIÓN

### **Documentos principales:**

1. **[📖 Arquitectura Completa](ARQUITECTURA_UBICACIONES_MULTI_PAIS.md)**  
   Documentación técnica detallada con toda la arquitectura, decisiones de diseño, y ejemplos de código.

2. **[⚡ Guía Rápida](GUIA_RAPIDA_UBICACIONES.md)**  
   Tutorial paso a paso con ejemplos prácticos de uso en formularios, AJAX, y queries.

3. **[📋 Resumen Ejecutivo](RESUMEN_ARQUITECTURA_UBICACIONES.md)**  
   Overview de alto nivel con métricas, casos de uso, y checklist de deployment.

### **Guías específicas:**

- **Cómo agregar un país nuevo:** Ver [Arquitectura Completa - Sección 5](ARQUITECTURA_UBICACIONES_MULTI_PAIS.md#5%EF%B8%8F%E2%83%A3-carga-de-datos)
- **Cómo usar en formularios:** Ver [Guía Rápida - Sección 4](GUIA_RAPIDA_UBICACIONES.md#%EF%B8%8F-uso-en-formularios)
- **Cómo migrar datos legacy:** Ver [Arquitectura Completa - Sección 4](ARQUITECTURA_UBICACIONES_MULTI_PAIS.md#4%EF%B8%8F%E2%83%A3-migraci%C3%B3n-desde-legacy)

---

## 🎓 EJEMPLOS PRÁCTICOS

### **Ejemplo 1: Obtener estados de un país**

```python
from taller.models.ubicacion import Estado

# Obtener todos los estados de Colombia
estados_colombia = Estado.objects.filter(pais="CO").order_by("nombre")

for estado in estados_colombia:
    print(f"{estado.codigo}: {estado.nombre}")
    # DC: Distrito Capital de Bogotá
    # ANT: Antioquia
    # ...
```

### **Ejemplo 2: Crear cliente con dirección**

```python
from taller.models.clientes import Cliente
from taller.models.ubicacion import Ciudad
from ubicacion.models import Address

# Obtener ciudad
ciudad = Ciudad.objects.get(
    nombre="Quito",
    estado__pais="EC"
)

# Crear dirección
address = Address.objects.create(
    line1="Av. 6 de Diciembre N36-109",
    city=ciudad,
    postal_code="170102"
)

# Crear cliente
cliente = Cliente.objects.create(
    nombre="María",
    apellido="González",
    billing_address=address,
    empresa=empresa
)

# Acceder al país desde el cliente
print(cliente.billing_address.pais)  # "EC"
```

### **Ejemplo 3: Filtrar clientes por país**

```python
# Clientes de Ecuador
clientes_ecuador = Cliente.objects.filter(
    billing_address__city__estado__pais="EC"
).select_related("billing_address__city__estado")

for cliente in clientes_ecuador:
    print(f"{cliente.nombre} - {cliente.billing_address.city.nombre}")
```

---

## 🛠️ COMANDOS DISPONIBLES

### **Carga de Datos**

```bash
# Cargar TODOS los países
python manage.py cargar_todas_ubicaciones

# Cargar países específicos
python manage.py cargar_todas_ubicaciones --paises CL CO EC

# Cargar país individual
python manage.py cargar_estados_chile
python manage.py cargar_estados_colombia
python manage.py cargar_estados_ecuador
python manage.py cargar_estados_usa
python manage.py cargar_estados_brasil
python manage.py cargar_estados_mexico
python manage.py cargar_estados_peru
python manage.py cargar_estados_venezuela
```

### **Verificación**

```bash
# Resumen general
python manage.py verificar_ubicaciones

# Ver solo Colombia
python manage.py verificar_ubicaciones --pais CO

# Con detalle completo
python manage.py verificar_ubicaciones --detallado
```

### **Migración Legacy**

```bash
# Preview (sin hacer cambios)
python manage.py backfill_addresses --dry-run

# Ejecutar migración
python manage.py backfill_addresses
```

---

## 🔍 CASOS DE USO COMUNES

### **1. Select dinámico Estado → Ciudad en formulario**

```javascript
// Cuando cambia el estado, cargar ciudades
$("#id_estado").on("change", function() {
    const estadoId = $(this).val();
    
    $.get("/api/ciudades/", { estado_id: estadoId }, function(ciudades) {
        const $select = $("#id_ciudad").empty();
        $select.append('<option value="">Seleccione ciudad</option>');
        
        ciudades.forEach(ciudad => {
            $select.append(`<option value="${ciudad.id}">${ciudad.nombre}</option>`);
        });
    });
});
```

### **2. Agregar ciudad nueva on-the-fly**

```python
# Desde formulario o endpoint
from taller.models.ubicacion import Estado, Ciudad

estado = Estado.objects.get(pais="CO", codigo="ANT")  # Antioquia
ciudad, created = Ciudad.objects.get_or_create(
    estado=estado,
    nombre="Envigado"
)

if created:
    print("✅ Ciudad creada")
```

### **3. Dashboard de clientes por país**

```python
from django.db.models import Count
from taller.models.clientes import Cliente

# Contar clientes por país
stats = Cliente.objects.filter(
    billing_address__isnull=False
).values(
    "billing_address__city__estado__pais"
).annotate(
    total=Count("id")
).order_by("-total")

for stat in stats:
    pais = stat["billing_address__city__estado__pais"]
    total = stat["total"]
    print(f"{pais}: {total} clientes")
```

---

## ⚙️ CONFIGURACIÓN

### **Agregar un país nuevo**

1. Agregar a `Estado.pais` choices en `taller/models/ubicacion.py`:
```python
choices=[
    # ... existentes ...
    ("AR", "Argentina"),  # Nuevo
]
```

2. Crear comando de carga:
```python
# taller/management/commands/cargar_estados_argentina.py
class Command(BaseCommand):
    help = "Carga provincias de Argentina"
    # ... (ver ejemplos existentes)
```

3. Ejecutar:
```bash
python manage.py cargar_estados_argentina
```

---

## 🎯 BENEFICIOS

### **Para Desarrolladores:**
- ✅ **API consistente** para todos los países
- ✅ **Comandos idempotentes** (ejecutar múltiples veces sin problemas)
- ✅ **Documentación completa** con ejemplos
- ✅ **Migración gradual** sin romper código existente

### **Para el Negocio:**
- ✅ **Expansión rápida** a nuevos países (solo agregar datos)
- ✅ **Reportes precisos** por ubicación geográfica
- ✅ **Cálculo correcto** de impuestos por estado/ciudad
- ✅ **Mapas y geolocalización** (coordenadas incluidas)

### **Para Usuarios:**
- ✅ **Formularios intuitivos** con selects dinámicos
- ✅ **Agregar ubicaciones** si no existen
- ✅ **Validación** de direcciones por país

---

## 🔗 RECURSOS EXTERNOS

- **ISO 3166-1 (Códigos de país):** https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2
- **ISO 3166-2 (Subdivisiones):** https://en.wikipedia.org/wiki/ISO_3166-2
- **Divisiones administrativas por país:** https://en.wikipedia.org/wiki/Table_of_administrative_divisions_by_country

---

## ✅ CHECKLIST DE IMPLEMENTACIÓN

### **Para desarrollar:**
- [x] ✅ Modelos de datos creados (`Estado`, `Ciudad`, `Address`)
- [x] ✅ Comandos de carga para 8 países
- [x] ✅ Comando maestro `cargar_todas_ubicaciones`
- [x] ✅ Comando de verificación `verificar_ubicaciones`
- [x] ✅ Documentación completa
- [ ] ⏳ Tests unitarios
- [ ] ⏳ Actualizar formularios de cliente

### **Para deployment:**
- [ ] ⏳ Ejecutar `cargar_todas_ubicaciones` en staging
- [ ] ⏳ Verificar con `verificar_ubicaciones`
- [ ] ⏳ Ejecutar `backfill_addresses` para migrar legacy
- [ ] ⏳ Validar migración
- [ ] ⏳ Deployment a producción
- [ ] ⏳ Monitoreo post-deployment

---

## 📞 SOPORTE

### **¿Tienes preguntas?**

1. **📖 Lee primero:** [Guía Rápida](GUIA_RAPIDA_UBICACIONES.md)
2. **🔍 Consulta:** [Arquitectura Completa](ARQUITECTURA_UBICACIONES_MULTI_PAIS.md)
3. **🐛 Debugging:** Ejecuta `python manage.py verificar_ubicaciones --detallado`

### **Problemas comunes:**

| Problema | Solución |
|----------|----------|
| "No hay estados/ciudades" | Ejecutar `cargar_todas_ubicaciones` |
| "Ciudad no existe" | Agregar con `Ciudad.objects.create()` o desde formulario |
| "Clientes sin billing_address" | Ejecutar `backfill_addresses` |
| "Query lento" | Usar `select_related("city__estado")` |

---

## 🎉 ¡Listo para usar!

```bash
# Un solo comando para empezar:
python manage.py cargar_todas_ubicaciones

# Ver el resultado:
python manage.py verificar_ubicaciones
```

**¡Disfruta de tu sistema de ubicaciones multi-país!** 🌎🚀

