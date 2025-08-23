# 🇺🇸 Cuenta de Prueba USA - Credenciales y Datos

## 🔑 **CREDENCIALES DE ACCESO**

### **Cuenta de Prueba USA**
```
Username: testuser_usa
Password: TestUSA2025!
Email: testuser@usa-garage.com
Country: USA (United States)
Company: USA Test Garage
```

### **URLs de Acceso**
- **Login USA**: http://127.0.0.1:8000/us/accounts/login/
- **Dashboard USA**: http://127.0.0.1:8000/us/
- **Documents USA**: http://127.0.0.1:8000/us/documentos/
- **Create Document**: http://127.0.0.1:8000/us/documentos/nuevo/

---

## 📊 **DATOS GENERADOS PARA USA**

### 📋 **Documentos por Tipo**
- **Presupuestos**: 10 documentos (US-PRE-xxxxx)
- **Órdenes de Trabajo**: 10 documentos (US-ORD-xxxxx)
- **Facturas**: 10 documentos (US-FAC-xxxxx)
- **TOTAL**: **30 documentos**

### 🔧 **Contenido de Documentos**
- **Repuestos en documentos**: 91 líneas
- **Servicios en documentos**: 64 líneas
- **Otros servicios**: 20 líneas
- **Repuestos disponibles**: 12 tipos

---

## 👥 **DATOS MAESTROS USA**

### **Clientes**: 8 customers
```
- Robert Anderson (robert.anderson@email.com)
- Jennifer Davis (jennifer.davis@email.com)
- Michael Wilson (michael.wilson@email.com)
- Lisa Martinez (lisa.martinez@email.com)
- David Taylor (david.taylor@email.com)
- Ashley Brown (ashley.brown@email.com)
- James Garcia (james.garcia@email.com)
- Emily Rodriguez (emily.rodriguez@email.com)
```

### **Vehículos**: 8 vehicles
```
- ABC1234 (2020), DEF5678 (2019), GHI9012 (2021)
- JKL3456 (2018), MNO7890 (2022), PQR1357 (2017)
- STU2468 (2020), VWX9753 (2019)
```

### **Técnicos**: 3 technicians
```
- John Smith (+1-555-111-2222)
- Sarah Johnson (+1-555-333-4444)
- Mike Williams (+1-555-555-6666)
```

---

## 🔧 **REPUESTOS USA (Precios en USD)**

### **Catálogo de Partes**
```
US-FLT001: Oil Filter Toyota           ($15.00)
US-FLT002: Air Filter Honda           ($22.00)
US-FLT003: Fuel Filter Universal      ($28.00)
US-BRK001: Front Brake Pads           ($45.00)
US-BRK002: Rear Brake Pads            ($38.00)
US-OIL001: Motor Oil 5W30 4Q          ($32.00)
US-SPK001: NGK Platinum Spark Plugs   ($12.00)
US-TIR001: Tire 185/65R15             ($95.00)
US-BAT001: 12V 70Ah Battery           ($145.00)
US-LMP001: H4 LED Bulb                ($18.00)
US-BEL001: Timing Belt                ($68.00)
US-FLU001: DOT4 Brake Fluid           ($25.00)
```

---

## 🏪 **INFRAESTRUCTURA USA**

### **Tienda Configurada**
```
Name: USA Main Parts Store
Address: 456 Parts Avenue, New York, NY 10002
Phone: +1-555-PARTS-1
Email: parts@usa-garage.com
Status: Active
```

### **Empresa Configurada**
```
Company: USA Test Garage LLC
Address: 123 Main Street, New York, NY 10001
Phone: +1-555-123-4567
Email: testuser@usa-garage.com
Country: US (United States)
Timezone: America/New_York (Eastern Time)
```

---

## 💰 **CARACTERÍSTICAS DE PRECIOS USA**

### **Repuestos** (en centavos para sistema)
- Rango: $12.00 - $145.00 USD
- Sistema almacena: 1200 - 14500 centavos

### **Servicios**
- Rango: $10.00 - $80.00 USD  
- Prefijo: "USA -" en nombres de servicios

### **Otros Servicios**
- Cliente: $50.00 - $150.00 USD
- Costo interno: $30.00 - $100.00 USD
- Empresas externas USA:
  - Advanced Auto Services LLC
  - Premium Garage Solutions
  - NYC Auto Specialists Inc
  - Metropolitan Car Care

---

## 🧪 **CASOS DE PRUEBA DISPONIBLES**

### **Documentos con Numeración USA**
- Prefijo "US-" en todos los números de documento
- Formato: US-PRE-xxxxx, US-ORD-xxxxx, US-FAC-xxxxx

### **Datos Multipaís**
- Clientes con nombres en inglés
- Direcciones formato USA
- Teléfonos formato +1-555-xxx-xxxx
- Zona horaria Eastern Time

### **Empresas Externas USA**
- Nombres típicos estadounidenses
- Servicios subcontratados locales

---

## ✅ **VALIDACIONES A REALIZAR**

### **Funcionalidades USA vs Chile**
- ✅ Login independiente por país
- ✅ Datos segregados por empresa
- ✅ Numeración diferenciada (US- vs PRE-)
- ✅ Precios en formato correcto
- ✅ Zona horaria configurada
- ✅ Catálogo de repuestos independiente

### **Reportes a Probar**
- 📊 Reportes por país (USA vs CL)
- 💰 Cálculos en USD vs CLP
- 📈 Analytics por región
- 🏪 Inventarios segregados
- 👥 Clientes por país

---

## 🌐 **COMPARACIÓN DE CUENTAS**

| Característica | Chile (mauricio1) | USA (testuser_usa) |
|---|---|---|
| **Username** | mauricio1 | testuser_usa |
| **Company** | Taller de mauricio1 | USA Test Garage |
| **Country** | CL | US |
| **Documents** | 64 | 30 |
| **Customers** | 8 | 8 |
| **Vehicles** | 8 | 8 |
| **Parts** | 12 | 12 |
| **Technicians** | 2 | 3 |
| **Prefix** | PRE-, ORD-, FAC- | US-PRE-, US-ORD-, US-FAC- |
| **Language** | Spanish | English |
| **Timezone** | Chile/Santiago | America/New_York |

---

## 🚀 **PRÓXIMOS PASOS PARA TESTING**

### **Acceso a Cuenta USA**
1. Ir a: http://127.0.0.1:8000/us/accounts/login/
2. Login: `testuser_usa` / `TestUSA2025!`
3. Verificar dashboard USA
4. Probar lista de documentos (30 docs)
5. Crear documento nuevo
6. Probar reportes USA

### **Testing Multi-País**
1. **Segregación de datos**: Verificar que USA no ve datos de Chile
2. **Reportes independientes**: Cada país debe mostrar solo sus datos
3. **Numeración**: Verificar prefijos US- vs sin prefijo
4. **Precios**: Verificar formato USD vs CLP
5. **Zona horaria**: Verificar reportes con hora local

### **Validar Funcionalidades**
- 🔄 Cambio entre países (/cl/ vs /us/)
- 📊 Reportes segregados por país
- 💰 Cálculos correctos por moneda
- 🏪 Inventarios independientes
- 👥 Gestión de clientes por región

¡**Ambas cuentas están listas para testing completo multi-país!** 🌍
