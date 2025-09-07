#!/usr/bin/env python
"""
Script de reproducción: Crear documento con repuesto "OF" y demostrar el problema
"""
import json
import os
import sys
from datetime import datetime

import django
import requests

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "garage_project.settings")
sys.path.append("e:\\projecto\\e_garage")
django.setup()

from django.contrib.auth import get_user_model

from taller.models import (
    Cliente,
    Documento,
    Repuesto,
    Tecnico,
    Vehiculo,
)


def crear_documento_con_repuesto_OF():
    print("🔧 REPRODUCCIÓN DEL PROBLEMA: Documento con repuesto 'OF'")
    print("=" * 70)

    # Verificar que existe repuesto con part_number "OF"
    repuesto_of = Repuesto.objects.filter(part_number__iexact="OF").first()
    if not repuesto_of:
        # Crear repuesto OF si no existe
        User = get_user_model()
        user = User.objects.get(username="testuser_cl")
        empresa = user.empresa

        repuesto_of = Repuesto.objects.create(
            empresa=empresa,
            nombre="Filtro de aceite",
            part_number="OF",
            precio_venta=9990,
        )
        print(
            f"✅ Creado repuesto OF: ID={repuesto_of.id}, part_number='{repuesto_of.part_number}'"
        )
    else:
        print(
            f"✅ Repuesto OF existente: ID={repuesto_of.id}, part_number='{repuesto_of.part_number}'"
        )

    # Setup session para login
    session = requests.Session()

    # GET login page para obtener CSRF
    login_url = "http://127.0.0.1:8000/cl/accounts/login/"
    print(f"\n📡 GET {login_url}")
    response = session.get(login_url)
    print(f"Status: {response.status_code}")

    if response.status_code != 200:
        print("❌ ERROR: No se pudo cargar página de login")
        return False

    # Extraer CSRF token
    csrf_token = None
    for line in response.text.split("\n"):
        if "csrfmiddlewaretoken" in line and "value=" in line:
            csrf_token = line.split('value="')[1].split('"')[0]
            break

    if not csrf_token:
        print("❌ ERROR: No se encontró CSRF token")
        return False

    print("✅ CSRF token obtenido")

    # POST login
    login_data = {
        "username": "testuser_cl",
        "password": "TestPass123!",
        "csrfmiddlewaretoken": csrf_token,
    }

    print("\n🔐 POST Login...")
    response = session.post(login_url, data=login_data)
    print(f"Status: {response.status_code}")
    print(f"Final URL: {response.url}")

    if "login" in response.url:
        print("❌ ERROR: Login falló")
        return False

    print("✅ Login exitoso")

    # Obtener datos necesarios
    User = get_user_model()
    user = User.objects.get(username="testuser_cl")
    empresa = user.empresa
    cliente = Cliente.objects.filter(empresa=empresa).first()
    tecnico = Tecnico.objects.filter(empresa=empresa).first()
    vehiculo = Vehiculo.objects.filter(cliente=cliente).first() if cliente else None

    if not all([cliente, tecnico, vehiculo]):
        print(
            f"❌ ERROR: Datos faltantes - cliente={bool(cliente)}, tecnico={bool(tecnico)}, vehiculo={bool(vehiculo)}"
        )
        return False

    print(
        f"✅ Datos: Cliente={cliente.id}, Técnico={tecnico.id}, Vehículo={vehiculo.id}"
    )

    # GET crear documento para obtener CSRF
    crear_url = "http://127.0.0.1:8000/cl/documentos/nuevo/"
    print(f"\n📡 GET {crear_url}")
    response = session.get(crear_url)
    print(f"Status: {response.status_code}")

    if response.status_code != 200:
        print("❌ ERROR: No se pudo cargar página de crear documento")
        return False

    # Extraer CSRF del formulario
    csrf_token = None
    for line in response.text.split("\n"):
        if "csrfmiddlewaretoken" in line and "value=" in line:
            csrf_token = line.split('value="')[1].split('"')[0]
            break

    if not csrf_token:
        print("❌ ERROR: No se pudo obtener CSRF del formulario")
        return False

    print("✅ CSRF formulario obtenido")

    # Preparar datos del documento con repuesto "OF"
    procesar_url = "http://127.0.0.1:8000/cl/documentos/procesar/"

    documento_data = {
        "csrfmiddlewaretoken": csrf_token,
        "tipo": "PRESUPUESTO",
        "fecha": datetime.now().strftime("%Y-%m-%d"),
        "cliente": str(cliente.id),
        "vehiculo": str(vehiculo.id),
        "tecnico": str(tecnico.id),
        "kilometraje": "50000",
        "estado": "borrador",
        "incluir_impuesto": "on",
        # Repuesto "OF" por ID (método normal)
        "repuestos_data": json.dumps(
            [
                {
                    "id": str(repuesto_of.id),  # Usar ID del repuesto OF
                    "cantidad": "1",
                    "precio": "9990",
                    "descuento": "0",
                }
            ]
        ),
        # Arrays alternativos (por si el template usa estos)
        "repuestos_ids[]": [str(repuesto_of.id)],
        "repuestos_cantidades[]": ["1"],
        "repuestos_precios[]": ["9990"],
        "repuestos_descuentos[]": ["0"],
        # Por part_number (por si hay problema con ID)
        "repuestos_partnumber[]": ["OF"],
        "servicios_data": "[]",
        "otros_servicios_data": "[]",
    }

    print("\n📝 DATOS POST:")
    print(f"  URL: {procesar_url}")
    print(f"  Cliente ID: {documento_data['cliente']}")
    print(f"  Vehículo ID: {documento_data['vehiculo']}")
    print(f"  Técnico ID: {documento_data['tecnico']}")
    print(f"  Repuesto OF ID: {repuesto_of.id}")
    print(f"  repuestos_data: {documento_data['repuestos_data']}")
    print(f"  repuestos_ids[]: {documento_data['repuestos_ids[]']}")
    print(f"  repuestos_partnumber[]: {documento_data['repuestos_partnumber[]']}")

    # Contar documentos antes
    docs_antes = Documento.objects.count()
    print(f"\n📊 Documentos ANTES: {docs_antes}")

    # POST creación documento
    print(f"\n🚀 POST {procesar_url}")
    response = session.post(procesar_url, data=documento_data, allow_redirects=False)

    # EVIDENCIA 1: Status code y Location
    print("\n📋 EVIDENCIA 1 - STATUS CODE:")
    print(f"Status: {response.status_code}")
    print(f"Location: {response.headers.get('Location', 'N/A')}")

    # Verificar documentos después
    docs_despues = Documento.objects.count()
    print(f"\n📊 Documentos DESPUÉS: {docs_despues}")

    if docs_despues <= docs_antes:
        print("❌ ERROR: No se creó ningún documento")
        return False

    # Obtener último documento creado
    ultimo_doc = Documento.objects.order_by("-id").first()
    doc_id = ultimo_doc.id

    print(f"✅ Documento creado: ID={doc_id}")

    # EVIDENCIA 2: Django shell output (exacta como solicita)
    print("\n📋 EVIDENCIA 2 - DJANGO SHELL OUTPUT:")
    print("from taller.models import Documento, LineaRepuesto")
    print("doc = Documento.objects.latest('id')")
    print(
        "print('DOC:', doc.id, doc.empresa_id, doc.cliente_id, doc.vehiculo_id, getattr(doc, 'millas', None))"
    )
    print("print('CNT rep:', doc.lineas_repuesto.count())")
    print("print('CNT serv:', doc.lineas_servicio.count())")
    print("print('CNT otros:', doc.lineas_otro_servicio.count())")
    print(
        "print('LIST rep ids:', list(doc.lineas_repuesto.values_list('id','repuesto_id','nombre','cantidad','precio_unitario','descuento')))"
    )

    # Ejecutar comandos Django shell
    doc = Documento.objects.latest("id")
    millas = getattr(doc, "millas", None)
    cnt_rep = doc.lineas_repuesto.count()
    cnt_serv = doc.lineas_servicio.count()
    cnt_otros = doc.lineas_otro_servicio.count()
    list_rep = list(
        doc.lineas_repuesto.values_list(
            "id", "repuesto_id", "nombre", "cantidad", "precio_unitario", "descuento"
        )
    )

    print("\n🔍 RESULTADO DJANGO SHELL:")
    print(f"DOC: {doc.id} {doc.empresa_id} {doc.cliente_id} {doc.vehiculo_id} {millas}")
    print(f"CNT rep: {cnt_rep}")
    print(f"CNT serv: {cnt_serv}")
    print(f"CNT otros: {cnt_otros}")
    print(f"LIST rep ids: {list_rep}")

    # EVIDENCIA 3: HTML del detalle donde NO aparece la línea
    detalle_url = f"http://127.0.0.1:8000/cl/documentos/{doc_id}/"
    print("\n📋 EVIDENCIA 3 - HTML DETALLE:")
    print(f"URL: {detalle_url}")

    response = session.get(detalle_url)
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        # Buscar tabla de repuestos en el HTML
        html_content = response.text
        if "repuesto" in html_content.lower() or "filtro" in html_content.lower():
            print("✅ HTML contiene referencias a repuestos")
            # Extraer sección relevante
            lines = html_content.split("\n")
            in_repuestos_section = False
            repuestos_html = []
            for line in lines:
                if "repuesto" in line.lower() or "filtro" in line.lower():
                    in_repuestos_section = True
                    repuestos_html.append(line.strip())
                elif in_repuestos_section and ("</table>" in line or "</div>" in line):
                    repuestos_html.append(line.strip())
                    break
                elif in_repuestos_section:
                    repuestos_html.append(line.strip())

            if repuestos_html:
                print("HTML relevante (repuestos):")
                for line in repuestos_html[:20]:  # Primeras 20 líneas
                    print(f"  {line}")
            else:
                print("❌ NO se encontraron líneas de repuestos en el HTML")
        else:
            print("❌ HTML NO contiene referencias a repuestos")
            print("Primeras 50 líneas del HTML:")
            for i, line in enumerate(html_content.split("\n")[:50]):
                print(f"  {i+1:2d}: {line.strip()}")

    # Análisis del problema
    print("\n🔍 ANÁLISIS DEL PROBLEMA:")
    if cnt_rep == 0:
        print("❌ PROBLEMA: CNT rep = 0 → La línea NO se guardó en la base de datos")
        print(
            "   Causa probable: POST no lleva datos correctos O la vista no los procesa"
        )
    elif cnt_rep > 0:
        print(f"✅ Líneas en BD: {cnt_rep}")
        print("❌ PROBLEMA: Líneas existen en BD pero NO se muestran en la vista")
        print(
            "   Causa probable: Template/vista de detalle no consulta o muestra las líneas"
        )
        print(f"   Líneas encontradas: {list_rep}")

    return cnt_rep > 0


if __name__ == "__main__":
    resultado = crear_documento_con_repuesto_OF()
    print(f"\n{'='*70}")
    if resultado:
        print("🎯 REPRODUCCIÓN COMPLETA: Problema identificado con evidencias")
    else:
        print("💥 REPRODUCCIÓN FALLÓ: No se pudo crear el documento")
    print("=" * 70)
