import hashlib
import json
import re
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from taller.models import Empresa
from taller.models.reciclaje import Catalitico


EXPECTED_CODES = {
    "Y1",
    "UDX011",
    "K564",
    "K208",
    "K357",
    "F0C",
    "C137",
    "K181",
    "5QM178AA",
    "2QB",
    "8K0131701S",
    "NA3",
    "79GC02",
    "K179",
    "T16",
    "25129125",
    "BG",
    "8X",
    "M8",
    "T24",
    "W2BS1",
    "K212",
    "K130",
}

EXPECTED_COUNT = 23


def normalize_code(value):
    return re.sub(r"[^A-Z0-9]", "", (value or "").upper())


def money(value):
    return Decimal(str(value)).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )


class Command(BaseCommand):
    help = (
        "Importa precios confirmados por Jorge para Atlanta Reciclajes. "
        "Por defecto SOLO hace dry-run. --apply habilita escrituras."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "json_path",
            help="JSON confirmado generado por la auditoría WhatsApp.",
        )
        parser.add_argument(
            "--empresa-id",
            type=int,
            required=True,
            help="ID exacto del tenant Atlanta.",
        )
        parser.add_argument(
            "--expected-sha256",
            required=True,
            help="SHA256 exacto esperado del JSON fuente.",
        )
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Aplica cambios. Sin esta opción nunca escribe.",
        )

    def handle(self, *args, **options):
        source = Path(options["json_path"])

        if not source.is_file():
            raise CommandError(f"JSON_NO_EXISTE={source}")

        raw = source.read_bytes()
        actual_sha = hashlib.sha256(raw).hexdigest()
        expected_sha = options["expected_sha256"].lower().strip()

        self.stdout.write(f"SOURCE={source}")
        self.stdout.write(f"SHA256={actual_sha}")

        if actual_sha != expected_sha:
            raise CommandError(
                "SHA256_NO_COINCIDE "
                f"esperado={expected_sha} actual={actual_sha}"
            )

        try:
            payload = json.loads(raw.decode("utf-8"))
        except Exception as exc:
            raise CommandError(f"JSON_INVALIDO={exc}")

        rows = self.extract_rows(payload)

        if len(rows) != EXPECTED_COUNT:
            raise CommandError(
                f"COUNT_INVALIDO esperado={EXPECTED_COUNT} actual={len(rows)}"
            )

        normalized_source = {}

        for row in rows:
            code = row["codigo"]
            normalized = normalize_code(code)

            if not normalized:
                raise CommandError(f"CODIGO_VACIO={code!r}")

            if normalized in normalized_source:
                raise CommandError(
                    "DUPLICADO_EN_FUENTE "
                    f"{normalized_source[normalized]['codigo']} / {code}"
                )

            normalized_source[normalized] = row

        expected_normalized = {
            normalize_code(code)
            for code in EXPECTED_CODES
        }

        if set(normalized_source) != expected_normalized:
            missing = sorted(
                expected_normalized - set(normalized_source)
            )
            extra = sorted(
                set(normalized_source) - expected_normalized
            )
            raise CommandError(
                f"CODIGOS_NO_COINCIDEN missing={missing} extra={extra}"
            )

        try:
            empresa = Empresa.objects.get(pk=options["empresa_id"])
        except Empresa.DoesNotExist:
            raise CommandError(
                f"EMPRESA_NO_EXISTE={options['empresa_id']}"
            )

        if "atlanta" not in (empresa.nombre_taller or "").lower():
            raise CommandError(
                f"EMPRESA_NO_PARECE_ATLANTA={empresa.nombre_taller}"
            )

        self.stdout.write(
            f"EMPRESA_ID={empresa.pk} EMPRESA={empresa.nombre_taller}"
        )

        existing_by_norm = {}

        for cat in Catalitico.objects.filter(empresa=empresa):
            normalized = normalize_code(cat.codigo)

            if not normalized:
                continue

            existing_by_norm.setdefault(normalized, []).append(cat)

        logical_duplicates = {
            key: values
            for key, values in existing_by_norm.items()
            if len(values) > 1
        }

        if logical_duplicates:
            details = {
                key: [(x.pk, x.codigo) for x in values]
                for key, values in logical_duplicates.items()
            }
            raise CommandError(
                f"DUPLICADOS_NORMALIZADOS_EN_DB={details}"
            )

        plan = []

        for normalized, row in normalized_source.items():
            codigo = row["codigo"].strip()
            jorge = money(row["precio_jorge"])

            if jorge <= 0:
                raise CommandError(
                    f"PRECIO_JORGE_INVALIDO codigo={codigo} precio={jorge}"
                )

            matches = existing_by_norm.get(normalized, [])

            source_action = row.get("source_action")
            source_status = row.get("source_status")

            source_expects_update = (
                source_action == "ACTUALIZAR_VALOR_VENTA"
                and source_status == "EXISTENTE_CON_ACTUALIZACION"
            )
            source_expects_create = (
                source_action == "CREAR_CATALITICO"
                and source_status == "NUEVO"
            )

            if not (source_expects_update or source_expects_create):
                raise CommandError(
                    "CONTRATO_FUENTE_INVALIDO "
                    f"codigo={codigo} "
                    f"action={source_action!r} "
                    f"status={source_status!r}"
                )

            db_exists = len(matches) == 1

            if source_expects_update != db_exists:
                raise CommandError(
                    "CONTRATO_FUENTE_BD_NO_COINCIDE "
                    f"codigo={codigo} "
                    f"fuente={'UPDATE' if source_expects_update else 'CREATE'} "
                    f"bd={'EXISTE' if db_exists else 'NO_EXISTE'}"
                )

            if len(matches) == 1:
                cat = matches[0]

                plan.append(
                    {
                        "action": "UPDATE",
                        "codigo": codigo,
                        "object": cat,
                        "old_compra": cat.precio_compra,
                        "new_compra": cat.precio_compra,
                        "old_venta": cat.precio_venta,
                        "new_venta": jorge,
                    }
                )
            else:
                compra = (jorge * Decimal("0.50")).quantize(
                    Decimal("0.01"),
                    rounding=ROUND_HALF_UP,
                )

                plan.append(
                    {
                        "action": "CREATE",
                        "codigo": codigo,
                        "object": None,
                        "old_compra": None,
                        "new_compra": compra,
                        "old_venta": None,
                        "new_venta": jorge,
                    }
                )

        creates = sum(x["action"] == "CREATE" for x in plan)
        updates = sum(x["action"] == "UPDATE" for x in plan)

        self.stdout.write("")
        self.stdout.write("PLAN:")

        for item in sorted(plan, key=lambda x: x["codigo"]):
            self.stdout.write(
                f"{item['action']} "
                f"codigo={item['codigo']} "
                f"compra:{item['old_compra']}->{item['new_compra']} "
                f"venta:{item['old_venta']}->{item['new_venta']}"
            )

        self.stdout.write("")
        self.stdout.write(f"CREATE={creates}")
        self.stdout.write(f"UPDATE={updates}")
        self.stdout.write(f"TOTAL={len(plan)}")

        if not options["apply"]:
            self.stdout.write("MODE=DRY_RUN")
            self.stdout.write("WRITES=0")
            return

        self.stdout.write("MODE=APPLY")

        with transaction.atomic():
            locked = {
                normalize_code(cat.codigo): cat
                for cat in Catalitico.objects.select_for_update().filter(
                    empresa=empresa
                )
                if normalize_code(cat.codigo)
            }

            for item in plan:
                normalized = normalize_code(item["codigo"])

                if item["action"] == "UPDATE":
                    cat = locked.get(normalized)

                    if cat is None:
                        raise CommandError(
                            f"CAMBIO_CONCURRENTE_FALTA={item['codigo']}"
                        )

                    # Regla comercial:
                    # una nueva cotización Jorge actualiza reventa,
                    # nunca pisa automáticamente la oferta al cliente.
                    cat.precio_venta = item["new_venta"]
                    cat.save(
                        update_fields=[
                            "precio_venta",
                            "updated_at",
                        ]
                    )

                else:
                    if normalized in locked:
                        raise CommandError(
                            f"CAMBIO_CONCURRENTE_EXISTE={item['codigo']}"
                        )

                    Catalitico.objects.create(
                        empresa=empresa,
                        codigo=item["codigo"],
                        nombre="Catalítico",
                        tipo_catalizador=Catalitico.TIPO_DESCONOCIDO,
                        precio_compra=item["new_compra"],
                        precio_venta=item["new_venta"],
                        cantidad_stock=1,
                        estado=Catalitico.ESTADO_DISPONIBLE,
                        activo=True,
                        observaciones=(
                            "Precio de reventa confirmado por Jorge; "
                            "precio de compra inicial sugerido al 50%."
                        ),
                    )

        self.stdout.write(f"WRITES={len(plan)}")
        self.stdout.write("APPLY_OK=1")

    def extract_rows(self, payload):
        """
        Acepta únicamente la estructura confirmada de la auditoría.
        La detección es deliberadamente estricta: si el contrato cambia,
        el comando debe fallar en vez de adivinar.
        """

        candidates = None

        if isinstance(payload, dict):
            for key in (
                "final_confirmed",
                "confirmed",
                "confirmados",
                "rows",
            ):
                value = payload.get(key)
                if isinstance(value, list):
                    candidates = value
                    break

        elif isinstance(payload, list):
            candidates = payload

        if candidates is None:
            raise CommandError(
                "NO_SE_ENCONTRO_LISTA_CONFIRMADA_EN_JSON"
            )

        rows = []

        for idx, item in enumerate(candidates):
            if not isinstance(item, dict):
                raise CommandError(
                    f"FILA_NO_ES_OBJETO index={idx}"
                )

            codigo = (
                item.get("codigo")
                or item.get("code")
            )

            precio = (
                item.get("price_jorge")
                or item.get("precio_jorge")
                or item.get("precio")
                or item.get("price")
                or item.get("valor_venta")
            )

            if not codigo or precio is None:
                raise CommandError(
                    f"FILA_INCOMPLETA index={idx} keys={sorted(item.keys())}"
                )

            rows.append(
                {
                    "codigo": str(codigo).strip(),
                    "precio_jorge": precio,
                    "source_action": item.get("action"),
                    "source_status": item.get("status"),
                }
            )

        return rows
