# taller/management/commands/seed_demo_data.py

from __future__ import annotations

import random
import string
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

# Ajusta imports si tus apps/nombres difieren
from taller.models import (
    Empresa,
    Cliente,
    Vehiculo,
    Tecnico,
    Documento,
    LineaRepuesto,
    LineaServicio,
    LineaOtroServicio,
)

User = get_user_model()


def _rand_digits(n: int) -> str:
    return "".join(random.choice(string.digits) for _ in range(n))


def _rut_fake() -> str:
    # Rut fake simple (no validación dígito verificador)
    return f"{random.randint(5_000_000, 25_000_000)}-{random.randint(0, 9)}"


def _patente_chile() -> str:
    # Formato tipo "ABCD12" o "AB12CD"
    letters = "BCDFGHJKLPRSTVWXYZ"
    if random.random() < 0.5:
        return (
            random.choice(letters)
            + random.choice(letters)
            + random.choice(letters)
            + random.choice(letters)
            + _rand_digits(2)
        )
    return (
        random.choice(letters)
        + random.choice(letters)
        + _rand_digits(2)
        + random.choice(letters)
        + random.choice(letters)
    )


def _vin_fake() -> str:
    chars = "ABCDEFGHJKLMNPRSTUVWXYZ0123456789"
    return "".join(random.choice(chars) for _ in range(17))


def _money_clp(min_v: int, max_v: int) -> int:
    # CLP enteros
    return random.randint(min_v, max_v)


def _pick(seq):
    return random.choice(seq)


