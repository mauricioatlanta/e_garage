# 📊 Instrucciones para Consultar Suscripciones Activas

Este documento explica cómo obtener un reporte completo de todas las suscripciones activas por país.

## 🚀 Método 1: Usando el Comando de Django (Recomendado)

Si el entorno de Django está funcionando correctamente, puedes ejecutar:

```bash
python manage.py listar_suscripciones_activas
```

Este comando mostrará:
- ✅ Suscripciones activas (modelo Suscripcion)
- ✅ Empresas con suscripción activa (modelo Empresa)
- ✅ Cuentas de prueba (trials) activas
- ✅ Usuarios registrados por país

## 🔧 Método 2: Usando el Shell de Django (Si hay problemas con el comando)

Si el comando no funciona debido a problemas de configuración, puedes usar el shell interactivo:

### Paso 1: Abrir el shell de Django
```bash
python manage.py shell
```

### Paso 2: Copiar y pegar el código

Abre el archivo `tools/consultar_suscripciones_manual.py` y copia todo su contenido, luego pégalo en el shell de Django.

O ejecuta directamente:
```bash
python manage.py shell < tools/consultar_suscripciones_manual.py
```

## 📋 Información que se mostrará

El reporte incluye:

### Por cada país:
1. **Suscripciones (Modelo Suscripcion)**
   - Estado (Activa/Vencida)
   - Usuario y email
   - Tipo de suscripción (trial, mensual, semestral, anual)
   - Fechas de inicio y fin
   - Información de la empresa asociada

2. **Empresas con Suscripción Activa**
   - Nombre del taller/empresa
   - Usuario asociado
   - Plan de suscripción
   - Fechas y días restantes
   - Información de contacto

3. **Cuentas de Prueba (Trials) Activas**
   - Nombre y email
   - Fechas de registro y activación
   - Días restantes
   - Empresa asociada

4. **Usuarios Registrados**
   - Usuarios activos (no staff/superuser)
   - Estado de suscripción
   - Información de la empresa

### Resumen Final:
- Total de países con actividad
- Lista completa de todos los trials activos

## 🎯 Países Soportados

El sistema revisa automáticamente todos los países donde hay empresas registradas:
- 🇨🇱 Chile (CL)
- 🇺🇸 Estados Unidos (US)
- 🇲🇽 México (MX)
- 🇵🇪 Perú (PE)
- 🇨🇴 Colombia (CO)
- 🇪🇨 Ecuador (EC)
- 🇧🇷 Brasil (BR)
- 🇻🇪 Venezuela (VE)

## ⚠️ Notas Importantes

1. **Suscripciones Vencidas**: El reporte marca claramente las suscripciones que están vencidas (❌ VENCIDA)

2. **Cuentas de Prueba**: Las cuentas de tipo "trial" se marcan claramente como "(TRIAL)"

3. **Usuarios sin Suscripción**: Los usuarios registrados que no tienen suscripción activa se marcan como "⚠️ Sin Suscripción"

4. **Fechas**: Todas las fechas se muestran en formato `YYYY-MM-DD HH:MM:SS`

## 🔍 Consultas Rápidas

Si solo necesitas información específica, puedes usar estas consultas en el shell:

```python
# Total de suscripciones activas
from taller.models.suscripcion import Suscripcion
Suscripcion.objects.filter(activa=True).count()

# Total de empresas activas por país
from taller.models.empresa import Empresa
Empresa.objects.filter(suscripcion_activa=True, pais='CL').count()  # Chile
Empresa.objects.filter(suscripcion_activa=True, pais='US').count()  # USA
Empresa.objects.filter(suscripcion_activa=True, pais='MX').count()  # México

# Total de trials activos
from taller.models.trial import TrialRegistro
TrialRegistro.objects.filter(prueba_activa=True).count()

# Listar todos los usuarios con empresa en un país
from django.contrib.auth.models import User
User.objects.filter(empresa__pais='CL', is_active=True, is_staff=False).values('username', 'email', 'empresa__nombre_taller')
```

## 📝 Archivos Relacionados

- `taller/management/commands/listar_suscripciones_activas.py` - Comando de Django
- `tools/listar_suscripciones_activas.py` - Script independiente (puede tener problemas de configuración)
- `tools/consultar_suscripciones_manual.py` - Código para ejecutar en shell manualmente



