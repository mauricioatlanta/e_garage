# -*- coding: utf-8 -*-
"""
Seed para la empresa GEORGE AUTO REPAIR:
- 10 clientes (3 con más de un vehículo)
- 15 repuestos (proveedores: AutoZone / NAPA)
- 10 documentos (cada uno con >1 repuesto, >1 servicio, >1 otro servicio)
- 2 compras (AutoZone y NAPA) con líneas de detalle si el modelo existe

Uso:
    python manage.py seed_george_auto_repair --company "GEORGE AUTO REPAIR"
Opcionales:
    --clients 10 --extra-vehicle-clients 3 --parts 15 --docs 10
"""

import random
from datetime import timedelta

from django.apps import apps
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from taller.models import (ConfiguracionEmpresa, Documento, Empresa,
                           LineaOtroServicio, LineaRepuesto, LineaServicio,
                           Repuesto, Tecnico)
from taller.models.clientes import Cliente
from taller.models.marca import Marca
from taller.models.modelo import Modelo
from taller.models.vehiculos import Vehiculo
from taller.servicios.models import (CategoriaServicio, Servicio,
                                     SubcategoriaServicio)

RND = random.Random(42)


def has_field(model, field_name: str) -> bool:
    try:
        model._meta.get_field(field_name)
        return True
    except Exception:
        return False


def get_model(app_label, names):
    """Devuelve el primer modelo existente por nombre de la lista."""
    for n in names:
        try:
            m = apps.get_model(app_label, n)
            if m:
                return m
        except Exception:
            pass
    return None


def pick_document_types():
    field = Documento._meta.get_field("tipo")
    choices = getattr(field, "choices", None) or []
    if choices:
        return [c[0] for c in choices]
    return [
        "PRESUPUESTO",
        "ORDEN_TRABAJO",
        "FACTURA",
        "BOLETA",
        "GUIA_DESPACHO",
        "NOTA_CREDITO",
        "NOTA_DEBITO",
        "DIAGNOSTICO",
        "COTIZACION",
        "PROFORMA",
    ]


def get_empresa_by_name(company_name: str):
    # Primero buscar por nombre_taller en Empresa
    try:
        return Empresa.objects.get(nombre_taller__iexact=company_name)
    except Empresa.DoesNotExist:
        pass

    # Luego buscar por empresa en Empresa
    try:
        return Empresa.objects.get(empresa__iexact=company_name)
    except Empresa.DoesNotExist:
        pass

    # Finalmente buscar en ConfiguracionEmpresa
    try:
        ce = ConfiguracionEmpresa.objects.get(nombre_publico__iexact=company_name)
        if hasattr(ce, "empresa") and ce.empresa_id:
            return ce.empresa
    except ConfiguracionEmpresa.DoesNotExist:
        pass

    raise Empresa.DoesNotExist(
        f"No se encontró la Empresa con nombre '{company_name}' en nombre_taller, empresa o nombre_publico"
    )


def get_or_create_tecnicos(empresa):
    """Crea 7 técnicos realistas para la empresa"""
    nombres_tecnicos = [
        "Mike Johnson",
        "Carlos Rodriguez",
        "David Thompson",
        "Robert Martinez",
        "James Wilson",
        "Anthony Garcia",
        "Kevin Anderson",
    ]

    tecnicos = []
    for nombre in nombres_tecnicos:
        tech, created = Tecnico.objects.get_or_create(
            empresa=empresa, nombre=nombre, defaults={"activo": True}
        )
        tecnicos.append(tech)

    return tecnicos


def make_fake_patente(i):
    return f"GT-{i:03d}{RND.randint(10,99)}"


def make_fake_vin(i):
    base = "1HGCM82633A"
    return f"{base}{i:06d}"[:17]


