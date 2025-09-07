#!/usr/bin/env python
"""
Script para agregar servicios y otros servicios al documento 44
usando SQL directo con servicios reales de la base de datos
"""

import os
import sqlite3

import django

# Configurar Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "e_garage.settings")
django.setup()

from django.db import connection


def agregar_servicios_documento_44():
    cursor = connection.cursor()

    # Verificar que el documento 44 existe
    cursor.execute("SELECT id FROM taller_documento WHERE id = 44")
    if not cursor.fetchone():
        print("Error: El documento 44 no existe")
        return

    # Limpiar servicios existentes por si acaso
    cursor.execute("DELETE FROM taller_lineaservicio WHERE documento_id = 44")
    cursor.execute("DELETE FROM taller_lineaotroservicio WHERE documento_id = 44")

    # Obtener algunos servicios reales
    cursor.execute("SELECT id, nombre FROM taller_servicio LIMIT 3")
    servicios = cursor.fetchall()

    print(f"Servicios encontrados: {servicios}")

    # Insertar líneas de servicio con servicios reales
    for i, (servicio_id, nombre) in enumerate(servicios, 1):
        cursor.execute(
            """
            INSERT INTO taller_lineaservicio 
            (nombre, cantidad, precio_unitario, descuento, observaciones, documento_id, servicio_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (
                nombre,  # nombre
                1,  # cantidad
                50000.00,  # precio_unitario
                0.00,  # descuento
                f"Observación del servicio {i}",  # observaciones
                44,  # documento_id
                servicio_id,  # servicio_id
            ),
        )

    # Insertar líneas de otros servicios
    otros_servicios = [
        ("Revisión general", 1, 25000.00),
        ("Diagnóstico computarizado", 1, 15000.00),
        ("Limpieza de motor", 1, 30000.00),
    ]

    for nombre, cantidad, precio in otros_servicios:
        cursor.execute(
            """
            INSERT INTO taller_lineaotroservicio 
            (nombre, cantidad, precio_unitario, descuento, observaciones, documento_id)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (
                nombre,  # nombre
                cantidad,  # cantidad
                precio,  # precio_unitario
                0.00,  # descuento
                f"Observación de {nombre}",  # observaciones
                44,  # documento_id
            ),
        )

    # Confirmar cambios
    connection.commit()

    # Verificar inserción
    cursor.execute("SELECT COUNT(*) FROM taller_lineaservicio WHERE documento_id = 44")
    servicios_count = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM taller_lineaotroservicio WHERE documento_id = 44"
    )
    otros_servicios_count = cursor.fetchone()[0]

    print(f"✅ Servicios agregados: {servicios_count}")
    print(f"✅ Otros servicios agregados: {otros_servicios_count}")

    # Mostrar detalles
    cursor.execute(
        "SELECT nombre, cantidad, precio_unitario FROM taller_lineaservicio WHERE documento_id = 44"
    )
    servicios_detail = cursor.fetchall()
    print("Servicios insertados:")
    for servicio in servicios_detail:
        print(f"  - {servicio[0]}: {servicio[1]} x ${servicio[2]}")

    cursor.execute(
        "SELECT nombre, cantidad, precio_unitario FROM taller_lineaotroservicio WHERE documento_id = 44"
    )
    otros_detail = cursor.fetchall()
    print("Otros servicios insertados:")
    for otro in otros_detail:
        print(f"  - {otro[0]}: {otro[1]} x ${otro[2]}")


if __name__ == "__main__":
    agregar_servicios_documento_44()
