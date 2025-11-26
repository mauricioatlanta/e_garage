# 🔍 Revisar Logs del Servidor para Diagnosticar Error

## El Error Persiste

El error "El modelo no pertenece a la marca seleccionada" sigue apareciendo cuando intentas guardar Chevrolet + Camaro.

## Revisar Logs en Tiempo Real

Ejecuta esto en el servidor para ver los logs en tiempo real:

```bash
cd ~/apps/egarage/current
tail -f logs/django.log | grep -i "clean\|coherencia\|marca\|modelo\|chevrolet\|camaro"
```

O si no tienes logs/django.log, revisa los logs de error en el panel de PythonAnywhere.

## Información que Necesitamos

Cuando intentes guardar el formulario, los logs deberían mostrar:

1. **En `clean_modelo()`:**
   - Qué marca se está comparando
   - Qué modelo se está comparando
   - Los IDs exactos que se están comparando
   - Si la comparación está fallando y por qué

2. **En `clean()`:**
   - Si la marca y modelo están correctamente en `cleaned_data`
   - Los IDs que se están comparando
   - Si la comparación está fallando

## Script de Verificación Directa

Ejecuta esto para verificar los datos directamente:

```bash
cd ~/apps/egarage/current
python3.10 manage.py shell
```

```python
from taller.models.marca import Marca
from taller.models.modelo import Modelo

# Verificar Chevrolet
chevrolet = Marca.objects.get(nombre="Chevrolet", country="US")
print(f"Chevrolet: ID={chevrolet.id}, tipo={type(chevrolet.id)}")

# Verificar Camaro
camaro = Modelo.objects.select_related('marca').get(nombre="Camaro", marca=chevrolet, country="US")
print(f"Camaro: ID={camaro.id}, marca_id={camaro.marca_id}, tipo={type(camaro.marca_id)}")
print(f"Chevrolet.id={chevrolet.id}, tipo={type(chevrolet.id)}")
print(f"¿Coinciden? {camaro.marca_id == chevrolet.id}")
print(f"¿Coinciden (int)? {int(camaro.marca_id) == int(chevrolet.id)}")
```

## Posibles Causas

1. **Problema de tipos**: Los IDs pueden ser strings en lugar de enteros
2. **Problema de caché**: El modelo puede estar usando datos en caché incorrectos
3. **Problema de orden**: La validación puede estar ejecutándose antes de que los datos estén listos
4. **Problema de datos**: Puede haber múltiples modelos "Camaro" y se está seleccionando el incorrecto

## Compartir los Logs

Por favor, comparte los logs que aparecen cuando intentas guardar el formulario, especialmente las líneas que dicen:
- `[clean_modelo] Comparando:`
- `[clean] Validando coherencia:`
- `[clean] ❌ Error de coherencia marca-modelo:`

Esto nos ayudará a identificar el problema exacto.