def ensure_marcas_y_modelos(empresa):
    """Crea marcas y modelos básicos si no existen"""
    bank = [
        ("Toyota", ["Corolla", "Camry", "RAV4", "Tacoma"]),
        ("Honda", ["Civic", "Accord", "CR-V", "Pilot"]),
        ("Ford", ["F-150", "Focus", "Fusion", "Escape"]),
        ("Chevrolet", ["Silverado", "Cruze", "Equinox", "Malibu"]),
        ("Nissan", ["Sentra", "Altima", "Rogue", "Frontier"]),
        ("Hyundai", ["Elantra", "Tucson", "Santa Fe", "Sonata"]),
        ("Kia", ["Rio", "Sportage", "Sorento", "Forte"]),
    ]

    marcas_creadas = {}
    for marca_nombre, modelos_list in bank:
        # Obtener marca existente o crear nueva
        try:
            marca = Marca.objects.filter(nombre=marca_nombre).first()
            if not marca:
                marca = Marca.objects.create(
                    nombre=marca_nombre, country=getattr(empresa, "pais", "CL")
                )
        except Exception:
            # Si hay múltiples, tomar la primera
            marca = Marca.objects.filter(nombre=marca_nombre).first()

        marcas_creadas[marca_nombre] = marca

        # Crear modelos para esta marca
        for modelo_nombre in modelos_list:
            try:
                Modelo.objects.get_or_create(
                    nombre=modelo_nombre,
                    marca=marca,
                    defaults={"country": marca.country},
                )
            except Exception:
                # Si ya existe, continuar
                pass

    return marcas_creadas


def pick_brand_model():
    bank = [
        ("Toyota", ["Corolla", "Camry", "RAV4", "Tacoma"]),
        ("Honda", ["Civic", "Accord", "CR-V", "Pilot"]),
        ("Ford", ["F-150", "Focus", "Fusion", "Escape"]),
        ("Chevrolet", ["Silverado", "Cruze", "Equinox", "Malibu"]),
        ("Nissan", ["Sentra", "Altima", "Rogue", "Frontier"]),
        ("Hyundai", ["Elantra", "Tucson", "Santa Fe", "Sonata"]),
        ("Kia", ["Rio", "Sportage", "Sorento", "Forte"]),
    ]
    marca, modelos = RND.choice(bank)
    modelo = RND.choice(modelos)
    return marca, modelo


def ensure_servicios_basicos(empresa):
    # Obtener el país de la empresa
    empresa_pais = getattr(empresa, "pais", "CL")

    # Crear categoría básica si no existe
    categoria, _ = CategoriaServicio.objects.get_or_create(
        code="MANTENIMIENTO", defaults={"country": empresa_pais}
    )

    # Crear subcategoría básica si no existe
    subcategoria, _ = SubcategoriaServicio.objects.get_or_create(
        code="GENERAL", categoria=categoria, defaults={"country": empresa_pais}
    )

    nombres = [
        "Cambio de aceite",
        "Alineación y balanceo",
        "Revisión de frenos",
        "Diagnóstico general",
        "Cambio de bujías",
        "Limpieza de inyectores",
        "Cambio de batería",
        "Ajuste de correas",
        "Revisión suspensión",
        "Cambio de filtro de aire",
    ]
    servicios = []
    for n in nombres:
        defaults = {"categoria": categoria, "subcategoria": subcategoria}
        if has_field(Servicio, "precio_base"):
            defaults["precio_base"] = RND.randint(45, 120)  # USD: $45-$120
        obj, _ = Servicio.objects.get_or_create(
            empresa=empresa, nombre=n, categoria=categoria, defaults=defaults
        )
        servicios.append(obj)
    return servicios


