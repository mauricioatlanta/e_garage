from taller.models.marcas_usa import MarcaVehiculo, ModeloVehiculo

print("=== Marcas USA y sus modelos asociados ===")
marcas = MarcaVehiculo.objects.all()
print(f"Total marcas: {marcas.count()}")
for marca in marcas:
    modelos = ModeloVehiculo.objects.filter(marca=marca)
    print(f"Marca: {marca.nombre} (id={marca.id}) - Modelos: {modelos.count()}")
    if modelos.count() > 0:
        print("  Ejemplo:", [m.nombre for m in modelos[:3]])
    print("---")
