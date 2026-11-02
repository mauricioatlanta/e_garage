from datetime import timedelta
from decimal import Decimal
from random import choice, randint

from django.apps import apps
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone


DEMO = "[DEMO_PUBLICIDAD]"


CATALOGO = [
    {
        "marca": "Toyota",
        "modelo": "Corolla",
        "motores": ["1.6 1ZR-FE", "1.8 2ZR-FE"],
        "cajas": ["Manual 6MT", "Automática CVT"],
    },
    {
        "marca": "Hyundai",
        "modelo": "Accent",
        "motores": ["1.4 Kappa", "1.6 Gamma"],
        "cajas": ["Manual 6MT", "Automática 6AT"],
    },
    {
        "marca": "Kia",
        "modelo": "Rio",
        "motores": ["1.4 MPI", "1.6 MPI"],
        "cajas": ["Manual 6MT", "Automática 6AT"],
    },
    {
        "marca": "Chevrolet",
        "modelo": "Sail",
        "motores": ["1.4 S-TEC", "1.5 DVVT"],
        "cajas": ["Manual 5MT", "Automática 4AT"],
    },
    {
        "marca": "Nissan",
        "modelo": "Versa",
        "motores": ["1.6 HR16DE"],
        "cajas": ["Manual 5MT", "Automática CVT"],
    },
    {
        "marca": "Mazda",
        "modelo": "3",
        "motores": ["2.0 Skyactiv-G", "2.5 Skyactiv-G"],
        "cajas": ["Manual 6MT", "Automática 6AT"],
    },
    {
        "marca": "Suzuki",
        "modelo": "Swift",
        "motores": ["1.2 Dualjet", "1.4 Boosterjet"],
        "cajas": ["Manual 5MT", "Automática CVT"],
    },
    {
        "marca": "Ford",
        "modelo": "Ranger",
        "motores": ["2.2 TDCi", "3.2 Duratorq"],
        "cajas": ["Manual 6MT", "Automática 6AT"],
    },
    {
        "marca": "Peugeot",
        "modelo": "208",
        "motores": ["1.2 PureTech", "1.6 BlueHDi"],
        "cajas": ["Manual 5MT", "Automática 6AT"],
    },
    {
        "marca": "Volkswagen",
        "modelo": "Gol",
        "motores": ["1.6 MSI", "1.0 MPI"],
        "cajas": ["Manual 5MT"],
    },
]


REPUESTOS = [
    ("Filtro de aceite", 8900),
    ("Pastillas de freno", 34900),
    ("Bujías", 24900),
    ("Aceite motor 5W30", 45900),
    ("Filtro de aire", 12900),
    ("Amortiguador delantero", 89900),
    ("Batería 60Ah", 79900),
    ("Correa accesorios", 29900),
]

SERVICIOS = [
    ("Mantención general", 45000),
    ("Cambio de aceite", 25000),
    ("Diagnóstico scanner", 30000),
    ("Cambio de pastillas", 35000),
    ("Alineación y balanceo", 40000),
    ("Revisión pre técnica", 28000),
]

EXTERNOS = [
    ("Rectificación de disco", "Rectificadora externa", 18000, 35000),
    ("Lavado premium", "Carwash aliado", 12000, 30000),
    ("Reparación tapiz", "Tapicería externa", 25000, 55000),
    ("Polarizado", "Láminas externas", 30000, 70000),
]


