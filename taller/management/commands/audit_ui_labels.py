from pathlib import Path
import re

from django.core.management.base import BaseCommand

IGNORE = {
    "Copyright",
    "OpenAI",
}

WORDS = [
    "Cliente",
    "Clientes",
    "Vehículo",
    "Vehículos",
    "Patente",
    "Placa",
    "Placas",
    "Matrícula",
    "Factura",
    "Boleta",
    "Comprobante",
    "Presupuesto",
    "Cotización",
    "Orden de Trabajo",
    "Orden de Servicio",
    "Inventario",
    "Stock",
    "Repuesto",
    "Repuestos",
    "Casa de Repuestos",
    "Refaccionaria",
    "Almacén de Repuestos",
    "Desarmaduría",
    "Desarmadero",
    "Deshuesadero",
    "Yonke",
    "Chatarrería",
    "Desmanche",
    "Salvage Yard",
]


class Command(BaseCommand):
    help = "Audita templates buscando textos visibles hardcodeados."

    def handle(self, *args, **kwargs):

        total = 0

        for path in sorted(Path("templates").rglob("*.html")):

            text = path.read_text(errors="ignore")
            lines = text.splitlines()

            printed = False

            for lineno, line in enumerate(lines, 1):

                if "{{ ui_labels." in line:
                    continue

                if "{% trans " in line:
                    continue

                for word in WORDS:

                    if word in IGNORE:
                        continue

                    if re.search(rf"\b{re.escape(word)}\b", line):

                        if not printed:
                            self.stdout.write(f"\n{path}")
                            printed = True

                        self.stdout.write(f"  {lineno:4d}: {word}")
                        total += 1

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(f"TOTAL HALLAZGOS: {total}"))
