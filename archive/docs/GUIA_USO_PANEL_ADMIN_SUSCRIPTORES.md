# 📊 Guía de Uso - Panel de Administración de Suscriptores

**Fecha**: 2025-01-27  
**Versión**: 1.0

---

## 🎯 OBJETIVO

Este panel te permite gestionar todos los suscriptores de eGarage de forma centralizada, extender suscripciones como gesto de fidelización y mantener un registro completo de todas las acciones.

---

## 🚀 ACCESO AL PANEL

### **URL**: `/admin/suscriptores/`

### **Requisitos**:
- Usuario debe ser `staff=True` o `is_superuser=True`
- Acceso restringido solo para administradores

---

## 📋 FUNCIONALIDADES DEL PANEL

### **1. Visualización de Suscriptores**

El panel muestra una tabla completa con:

| Columna | Descripción | Fuente |
|---------|-------------|--------|
| **Empresa** | Nombre del taller + teléfono | `empresa.nombre_taller`, `empresa.telefono` |
| **País** | Código de país | `empresa.pais` (CL, US, MX, PE, CO, EC, BR, VE) |
| **Email** | Email del usuario | `empresa.user.email` |
| **Plan** | Tipo de plan | `empresa.plan` (trial, basic, premium, etc.) |
| **Días Restantes** | Días hasta vencimiento | `empresa.dias_restantes` (cálculo automático) |
| **Status** | Estado visual | `empresa.estado_suscripcion` |
| **Vencimiento** | Fecha de expiración | `empresa.fecha_fin` |
| **Acciones** | Botones de acción | Extender, Ver detalle |

---

### **2. Estados Visuales**

El panel muestra estados con colores según la propiedad `estado_suscripcion`:

#### **🟢 Activa (Verde)**
- **Condición**: Más de 5 días restantes
- **Visualización**: `✅ Activa` (fondo verde)
- **Significado**: Suscripción funcionando normalmente

#### **🟡 Advertencia (Naranja/Amarillo)**
- **Condición**: Entre 1 y 5 días restantes
- **Visualización**: `⚠️ Advertencia` (fondo amarillo)
- **Significado**: Vencimiento próximo, considerar renovación

#### **🔴 Crítico (Rojo)**
- **Condición**: 1 día o menos (pero no vencido)
- **Visualización**: `🔴 Crítico` (fondo rojo)
- **Significado**: Vencimiento inminente

#### **⚫ Vencida (Gris)**
- **Condición**: Fecha de fin ya pasada (`debe_bloquear=True`)
- **Visualización**: `❌ Vencida` (fondo gris)
- **Significado**: Suscripción expirada

---

### **3. Filtros Disponibles**

#### **Filtro por País**
- Selecciona un país específico (CL, US, MX, PE, CO, EC, BR, VE)
- Muestra solo suscriptores de ese país
- Útil para gestión regional

#### **Filtro por Status**
- **Activa**: Solo suscripciones activas
- **Vencida**: Solo suscripciones vencidas
- **Trial**: Solo planes de prueba

#### **Filtro por Días Restantes**
- **Crítico (≤1 día)**: Suscriptores que vencen hoy o mañana
- **Advertencia (≤5 días)**: Suscriptores que vencen en menos de 5 días
- **Vencido**: Suscriptores ya vencidos

#### **Búsqueda**
- Busca por nombre de taller, email o teléfono
- Búsqueda parcial (no necesita coincidencia exacta)

---

### **4. Extensión de Suscripciones**

#### **Cómo Extender**:
1. Clic en botón "⏱️ Extender" en la fila del suscriptor
2. Se abre un modal
3. Seleccionar meses: **1, 6 o 12 meses** (solo estas opciones)
4. Opción de enviar notificación (marcada por defecto)
5. Clic en "✅ Extender"

#### **Qué Sucede**:
1. ✅ Sistema ejecuta `admin_grant_courtesy_extension()`
2. ✅ Calcula días según meses (30, 180, 365)
3. ✅ Actualiza fecha de vencimiento
4. ✅ Activa suscripción si estaba vencida
5. ✅ Registra en auditoría con razón "Cortesía eGarage"
6. ✅ Envía email al cliente
7. ✅ Envía WhatsApp al cliente
8. ✅ Sincroniza con modelo `Suscripcion`
9. ✅ Muestra confirmación

#### **Mensaje Enviado al Cliente**:

**WhatsApp**:
```
🚀 *¡Hola [Nombre del Taller]!*

Queremos agradecerte por formar parte de la familia eGarage. Como gesto de agradecimiento por pertenecer a nuestro equipo, hemos extendido tu suscripción por [Meses] mes(es).

📅 Nueva fecha de vencimiento: [Fecha]

¡Es un gusto tenerte con nosotros! 🙏
```

**Email**:
```
¡Hola [Nombre del Taller]! 🚀

Queremos agradecerte por formar parte de la familia eGarage. Como gesto de agradecimiento por pertenecer a nuestro equipo, hemos extendido tu suscripción por [Meses] mes(es).

📅 Nueva fecha de vencimiento: [Fecha]

¡Es un gusto tenerte con nosotros!

Saludos,
Equipo eGarage
```

