"""
Comando maestro para cargar todas las ubicaciones de todos los países soportados
"""

from django.core.management import call_command
from django.core.management.base import BaseCommand

from taller.models.ubicacion import Ciudad, Estado


class Command(BaseCommand):
    help = "Carga estados y ciudades para TODOS los países soportados"

    def add_arguments(self, parser):
        parser.add_argument(
            "--paises",
            nargs="+",
            help="Lista de países a cargar (CL US BR MX PE VE CO EC). Si no se especifica, carga todos.",
        )
        parser.add_argument(
            "--skip-existing",
            action="store_true",
            help="Saltar países que ya tienen datos cargados",
        )

    def handle(self, *args, **options):
        paises_disponibles = {
            "CL": {"comando": "cargar_estados_chile", "nombre": "Chile"},
            "US": {"comando": "cargar_estados_usa", "nombre": "Estados Unidos"},
            "BR": {"comando": "cargar_estados_brasil", "nombre": "Brasil"},
            "MX": {"comando": "cargar_estados_mexico", "nombre": "México"},
            "PE": {"comando": "cargar_estados_peru", "nombre": "Perú"},
            "VE": {"comando": "cargar_estados_venezuela", "nombre": "Venezuela"},
            "CO": {"comando": "cargar_estados_colombia", "nombre": "Colombia"},
            "EC": {"comando": "cargar_estados_ecuador", "nombre": "Ecuador"},
        }

        # Determinar qué países cargar
        if options["paises"]:
            paises_a_cargar = []
            for codigo in options["paises"]:
                codigo_upper = codigo.upper()
                if codigo_upper in paises_disponibles:
                    paises_a_cargar.append(codigo_upper)
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            f"Pais '{codigo}' no reconocido. Disponibles: {', '.join(paises_disponibles.keys())}"
                        )
                    )
        else:
            paises_a_cargar = list(paises_disponibles.keys())

        if not paises_a_cargar:
            self.stdout.write(self.style.ERROR("No hay paises para cargar"))
            return

        self.stdout.write("=" * 70)
        self.stdout.write(self.style.SUCCESS("CARGA MASIVA DE UBICACIONES MULTI-PAIS"))
        self.stdout.write("=" * 70)
        self.stdout.write(f"\nPaíses a procesar: {', '.join(paises_a_cargar)}\n")

        resultados = []

        for codigo_pais in paises_a_cargar:
            info = paises_disponibles[codigo_pais]

            # Verificar si ya tiene datos
            if options["skip_existing"]:
                count_estados = Estado.objects.filter(pais=codigo_pais).count()
                count_ciudades = Ciudad.objects.filter(estado__pais=codigo_pais).count()

                if count_estados > 0 or count_ciudades > 0:
                    self.stdout.write(
                        self.style.WARNING(
                            f"Saltando {info['nombre']} ({codigo_pais}) - Ya tiene {count_estados} estados y {count_ciudades} ciudades"
                        )
                    )
                    resultados.append(
                        {
                            "pais": codigo_pais,
                            "nombre": info["nombre"],
                            "status": "skipped",
                            "estados": count_estados,
                            "ciudades": count_ciudades,
                        }
                    )
                    continue

            # Ejecutar comando de carga
            self.stdout.write("\n" + "-" * 70)
            self.stdout.write(f"Cargando {info['nombre']} ({codigo_pais})...")
            self.stdout.write("-" * 70 + "\n")

            try:
                call_command(info["comando"])

                # Contar resultados
                count_estados = Estado.objects.filter(pais=codigo_pais).count()
                count_ciudades = Ciudad.objects.filter(estado__pais=codigo_pais).count()

                resultados.append(
                    {
                        "pais": codigo_pais,
                        "nombre": info["nombre"],
                        "status": "success",
                        "estados": count_estados,
                        "ciudades": count_ciudades,
                    }
                )
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error al cargar {info['nombre']}: {str(e)}"))
                resultados.append(
                    {
                        "pais": codigo_pais,
                        "nombre": info["nombre"],
                        "status": "error",
                        "error": str(e),
                    }
                )

        # Resumen final
        self.stdout.write("\n" + "=" * 70)
        self.stdout.write(self.style.SUCCESS("📊 RESUMEN DE CARGA"))
        self.stdout.write("=" * 70 + "\n")

        # Tabla de resultados
        self.stdout.write(
            f"{'País':<20} {'Código':<8} {'Estados':<12} {'Ciudades':<12} {'Status':<10}"
        )
        self.stdout.write("-" * 70)

        total_estados = 0
        total_ciudades = 0
        exitosos = 0
        errores = 0
        saltados = 0

        for res in resultados:
            estados = res.get("estados", 0)
            ciudades = res.get("ciudades", 0)
            status = res.get("status", "unknown")

            if status == "success":
                status_icon = "[OK]"
                exitosos += 1
                total_estados += estados
                total_ciudades += ciudades
            elif status == "error":
                status_icon = "[ERROR]"
                errores += 1
            elif status == "skipped":
                status_icon = "[SKIP]"
                saltados += 1
                total_estados += estados
                total_ciudades += ciudades
            else:
                status_icon = "[?]"

            self.stdout.write(
                f"{res['nombre']:<20} {res['pais']:<8} {estados:<12} {ciudades:<12} {status_icon:<10}"
            )

        self.stdout.write("-" * 70)
        self.stdout.write(f"{'TOTAL':<20} {'':<8} {total_estados:<12} {total_ciudades:<12}")

        self.stdout.write("\n" + "=" * 70)
        self.stdout.write(
            self.style.SUCCESS(
                f"Carga completada:\n"
                f"   • Países exitosos: {exitosos}\n"
                f"   • Países saltados: {saltados}\n"
                f"   • Errores: {errores}\n"
                f"   • Total estados cargados: {total_estados}\n"
                f"   • Total ciudades cargadas: {total_ciudades}"
            )
        )
        self.stdout.write("=" * 70)

        # Cobertura por país
        self.stdout.write("\n📍 COBERTURA POR PAÍS:\n")
        for codigo_pais, info in paises_disponibles.items():
            count_estados = Estado.objects.filter(pais=codigo_pais).count()
            count_ciudades = Ciudad.objects.filter(estado__pais=codigo_pais).count()

            if count_estados > 0:
                marca = "[OK]"
            else:
                marca = "[!]"

            self.stdout.write(
                f"{marca} {info['nombre']:20} ({codigo_pais}): {count_estados:3} estados, {count_ciudades:4} ciudades"
            )
