#!/usr/bin/env python
"""
Script para sembrar documentos de prueba
"""

import os

import django

# Configurar Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
django.setup()

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.utils import timezone

from taller.models.clientes import Cliente

# Imports de modelos
from taller.models.documento import Documento
from taller.models.lineas_documento import LineaRepuesto, LineaServicio
from taller.models.repuesto import Repuesto
from taller.models.sequence import DocumentSequence
from taller.models.tecnico import Tecnico
from taller.models.vehiculos import Marca, Modelo, Vehiculo
from taller.servicios.models import Servicio

User = get_user_model()


def seed_documentos():
    print("=== SEMBRANDO DOCUMENTOS DE PRUEBA ===")

    # 1) Usuario de prueba y su empresa
    try:
        u = User.objects.get(username="testuser_cl")
        emp = u.empresa
        print(f"✅ Usuario: {u.username}, Empresa: {emp.nombre_taller}")
    except User.DoesNotExist:
        print("❌ Usuario testuser_cl no encontrado")
        return

    # 2) Técnicos mínimos
    tec, _ = Tecnico.objects.get_or_create(
        empresa=emp, nombre="Técnico Principal", defaults={"activo": True}
    )
    print(f"✅ Técnico: {tec.nombre}")

    # 3) Marcas/Modelos/Vehículos de clientes
    mar_chev = Marca.objects.filter(nombre="Chevrolet").first()
    if not mar_chev:
        mar_chev = Marca.objects.create(nombre="Chevrolet", country="CL")

    mod_onix = Modelo.objects.filter(marca=mar_chev, nombre="Onix").first()
    if not mod_onix:
        mod_onix = Modelo.objects.create(marca=mar_chev, nombre="Onix")

    mar_bmw = Marca.objects.filter(nombre="BMW").first()
    if not mar_bmw:
        mar_bmw = Marca.objects.create(nombre="BMW", country="CL")

    mod_2s = Modelo.objects.filter(marca=mar_bmw, nombre="2 Series").first()
    if not mod_2s:
        mod_2s = Modelo.objects.create(marca=mar_bmw, nombre="2 Series")

    mar_chr = Marca.objects.filter(nombre="Chrysler").first()
    if not mar_chr:
        mar_chr = Marca.objects.create(nombre="Chrysler", country="CL")

    mod_chr = Modelo.objects.filter(marca=mar_chr, nombre="200").first()
    if not mod_chr:
        mod_chr = Modelo.objects.create(marca=mar_chr, nombre="200")

    c1, _ = Cliente.objects.get_or_create(
        empresa=emp,
        nombre="Alberto",
        apellido="Acosta",
        defaults={"tax_id": "11111111-1"},
    )
    c2, _ = Cliente.objects.get_or_create(
        empresa=emp,
        nombre="Fernando",
        apellido="Zampedri",
        defaults={"tax_id": "22222222-2"},
    )
    c3, _ = Cliente.objects.get_or_create(
        empresa=emp,
        nombre="Daniela",
        apellido="Silva",
        defaults={"tax_id": "33333333-3"},
    )

    v1, _ = Vehiculo.objects.get_or_create(
        empresa=emp,
        cliente=c1,
        patente="AAA1111",
        marca=mar_chr,
        modelo=mod_chr,
        defaults={"anio": 2020},
    )
    v2, _ = Vehiculo.objects.get_or_create(
        empresa=emp,
        cliente=c2,
        patente="BBB1111",
        marca=mar_chev,
        modelo=mod_onix,
        defaults={"anio": 2021},
    )
    v3, _ = Vehiculo.objects.get_or_create(
        empresa=emp,
        cliente=c3,
        patente="CCC1111",
        marca=mar_bmw,
        modelo=mod_2s,
        defaults={"anio": 2022},
    )

    print(
        f"✅ Clientes: {c1.nombre} {c1.apellido}, {c2.nombre} {c2.apellido}, {c3.nombre} {c3.apellido}"
    )
    print(f"✅ Vehículos: {v1.patente}, {v2.patente}, {v3.patente}")

    # 4) Repuestos y Servicios
    rep_datos = [
        ("r001", "Filtro de aire", 3500, 15000),
        ("r002", "Aceite motor", 5500, 19000),
        ("r003", "Bujía", 1200, 6000),
        ("r004", "Pastillas freno", 8000, 32000),
        ("r005", "Filtro aceite", 3000, 12000),
    ]
    repuestos = {}
    for code, nombre, pc, pv in rep_datos:
        r, _ = Repuesto.objects.get_or_create(
            empresa=emp,
            part_number=code,
            defaults={"nombre": nombre, "precio_compra": pc, "precio_venta": pv},
        )
        # actualiza precios por si ya existía
        r.nombre = nombre
        r.precio_compra = pc
        r.precio_venta = pv
        r.save()
        repuestos[code] = r

    serv_cambio, _ = Servicio.objects.get_or_create(
        empresa=emp, nombre="Cambio de Aceite Estándar", defaults={"precio": 25000}
    )
    serv_frenos, _ = Servicio.objects.get_or_create(
        empresa=emp,
        nombre="Reparación y Mantenimiento de Frenos",
        defaults={"precio": 45000},
    )

    print(f"✅ Repuestos: {len(repuestos)} creados")
    print(f"✅ Servicios: {serv_cambio.nombre}, {serv_frenos.nombre}")

    def next_num(empresa, tipo):
        n = DocumentSequence.next(empresa, tipo)
        pref = {"OT": "OT", "FAC": "F", "PRES": "P"}.get(tipo, "D")
        return f"{pref}{n:03d}", n

    def crear_doc(cliente, vehiculo, tipo="FAC", rep_lines=None, serv_lines=None, km=10000):
        numero, correl = next_num(emp, tipo)
        doc = Documento.objects.create(
            empresa=emp,
            tipo=tipo,
            numero=numero,
            correlativo=correl,
            cliente=cliente,
            vehiculo=vehiculo,
            tecnico_responsable=tec,
            fecha_emision=timezone.now().date(),
            kilometraje=km,
            country="CL",
            moneda="CLP",
            estado="EMITIDO",
            estado_pago="NO_PAGADO",
            pagado=False,
            apply_vat=True,
            tax_rate_applied=Decimal("19"),
        )

        # líneas repuesto
        rep_lines = rep_lines or []
        for code, cant, pv in rep_lines:
            r = repuestos[code]
            LineaRepuesto.objects.create(
                documento=doc,
                repuesto=r,
                codigo=r.part_number,
                nombre=r.nombre,
                cantidad=cant,
                precio_unitario=pv,
            )

        # líneas servicio
        serv_lines = serv_lines or []
        for serv, cant, pv in serv_lines:
            LineaServicio.objects.create(
                documento=doc,
                servicio=serv,
                nombre=serv.nombre,
                cantidad=cant,
                precio_unitario=pv,
            )

        # totales (servidor autoridad)
        try:
            doc.recalcular_totales()
            doc.save(
                update_fields=[
                    "neto_repuestos",
                    "neto_servicios",
                    "tax_amount",
                    "total",
                ]
            )
        except Exception as e:
            print(f"WARN recalcular_totales: {e}")

        return doc

    # 5) Crea 5 documentos variados
    docs = []
    docs.append(
        crear_doc(
            c1,
            v1,
            "FAC",
            rep_lines=[("r002", 5, 19000), ("r005", 2, 12000)],
            serv_lines=[(serv_cambio, 1, 25000)],
            km=15000,
        )
    )
    docs.append(
        crear_doc(
            c2,
            v2,
            "FAC",
            rep_lines=[("r001", 1, 15000)],
            serv_lines=[(serv_frenos, 1, 45000)],
            km=25000,
        )
    )
    docs.append(
        crear_doc(
            c3,
            v3,
            "OT",
            rep_lines=[("r003", 4, 6000)],
            serv_lines=[(serv_cambio, 1, 25000)],
            km=8000,
        )
    )
    docs.append(crear_doc(c1, v1, "PRES", rep_lines=[("r004", 1, 32000)], serv_lines=[], km=16000))
    docs.append(
        crear_doc(
            c2,
            v2,
            "OT",
            rep_lines=[("r001", 2, 15000), ("r005", 1, 12000)],
            serv_lines=[],
            km=30000,
        )
    )

    print("✅ DOCUMENTOS CREADOS:")
    for doc in docs:
        print(
            f"   {doc.numero} - {doc.tipo} - {doc.cliente.nombre} {doc.cliente.apellido} - ${doc.total:,.0f}"
        )

    print("\n🎉 SEMBRADO COMPLETADO!")
    print(f"📊 Total documentos en BD: {Documento.objects.filter(empresa=emp).count()}")


if __name__ == "__main__":
    seed_documentos()
