# 🔍 Verificar Marca con ID 91

## Problema Detectado

En el formulario aparece una opción incorrecta:
- `value="91" text="55"`

Esto sugiere que hay una marca con ID 91 que tiene nombre "55", lo cual es incorrecto.

## Verificación en el Servidor

Ejecuta esto en el servidor:

```bash
cd ~/apps/egarage/current
python3.10 manage.py shell
```

```python
from taller.models.marca import Marca

# Verificar marca con ID 91
marca_91 = Marca.objects.filter(pk=91, country="US").first()
if marca_91:
    print(f"❌ PROBLEMA ENCONTRADO:")
    print(f"   - ID: {marca_91.id}")
    print(f"   - Nombre: '{marca_91.nombre}'")
    print(f"   - Country: {marca_91.country}")
    print(f"\n💡 Esta marca tiene un nombre incorrecto ('55' en lugar de un nombre de marca)")
    
    # Verificar si hay una marca con nombre "55"
    marca_nombre_55 = Marca.objects.filter(nombre="55", country="US").first()
    if marca_nombre_55:
        print(f"\n⚠️ También existe una marca con nombre '55':")
        print(f"   - ID: {marca_nombre_55.id}")
        print(f"   - Nombre: '{marca_nombre_55.nombre}'")
        print(f"   - Country: {marca_nombre_55.country}")
    
    # Verificar Chevrolet (debería ser ID 55)
    chevrolet = Marca.objects.filter(nombre="Chevrolet", country="US").first()
    if chevrolet:
        print(f"\n✅ Chevrolet encontrado:")
        print(f"   - ID: {chevrolet.id}")
        print(f"   - Nombre: '{chevrolet.nombre}'")
        print(f"   - Country: {chevrolet.country}")
        
        if chevrolet.id == 91:
            print(f"\n⚠️ PROBLEMA: Chevrolet tiene ID 91, pero debería tener ID 55")
        elif chevrolet.id == 55:
            print(f"\n✅ Chevrolet tiene el ID correcto (55)")
else:
    print("✅ No hay marca con ID 91 para USA")

# Listar todas las marcas USA para verificar
print("\n📋 Todas las marcas USA:")
marcas_usa = Marca.objects.filter(country="US").order_by("id")
for m in marcas_usa:
    print(f"   ID={m.id:3d} | Nombre='{m.nombre}'")
```

## Solución

Si encuentras el problema:

### Opción 1: Corregir la marca con ID 91

```python
# Si la marca ID 91 debería ser otra cosa
marca_91 = Marca.objects.get(pk=91, country="US")
# Corregir el nombre
marca_91.nombre = "Nombre Correcto"  # Reemplazar con el nombre correcto
marca_91.save()
```

### Opción 2: Eliminar marca duplicada/incorrecta

```python
# Si la marca ID 91 es incorrecta y hay una duplicada
marca_91 = Marca.objects.get(pk=91, country="US")
# Verificar si hay modelos asociados
modelos_count = marca_91.modelo_set.count()
print(f"Modelos asociados a marca ID 91: {modelos_count}")

if modelos_count == 0:
    # Si no hay modelos, se puede eliminar
    marca_91.delete()
    print("✅ Marca ID 91 eliminada")
else:
    print("⚠️ No se puede eliminar, tiene modelos asociados")
    # En este caso, corregir el nombre
    marca_91.nombre = "Nombre Correcto"
    marca_91.save()
```

### Opción 3: Verificar si hay conflicto de IDs

```python
# Verificar si hay marcas con nombres numéricos incorrectos
marcas_problematicas = Marca.objects.filter(
    country="US",
    nombre__regex=r'^\d+$'  # Nombres que son solo números
)
print(f"Marcas con nombres numéricos: {marcas_problematicas.count()}")
for m in marcas_problematicas:
    print(f"   ID={m.id}, Nombre='{m.nombre}'")
```



