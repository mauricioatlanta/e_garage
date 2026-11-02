"""
python manage.py import_monteazul_vehicles --db /ruta/monteazul.sqlite3 --empresa 2

Importa marcas y modelos de vehículo desde la BD SQLite de MonteAzul hacia Django.
Tablas leídas: catalog_vehiclebrand, catalog_vehiclemodel.

Idempotente: actualiza nombre si ya existe el external_id, crea si no existe.
"""
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Importa marcas y modelos de vehículo desde el SQLite de MonteAzul."

    def add_arguments(self, parser):
        parser.add_argument("--db", required=True, help="Ruta al archivo SQLite de MonteAzul")
        parser.add_argument("--empresa", type=int, required=True, help="ID de la Empresa destino")

    def handle(self, *args, **options):
        import sqlite3
        from taller.models import Empresa
        from commerce.models import CommerceVehicleBrand, CommerceVehicleModel

        try:
            empresa = Empresa.objects.get(pk=options["empresa"])
        except Empresa.DoesNotExist:
            raise CommandError(f"No existe Empresa con id={options['empresa']}")

        db_path = options["db"]
        try:
            con = sqlite3.connect(db_path)
        except Exception as exc:
            raise CommandError(f"No se pudo abrir {db_path}: {exc}")

        brands_rows = con.execute("SELECT id, name FROM catalog_vehiclebrand ORDER BY name").fetchall()
        models_rows = con.execute(
            "SELECT id, name, brand_id FROM catalog_vehiclemodel ORDER BY brand_id, name"
        ).fetchall()
        con.close()

        brands_created = brands_updated = 0
        brand_map = {}  # external_id → CommerceVehicleBrand

        for ext_id, name in brands_rows:
            obj, created = CommerceVehicleBrand.objects.update_or_create(
                empresa=empresa,
                external_id=ext_id,
                defaults={"name": name},
            )
            brand_map[ext_id] = obj
            if created:
                brands_created += 1
            else:
                brands_updated += 1

        models_created = models_updated = 0
        for ext_id, name, brand_ext_id in models_rows:
            brand = brand_map.get(brand_ext_id)
            if not brand:
                continue
            _, created = CommerceVehicleModel.objects.update_or_create(
                empresa=empresa,
                external_id=ext_id,
                defaults={"name": name, "brand": brand},
            )
            if created:
                models_created += 1
            else:
                models_updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"✔ Marcas: {brands_created} creadas, {brands_updated} actualizadas\n"
                f"  Modelos: {models_created} creados, {models_updated} actualizados"
            )
        )
