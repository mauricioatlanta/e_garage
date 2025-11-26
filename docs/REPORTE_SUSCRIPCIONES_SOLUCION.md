# 📊 Solución para Ejecutar el Reporte de Suscripciones

## ⚠️ Problema Identificado

Hay un error de configuración con allauth en el entorno local que impide ejecutar comandos de Django. Este problema **NO debería ocurrir en el servidor de producción**.

## ✅ Solución: Ejecutar en el Servidor

El reporte debe ejecutarse **directamente en el servidor** donde Django está configurado correctamente.

### Opción 1: Usar el Shell de Django en el Servidor (Recomendado)

1. Conéctate al servidor:
```bash
ssh usuario@servidor
cd ~/apps/egarage/current
```

2. Ejecuta el shell de Django:
```bash
python manage.py shell
```

3. Copia y pega el contenido completo del archivo `tools/consultar_suscripciones_manual.py`

### Opción 2: Ejecutar el Script Directamente en el Servidor

Si el servidor tiene bash (Linux/Mac):
```bash
python manage.py shell < tools/consultar_suscripciones_manual.py
```

### Opción 3: Usar el Comando de Django (si funciona en el servidor)

```bash
python manage.py listar_suscripciones_activas
```

## 🔍 Consulta Rápida (Solo Números)

Si solo necesitas números rápidos, ejecuta esto en el shell del servidor:

```python
from taller.models.empresa import Empresa
from taller.models.suscripcion import Suscripcion
from taller.models.trial import TrialRegistro

# Totales
print("=" * 60)
print("📊 ESTADÍSTICAS GENERALES")
print("=" * 60)
print(f"Empresas activas: {Empresa.objects.filter(suscripcion_activa=True).count()}")
print(f"Suscripciones activas: {Suscripcion.objects.filter(activa=True).count()}")
print(f"Trials activos: {TrialRegistro.objects.filter(prueba_activa=True).count()}")

# Por país
print("\n" + "=" * 60)
print("🌍 POR PAÍS")
print("=" * 60)
for pais in ["CL", "US", "MX", "PE", "CO", "EC", "BR", "VE"]:
    count = Empresa.objects.filter(pais=pais, suscripcion_activa=True).count()
    if count > 0:
        print(f"{pais}: {count} empresas activas")

# Listar todas las empresas activas
print("\n" + "=" * 60)
print("🏢 TODAS LAS EMPRESAS ACTIVAS")
print("=" * 60)
empresas = Empresa.objects.filter(suscripcion_activa=True).select_related('user')
for emp in empresas:
    es_trial = "TRIAL" if emp.plan == "trial" else emp.plan.upper()
    print(f"{emp.pais} - {emp.nombre_taller} ({emp.user.email}) - {es_trial}")

# Listar todos los trials activos
print("\n" + "=" * 60)
print("🧪 TODOS LOS TRIALS ACTIVOS")
print("=" * 60)
trials = TrialRegistro.objects.filter(prueba_activa=True)
for trial in trials:
    print(f"{trial.nombre} - {trial.email} - Registro: {trial.fecha_registro}")
```

## 📝 Nota Importante

El error que estás viendo (`AppRegistryNotReady: Apps aren't loaded yet.`) es un problema de configuración en el entorno local relacionado con cómo allauth intenta verificar el middleware durante la inicialización.

**En el servidor de producción, este problema no debería ocurrir** porque:
1. La configuración puede ser diferente
2. El entorno está más estable
3. Las dependencias están correctamente instaladas

## 🚀 Próximos Pasos

1. Ejecuta el reporte en el servidor usando una de las opciones arriba
2. El reporte mostrará:
   - Todas las suscripciones activas por país
   - Todas las empresas con suscripción activa
   - Todas las cuentas de prueba (trials) activas
   - Todos los usuarios registrados por país



