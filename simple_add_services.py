#!/usr/bin/env python

import os
import sys

import django

# Configurar el path y Django
sys.path.append("e:/projecto/e_garage")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "e_garage.settings")
django.setup()

from django.db import connection


def agregar_servicios():
    cursor = connection.cursor()

    # Obtener servicios reales
    cursor.execute("SELECT id, nombre FROM taller_servicio LIMIT 3")
    servicios = cursor.fetchall()
    print(f"Servicios encontrados: {servicios}")

    # Limpiar servicios existentes
    cursor.execute("DELETE FROM taller_lineaservicio WHERE documento_id = 44")
    cursor.execute("DELETE FROM taller_lineaotroservicio WHERE documento_id = 44")

    # Insertar servicios usando formato compatible
    for i, (servicio_id, nombre) in enumerate(servicios, 1):
        sql = """
            INSERT INTO taller_lineaservicio
            (nombre, cantidad, precio_unitario, descuento, observaciones, documento_id, servicio_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(
            sql,
            [
                nombre,  # nombre
                1,  # cantidad
                50000.00,  # precio_unitario
                0.00,  # descuento
                f"Observación del servicio {i}",  # observaciones
                44,  # documento_id
                servicio_id,  # servicio_id
            ],
        )

    # Insertar otros servicios
    otros_servicios = [
        ("Revisión general", 1, 25000.00),
        ("Diagnóstico computarizado", 1, 15000.00),
    ]

    for nombre, cantidad, precio in otros_servicios:
        sql = """
            INSERT INTO taller_lineaotroservicio
            (nombre, cantidad, precio_unitario, descuento, observaciones, documento_id)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(
            sql,
            [
                nombre,  # nombre
                cantidad,  # cantidad
                precio,  # precio_unitario
                0.00,  # descuento
                f"Observación de {nombre}",  # observaciones
                44,  # documento_id
            ],
        )

    # Confirmar cambios
    cursor.connection.commit()

    # Verificar
    cursor.execute("SELECT COUNT(*) FROM taller_lineaservicio WHERE documento_id = 44")
    servicios_count = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM taller_lineaotroservicio WHERE documento_id = 44"
    )
    otros_count = cursor.fetchone()[0]

    print(f"✅ Servicios agregados: {servicios_count}")
    print(f"✅ Otros servicios agregados: {otros_count}")


if __name__ == "__main__":
    agregar_servicios()
