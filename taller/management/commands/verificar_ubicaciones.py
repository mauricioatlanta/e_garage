"""
Comando para verificar el estado de las ubicaciones cargadas en el sistema
"""

from django.core.management.base import BaseCommand
from django.db.models import Count

from taller.models.clientes import Cliente
from taller.models.ubicacion import Ciudad, Estado


class Command(BaseCommand):
    help = "Verifica el estado de las ubicaciones cargadas y su uso en clientes"

    def add_arguments(self, parser):
        parser.add_argument(
            "--pais",
            type=str,
            help="Verificar solo un país específico (CL, US, BR, MX, PE, VE, CO, EC)",
        )
        parser.add_argument(
            "--detallado",
            action="store_true",
            help="Mostrar detalles de cada estado/ciudad",
        )

    def handle(self, *args, **options):
        self.stdout.write("=" * 80)
        self.stdout.write(self.style.SUCCESS("🔍 VERIFICACIÓN DE UBICACIONES"))
        self.stdout.write("=" * 80 + "\n")

        # Filtro de país
        pais_filtro = options.get("pais", "").upper() if options.get("pais") else None

        # 1. Resumen general
        self.stdout.write("📊 RESUMEN GENERAL:\n")

        if pais_filtro:
            estados_qs = Estado.objects.filter(pais=pais_filtro)
            ciudades_qs = Ciudad.objects.filter(estado__pais=pais_filtro)
        else:
            estados_qs = Estado.objects.all()
            ciudades_qs = Ciudad.objects.all()

        total_estados = estados_qs.count()
        total_ciudades = ciudades_qs.count()

        self.stdout.write(f"  • Total estados/regiones: {total_estados}")
        self.stdout.write(f"  • Total ciudades: {total_ciudades}")

        # 2. Desglose por país
        self.stdout.write("\n" + "=" * 80)
        self.stdout.write("🌍 COBERTURA POR PAÍS:\n")
        self.stdout.write("-" * 80)
        self.stdout.write(
            f"{'País':<25} {'Código':<8} {'Estados':<10} {'Ciudades':<10} {'Clientes':<10}"
        )
        self.stdout.write("-" * 80)

        paises_info = [
            ("CL", "Chile"),
            ("US", "Estados Unidos"),
            ("BR", "Brasil"),
            ("MX", "México"),
            ("PE", "Perú"),
            ("VE", "Venezuela"),
            ("CO", "Colombia"),
            ("EC", "Ecuador"),
        ]

        for codigo_pais, nombre_pais in paises_info:
            if pais_filtro and codigo_pais != pais_filtro:
                continue

            count_estados = Estado.objects.filter(pais=codigo_pais).count()
            count_ciudades = Ciudad.objects.filter(estado__pais=codigo_pais).count()

            # Contar clientes legacy que usan ubicaciones de este país
            if codigo_pais == "CL":
                # Chile usa region/ciudad (legacy)
                count_clientes = Cliente.objects.filter(region__isnull=False).count()
            else:
                # Otros usan estado_usa/ciudad_usa o billing_address
                count_clientes_legacy = Cliente.objects.filter(estado_usa__pais=codigo_pais).count()
                count_clientes_address = Cliente.objects.filter(
                    billing_address__city__estado__pais=codigo_pais
                ).count()
                count_clientes = count_clientes_legacy + count_clientes_address

            # Determinar status
            if count_estados > 0:
                status = "✅"
            else:
                status = "⚠️ "

            self.stdout.write(
                f"{status} {nombre_pais:<23} {codigo_pais:<8} {count_estados:<10} "
                f"{count_ciudades:<10} {count_clientes:<10}"
            )

        self.stdout.write("-" * 80)

        # 3. Detalle por estado (si se solicita)
        if options["detallado"]:
            self.stdout.write("\n" + "=" * 80)
            self.stdout.write("📍 DETALLE POR ESTADO/REGIÓN:\n")
            self.stdout.write("-" * 80)

            for codigo_pais, nombre_pais in paises_info:
                if pais_filtro and codigo_pais != pais_filtro:
                    continue

                estados = Estado.objects.filter(pais=codigo_pais).order_by("nombre")

                if not estados.exists():
                    continue

                self.stdout.write(f"\n🌎 {nombre_pais} ({codigo_pais}):")

                for estado in estados:
                    ciudades_count = Ciudad.objects.filter(estado=estado).count()
                    self.stdout.write(
                        f"  • {estado.nombre} ({estado.codigo}): {ciudades_count} ciudades"
                    )

                    # Mostrar ciudades si es muy detallado
                    if ciudades_count <= 10:  # Solo si son pocas
                        ciudades = Ciudad.objects.filter(estado=estado).order_by("nombre")
                        for ciudad in ciudades:
                            capital = " 🏛️" if ciudad.es_capital else ""
                            self.stdout.write(f"      - {ciudad.nombre}{capital}")

        # 4. Análisis de uso en clientes
        self.stdout.write("\n" + "=" * 80)
        self.stdout.write("👥 USO EN CLIENTES:\n")
        self.stdout.write("-" * 80)

        # Clientes con campos legacy
        clientes_con_region = Cliente.objects.filter(region__isnull=False).count()
        clientes_con_ciudad = Cliente.objects.filter(ciudad__isnull=False).count()
        clientes_con_estado_usa = Cliente.objects.filter(estado_usa__isnull=False).count()
        clientes_con_ciudad_usa = Cliente.objects.filter(ciudad_usa__isnull=False).count()

        # Clientes con Address nuevo
        clientes_con_billing_address = Cliente.objects.filter(billing_address__isnull=False).count()
        clientes_con_shipping_address = Cliente.objects.filter(
            shipping_address__isnull=False
        ).count()

        total_clientes = Cliente.objects.count()

        self.stdout.write(f"\n📊 Total de clientes: {total_clientes}\n")

        self.stdout.write("🔴 CAMPOS LEGACY (deprecados):")
        self.stdout.write(f"  • Con region (Chile): {clientes_con_region}")
        self.stdout.write(f"  • Con ciudad (Chile): {clientes_con_ciudad}")
        self.stdout.write(f"  • Con estado_usa: {clientes_con_estado_usa}")
        self.stdout.write(f"  • Con ciudad_usa: {clientes_con_ciudad_usa}")

        self.stdout.write("\n✅ CAMPOS NUEVOS (Address):")
        self.stdout.write(f"  • Con billing_address: {clientes_con_billing_address}")
        self.stdout.write(f"  • Con shipping_address: {clientes_con_shipping_address}")

        # Porcentaje de migración
        if total_clientes > 0:
            porcentaje_migrado = (clientes_con_billing_address / total_clientes) * 100
            self.stdout.write(f"\n📈 Progreso de migración: {porcentaje_migrado:.1f}%")

            if porcentaje_migrado >= 100:
                self.stdout.write(self.style.SUCCESS("   🎉 ¡Migración completa!"))
            elif porcentaje_migrado >= 50:
                self.stdout.write(self.style.WARNING("   ⚠️  Migración en progreso (más del 50%)"))
            else:
                self.stdout.write(
                    self.style.ERROR(
                        "   ❌ Migración pendiente (menos del 50%)\n"
                        "   💡 Ejecutar: python manage.py backfill_addresses"
                    )
                )

        # 5. Recomendaciones
        self.stdout.write("\n" + "=" * 80)
        self.stdout.write("💡 RECOMENDACIONES:\n")

        if total_estados == 0:
            self.stdout.write(
                self.style.WARNING(
                    "⚠️  No hay ubicaciones cargadas. Ejecutar:\n"
                    "   python manage.py cargar_todas_ubicaciones"
                )
            )
        else:
            paises_sin_datos = []
            for codigo_pais, nombre_pais in paises_info:
                if Estado.objects.filter(pais=codigo_pais).count() == 0:
                    paises_sin_datos.append(nombre_pais)

            if paises_sin_datos:
                self.stdout.write(
                    self.style.WARNING(
                        f"⚠️  Países sin datos: {', '.join(paises_sin_datos)}\n"
                        f"   Ejecutar: python manage.py cargar_todas_ubicaciones --paises {' '.join([p[0] for p in paises_info if p[1] in paises_sin_datos])}"
                    )
                )

        if clientes_con_billing_address < total_clientes and total_clientes > 0:
            self.stdout.write(
                self.style.WARNING(
                    f"⚠️  {total_clientes - clientes_con_billing_address} clientes sin billing_address\n"
                    "   Ejecutar: python manage.py backfill_addresses"
                )
            )

        self.stdout.write("\n" + "=" * 80)
        self.stdout.write(self.style.SUCCESS("✅ Verificación completada"))
        self.stdout.write("=" * 80)