def ensure_repuestos(empresa, total_parts=15):
    proveedores = ["AutoZone", "NAPA"]
    nombres = [
        "Filtro de aceite",
        "Filtro de aire",
        "Pastillas de freno",
        "Batería 12V",
        "Amortiguador delantero",
        "Correa de distribución",
        "Bujía iridio",
        "Aceite sintético 5W-30",
        "Sensor de oxígeno",
        "Bobina de encendido",
        "Bomba de agua",
        "Termostato",
        "Alternador",
        "Radiador",
        "Filtro de combustible",
        "Kit embrague",
        "Disco de freno",
        "Lámpara H7",
        "Líquido frenos DOT4",
    ]
    RND.shuffle(nombres)
    repuestos = []
    for i in range(total_parts):
        name = nombres[i % len(nombres)]
        prov = proveedores[i % len(proveedores)]
        defaults = {}
        if has_field(Repuesto, "part_number"):
            defaults["part_number"] = f"{prov[:2].upper()}-{RND.randint(100000,999999)}"
        if has_field(Repuesto, "precio_compra"):
            defaults["precio_compra"] = RND.randint(15, 80)  # USD: $15-$80
        if has_field(Repuesto, "precio_venta"):
            defaults["precio_venta"] = RND.randint(25, 150)  # USD: $25-$150
        if has_field(Repuesto, "proveedor"):
            defaults["proveedor"] = prov
        if has_field(Repuesto, "marca"):
            defaults.setdefault("marca", prov)

        obj, _ = Repuesto.objects.get_or_create(
            empresa=empresa, nombre=f"{name} ({prov})", defaults=defaults
        )
        repuestos.append(obj)
    return repuestos


def create_clientes_y_vehiculos(
    empresa, marcas_creadas, total_clients=10, extra_vehicle_clients=3
):
    first_names = [
        "George",
        "Anna",
        "Mike",
        "Laura",
        "Carlos",
        "Sofía",
        "Diego",
        "Marta",
        "James",
        "Patricia",
        "Kevin",
    ]
    last_names = [
        "Brown",
        "Smith",
        "Johnson",
        "Martínez",
        "González",
        "Díaz",
        "Ramírez",
        "Taylor",
        "Anderson",
        "Moore",
    ]
    clientes, vehiculos = [], []

    for i in range(total_clients):
        name = f"{RND.choice(first_names)} {RND.choice(last_names)}"
        kwargs = dict(empresa=empresa, nombre=name)
        if has_field(Cliente, "rut"):
            kwargs["rut"] = f"1{i}23456-{RND.randint(0,9)}"
        if has_field(Cliente, "ein"):
            kwargs["ein"] = f"9{i}{RND.randint(100000,999999)}"
        cli, _ = Cliente.objects.get_or_create(**kwargs)
        clientes.append(cli)

    multi_idx = RND.sample(
        range(total_clients), k=min(extra_vehicle_clients, total_clients)
    )
    for idx, cli in enumerate(clientes):
        qty = RND.randint(2, 3) if idx in multi_idx else 1
        for v in range(qty):
            marca_nombre, modelo_nombre = pick_brand_model()
            marca = marcas_creadas[marca_nombre]
            modelo = Modelo.objects.get(nombre=modelo_nombre, marca=marca)

            vkwargs = dict(empresa=empresa, cliente=cli, marca=marca, modelo=modelo)
            if has_field(Vehiculo, "patente"):
                vkwargs["patente"] = make_fake_patente(1000 + idx * 10 + v)
            if has_field(Vehiculo, "vin"):
                vkwargs["vin"] = make_fake_vin(1000 + idx * 10 + v)
            if has_field(Vehiculo, "anio"):
                vkwargs["anio"] = RND.randint(2010, 2024)
            veh, _ = Vehiculo.objects.get_or_create(**vkwargs)
            vehiculos.append(veh)

    return clientes, vehiculos


def add_lineas_repuesto(doc, repuestos):
    count = RND.randint(2, 4)
    picks = RND.sample(repuestos, k=min(count, len(repuestos)))
    for rep in picks:
        precio = getattr(rep, "precio_venta", None) or RND.randint(
            25, 150
        )  # USD: $25-$150
        codigo = getattr(rep, "part_number", None) or f"REP-{rep.pk:04d}"
        LineaRepuesto.objects.create(
            documento=doc,
            repuesto=rep,
            codigo=codigo,
            nombre=rep.nombre,
            cantidad=RND.randint(1, 3),
            precio_unitario=precio,
            descuento=0,
        )


