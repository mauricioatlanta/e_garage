# 🇺🇸 CREDENCIALES DE PRUEBA USA - COPIAS LOCALES

## ✅ USUARIO CREADO EXITOSAMENTE

El usuario de prueba para USA ha sido creado en tu copia local (PC). Ahora puedes acceder al sistema.

---

## 🔑 CREDENCIALES DE ACCESO

### **Usuario de Prueba USA:**
- **Usuario**: `testuser_usa`
- **Contraseña**: `TestUSA2025!`
- **Email**: `testuser@usa-garage.com`

### **URLs de Acceso:**
- **Login USA**: http://127.0.0.1:8000/us/accounts/login/
- **Dashboard USA**: http://127.0.0.1:8000/us/

---

## ✅ ESTADO DEL USUARIO

### **Usuario:**
- ✅ **Activo**: Sí
- ✅ **Staff**: No
- ✅ **Superuser**: No

### **Empresa:**
- ✅ **Nombre**: Taller de testuser_usa
- ✅ **País**: US (Estados Unidos)
- ✅ **Moneda**: USD

### **Suscripción:**
- ✅ **Tipo**: trial (prueba gratuita)
- ✅ **Estado**: Activa
- ✅ **Fecha inicio**: 2025-11-23
- ✅ **Fecha fin**: 2025-12-23 (30 días)
- ✅ **Vigente**: Sí (no vencida)

---

## 🚀 INSTRUCCIONES DE ACCESO

### **1. Iniciar el servidor Django (si no está corriendo):**
```bash
python manage.py runserver
```

### **2. Ir a la URL de Login USA:**
```
http://127.0.0.1:8000/us/accounts/login/
```

### **3. Ingresar Credenciales:**
- **Usuario**: `testuser_usa`
- **Contraseña**: `TestUSA2025!`

### **4. Acceder al Dashboard:**
Una vez logueado, serás redirigido a:
```
http://127.0.0.1:8000/us/
```

---

## 🔧 COMANDOS ÚTILES

### **Verificar usuario (si es necesario):**
```bash
python manage.py crear_usuario_usa_completo
```

Este comando verifica y crea/actualiza el usuario, empresa y suscripción si es necesario.

### **Crear usuario desde cero:**
Si necesitas recrear el usuario completamente, puedes:
1. Eliminar el usuario desde el admin de Django
2. Ejecutar: `python manage.py crear_usuario_usa_completo`

---

## 📋 PROBLEMAS COMUNES

### **No puedo iniciar sesión:**
1. Verifica que el servidor Django esté corriendo
2. Verifica que estés usando la URL correcta: `/us/accounts/login/`
3. Verifica que las credenciales sean exactas (sin espacios extra)

### **El usuario está bloqueado:**
Si el usuario aparece bloqueado o sin acceso:
```bash
python manage.py crear_usuario_usa_completo
```
Esto actualizará la suscripción para asegurar que esté activa.

### **Error de suscripción:**
El comando anterior también renueva la suscripción si está vencida, extendiéndola por 30 días más.

---

## 📊 OTRAS CREDENCIALES DISPONIBLES

### **Chile:**
Según la documentación, también hay usuarios de prueba para Chile. Consulta `tools/USA_USER_CREDENTIALS.md` para más información.

---

## ✅ VERIFICACIÓN

Para verificar que todo está correcto:
- El usuario debe poder iniciar sesión
- Debe ser redirigido al dashboard de USA
- Debe tener acceso a todas las funcionalidades del sistema
- La moneda debe mostrarse en USD

---

**Fecha de creación**: 2025-11-23
**Estado**: ✅ **USUARIO CREADO Y CONFIGURADO**
**Acceso**: ✅ **FUNCIONAL**







