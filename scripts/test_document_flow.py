import json
import traceback

from django.test import Client
from django.contrib.auth import get_user_model

from taller.models import Cliente
from taller.models import Vehiculo
from taller.models import Repuesto
from taller.models import Documento

try:
    from taller.models import Service as Servicio
except Exception:
    Servicio = None


def _pick_admin():
    User = get_user_model()
    user = (
        User.objects.filter(is_active=True, is_superuser=True).order_by("id").first()
        or User.objects.filter(is_active=True, is_staff=True).order_by("id").first()
    )
    assert user, "No existe usuario admin/staff para pruebas"
    return user


def _print_last_objects():
    print(
        "ULTIMO CLIENTE:",
        Cliente.objects.order_by("-id").values("id", "nombre", "empresa_id").first(),
    )
    print(
        "ULTIMO VEHICULO:",
        Vehiculo.objects.order_by("-id")
        .values("id", "patente", "cliente_id", "empresa_id")
        .first(),
    )
    print(
        "ULTIMO REPUESTO:",
        Repuesto.objects.order_by("-id").values("id", "nombre", "empresa_id").first(),
    )
    print(
        "ULTIMO DOCUMENTO:",
        Documento.objects.order_by("-id")
        .values("id", "tipo", "cliente_id", "vehiculo_id", "empresa_id")
        .first(),
    )
    if Servicio:
        print("ULTIMO SERVICIO:", Servicio.objects.order_by("-id").values("id", "nombre").first())