def add_lineas_servicio(doc, servicios):
    count = RND.randint(2, 3)
    picks = RND.sample(servicios, k=min(count, len(servicios)))
    for s in picks:
        precio_linea = getattr(s, "precio_base", None) or RND.randint(
            45, 120
        )  # USD: $45-$120
        LineaServicio.objects.create(
            documento=doc,
            servicio=s,
            nombre=s.nombre,
            cantidad=1,
            precio_unitario=precio_linea,
            descuento=0,
        )


def add_lineas_otro_servicio(doc, servicios):
    names = [
        "Balanceo externo",
        "Rectificado de discos",
        "Pulido de faros",
        "Alineación 3D externa",
        "Reparación radiador",
        "Soldadura escape",
        "Tapicería asiento",
        "Reparación parabrisas",
        "Lavado motor",
    ]
    count = RND.randint(2, 3)
    for _ in range(count):
        base_serv = RND.choice(servicios)
        nombre = RND.choice(names)
        cantidad = RND.randint(1, 2)
        costo = RND.randint(20, 50)  # USD: $20-$50
        precio = costo + RND.randint(15, 40)  # USD: $35-$90 total
        LineaOtroServicio.objects.create(
            documento=doc,
            servicio=base_serv,
            nombre=nombre,
            empresa_externa=RND.choice(["Proveedor X", "Proveedor Y", "Proveedor Z"]),
            cantidad=cantidad,
            costo_interno=costo,
            precio_cliente=precio,
        )


def create_documentos(
    empresa, clientes, vehiculos, repuestos, servicios, tecnicos, docs_count=20
):
    tipos = pick_document_types()
    docs = []
    for i in range(docs_count):
        cliente = RND.choice(clientes)
        vehiculos_cli = [v for v in vehiculos if v.cliente_id == cliente.id]
        vehiculo = RND.choice(vehiculos_cli) if vehiculos_cli else RND.choice(vehiculos)
        tipo_value = tipos[i % len(tipos)]
        fecha = timezone.now() - timedelta(days=RND.randint(0, 40))
        tecnico = RND.choice(tecnicos)  # Asignar técnico aleatorio

        doc_kwargs = dict(
            empresa=empresa, cliente=cliente, vehiculo=vehiculo, fecha_emision=fecha
        )
        if has_field(Documento, "tipo"):
            doc_kwargs["tipo"] = tipo_value
        if has_field(Documento, "estado"):
            try:
                estado_field = Documento._meta.get_field("estado")
                ch = getattr(estado_field, "choices", []) or []
                doc_kwargs["estado"] = ch[0][0] if ch else None
            except Exception:
                pass
        if has_field(Documento, "tecnico_responsable"):
            doc_kwargs["tecnico_responsable"] = tecnico
        if has_field(Documento, "country"):
            doc_kwargs["country"] = getattr(empresa, "pais", "CL")
        if has_field(Documento, "numero"):
            doc_kwargs["numero"] = str(i + 1)

        doc = Documento.objects.create(
            **{k: v for k, v in doc_kwargs.items() if v is not None}
        )
        add_lineas_repuesto(doc, repuestos)
        add_lineas_servicio(doc, servicios)
        add_lineas_otro_servicio(doc, servicios)
        docs.append(doc)
    return docs


