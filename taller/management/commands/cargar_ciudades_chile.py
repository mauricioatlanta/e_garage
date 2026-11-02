"""
Comando para cargar ciudades de Chile en el modelo legacy TallerCiudad
"""

from django.core.management.base import BaseCommand

from taller.models.region_ciudad import TallerCiudad, TallerRegion


class Command(BaseCommand):
    help = "Carga ciudades de Chile para las regiones existentes en TallerRegion"

    def handle(self, *args, **options):
        self.stdout.write("[CL] Cargando ciudades de Chile...")

        # Mapeo de regiones a ciudades principales
        regiones_ciudades = {
            "Arica y Parinacota": ["Arica", "Putre", "Camarones"],
            "Tarapacá": ["Iquique", "Alto Hospicio", "Pozo Almonte", "Pica"],
            "Antofagasta": ["Antofagasta", "Calama", "Tocopilla", "Mejillones", "Taltal"],
            "Atacama": ["Copiapó", "Vallenar", "Chañaral", "Caldera"],
            "Coquimbo": ["La Serena", "Coquimbo", "Ovalle", "Illapel", "Vicuña"],
            "Valparaíso": [
                "Valparaíso",
                "Viña del Mar",
                "Quilpué",
                "Villa Alemana",
                "San Antonio",
                "Quillota",
                "Los Andes",
                "San Felipe",
            ],
            "Metropolitana de Santiago": [
                "Santiago",
                "Puente Alto",
                "Maipú",
                "La Florida",
                "San Bernardo",
                "Las Condes",
                "Pudahuel",
                "Ñuñoa",
                "Peñalolén",
                "El Bosque",
                "La Pintana",
                "San Miguel",
                "Quilicura",
                "Recoleta",
                "Colina",
                "Melipilla",
            ],
            "Libertador General Bernardo O'Higgins": [
                "Rancagua",
                "San Fernando",
                "Rengo",
                "Pichilemu",
                "Santa Cruz",
            ],
            "Maule": ["Talca", "Curicó", "Linares", "Cauquenes", "Constitución"],
            "Ñuble": ["Chillán", "San Carlos", "Bulnes", "Yungay"],
            "Biobío": [
                "Concepción",
                "Talcahuano",
                "Los Ángeles",
                "Chiguayante",
                "Coronel",
                "San Pedro de la Paz",
                "Penco",
                "Tomé",
            ],
            "La Araucanía": ["Temuco", "Angol", "Villarrica", "Pucón", "Lautaro"],
            "Los Ríos": ["Valdivia", "La Unión", "Río Bueno", "Paillaco"],
            "Los Lagos": [
                "Puerto Montt",
                "Osorno",
                "Castro",
                "Ancud",
                "Puerto Varas",
                "Quellón",
            ],
            "Aysén del General Carlos Ibáñez del Campo": [
                "Coyhaique",
                "Puerto Aysén",
                "Chile Chico",
                "Cochrane",
            ],
            "Magallanes y de la Antártica Chilena": [
                "Punta Arenas",
                "Puerto Natales",
                "Porvenir",
                "Puerto Williams",
            ],
        }

        ciudades_creadas = 0
        ciudades_existentes = 0
        regiones_no_encontradas = []

        for nombre_region, ciudades in regiones_ciudades.items():
            try:
                region = TallerRegion.objects.get(nombre=nombre_region)
            except TallerRegion.DoesNotExist:
                regiones_no_encontradas.append(nombre_region)
                continue

            for ciudad_nombre in ciudades:
                ciudad, created = TallerCiudad.objects.get_or_create(
                    nombre=ciudad_nombre, region=region
                )
                if created:
                    ciudades_creadas += 1
                    self.stdout.write(
                        self.style.SUCCESS(f"  [OK] Creada: {ciudad_nombre} ({nombre_region})")
                    )
                else:
                    ciudades_existentes += 1

        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(
            self.style.SUCCESS(
                f"[OK] Proceso completado:\n"
                f"   - Ciudades creadas: {ciudades_creadas}\n"
                f"   - Ciudades existentes: {ciudades_existentes}\n"
                f"   - Total ciudades: {TallerCiudad.objects.count()}"
            )
        )
        if regiones_no_encontradas:
            self.stdout.write(
                self.style.WARNING(
                    f"\n[WARN] Regiones no encontradas: {', '.join(regiones_no_encontradas)}"
                )
            )
        self.stdout.write("=" * 60)
