# 🧹 Eliminar Todas las Marcas con Nombres Numéricos

## Script Completo para Ejecutar en el Servidor

```bash
cd ~/apps/egarage/current
python3.10 manage.py shell
```

Luego pega este código completo:

```python
from taller.models.marca import Marca

# Buscar y eliminar TODAS las marcas con nombres que son solo números
marcas_eliminadas = []
marcas_con_modelos = []

print("🔍 Buscando marcas con nombres numéricos...\n")

for marca in Marca.objects.all():
    if marca.nombre and marca.nombre.strip().isdigit():
        modelos_count = marca.modelo_set.count()
        
        if modelos_count == 0:
            print(f"✅ Eliminando: ID={marca.id}, Nombre='{marca.nombre}', Country='{marca.country}'")
            marca.delete()
            marcas_eliminadas.append(marca.id)
        else:
            print(f"⚠️ NO eliminada (tiene {modelos_count} modelos): ID={marca.id}, Nombre='{marca.nombre}', Country='{marca.country}'")
            marcas_con_modelos.append((marca.id, marca.nombre, modelos_count))

print(f"\n🎉 RESUMEN:")
print(f"✅ Marcas eliminadas: {len(marcas_eliminadas)}")
if marcas_eliminadas:
    print(f"   IDs eliminados: {marcas_eliminadas}")

if marcas_con_modelos:
    print(f"\n⚠️ Marcas con modelos (NO eliminadas): {len(marcas_con_modelos)}")
    for marca_id, nombre, count in marcas_con_modelos:
        print(f"   - ID={marca_id}, Nombre='{nombre}', Modelos={count}")

# Verificar marcas USA después de limpieza
total_usa = Marca.objects.filter(country="US").count()
print(f"\n🚗 Total marcas USA después de limpieza: {total_usa}")

# Verificar Chevrolet específicamente
chevrolet = Marca.objects.filter(nombre="Chevrolet", country="US").first()
if chevrolet:
    print(f"\n✅ Chevrolet: ID={chevrolet.id}, Nombre='{chevrolet.nombre}'")
else:
    print("\n❌ Chevrolet no encontrado!")

exit()
```

## Alternativa: Usar el Comando de Gestión

Si ya hiciste push del comando:

```bash
cd ~/apps/egarage/current
python3.10 manage.py limpiar_marcas_numericas --delete
```



