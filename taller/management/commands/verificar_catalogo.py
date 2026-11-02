"""
Management command para verificar que el catálogo maestro se cargó correctamente

Uso:
    python manage.py verificar_catalogo
"""

from django.core.management.base import BaseCommand
from taller.servicios.models import Servicio, ServicioName, CategoriaServicio, CategoriaServicioName


class Command(BaseCommand):
    help = "Verifica que el catálogo maestro se cargó correctamente"

    def handle(self, *args, **options):
        print("=" * 70)
        print("VERIFICACIÓN DEL CATÁLOGO MAESTRO")
        print("=" * 70)

        # Servicios maestros
        servicios_maestros = Servicio.objects.filter(empresa_id=1)
        print(f"\n[INFO] Servicios maestros (empresa_id=1): {servicios_maestros.count()}")

        # Nombres localizados
        nombres_localizados = ServicioName.objects.filter(servicio__empresa_id=1)
        print(f"[INFO] Nombres localizados: {nombres_localizados.count()}")

        # Categorías
        categorias = CategoriaServicio.objects.all()
        print(f"[INFO] Categorías creadas: {categorias.count()}")

        # Ejemplo de servicio
        if servicios_maestros.exists():
            ejemplo = servicios_maestros.first()
            print(f"\n[EJEMPLO] Servicio: {ejemplo.nombre}")
            print(f"[EJEMPLO] Categoría: {ejemplo.categoria}")
            
            nombres = ServicioName.objects.filter(servicio=ejemplo)
            print(f"[EJEMPLO] Nombres localizados para este servicio: {nombres.count()}")
            for nombre in nombres[:5]:
                aliases_str = ', '.join(nombre.aliases[:3]) if nombre.aliases else 'N/A'
                print(f"  - [{nombre.language}] {nombre.label} - Aliases: {aliases_str}")

        # Distribución por país
        print("\n[INFO] Distribución de nombres por idioma:")
        for lang in ['es', 'en', 'pt']:
            count = nombres_localizados.filter(language=lang).count()
            print(f"  - {lang.upper()}: {count} nombres")

        # Listar algunos servicios
        print("\n[INFO] Primeros 5 servicios maestros:")
        for servicio in servicios_maestros[:5]:
            print(f"  - {servicio.nombre} (ID: {servicio.id})")

        print("\n" + "=" * 70)
        print("[OK] Verificación completada")
        print("=" * 70)






