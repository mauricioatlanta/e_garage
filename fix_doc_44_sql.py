#!/usr/bin/env python
import os
import sqlite3
from decimal import Decimal

import django

# Configurar Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
django.setup()

from django.db import connection


def agregar_servicios_sql():
    """Agregar servicios directamente usando SQL para evitar validaciones"""
    try:
        with connection.cursor() as cursor:
            # Verificar que el documento 44 existe
            cursor.execute(
                "SELECT id, numero_documento FROM taller_documento WHERE id = 44"
            )
            doc_result = cursor.fetchone()

            if not doc_result:
                print("❌ Documento 44 no encontrado")
                return False

            print(
                f"✅ Documento encontrado: ID {doc_result[0]}, Número: {doc_result[1]}"
            )

            # Verificar servicios existentes
            cursor.execute(
                "SELECT COUNT(*) FROM taller_lineaservicio WHERE documento_id = 44"
            )
            servicios_count = cursor.fetchone()[0]
            print(f"Servicios existentes: {servicios_count}")

            # Agregar servicios si no existen
            if servicios_count == 0:
                print("📝 Agregando servicios...")

                # Insertar líneas de servicio usando SQL directo
                cursor.execute(
                    """
                    INSERT INTO taller_lineaservicio 
                    (documento_id, servicio_id, nombre, cantidad, precio_unitario, descuento, observaciones)
                    VALUES (44, NULL, 'Cambio de aceite motor', 1, '30.00', '0.00', '')
                """
                )

                cursor.execute(
                    """
                    INSERT INTO taller_lineaservicio 
                    (documento_id, servicio_id, nombre, cantidad, precio_unitario, descuento, observaciones)
                    VALUES (44, NULL, 'Revisión de frenos', 1, '25.00', '0.00', '')
                """
                )

                print("✅ Servicios agregados vía SQL")

            # Verificar otros servicios existentes
            cursor.execute(
                "SELECT COUNT(*) FROM taller_lineaotroservicio WHERE documento_id = 44"
            )
            otros_count = cursor.fetchone()[0]
            print(f"Otros servicios existentes: {otros_count}")

            # Agregar otros servicios si no existen
            if otros_count == 0:
                print("📝 Agregando otros servicios...")

                cursor.execute(
                    """
                    INSERT INTO taller_lineaotroservicio 
                    (documento_id, servicio_externo_id, servicio_id, nombre, empresa_externa, cantidad, costo_interno, precio_cliente, observaciones)
                    VALUES (44, NULL, NULL, 'Instalación de Audio', 'AudioCar Professional', 1, '25.00', '40.00', '')
                """
                )

                cursor.execute(
                    """
                    INSERT INTO taller_lineaotroservicio 
                    (documento_id, servicio_externo_id, servicio_id, nombre, empresa_externa, cantidad, costo_interno, precio_cliente, observaciones)
                    VALUES (44, NULL, NULL, 'Polarizado de ventanas', 'TintPro Services', 1, '35.00', '60.00', '')
                """
                )

                print("✅ Otros servicios agregados vía SQL")

            # Verificar que las líneas fueron creadas
            cursor.execute(
                "SELECT COUNT(*) FROM taller_lineaservicio WHERE documento_id = 44"
            )
            servicios_final = cursor.fetchone()[0]

            cursor.execute(
                "SELECT COUNT(*) FROM taller_lineaotroservicio WHERE documento_id = 44"
            )
            otros_final = cursor.fetchone()[0]

            print(f"\n💰 RESULTADO FINAL:")
            print(f"Servicios internos: {servicios_final}")
            print(f"Otros servicios: {otros_final}")

            # Actualizar totales del documento
            cursor.execute(
                """
                UPDATE taller_documento 
                SET neto_servicios = (
                    SELECT COALESCE(SUM(cantidad * precio_unitario), 0) 
                    FROM taller_lineaservicio 
                    WHERE documento_id = 44
                ) + (
                    SELECT COALESCE(SUM(cantidad * precio_cliente), 0) 
                    FROM taller_lineaotroservicio 
                    WHERE documento_id = 44
                )
                WHERE id = 44
            """
            )

            print("✅ Totales del documento actualizados")

            return True

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = agregar_servicios_sql()
    if success:
        print(f"\n🎉 ¡Documento 44 actualizado!")
        print(f"Ver en: http://127.0.0.1:8000/us/documentos/44/")
    else:
        print(f"\n💥 No se pudo actualizar el documento")