# -----------------------------
# NUEVO: COMPRAS + DETALLES
# -----------------------------
def create_compras_con_detalle(empresa, repuestos):
    """
    Crea 2 compras (AutoZone y NAPA). Si existe un modelo de detalle de compra,
    agrega líneas (cantidad, precio_unitario, subtotal). Ajusta totales si hay campo.
    """
    Compra = get_model("taller", ["Compra", "Purchase"])
    DetalleCompra = get_model("taller", ["DetalleCompra", "CompraDetalle", "Detalle"])
    Proveedor = get_model("taller", ["Proveedor", "Supplier"])

    if not Compra:
        # Si tu esquema no tiene compras, salimos silenciosamente
        return []

    compras = []
    proveedores_nombres = ["AutoZone", "NAPA"]

    # Distribuye repuestos en 2 listas por proveedor si el campo existe
    if has_field(Repuesto, "proveedor"):
        rep_auto = [
            r
            for r in repuestos
            if (getattr(r, "proveedor", None) or "").lower() == "autozone"
        ]
        rep_napa = [
            r
            for r in repuestos
            if (getattr(r, "proveedor", None) or "").lower() == "napa"
        ]
    else:
        half = len(repuestos) // 2
        rep_auto = repuestos[:half]
        rep_napa = repuestos[half:]

    prov_map = {"AutoZone": rep_auto, "NAPA": rep_napa}

    for prov_name in proveedores_nombres:
        # Preparar kwargs dinámicos para Compra
        compra_kwargs = {}
        if has_field(Compra, "empresa"):
            compra_kwargs["empresa"] = empresa
        if has_field(Compra, "fecha"):
            compra_kwargs["fecha"] = timezone.now() - timedelta(days=RND.randint(0, 20))
        if has_field(Compra, "moneda"):
            compra_kwargs["moneda"] = "USD"
        if has_field(Compra, "observaciones"):
            compra_kwargs["observaciones"] = f"Compra de repuestos en {prov_name}"

        # Proveedor: intenta FK a Proveedor, si existe; si no, prueba campos de texto
        proveedor_obj = None
        if Proveedor:
            # Crea/obtiene proveedor multi-tenant si aplica
            prov_kwargs = {"nombre": prov_name}
            if has_field(Proveedor, "empresa"):
                prov_kwargs["empresa"] = empresa
            proveedor_obj, _ = Proveedor.objects.get_or_create(**prov_kwargs)

        # Asignar proveedor a Compra según el campo disponible
        # (varía por proyecto)
        for fname in [
            "proveedor",
            "proveedor_fk",
            "supplier",
            "proveedor_externo",
            "empresa_externa",
        ]:
            if has_field(Compra, fname):
                compra_kwargs[fname] = (
                    proveedor_obj if (Proveedor and proveedor_obj) else prov_name
                )
                break
        # Otros campos comunes
        for fname in ["estado", "tipo", "numero", "documento_referencia"]:
            if has_field(Compra, fname):
                compra_kwargs[fname] = compra_kwargs.get(fname, None)

        compra = Compra.objects.create(**compra_kwargs)

        # Agregar detalles si existe el modelo de detalle
        sum_subtotal = 0
        if DetalleCompra:
            rep_list = prov_map.get(prov_name, [])
            # Si no hay repuestos en ese grupo, usar algunos aleatorios
            if not rep_list:
                rep_list = RND.sample(repuestos, k=min(6, len(repuestos)))

            used = RND.sample(
                rep_list, k=min(max(4, len(rep_list) // 2), len(rep_list))
            )
            for rep in used:
                cantidad = RND.randint(1, 5)
                # precio = precio_compra del repuesto si existe, si no aleatorio
                precio = getattr(rep, "precio_compra", None) or RND.randint(
                    15, 80
                )  # USD: $15-$80
                subtotal = precio * cantidad

                det_kwargs = {}
                # FKs
                if has_field(DetalleCompra, "compra"):
                    det_kwargs["compra"] = compra
                if has_field(DetalleCompra, "repuesto"):
                    det_kwargs["repuesto"] = rep
                # Empresa si multi-tenant
                if has_field(DetalleCompra, "empresa"):
                    det_kwargs["empresa"] = empresa
                # Nombre descriptivo (si existe)
                if has_field(DetalleCompra, "nombre"):
                    det_kwargs["nombre"] = rep.nombre

                # Cantidad y precio
                for f in ["cantidad", "qty", "unidades"]:
                    if has_field(DetalleCompra, f):
                        det_kwargs[f] = cantidad
                        break
                for f in [
                    "precio_unitario",
                    "precio",
                    "costo_unitario",
                    "valor_unitario",
                ]:
                    if has_field(DetalleCompra, f):
                        det_kwargs[f] = precio
                        break
                # Subtotal si el modelo lo define
                for f in ["subtotal", "total_linea", "importe"]:
                    if has_field(DetalleCompra, f):
                        det_kwargs[f] = subtotal
                        break

                DetalleCompra.objects.create(**det_kwargs)
                sum_subtotal += subtotal

        # Actualizar totales de la compra si hay campo
        for f in ["subtotal", "monto_neto", "base", "total"]:
            if has_field(Compra, f):
                try:
                    setattr(compra, f, sum_subtotal)
                except Exception:
                    pass
        # Si hay IVA/impuestos, no los recalculamos (depende de tu lógica)
        compra.save()
        compras.append(compra)

    return compras


class Command(BaseCommand):
    help = "Seed de datos para la empresa GEORGE AUTO REPAIR."

    def add_arguments(self, parser):
        parser.add_argument("--company", default="GEORGE AUTO REPAIR")
        parser.add_argument("--clients", type=int, default=10)
        parser.add_argument("--extra_vehicle_clients", type=int, default=3)
        parser.add_argument("--parts", type=int, default=15)
        parser.add_argument("--docs", type=int, default=20)

    @transaction.atomic
    def handle(self, *args, **opts):
        company_name = opts["company"]
        clients_n = int(opts["clients"])
        extra_vehicle_clients = int(opts["extra_vehicle_clients"])
        parts_n = int(opts["parts"])
        docs_n = int(opts["docs"])

        empresa = get_empresa_by_name(company_name)
        self.stdout.write(
            self.style.SUCCESS(
                f"Empresa objetivo: {getattr(empresa, 'nombre_taller', str(empresa))} (id={empresa.id})"
            )
        )

        # Crear marcas y modelos primero
        marcas_creadas = ensure_marcas_y_modelos(empresa)
        self.stdout.write(
            self.style.SUCCESS(
                f"Marcas y modelos creados: {len(marcas_creadas)} marcas"
            )
        )

        clientes, vehiculos = create_clientes_y_vehiculos(
            empresa,
            marcas_creadas,
            total_clients=clients_n,
            extra_vehicle_clients=extra_vehicle_clients,
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"Clientes creados: {len(clientes)}; Vehículos creados: {len(vehiculos)}"
            )
        )

        servicios = ensure_servicios_basicos(empresa)
        repuestos = ensure_repuestos(empresa, total_parts=parts_n)
        self.stdout.write(
            self.style.SUCCESS(
                f"Servicios base: {len(servicios)}; Repuestos: {len(repuestos)}"
            )
        )

        # NUEVO: Compras a AutoZone y NAPA
        compras = create_compras_con_detalle(empresa, repuestos)
        self.stdout.write(
            self.style.SUCCESS(
                f"Compras creadas: {len(compras)} (con detalle si el modelo lo soporta)"
            )
        )

        tecnicos = get_or_create_tecnicos(empresa)
        self.stdout.write(self.style.SUCCESS(f"Técnicos creados: {len(tecnicos)}"))

        docs = create_documentos(
            empresa,
            clientes,
            vehiculos,
            repuestos,
            servicios,
            tecnicos,
            docs_count=docs_n,
        )
        self.stdout.write(self.style.SUCCESS(f"Documentos creados: {len(docs)}"))
        self.stdout.write(self.style.SUCCESS("✅ Seed completado sin errores."))