class Command(BaseCommand):
    help = "Pobla datos demo completos para mauricioatlanta@gmail.com"

    def add_arguments(self, parser):
        parser.add_argument("--email", default="mauricioatlanta@gmail.com")
        parser.add_argument("--clear-demo", action="store_true")

    def get_model_or_none(self, name):
        try:
            return apps.get_model("taller", name)
        except Exception:
            return None

    def clean_kwargs(self, Model, kwargs):
        valid = {f.name for f in Model._meta.fields}
        return {k: v for k, v in kwargs.items() if k in valid}

    def create_obj(self, Model, **kwargs):
        return Model.objects.create(**self.clean_kwargs(Model, kwargs))

    def get_or_create_flexible(self, Model, defaults=None, **lookup):
        defaults = defaults or {}
        lookup = self.clean_kwargs(Model, lookup)
        defaults = self.clean_kwargs(Model, defaults)
        return Model.objects.get_or_create(defaults=defaults, **lookup)

    def assign_first_existing_field(self, obj, candidates, value):
        for field in candidates:
            if hasattr(obj, field):
                setattr(obj, field, value)
                return field
        return None

    def ensure_catalogo_modelos_motores_cajas(self, empresa):
        MarcaVehiculo = None
        ModeloVehiculo = None
        Motor = None
        Caja = None

        created = {
            "marcas": 0,
            "modelos": 0,
            "motores": 0,
            "cajas": 0,
        }

        marcas_obj = {}
        modelos_obj = {}
        motores_obj = {}
        cajas_obj = {}

        for item in CATALOGO:
            marca_nombre = item["marca"]
            modelo_nombre = item["modelo"]

            marca_obj = marca_nombre
            if MarcaVehiculo:
                lookup = {"nombre": marca_nombre}
                if hasattr(MarcaVehiculo, "empresa"):
                    lookup["empresa"] = empresa
                marca_obj, was_created = self.get_or_create_flexible(
                    MarcaVehiculo,
                    **lookup,
                    defaults={"activo": True},
                )
                created["marcas"] += int(was_created)

            modelo_obj = modelo_nombre
            if ModeloVehiculo:
                lookup = {"nombre": modelo_nombre}
                if hasattr(ModeloVehiculo, "empresa"):
                    lookup["empresa"] = empresa
                if hasattr(ModeloVehiculo, "marca"):
                    lookup["marca"] = marca_obj
                modelo_obj, was_created = self.get_or_create_flexible(
                    ModeloVehiculo,
                    **lookup,
                    defaults={"activo": True},
                )
                created["modelos"] += int(was_created)

            marcas_obj[marca_nombre] = marca_obj
            modelos_obj[(marca_nombre, modelo_nombre)] = modelo_obj

            for motor_nombre in item["motores"]:
                motor_obj = motor_nombre
                if Motor:
                    lookup = {"nombre": motor_nombre}
                    if hasattr(Motor, "empresa"):
                        lookup["empresa"] = empresa
                    if hasattr(Motor, "marca"):
                        lookup["marca"] = marca_obj
                    if hasattr(Motor, "modelo"):
                        lookup["modelo"] = modelo_obj
                    motor_obj, was_created = self.get_or_create_flexible(
                        Motor,
                        **lookup,
                        defaults={"activo": True},
                    )
                    created["motores"] += int(was_created)
                motores_obj[(marca_nombre, modelo_nombre, motor_nombre)] = motor_obj

            for caja_nombre in item["cajas"]:
                caja_obj = caja_nombre
                if Caja:
                    lookup = {"nombre": caja_nombre}
                    if hasattr(Caja, "empresa"):
                        lookup["empresa"] = empresa
                    if hasattr(Caja, "marca"):
                        lookup["marca"] = marca_obj
                    if hasattr(Caja, "modelo"):
                        lookup["modelo"] = modelo_obj
                    caja_obj, was_created = self.get_or_create_flexible(
                        Caja,
                        **lookup,
                        defaults={"activo": True},
                    )
                    created["cajas"] += int(was_created)
                cajas_obj[(marca_nombre, modelo_nombre, caja_nombre)] = caja_obj

        return marcas_obj, modelos_obj, motores_obj, cajas_obj, created

    @transaction.atomic
    def handle(self, *args, **opts):
        email = opts["email"]

        User = get_user_model()
        user = User.objects.filter(email=email).first()
        if not user:
            raise SystemExit(f"No existe usuario con email {email}")

        empresa = getattr(user, "empresa", None)
        if not empresa:
            Empresa = apps.get_model("taller", "Empresa")
            empresa = Empresa.objects.first()
            if hasattr(user, "empresa") and empresa:
                user.empresa = empresa
                user.save(update_fields=["empresa"])

        if not empresa:
            raise SystemExit("No se encontró empresa para poblar datos.")

        Cliente = apps.get_model("taller", "Cliente")
        Vehiculo = apps.get_model("taller", "Vehiculo")
        Documento = apps.get_model("taller", "Documento")
        Tecnico = apps.get_model("taller", "Tecnico")
        Repuesto = apps.get_model("taller", "Repuesto")
        LineaRepuesto = apps.get_model("taller", "LineaRepuesto")
        LineaServicio = apps.get_model("taller", "LineaServicio")
        LineaOtroServicio = apps.get_model("taller", "LineaOtroServicio")

        if opts["clear_demo"]:
            Documento.objects.filter(empresa=empresa, observaciones__icontains=DEMO).delete()
            Vehiculo.objects.filter(empresa=empresa, observaciones_desarme__icontains=DEMO).delete()
            Cliente.objects.filter(empresa=empresa, nombre__startswith="Cliente Demo").delete()
            Tecnico.objects.filter(empresa=empresa, nombre__startswith="Mecánico Demo").delete()

        Marca = apps.get_model("taller", "Marca")
        Modelo = apps.get_model("taller", "Modelo")
        MotorVehiculo = apps.get_model("taller", "MotorVehiculo")
        CajaVehiculo = apps.get_model("taller", "CajaVehiculo")

        marcas_obj = {}
        modelos_obj = {}
        motores_obj = {}
        cajas_obj = {}
        catalog_counts = {"marcas": 0, "modelos": 0, "motores": 0, "cajas": 0}

        for item in CATALOGO:
            marca_obj = Marca.objects.filter(nombre__iexact=item["marca"]).first()
            if not marca_obj:
                marca_obj = Marca.objects.create(nombre=item["marca"], country="CL")
                catalog_counts["marcas"] += 1

            modelo_obj = Modelo.objects.filter(
                nombre__iexact=item["modelo"],
                marca=marca_obj,
            ).first()
            if not modelo_obj:
                modelo_obj = Modelo.objects.create(
                    nombre=item["modelo"],
                    marca=marca_obj,
                    country="CL",
                )
                catalog_counts["modelos"] += 1

            marcas_obj[item["marca"]] = marca_obj
            modelos_obj[(item["marca"], item["modelo"])] = modelo_obj

            for motor_nombre in item["motores"]:
                motor_obj = MotorVehiculo.objects.filter(nombre__iexact=motor_nombre).first()
                if not motor_obj:
                    motor_obj = MotorVehiculo.objects.create(nombre=motor_nombre, country="CL")
                    catalog_counts["motores"] += 1
                motores_obj[(item["marca"], item["modelo"], motor_nombre)] = motor_obj

            for caja_nombre in item["cajas"]:
                caja_obj = CajaVehiculo.objects.filter(nombre__iexact=caja_nombre).first()
                if not caja_obj:
                    caja_obj = CajaVehiculo.objects.create(nombre=caja_nombre, country="CL")
                    catalog_counts["cajas"] += 1
                cajas_obj[(item["marca"], item["modelo"], caja_nombre)] = caja_obj

        mecanicos = []
        for nombre in ["Mecánico Demo A", "Mecánico Demo B", "Mecánico Demo C"]:
            obj, _ = self.get_or_create_flexible(
                Tecnico,
                empresa=empresa,
                nombre=nombre,
                defaults={"activo": True},
            )
            mecanicos.append(obj)

        documentos_creados = 0
        vehiculos_creados = 0
        clientes_creados = 0

        TallerRegion = apps.get_model("taller", "TallerRegion")
        TallerCiudad = apps.get_model("taller", "TallerCiudad")
        ColorVehiculo = apps.get_model("taller", "ColorVehiculo")

        colores_demo = list(
            ColorVehiculo.objects.all()[:20]
        )

        if not colores_demo:
            raise SystemExit("NO_EXISTEN_COLORES_EN_COLORVEHICULO")

        region_demo = (
            TallerRegion.objects.filter(nombre__icontains="Valpara").first()
            or TallerRegion.objects.first()
        )
        ciudad_demo = (
            TallerCiudad.objects.filter(region=region_demo, nombre__icontains="Viña").first()
            or TallerCiudad.objects.filter(region=region_demo).first()
            or TallerCiudad.objects.first()
        )

        for i in range(1, 11):
            cliente = self.create_obj(
                Cliente,
                empresa=empresa,
                nombre=f"Cliente Demo {i:02d}",
                rut=f"{randint(10000000, 22000000)}-{randint(0, 9)}",
                telefono=f"+569{randint(10000000, 99999999)}",
                email=f"cliente.demo{i}@egarage.cl",
                direccion=f"Av. Demo {i * 123}",
                ciudad=ciudad_demo,
                region=region_demo,
            )
            clientes_creados += 1

            vehiculos = []
            for j in range(1, 3):
                item = choice(CATALOGO)
                marca_nombre = item["marca"]
                modelo_nombre = item["modelo"]
                motor_nombre = choice(item["motores"])
                caja_nombre = choice(item["cajas"])

                marca_value = marcas_obj.get(marca_nombre, marca_nombre)
                modelo_value = modelos_obj.get((marca_nombre, modelo_nombre), modelo_nombre)
                motor_value = motores_obj.get((marca_nombre, modelo_nombre, motor_nombre), motor_nombre)
                caja_value = cajas_obj.get((marca_nombre, modelo_nombre, caja_nombre), caja_nombre)

                vehiculo = Vehiculo(
                    **self.clean_kwargs(
                        Vehiculo,
                        {
                            "empresa": empresa,
                            "cliente": cliente,
                            "patente": f"DM{i}{j}{randint(10, 99)}",
                            "anio": randint(2014, 2024),
                            "color": choice(colores_demo),
                            "vin": f"VINDEMO{i:02d}{j:02d}{randint(100000,999999)}",
                            "observaciones_desarme": f"{DEMO} Vehículo creado para pruebas comerciales.",
                        },
                    )
                )

                self.assign_first_existing_field(vehiculo, ["marca"], marca_value)
                self.assign_first_existing_field(vehiculo, ["modelo"], modelo_value)
                self.assign_first_existing_field(vehiculo, ["motor"], motor_value)
                self.assign_first_existing_field(vehiculo, ["caja", "transmision", "transmisión"], caja_value)

                vehiculo.save()
                vehiculos.append(vehiculo)
                vehiculos_creados += 1

            for d in range(1, 6):
                fecha = timezone.now().date() - timedelta(days=randint(0, 90))
                mecanico = choice(mecanicos)
                vehiculo = choice(vehiculos)

                documento = self.create_obj(
                    Documento,
                    empresa=empresa,
                    cliente=cliente,
                    vehiculo=vehiculo,
                    tecnico_responsable=mecanico,
                    mecanico=mecanico,
                    fecha_emision=fecha,
                    tipo=choice(["OT", "FAC", "PRE"]),
                    estado=choice(["BORRADOR", "EN_PROCESO", "PAGADO", "FINALIZADO"]),
                    observaciones=f"{DEMO} Documento generado para reportes y capturas.",
                    created_by=user,
                    updated_by=user,
                )

                total_repuestos = Decimal("0")
                total_servicios = Decimal("0")
                total_externos = Decimal("0")

                repuestos_db = list(
                    Repuesto.objects.filter(empresa=empresa)[:20]
                )

                if not repuestos_db:
                    for idx, (nombre_rep, precio_rep) in enumerate(REPUESTOS, start=1):
                        Repuesto.objects.create(
                            empresa=empresa,
                            part_number=f"DEMO-REP-{idx:03d}",
                            nombre=nombre_rep,
                            precio_compra=Decimal(precio_rep) * Decimal("0.55"),
                            precio_venta=Decimal(precio_rep),
                            cantidad_stock=50,
                            proveedor="Proveedor Demo eGarage",
                        )

                    repuestos_db = list(
                        Repuesto.objects.filter(empresa=empresa)[:20]
                    )

                for _ in range(3):
                    repuesto = choice(repuestos_db)

                    precio = (
                        repuesto.precio_venta
                        or Decimal("19990")
                    )

                    cantidad = randint(1, 3)
                    subtotal = Decimal(precio) * cantidad

                    codigo = (
                        repuesto.part_number
                        or f"REP-{repuesto.id}"
                    )

                    self.create_obj(
                        LineaRepuesto,
                        documento=documento,
                        repuesto=repuesto,
                        codigo=codigo[:50],
                        nombre=repuesto.nombre[:255],
                        cantidad=cantidad,
                        precio_unitario=precio,
                        descuento=0,
                        observaciones="Demo publicidad",
                        tecnico_responsable=mecanico,
                    )

                    total_repuestos += subtotal

                for _ in range(2):
                    nombre, precio = choice(SERVICIOS)
                    subtotal = Decimal(precio)

                    self.create_obj(
                        LineaServicio,
                        documento=documento,
                        nombre=nombre,
                        cantidad=1,
                        precio_unitario=precio,
                        descuento=0,
                        subtotal=subtotal,
                        mecanico=mecanico,
                        tecnico_responsable=mecanico,
                    )
                    total_servicios += subtotal

                nombre, empresa_externa, costo, precio_cliente = choice(EXTERNOS)
                ganancia = Decimal(precio_cliente - costo)

                self.create_obj(
                    LineaOtroServicio,
                    documento=documento,
                    nombre=nombre,
                    empresa_externa=empresa_externa,
                    cantidad=1,
                    costo_interno=costo,
                    precio_cliente=precio_cliente,
                    observaciones=f"Ganancia demo: {ganancia}",
                    tecnico_responsable=mecanico,
                )
                total_externos += Decimal(precio_cliente)

                neto = total_repuestos + total_servicios + total_externos
                iva = (total_repuestos * Decimal("0.19")).quantize(Decimal("1"))
                total = neto + iva
                pagado = total if randint(1, 100) <= 70 else (total * Decimal("0.5")).quantize(Decimal("1"))
                saldo = total - pagado

                update_map = {
                    "subtotal": neto,
                    "neto": neto,
                    "iva": iva,
                    "total": total,
                    "total_general": total,
                    "monto_total": total,
                    "monto_pagado": pagado,
                    "saldo_pendiente": saldo,
                }

                for field, value in update_map.items():
                    if hasattr(documento, field):
                        setattr(documento, field, value)

                documento.save()
                documentos_creados += 1

        self.stdout.write(self.style.SUCCESS("DATA_DEMO_OK"))
        self.stdout.write(f"Empresa: {empresa}")
        self.stdout.write(f"Catálogo creado: {catalog_counts}")
        self.stdout.write(f"Clientes: {clientes_creados}")
        self.stdout.write(f"Vehículos: {vehiculos_creados}")
        self.stdout.write(f"Documentos: {documentos_creados}")
        self.stdout.write("Mecánicos: 3")
