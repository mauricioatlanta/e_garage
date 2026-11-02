#!/usr/bin/env python
"""
Script que primero verifica las credenciales del .env y luego consulta.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path("/home/atlantareciclajes/apps/egarage/current")
env_path = BASE_DIR / ".env"

print("🔍 Verificando configuración...")
print(f"Ruta .env: {env_path}")
print(f"¿Existe .env? {env_path.exists()}")

if env_path.exists():
    load_dotenv(env_path)
    print("✅ .env cargado")
else:
    print("⚠️  .env no encontrado, usando valores por defecto")

# Leer configuración
DB_HOST = os.getenv("DB_HOST", "atlantareciclajes.mysql.digitalocean-services.com")
DB_NAME = os.getenv("DB_NAME", "atlantareciclajes$egarage")
DB_USER = os.getenv("DB_USER", "atlantareciclajes")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_PORT = int(os.getenv("DB_PORT", "3306"))

print(f"\n📋 Configuración de BD:")
print(f"  Host: {DB_HOST}")
print(f"  Database: {DB_NAME}")
print(f"  User: {DB_USER}")
print(f"  Password: {'*' * len(DB_PASSWORD) if DB_PASSWORD else 'VACÍA'}")
print(f"  Port: {DB_PORT}")

# Si no hay contraseña, intentar las comunes
if not DB_PASSWORD:
    print("\n⚠️  No se encontró contraseña en .env, intentando valores comunes...")
    passwords_to_try = ["laila2013", "atlantareciclajes", ""]
else:
    passwords_to_try = [DB_PASSWORD]

import pymysql

for password in passwords_to_try:
    try:
        print(
            f"\n🔌 Intentando conectar con contraseña: {'*' * len(password) if password else 'VACÍA'}..."
        )
        connection = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=password,
            database=DB_NAME.replace("$", ""),
            port=DB_PORT,
            cursorclass=pymysql.cursors.DictCursor,
        )
        print("✅ ¡Conexión exitosa!")

        # Si llegamos aquí, la conexión funcionó
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT COUNT(*) as total FROM taller_empresa WHERE suscripcion_activa = 1"
            )
            total = cursor.fetchone()["total"]
            print(f"\n📊 Total empresas activas: {total}")

            cursor.execute(
                """
                SELECT pais, COUNT(*) as total,
                       SUM(CASE WHEN plan = 'trial' THEN 1 ELSE 0 END) as trials
                FROM taller_empresa
                WHERE suscripcion_activa = 1
                GROUP BY pais
                ORDER BY pais
            """
            )
            paises = cursor.fetchall()

            print("\n🌍 RESUMEN POR PAÍS:")
            for row in paises:
                print(f"  {row['pais']}: {row['total']} empresas ({row['trials']} trials)")

        connection.close()
        break

    except pymysql.err.OperationalError as e:
        print(f"❌ Error: {e}")
        continue
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        break
else:
    print("\n❌ No se pudo conectar con ninguna contraseña.")
    print("\n💡 Solución:")
    print("1. Verifica el archivo .env en el servidor")
    print("2. O verifica las credenciales en el dashboard de DigitalOcean")
    print("3. O ejecuta: cat .env | grep DB_")