---

### **5. Estadísticas del Panel**

El panel muestra:

- **Total Empresas**: Todas las empresas registradas
- **Activas**: Empresas con `suscripcion_activa=True`
- **Vencidas**: Empresas con `suscripcion_activa=False`
- **Críticas (<5 días)**: Empresas con menos de 5 días restantes
- **Estadísticas por País**: Total, activas, vencidas por cada país

---

## 🔒 SEGURIDAD Y AUDITORÍA

### **Auditoría Automática**

Cada extensión se registra en `LogAuditoria` con:

- **Usuario Admin**: Quién ejecutó la acción
- **Empresa**: A quién se le otorgó la cortesía
- **Acción**: "UPDATE"
- **Modelo**: "EMPRESA"
- **Descripción**: Detalles completos de la extensión
- **Razón**: "Cortesía eGarage - Extendido por [admin_username]"
- **Datos Antes/Después**: Estado completo antes y después

### **Protección contra Fraude**

- ✅ **`trial_already_used`**: El sistema verifica si el email o teléfono ya usaron trial
- ✅ **Validación de duraciones**: Solo permite 1, 6 o 12 meses
- ✅ **Acceso restringido**: Solo staff/admin puede acceder
- ✅ **Registro completo**: Todas las acciones quedan registradas

### **Notificación Interna**

Cuando se otorga una cortesía, el sistema envía un WhatsApp al administrador con:

```
🚨 AUDITORÍA - CORTESÍA APROBADA
✅ Extensión de plan ejecutada por Admin.
👤 USUARIO: [email]
🎁 DURACIÓN: [X] Meses
📜 RAZÓN: Cortesía eGarage - Extendido por [admin]
📅 NUEVA FECHA FIN: [fecha]
```

---

## 📊 EJEMPLO DE USO COMPLETO

### **Escenario**: Extender suscripción de "Taller Los Ángeles" (Chile) por 6 meses

1. **Acceder al panel**: `/admin/suscriptores/`
2. **Filtrar por país**: Seleccionar "CL" (Chile)
3. **Buscar empresa**: Buscar "Taller Los Ángeles"
4. **Ver estado**: 
   - Días restantes: 3 días
   - Status: ⚠️ Advertencia (naranja)
5. **Extender**:
   - Clic en "⏱️ Extender"
   - Seleccionar "6 meses"
   - Marcar "Enviar notificación"
   - Clic en "✅ Extender"
6. **Resultado**:
   - ✅ Suscripción extendida 180 días
   - ✅ Nueva fecha: 15/07/2025
   - ✅ Status actualizado a "✅ Activa"
   - ✅ Email enviado a `taller@example.com`
   - ✅ WhatsApp enviado a `+56912345678`
   - ✅ Registrado en auditoría
   - ✅ Notificación interna al admin

---

## 🎨 INTERFAZ VISUAL

### **Colores y Estilos**:

- **Fondo de fila**: Cambia según estado (rojo para crítico, amarillo para advertencia, gris para vencido)
- **Badges de status**: Colores distintivos para cada estado
- **Días restantes**: Color según urgencia (verde, amarillo, rojo, gris)
- **Botones**: Estilo futurista consistente con el diseño de eGarage

---

## 📝 NOTAS IMPORTANTES

### **Limitaciones**:
- Solo se pueden extender 1, 6 o 12 meses (según `admin_grant_courtesy_extension()`)
- WhatsApp solo se envía si la empresa tiene teléfono registrado
- Email puede fallar si el servidor SMTP no está configurado (pero no bloquea la extensión)

### **Mejores Prácticas**:
- Revisar estado antes de extender
- Usar razón descriptiva en auditoría
- Verificar que las notificaciones llegaron
- Monitorear logs para errores

---

## 🧪 PRUEBAS RECOMENDADAS

1. **Filtros**: Probar todos los filtros combinados
2. **Extensión**: Extender con 1, 6 y 12 meses
3. **Notificaciones**: Verificar que llegan email y WhatsApp
4. **Auditoría**: Verificar que se registra correctamente
5. **Estados**: Verificar que los colores cambian correctamente
6. **Búsqueda**: Probar búsqueda por nombre, email, teléfono

---

## 🆘 SOLUCIÓN DE PROBLEMAS

### **No puedo acceder al panel**:
- Verificar que el usuario es `staff=True` o `is_superuser=True`
- Verificar la URL: `/admin/suscriptores/`

### **No se envían notificaciones**:
- Verificar configuración de email en `settings.py`
- Verificar configuración de WhatsApp
- Revisar logs para errores

### **Error al extender**:
- Verificar que los meses sean 1, 6 o 12
- Verificar que la empresa existe
- Revisar logs para detalles del error

---

**Documentación creada por**: AI Assistant  
**Última actualización**: 2025-01-27

