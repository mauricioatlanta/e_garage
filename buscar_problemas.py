#!/usr/bin/env python
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_taller.settings')
django.setup()

from taller.models import MarcaVehiculo, ModeloVehiculo
from collections import defaultdict

print('=== BÚSQUEDA DE PROBLEMAS EN MODELOS ===\n')

# 1. Buscar modelos duplicados
print("🔍 1. VERIFICANDO MODELOS DUPLICADOS:")
modelos_por_nombre = defaultdict(list)
todos_modelos = ModeloVehiculo.objects.filter(activo=True)

for modelo in todos_modelos:
    modelos_por_nombre[modelo.nombre].append(f"{modelo.marca.nombre} (ID: {modelo.id})")

duplicados_encontrados = False
for nombre, marcas in modelos_por_nombre.items():
    if len(marcas) > 1:
        duplicados_encontrados = True
        print(f"❌ DUPLICADO: {nombre}")
        for marca in marcas:
            print(f"   - {marca}")

if not duplicados_encontrados:
    print("✅ No se encontraron modelos duplicados")

# 2. Verificar modelos que podrían estar en marca incorrecta
print(f"\n🔍 2. VERIFICANDO POSIBLES ASIGNACIONES INCORRECTAS:")

# Modelos que deberían estar en marcas específicas
asignaciones_correctas = {
    'Camry': 'Toyota',
    'Corolla': 'Toyota', 
    'Prius': 'Toyota',
    'RAV4': 'Toyota',
    'Highlander': 'Toyota',
    'Tacoma': 'Toyota',
    'Tundra': 'Toyota',
    'Sienna': 'Toyota',
    
    'Civic': 'Honda',
    'Accord': 'Honda',
    'CR-V': 'Honda',
    'Pilot': 'Honda',
    'Odyssey': 'Honda',
    'Ridgeline': 'Honda',
    'Fit': 'Honda',
    
    'Altima': 'Nissan',
    'Sentra': 'Nissan',
    'Rogue': 'Nissan',
    'Pathfinder': 'Nissan',
    'Maxima': 'Nissan',
    'Armada': 'Nissan',
    'Titan': 'Nissan',
    
    'Mustang': 'Ford',
    'F-150': 'Ford',
    'Explorer': 'Ford',
    'Focus': 'Ford',
    'Escape': 'Ford',
    'Fusion': 'Ford',
    'Edge': 'Ford',
    'Expedition': 'Ford',
}

problemas_encontrados = False
for nombre_modelo, marca_correcta in asignaciones_correctas.items():
    try:
        modelo = ModeloVehiculo.objects.get(nombre=nombre_modelo, activo=True)
        if modelo.marca.nombre != marca_correcta:
            problemas_encontrados = True
            print(f"❌ INCORRECTO: {nombre_modelo} está en {modelo.marca.nombre}, debería estar en {marca_correcta}")
        else:
            print(f"✅ CORRECTO: {nombre_modelo} está en {modelo.marca.nombre}")
    except ModeloVehiculo.DoesNotExist:
        print(f"⚠️ FALTANTE: {nombre_modelo} no encontrado")
    except ModeloVehiculo.MultipleObjectsReturned:
        modelos = ModeloVehiculo.objects.filter(nombre=nombre_modelo, activo=True)
        print(f"❌ MÚLTIPLE: {nombre_modelo} encontrado en múltiples marcas:")
        for m in modelos:
            print(f"   - {m.marca.nombre}")

if not problemas_encontrados:
    print("✅ Todas las asignaciones verificadas son correctas")

# 3. Mostrar conteo total actualizado
print(f"\n📊 3. ESTADÍSTICAS FINALES:")
total_modelos = ModeloVehiculo.objects.filter(activo=True).count()
total_marcas = MarcaVehiculo.objects.filter(activa=True).count()
print(f"Total marcas activas: {total_marcas}")
print(f"Total modelos activos: {total_modelos}")

# 4. Verificar si hay modelos huérfanos (sin marca)
modelos_huerfanos = ModeloVehiculo.objects.filter(activo=True, marca__isnull=True)
if modelos_huerfanos.exists():
    print(f"❌ Modelos huérfanos encontrados: {modelos_huerfanos.count()}")
else:
    print("✅ No hay modelos huérfanos")
