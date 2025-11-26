# 🔍 Debug: Validación Marca-Modelo

## Verificar en el Servidor

Ejecuta esto para ver exactamente qué está pasando:

```bash
cd ~/apps/egarage/current
python3.10 manage.py shell
```

```python
from taller.models.marca import Marca
from taller.models.modelo import Modelo

# Verificar Chevrolet
chevrolet = Marca.objects.filter(nombre="Chevrolet", country="US").first()
print(f"✅ Chevrolet: ID={chevrolet.id}, Nombre='{chevrolet.nombre}', Country='{chevrolet.country}'")

# Verificar TODOS los modelos Camaro
todos_camaros = Modelo.objects.filter(nombre__icontains="Camaro", country="US").select_related('marca')
print(f"\n📋 Modelos con 'Camaro' encontrados: {todos_camaros.count()}")
for m in todos_camaros:
    print(f"   - ID={m.pk}, Nombre='{m.nombre}', Marca='{m.marca.nombre}' (ID={m.marca_id}), Country='{m.country}'")

# Verificar específicamente Camaro de Chevrolet
camaro_chevrolet = Modelo.objects.filter(nombre="Camaro", marca=chevrolet, country="US").first()
if camaro_chevrolet:
    print(f"\n✅ Camaro de Chevrolet: ID={camaro_chevrolet.id}, Marca_ID={camaro_chevrolet.marca_id}, Chevrolet_ID={chevrolet.id}")
    print(f"   Coherencia: {camaro_chevrolet.marca_id} == {chevrolet.id} ? {camaro_chevrolet.marca_id == chevrolet.id}")
else:
    print("\n❌ Camaro de Chevrolet NO encontrado")

# Verificar si hay modelos con el mismo nombre pero diferentes marcas
print("\n🔍 Verificando posibles duplicados...")
modelos_por_nombre = {}
for m in Modelo.objects.filter(country="US").select_related('marca'):
    if m.nombre not in modelos_por_nombre:
        modelos_por_nombre[m.nombre] = []
    modelos_por_nombre[m.nombre].append(m)

duplicados = {nombre: modelos for nombre, modelos in modelos_por_nombre.items() if len(modelos) > 1}
if duplicados:
    print(f"\n⚠️ Modelos con nombres duplicados:")
    for nombre, modelos in duplicados.items():
        print(f"   '{nombre}':")
        for m in modelos:
            print(f"      - ID={m.pk}, Marca='{m.marca.nombre}' (ID={m.marca_id})")
```

## Revisar Logs del Servidor

Cuando intentes guardar el formulario, revisa los logs:

```bash
cd ~/apps/egarage/current
tail -f logs/django.log | grep -i "clean_modelo\|clean\]\|coherencia\|marca\|modelo"
```

O en PythonAnywhere, revisa los logs de error en el panel.



