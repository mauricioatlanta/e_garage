# 🚀 ACTIVAR GOOGLE ANALYTICS 4 - GUÍA PASO A PASO

## 📋 **Instrucciones para activar Analytics hoy mismo**

### **1. Crear cuenta de Google Analytics 4**
1. Ve a: https://analytics.google.com/
2. Clic en "Empezar a usar Analytics"
3. Inicia sesión con tu cuenta de Google

### **2. Configurar cuenta**
- **Nombre de cuenta**: `eGarage Analytics`
- **País**: `Chile`
- **Configuración de datos**: Acepta los términos

### **3. Crear propiedad**
- **Nombre de propiedad**: `eGarage Landing`
- **Zona horaria**: `(GMT-3:00) Santiago`
- **Moneda**: `Peso chileno (CLP)`

### **4. Configurar flujo de datos**
- **Plataforma**: Web
- **URL del sitio web**:
  - Desarrollo: `http://127.0.0.1:8000`
  - Producción: `https://tudominio.com`
- **Nombre del stream**: `eGarage Landing Page`

### **5. Obtener ID de medición**
Después de crear el flujo de datos, obtendrás un ID que se ve así:
```
G-XXXXXXXXXX
```

### **6. REEMPLAZAR en el código**
En el archivo `templates/landing_egarage.html`, busca y reemplaza:

**BUSCAR:**
```javascript
gtag('config', 'G-EGARAGE2025', {
```

**REEMPLAZAR CON:**
```javascript
gtag('config', 'TU_ID_REAL_AQUI', {
```

**TAMBIÉN BUSCAR:**
```javascript
'send_to': 'G-EGARAGE2025/CONVERSION_ID'
```

**REEMPLAZAR CON:**
```javascript
'send_to': 'TU_ID_REAL_AQUI/CONVERSION_ID'
```

### **7. Configurar conversiones en GA4**
En Google Analytics:
1. Ve a **Administrar** > **Conversiones**
2. Clic en **Crear evento de conversión**
3. Agrega estos eventos como conversiones:
   - `form_submission`
   - `plan_selection`
   - `generate_lead`

### **8. Verificar funcionamiento**
1. Guarda los cambios
2. Recarga la página: http://127.0.0.1:8000/egarage/
3. En GA4, ve a **Informes en tiempo real**
4. Deberías ver tu visita en tiempo real

## 📊 **Eventos que se rastrean automáticamente:**

### **🎯 Conversiones principales:**
- ✅ Envío de formulario de contacto
- ✅ Selección de plan de precios
- ✅ Generación de leads

### **🔍 Interacciones:**
- ✅ Clics en botones de WhatsApp
- ✅ Navegación entre secciones
- ✅ Scroll hasta arriba
- ✅ Redirección a login

### **💰 eCommerce tracking:**
- ✅ Productos (planes) agregados al carrito
- ✅ Valores en pesos chilenos (CLP)
- ✅ Categorización por tipo de plan

## 🚨 **IMPORTANTE:**
- Reemplaza `G-EGARAGE2025` con tu ID real
- Configura las conversiones en GA4
- Prueba en tiempo real antes de ir a producción

## 📈 **Métricas clave que verás:**
- Visitantes únicos
- Conversiones por plan
- Fuentes de tráfico
- Tiempo en página
- Abandono de formularios
- ROI por canal de marketing

¡Analytics estará funcionando en 5 minutos! 🎉