class Command(BaseCommand):
    help = "Puebla datos de prueba (Chile) para validar reportes: clientes, vehiculos, repuestos, documentos y lineas."

    def add_arguments(self, parser):
        parser.add_argument(
            "--admin-username", default="admin", help="Username del admin a usar (default: admin)."
        )
        parser.add_argument(
            "--empresa-id", type=int, default=None, help="ID de Empresa (si no se puede inferir)."
        )
        parser.add_argument(
            "--wipe",
            action="store_true",
            help="Borra solo los datos seed previos (tag SEED) de esa empresa.",
        )
        parser.add_argument(
            "--seed", type=int, default=1234, help="Seed aleatoria (default: 1234)."
        )

        parser.add_argument("--clientes", type=int, default=50)
        parser.add_argument("--vehiculos", type=int, default=60)
        parser.add_argument("--repuestos", type=int, default=50)
        parser.add_argument("--documentos", type=int, default=50)

    def _infer_empresa(self, admin_username: str, empresa_id: int | None):
        if empresa_id:
            try:
                return Empresa.objects.get(id=empresa_id)
            except Empresa.DoesNotExist:
                raise CommandError(f"No existe Empresa con id={empresa_id}")

        # 1) intenta por usuario admin -> si tienes perfil/relación, ajusta acá
        try:
            admin_user = User.objects.get(username=admin_username)
        except User.DoesNotExist:
            raise CommandError(f"No existe usuario username='{admin_username}'")

        # Casos comunes:
        # - admin_user.empresa
        # - admin_user.profile.empresa
        # - admin_user.empresas.first() (m2m)
        for attr_path in ("empresa", "profile.empresa"):
            obj = admin_user
            ok = True
            for part in attr_path.split("."):
                if not hasattr(obj, part):
                    ok = False
                    break
                obj = getattr(obj, part)
            if ok and obj:
                return obj

        if hasattr(admin_user, "empresas"):
            emp = admin_user.empresas.first()
            if emp:
                return emp

        # 2) fallback: primera Empresa Chile (si tienes campo pais)
        for field in ("pais", "country"):
            if hasattr(Empresa, field):
                kwargs = {field: "CL"}
                emp = Empresa.objects.filter(**kwargs).first()
                if emp:
                    return emp

        # 3) fallback total: primera empresa
        emp = Empresa.objects.first()
        if emp:
            return emp

        raise CommandError("No pude inferir Empresa. Crea una Empresa o usa --empresa-id.")

    def _ensure_tecnicos(self, empresa: Empresa) -> list[Tecnico]:
        """
        Garantiza 2 técnicos activos para repartir documentos/líneas.
        Ajusta nombres si lo necesitas.
        """
        qs = Tecnico.objects.filter(empresa=empresa, activo=True).order_by("id")
        tecnicos = list(qs[:2])

        # crea faltantes
        while len(tecnicos) < 2:
            idx = len(tecnicos) + 1
            t = Tecnico.objects.create(
                empresa=empresa,
                nombre=f"SEED Técnico {idx}",
                activo=True,
            )
            tecnicos.append(t)

        return tecnicos

    def _wipe_seed(self, empresa: Empresa):
        """
        Borra SOLO lo que creamos con el tag 'SEED-' en esa empresa.
        """
        # Documentos seed
        seed_docs = Documento.objects.filter(empresa=empresa, numero__startswith="SEED-")
        # líneas por reverse related_name (según tu pack: lineas_repuesto/servicio/otro_servicio)
        LineaRepuesto.objects.filter(documento__in=seed_docs).delete()
        LineaServicio.objects.filter(documento__in=seed_docs).delete()
        LineaOtroServicio.objects.filter(documento__in=seed_docs).delete()
        seed_docs.delete()

        # Vehículos seed
        Vehiculo.objects.filter(empresa=empresa, vin__startswith="SEEDVIN").delete()

        # Clientes seed
        Cliente.objects.filter(empresa=empresa, nombre__startswith="SEED ").delete()

        # Repuestos seed: depende de tu modelo (si tienes modelo Repuesto)
        # Como en tu pack las líneas guardan repuesto + nombre, aquí no borramos un modelo Repuesto específico
        # (si existe, agrega el delete aquí)

    @transaction.atomic
    def handle(self, *args, **opts):
        random.seed(opts["seed"])

        empresa = self._infer_empresa(opts["admin_username"], opts["empresa_id"])
        self.stdout.write(self.style.SUCCESS(f"Empresa objetivo: {empresa} (id={empresa.id})"))

        if opts["wipe"]:
            self.stdout.write("Wipe: borrando datos SEED previos...")
            self._wipe_seed(empresa)

        tecnicos = self._ensure_tecnicos(empresa)
        self.stdout.write(
            self.style.SUCCESS(f"Técnicos para reparto: {[t.nombre for t in tecnicos]}")
        )

        # ---------- Crear clientes ----------
        clientes = []
        for i in range(opts["clientes"]):
            c = Cliente.objects.create(
                empresa=empresa,
                nombre=f"SEED Cliente {i+1:02d}",
                rut=_rut_fake() if hasattr(Cliente, "rut") else None,
                ein=_rand_digits(9) if hasattr(Cliente, "ein") else None,
                contacto=f"+56 9 {_rand_digits(8)}" if hasattr(Cliente, "contacto") else None,
            )
            clientes.append(c)

        self.stdout.write(self.style.SUCCESS(f"Clientes creados: {len(clientes)}"))

        # ---------- Crear vehículos ----------
        marcas = [
            "Toyota",
            "Hyundai",
            "Kia",
            "Chevrolet",
            "Nissan",
            "Ford",
            "Mazda",
            "VW",
            "Peugeot",
            "Renault",
        ]
        modelos = [
            "Corolla",
            "Yaris",
            "Accent",
            "Rio",
            "Spark",
            "Versa",
            "Ranger",
            "CX-5",
            "Gol",
            "208",
            "Duster",
        ]
        vehiculos = []
        # asigna varios vehículos a algunos clientes
        for i in range(opts["vehiculos"]):
            cliente = random.choice(clientes)
            v = Vehiculo.objects.create(
                empresa=empresa,
                cliente=cliente,
                patente=_patente_chile() if hasattr(Vehiculo, "patente") else None,
                vin=f"SEEDVIN{_vin_fake()}" if hasattr(Vehiculo, "vin") else None,
                marca=_pick(marcas) if hasattr(Vehiculo, "marca") else None,
                modelo=_pick(modelos) if hasattr(Vehiculo, "modelo") else None,
            )
            vehiculos.append(v)

        self.stdout.write(self.style.SUCCESS(f"Vehículos creados: {len(vehiculos)}"))

        # ---------- “Catálogo” de repuestos (para líneas) ----------
        repuestos = []
        rep_nombres = [
            "Pastillas de freno",
            "Disco de freno",
            "Filtro de aceite",
            "Filtro de aire",
            "Bujías",
            "Correa de distribución",
            "Amortiguador",
            "Batería",
            "Radiador",
            "Bomba de agua",
            "Alternador",
            "Motor de partida",
            "Sensor O2",
            "Bobina",
            "Termostato",
        ]
        for i in range(opts["repuestos"]):
            part_number = f"SEED-PN-{i+1:04d}"
            nombre = f"{_pick(rep_nombres)} {part_number}"
            # guardamos como dict porque tu pack indica que la línea tiene repuesto (FK) + nombre
            repuestos.append(
                {
                    "part_number": part_number,
                    "nombre": nombre,
                    "precio": _money_clp(8_000, 180_000),
                }
            )

        self.stdout.write(self.style.SUCCESS(f"Repuestos “base” preparados: {len(repuestos)}"))

        # ---------- Tipos de documentos ----------
        # Ajusta a tus choices reales si son distintos.
        tipos = []
        if hasattr(Documento, "TIPO_CHOICES"):
            # si existe una constante propia
            tipos = [t[0] for t in Documento.TIPO_CHOICES]
        else:
            # fallback genérico (ajusta si tu app usa otros códigos)
            tipos = ["PRESUPUESTO", "OT", "FACTURA", "BOLETA"]

        estados = []
        if hasattr(Documento, "ESTADO_CHOICES"):
            estados = [e[0] for e in Documento.ESTADO_CHOICES]
        else:
            estados = ["BORRADOR", "EMITIDO", "PAGADO"]

        # ---------- Crear documentos + líneas ----------
        documentos = []
        today = timezone.localdate()

        for i in range(opts["documentos"]):
            cliente = random.choice(clientes)
            vehiculo = random.choice(
                [v for v in vehiculos if v.cliente_id == cliente.id] or vehiculos
            )

            tecnico_doc = tecnicos[i % 2]  # reparto 50/50 entre 2 técnicos
            fecha = today - timedelta(days=random.randint(0, 180))
            tipo = random.choice(tipos)
            estado = random.choice(estados)

            # numero: tag SEED para poder borrar fácil
            numero = f"SEED-{tipo[:3]}-{i+1:04d}"

            doc = Documento.objects.create(
                empresa=empresa,
                cliente=cliente,
                vehiculo=vehiculo,
                tipo=tipo if hasattr(Documento, "tipo") else None,
                estado=estado if hasattr(Documento, "estado") else None,
                fecha_emision=fecha,
                tecnico_responsable=(
                    tecnico_doc if hasattr(Documento, "tecnico_responsable") else None
                ),
                numero=numero if hasattr(Documento, "numero") else None,
            )
            documentos.append(doc)

            # --- 4 repuestos ---
            for _ in range(4):
                r = random.choice(repuestos)
                cantidad = random.randint(1, 4)
                precio = r["precio"]
                descuento = random.choice([0, 0, 0, 5, 10])  # %
                subtotal = int(cantidad * precio * (1 - (descuento / 100)))

                LineaRepuesto.objects.create(
                    documento=doc,
                    repuesto=(
                        None if not hasattr(LineaRepuesto, "repuesto") else None
                    ),  # si tu FK existe, aquí debes setearlo
                    nombre=r["nombre"],
                    cantidad=cantidad,
                    precio_unitario=precio,
                    descuento=descuento,
                    subtotal=subtotal,
                    # si tu línea tiene técnico/mecánico, lo alternamos también:
                    **(
                        {"tecnico": tecnicos[(i + _) % 2]}
                        if hasattr(LineaRepuesto, "tecnico")
                        else {}
                    ),
                )

            # --- 3 servicios ---
            servicios_base = [
                "Cambio de aceite",
                "Alineación",
                "Balanceo",
                "Diagnóstico scanner",
                "Cambio pastillas freno",
                "Limpieza inyectores",
                "Revisión general",
            ]
            for j in range(3):
                nombre_serv = random.choice(servicios_base)
                cantidad = 1
                precio = _money_clp(15_000, 120_000)
                descuento = random.choice([0, 0, 10])
                subtotal = int(cantidad * precio * (1 - (descuento / 100)))

                LineaServicio.objects.create(
                    documento=doc,
                    servicio=None if not hasattr(LineaServicio, "servicio") else None,
                    nombre=nombre_serv,
                    cantidad=cantidad,
                    precio_unitario=precio,
                    descuento=descuento,
                    subtotal=subtotal,
                    **(
                        {"tecnico": tecnicos[(i + j) % 2]}
                        if hasattr(LineaServicio, "tecnico")
                        else {}
                    ),
                )

            # --- 2 servicios externos ---
            externos = [
                ("Rectificadora Andes", "Rectificado culata"),
                ("ElectroAuto Central", "Reparación alternador"),
                ("AirePro", "Carga A/C"),
                ("Tapicería Premium", "Reparación tapiz"),
            ]
            for j in range(2):
                empresa_externa, nombre_ext = random.choice(externos)
                cantidad = 1
                costo = _money_clp(20_000, 150_000)
                ganancia = _money_clp(5_000, 60_000)
                precio_cliente = costo + ganancia

                LineaOtroServicio.objects.create(
                    documento=doc,
                    servicio=None if not hasattr(LineaOtroServicio, "servicio") else None,
                    nombre=nombre_ext,
                    empresa_externa=empresa_externa,
                    cantidad=cantidad,
                    costo_interno=costo,
                    precio_cliente=precio_cliente,
                    ganancia=ganancia,
                    **(
                        {"tecnico": tecnicos[(i + j) % 2]}
                        if hasattr(LineaOtroServicio, "tecnico")
                        else {}
                    ),
                )

        self.stdout.write(self.style.SUCCESS(f"Documentos creados: {len(documentos)}"))
        self.stdout.write(
            self.style.SUCCESS("OK: Seed finalizado. Ya puedes validar reportes/KPIs.")
        )
        self.stdout.write("Tip: si quieres borrar todo lo seed, vuelve a correr con --wipe.")
