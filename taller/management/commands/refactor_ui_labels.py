from pathlib import Path

from django.core.management.base import BaseCommand

MODULES = {
    "dashboard": [
        "templates/dashboard",
        "templates/components/sidebar.html",
        "templates/taller/layout/sidebar.html",
        "templates/cl/es/dashboard",
        "templates/ar/es/dashboard",
    ],
    "workspace": [
        "templates/workspace",
        "templates/taller/workspace",
    ],
    "documentos": [
        "templates/taller/documentos",
        "templates/taller/common/documentos",
    ],
    "vehiculos": [
        "templates/taller/vehiculos",
        "templates/taller/common/vehiculos",
    ],
    "reportes": [
        "templates/taller/reportes",
        "templates/taller/pdf",
    ],
    "commerce": [
        "templates/public",
        "templates/commerce",
    ],
    "onboarding": [
        "templates/onboarding",
        "templates/account",
    ],
}

REPLACEMENTS = {
    ">Cliente<": ">{{ ui_labels.customer }}<",
    ">Clientes<": ">{{ ui_labels.customers }}<",
    ">Vehículo<": ">{{ ui_labels.vehicle }}<",
    ">Vehículos<": ">{{ ui_labels.vehicles }}<",
    ">Repuesto<": ">{{ ui_labels.part }}<",
    ">Repuestos<": ">{{ ui_labels.parts }}<",
    ">Inventario<": ">{{ ui_labels.inventory }}<",
    ">Stock<": ">{{ ui_labels.stock }}<",
    ">Patente<": ">{{ ui_labels.vehicle_plate }}<",
    "Patente:": "{{ ui_labels.vehicle_plate }}:",
    "Cliente:": "{{ ui_labels.customer }}:",
    "Vehículo:": "{{ ui_labels.vehicle }}:",
}


class Command(BaseCommand):
    help = "Refactoriza ui_labels por módulo."

    def add_arguments(self, parser):
        parser.add_argument("module", choices=MODULES.keys())
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **opts):
        module = opts["module"]
        dry_run = opts["dry_run"]

        modified = 0

        for item in MODULES[module]:
            p = Path(item)

            if p.is_dir():
                files = sorted(p.rglob("*.html"))
            elif p.exists():
                files = [p]
            else:
                continue

            for f in files:
                original = f.read_text(errors="ignore")
                updated = original

                for old, new in REPLACEMENTS.items():
                    updated = updated.replace(old, new)

                if updated != original:
                    modified += 1
                    self.stdout.write(str(f))

                    if not dry_run:
                        f.write_text(updated)

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(f"Archivos modificados: {modified}")
        )
