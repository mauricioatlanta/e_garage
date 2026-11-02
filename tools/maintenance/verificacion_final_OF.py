#!/usr/bin/env python
"""
Script final de verificación manual
Ejecutar después de los fixes para demostrar que funciona
"""

import os
import sys

import django

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "garage_project.settings")
sys.path.append("e:\\projecto\\e_garage")
django.setup()


from taller.models import Documento, Repuesto


def verificacion_final():
    print("🔧 VERIFICACIÓN FINAL - DESPUÉS DE LOS FIXES")
    print("=" * 70)

    # 1. Verificar que existe repuesto OF
    repuesto_of = Repuesto.objects.filter(part_number__iexact="OF").first()
    if not repuesto_of:
        print("❌ No existe repuesto con part_number 'OF'")
        return False

    print(
        f"✅ Repuesto OF: ID={repuesto_of.id}, nombre='{repuesto_of.nombre}', part_number='{repuesto_of.part_number}'"
    )

    # 2. Verificar último documento
    if not Documento.objects.exists():
        print("❌ No hay documentos en la base de datos")
        return False

    ultimo_doc = Documento.objects.latest("id")
    print("\n📄 ÚLTIMO DOCUMENTO:")
    print(
        f"DOC: {ultimo_doc.id} {ultimo_doc.empresa_id} {ultimo_doc.cliente_id} {ultimo_doc.vehiculo_id} {getattr(ultimo_doc, 'millas', None)}"
    )

    # 3. Contar líneas
    cnt_rep = ultimo_doc.lineas_repuesto.count()
    cnt_serv = ultimo_doc.lineas_servicio.count()
    cnt_otros = ultimo_doc.lineas_otro_servicio.count()

    print(f"CNT rep: {cnt_rep}")
    print(f"CNT serv: {cnt_serv}")
    print(f"CNT otros: {cnt_otros}")

    # 4. Listar repuestos
    list_rep = list(
        ultimo_doc.lineas_repuesto.values_list(
            "id", "repuesto_id", "nombre", "cantidad", "precio_unitario", "descuento"
        )
    )
    print(f"LIST rep ids: {list_rep}")

    # 5. Verificar si hay repuesto OF
    repuesto_of_en_doc = False
    for linea in ultimo_doc.lineas_repuesto.all():
        if linea.repuesto and linea.repuesto.part_number == "OF":
            repuesto_of_en_doc = True
            print(f"✅ REPUESTO OF ENCONTRADO: {linea.nombre} (ID línea: {linea.id})")
            break

    if not repuesto_of_en_doc:
        print("❌ REPUESTO OF NO ESTÁ EN EL DOCUMENTO")

    # 6. Estado del problema
    print("\n🔍 DIAGNÓSTICO:")
    if cnt_rep == 0:
        print("❌ PROBLEMA PERSISTE: No se guardan líneas de repuestos")
        print("   Causa: Vista no procesa los datos POST correctamente")
    elif cnt_rep > 0 and not repuesto_of_en_doc:
        print("✅ Se guardan líneas, pero no el repuesto OF específico")
        print("   Causa: Problema con resolución de part_number o datos específicos")
    elif repuesto_of_en_doc:
        print("✅ PROBLEMA RESUELTO: Repuesto OF se guarda correctamente")

    return repuesto_of_en_doc


def comandos_shell_manuales():
    print("\n📋 COMANDOS SHELL MANUALES:")
    print("# Ejecutar en Django shell:")
    print("python manage.py shell")
    print("")
    print("from taller.models import Documento, LineaRepuesto, Repuesto")
    print("# Verificar repuesto OF")
    print("of_rep = Repuesto.objects.filter(part_number__iexact='OF').first()")
    print(
        "print('Repuesto OF:', of_rep.id if of_rep else 'No existe', of_rep.nombre if of_rep else '')"
    )
    print("")
    print("# Verificar último documento")
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
    print("")
    print("# Verificar si hay repuesto OF en las líneas")
    print("for linea in doc.lineas_repuesto.all():")
    print("    if linea.repuesto and linea.repuesto.part_number == 'OF':")
    print("        print('REPUESTO OF ENCONTRADO:', linea.nombre)")


if __name__ == "__main__":
    resultado = verificacion_final()
    comandos_shell_manuales()

    print(f"\n{'='*70}")
    if resultado:
        print("🎉 ¡ÉXITO! El repuesto OF funciona correctamente")
    else:
        print("💥 Problema persiste - Revisar fixes implementados")
    print("=" * 70)
