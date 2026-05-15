# 🔍 Instrucciones para Diagnosticar Usuario Específico

## 📋 Problema

Un usuario reportó que llenó el formulario de registro pero:
- Se devuelve a la misma página
- No recibe correo de bienvenida

## 🔍 Pasos de Diagnóstico

### Paso 1: Buscar el Usuario por Email

Si conoces el email del usuario que reportó el problema:

```bash
cd /home/atlantareciclajes/apps/egarage/current
python3.10 diagnostico_registro.py email-del-usuario@ejemplo.com
```

Esto mostrará:
- ✅ Si el usuario se creó
- ✅ Si tiene empresa asociada
- ❌ Si no existe (el registro falló completamente)

### Paso 2: Ver Todos los Usuarios Recientes

```bash
python3.10 diagnostico_registro.py
```

Esto mostrará los últimos 20 usuarios registrados.

### Paso 3: Revisar Logs del Servidor

En PythonAnywhere:
1. Ve a **Web** → **Error log**
2. Busca líneas con:
   - `[Registro]` - Errores del formulario
   - `[RegistrationService]` - Errores del servicio
   - `[EgarageEmailBackend]` - Errores de email

O en terminal:
```bash
tail -100 /var/log/www.egarage.cl.error.log | grep -i registro
```

### Paso 4: Verificar en Django Shell

```bash
python3.10 manage.py shell
```

```python
from django.contrib.auth.models import User
from taller.models.empresa import Empresa

# Buscar usuario específico
email = "email-del-usuario@ejemplo.com"
user = User.objects.filter(email__iexact=email).first()

if user:
    print(f"Usuario: {user.username}")
    print(f"Creado: {user.date_joined}")
    empresa = Empresa.objects.filter(user=user).first()
    if empresa:
        print(f"Empresa: {empresa.nombre_taller}")
    else:
        print("ERROR: Usuario sin empresa")
else:
    print("Usuario NO existe - El registro falló")
```

## 🎯 Escenarios Posibles

### Escenario 1: Usuario NO existe
**Causa**: El registro falló completamente
**Solución**: 
- Revisar logs para ver el error específico
- Verificar validación del formulario
- Probar registro manualmente

### Escenario 2: Usuario existe pero NO tiene empresa
**Causa**: Error al crear la empresa
**Solución**:
- Revisar logs de `[RegistrationService]`
- Verificar que la base de datos esté accesible
- Crear empresa manualmente si es necesario

### Escenario 3: Usuario y empresa existen pero no recibió correo
**Causa**: Error al enviar correo
**Solución**:
- Verificar logs de `[EgarageEmailBackend]`
- Probar envío de correo manualmente
- Verificar configuración SMTP

## 📝 Información a Solicitar al Usuario

Si necesitas más información, pregunta al usuario:

1. **¿Qué mensaje de error vio?** (si hubo alguno)
2. **¿Qué datos ingresó?** (email, nombre, teléfono, etc.)
3. **¿El formulario mostró algún error en rojo?**
4. **¿Cuándo intentó registrarse?** (fecha y hora aproximada)
5. **¿Puede intentar registrarse de nuevo?** (para capturar el error en tiempo real)

## 🚀 Próximos Pasos

1. **Ejecutar diagnóstico** con el email del usuario
2. **Revisar logs** del servidor
3. **Identificar el error específico**
4. **Aplicar la solución correspondiente**

---

**Última actualización**: Diciembre 2024
