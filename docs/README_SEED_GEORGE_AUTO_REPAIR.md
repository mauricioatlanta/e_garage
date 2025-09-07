# 🌟 Seed GEORGE AUTO REPAIR - Comando Django

## 📋 Descripción

Comando de Django para poblar automáticamente la empresa **GEORGE AUTO REPAIR** con datos de prueba completos y realistas.

## 🚀 Cómo Ejecutar

### Comando Básico
```bash
python manage.py seed_george_auto_repair --company "GEORGE AUTO REPAIR"
```

### Con Parámetros Personalizados
```bash
# Más clientes y documentos
python manage.py seed_george_auto_repair --company "GEORGE AUTO REPAIR" --clients 15 --docs 20

# Solo algunos repuestos
python manage.py seed_george_auto_repair --company "GEORGE AUTO REPAIR" --parts 10

# Más clientes con múltiples vehículos
python manage.py seed_george_auto_repair --company "GEORGE AUTO REPAIR" --extra-vehicle-clients 5
```

## 📊 Datos Creados

### 👥 Clientes (10 por defecto)
- **3 clientes** con **2-3 vehículos** cada uno
- **7 clientes** con **1 vehículo** cada uno
- Nombres realistas: George Brown, Anna Smith, Mike Johnson, etc.
- IDs fiscales (RUT/EIN) según el modelo

### 🚗 Vehículos
- **Marcas populares**: Toyota, Honda, Ford, Chevrolet, Nissan, Hyundai, Kia
- **Modelos realistas**: Corolla, Civic, F-150, Silverado, etc.
- **Patentes**: Formato GT-XXX-XX
- **VINs**: Formato estándar de 17 caracteres

### 🔧 Repuestos (15 por defecto)
- **Proveedores**: AutoZone y NAPA
- **Tipos**: Filtros, pastillas, baterías, aceites, sensores, etc.
- **Precios**: Compra y venta realistas
- **Part Numbers**: Formato AZ-XXXXXX o NA-XXXXXX

### 📄 Documentos (10 por defecto)
- **Tipos**: Presupuesto, Orden de Trabajo, Factura, Boleta, etc.
- **Cada documento incluye**:
  - **2-4 líneas de repuestos**
  - **2-3 líneas de servicios**
  - **2-3 líneas de otros servicios**
- **Fechas**: Últimos 40 días
- **Técnico responsable**: "Test Tech"

### 🛒 Compras (2 por defecto)
- **AutoZone**: Compra con repuestos de AutoZone
- **NAPA**: Compra con repuestos de NAPA
- **Detalles**: Cantidad, precio unitario, subtotal
- **Totales**: Calculados automáticamente

## ⚙️ Parámetros Disponibles

| Parámetro | Descripción | Valor por Defecto |
|-----------|-------------|-------------------|
| `--company` | Nombre de la empresa | "GEORGE AUTO REPAIR" |
| `--clients` | Número de clientes | 10 |
| `--extra-vehicle-clients` | Clientes con múltiples vehículos | 3 |
| `--parts` | Número de repuestos | 15 |
| `--docs` | Número de documentos | 10 |

## 🔧 Características Técnicas

### ✅ Multi-Tenant
- Todos los datos se crean para la empresa especificada
- Respeta el aislamiento de datos entre empresas

### ✅ Detección Dinámica
- Detecta automáticamente campos disponibles en los modelos
- Se adapta a diferentes esquemas de base de datos
- No falla si faltan campos opcionales

### ✅ Transaccional
- Usa `@transaction.atomic` para consistencia
- Si algo falla, se revierte todo

### ✅ Reutilizable
- Usa `get_or_create` para evitar duplicados
- Se puede ejecutar múltiples veces sin problemas

## 📁 Estructura de Archivos

```
taller/management/commands/
└── seed_george_auto_repair.py  # Comando principal
```

## 🎯 Casos de Uso

### 1. Desarrollo Local
```bash
# Poblar base de datos de desarrollo
python manage.py seed_george_auto_repair
```

### 2. Demostración
```bash
# Crear más datos para demo
python manage.py seed_george_auto_repair --clients 20 --docs 30
```

### 3. Testing
```bash
# Datos mínimos para tests
python manage.py seed_george_auto_repair --clients 5 --parts 8 --docs 5
```

## 🔍 Verificación

Después de ejecutar el comando, puedes verificar los datos:

### En Django Admin
- Ve a `/admin/`
- Navega por Clientes, Vehículos, Repuestos, Documentos

### En la Aplicación
- Ve a la lista de clientes
- Revisa los documentos creados
- Verifica las compras en el módulo correspondiente

## 🚨 Notas Importantes

1. **Empresa Requerida**: La empresa "GEORGE AUTO REPAIR" debe existir antes de ejecutar
2. **Permisos**: Asegúrate de tener permisos para crear datos
3. **Backup**: Considera hacer backup antes de ejecutar en producción
4. **Espacio**: Los datos ocupan espacio en la base de datos

## 🐛 Solución de Problemas

### Error: "No se encontró la Empresa"
```bash
# Verifica que la empresa existe
python manage.py shell
>>> from taller.models import Empresa
>>> Empresa.objects.filter(nombre_publico__icontains="GEORGE").values_list('nombre_publico', flat=True)
```

### Error: "Campo no encontrado"
- El comando detecta automáticamente los campos disponibles
- Si falla, verifica que los modelos estén importados correctamente

### Error: "Permisos insuficientes"
- Asegúrate de que el usuario tenga permisos de escritura en la base de datos

## 📈 Personalización

Para personalizar los datos generados, edita las funciones en el archivo:

- `pick_brand_model()`: Cambiar marcas y modelos
- `ensure_repuestos()`: Modificar tipos de repuestos
- `create_clientes_y_vehiculos()`: Ajustar nombres y datos de clientes

## 🎉 ¡Listo!

Con este comando tendrás una base de datos completamente poblada para **GEORGE AUTO REPAIR** con datos realistas y funcionales. ¡Perfecto para desarrollo, testing y demostraciones!