def run():
    c = Client()
    user = _pick_admin()
    c.force_login(user)

    empresa = getattr(user, "empresa", None)
    print("USER:", user.pk, getattr(user, "username", None), getattr(user, "email", None))
    print(
        "EMPRESA USER:",
        getattr(empresa, "id", None),
        getattr(empresa, "nombre_taller", None),
        getattr(empresa, "pais", None),
    )

    print("\n=== STEP 0: GET FORM DOCUMENTO ===")
    r = c.get("/cl/es/documentos/form/")
    print("GET /cl/es/documentos/form/ =>", r.status_code)

    print("\n=== STEP 1: CREAR CLIENTE ===")
    cliente_payload = {
        "nombre": "Cliente Test Flujo",
        "apellido": "Modal",
        "telefono": "987654321",
        "email": "cliente.test.flujo@example.com",
        "direccion": "Direccion Test 123",
        "ciudad": "Viña del Mar",
        "comuna": "Viña del Mar",
        "region": "Valparaíso",
        "pais": "Chile",
        "return_to": "/cl/es/documentos/form/",
        "select_field": "cliente",
    }
    r = c.post(
        "/cl/es/clientes/crear/?return_to=/cl/es/documentos/form/&select_field=cliente",
        cliente_payload,
        follow=True,
    )
    print("POST cliente =>", r.status_code)
    print("REDIRECTS cliente =>", getattr(r, "redirect_chain", None))

    cliente = Cliente.objects.order_by("-id").first()
    assert cliente, "No se creó cliente"
    print(
        "CLIENTE:",
        cliente.id,
        getattr(cliente, "nombre", None),
        getattr(cliente, "empresa_id", None),
    )

    print("\n=== STEP 2: CREAR VEHICULO ===")
    vehiculo_payload = {
        "cliente": cliente.id,
        "patente": "TEST123",
        "vin": "1HGCM82633A123456",
        "anio": "2020",
        "marca_texto": "Toyota",
        "modelo_texto": "Yaris",
        "color": "Blanco",
        "return_to": f"/cl/es/documentos/form/?cliente_id={cliente.id}",
        "select_field": "vehiculo",
    }
    r = c.post(
        f"/cl/es/vehiculos/crear/?return_to=/cl/es/documentos/form/?cliente_id={cliente.id}&select_field=vehiculo&cliente_id={cliente.id}",
        vehiculo_payload,
        follow=True,
    )
    print("POST vehiculo =>", r.status_code)
    print("REDIRECTS vehiculo =>", getattr(r, "redirect_chain", None))

    vehiculo = Vehiculo.objects.order_by("-id").first()
    assert vehiculo, "No se creó vehículo"
    print(
        "VEHICULO:",
        vehiculo.id,
        getattr(vehiculo, "patente", None),
        getattr(vehiculo, "cliente_id", None),
        getattr(vehiculo, "empresa_id", None),
    )

    print("\n=== STEP 3: CREAR REPUESTO ===")
    repuesto_payload = {
        "nombre": "Filtro Aceite Test Flujo",
        "part_number": "PN-TEST-001",
        "precio_venta": "12990",
        "precio_compra": "7990",
        "stock": "5",
        "return_to": f"/cl/es/documentos/form/?cliente_id={cliente.id}&vehiculo_id={vehiculo.id}",
        "select_field": "repuesto",
    }
    r = c.post(
        "/cl/es/repuestos/crear/?return_to=/cl/es/documentos/form/&select_field=repuesto",
        repuesto_payload,
        follow=True,
    )
    print("POST repuesto =>", r.status_code)
    print("REDIRECTS repuesto =>", getattr(r, "redirect_chain", None))

    repuesto = Repuesto.objects.order_by("-id").first()
    assert repuesto, "No se creó repuesto"
    print(
        "REPUESTO:",
        repuesto.id,
        getattr(repuesto, "nombre", None),
        getattr(repuesto, "empresa_id", None),
    )

    servicio_ids = []
    if Servicio:
        print("\n=== STEP 4: CREAR 3 SERVICIOS ===")
        for i in range(1, 4):
            servicio_payload = {
                "nombre": f"Servicio Test Flujo {i}",
                "descripcion": f"Servicio generado por test {i}",
                "precio": str(10000 + (i * 1000)),
                "return_to": f"/cl/es/documentos/form/?cliente_id={cliente.id}&vehiculo_id={vehiculo.id}",
                "select_field": "servicio",
            }
            r = c.post(
                "/cl/es/servicios/crear/?return_to=/cl/es/documentos/form/&select_field=servicio",
                servicio_payload,
                follow=True,
            )
            print(f"POST servicio {i} =>", r.status_code)
            print(f"REDIRECTS servicio {i} =>", getattr(r, "redirect_chain", None))
            srv = Servicio.objects.order_by("-id").first()
            if srv:
                servicio_ids.append(srv.id)
                print("SERVICIO:", srv.id, getattr(srv, "nombre", None))

    print("\n=== STEP 5: CREAR DOCUMENTO ===")
    documentos_a_testear = [
        ("orden_trabajo", "OT"),
        ("presupuesto", "PRESUPUESTO"),
        ("factura", "FACTURA"),
    ]

    for label, tipo in documentos_a_testear:
        print(f"\n--- DOCUMENTO {label.upper()} / tipo={tipo} ---")
        payload = {
            "tipo": tipo,
            "fecha_emision": "2026-04-16",
            "cliente": str(cliente.id),
            "cliente_id": str(cliente.id),
            "vehiculo": str(vehiculo.id),
            "vehiculo_id": str(vehiculo.id),
            "observaciones": f"Documento automático {label}",
            "repuestos_json": json.dumps(
                [
                    {
                        "repuesto_id": repuesto.id,
                        "part_number": "PN-TEST-001",
                        "nombre": "Filtro Aceite Test Flujo",
                        "cantidad": 1,
                        "precio": 12990,
                        "precio_unitario": 12990,
                        "subtotal": 12990,
                    }
                ]
            ),
            "servicios_json": json.dumps(
                [
                    {
                        "servicio_id": servicio_ids[0] if len(servicio_ids) > 0 else "",
                        "nombre": "Servicio Test Flujo 1",
                        "cantidad": 1,
                        "precio": 11000,
                        "precio_unitario": 11000,
                        "subtotal": 11000,
                    },
                    {
                        "servicio_id": servicio_ids[1] if len(servicio_ids) > 1 else "",
                        "nombre": "Servicio Test Flujo 2",
                        "cantidad": 1,
                        "precio": 12000,
                        "precio_unitario": 12000,
                        "subtotal": 12000,
                    },
                    {
                        "servicio_id": servicio_ids[2] if len(servicio_ids) > 2 else "",
                        "nombre": "Servicio Test Flujo 3",
                        "cantidad": 1,
                        "precio": 13000,
                        "precio_unitario": 13000,
                        "subtotal": 13000,
                    },
                ]
            ),
            "otros_json": json.dumps(
                [
                    {
                        "nombre": "Otro Servicio Test",
                        "empresa_externa": "Proveedor Externo Test",
                        "cantidad": 1,
                        "costo_interno": 8000,
                        "precio_cliente": 15000,
                        "ganancia": 7000,
                        "subtotal": 15000,
                    }
                ]
            ),
        }

        before_id = Documento.objects.order_by("-id").values_list("id", flat=True).first()
        r = c.post("/cl/es/documentos/form/", payload, follow=True)
        after_id = Documento.objects.order_by("-id").values_list("id", flat=True).first()

        print("POST documento =>", r.status_code)
        print("REDIRECTS documento =>", getattr(r, "redirect_chain", None))
        print("DOC BEFORE:", before_id, "DOC AFTER:", after_id)
        print("CONTENT SNIPPET:", (r.content[:600] if hasattr(r, "content") else b""))

    print("\n=== RESUMEN OBJETOS ===")
    _print_last_objects()


def run_safe():
    try:
        run()
    except Exception as e:
        print("\n=== EXCEPCION DETECTADA ===")
        print(type(e).__name__, str(e))
        traceback.print_exc()
        print("\n=== RESUMEN OBJETOS AL FALLAR ===")
        _print_last_objects()
