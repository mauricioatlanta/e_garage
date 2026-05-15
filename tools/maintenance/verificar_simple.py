from taller.models.catalogo import CatalogoModeloAuto

# Verificar total
total = CatalogoModeloAuto.objects.count()
print(f"📊 Total de modelos: {total}")

# Verificar algunas marcas
marcas_count = CatalogoModeloAuto.objects.values("marca").distinct().count()
print(f"🏷️ Total de marcas: {marcas_count}")

# Algunos ejemplos
print("🚗 Primeros 5 registros:")
for model in CatalogoModeloAuto.objects.all()[:5]:
    print(f"  {model.marca} - {model.modelo}")

print("✅ Verificación completada")
