#!/usr/bin/env python
"""
Script para generar suscripciones consolidadas del backup real
Ejecutar en DigitalOcean
"""
import os, sys, sqlite3, json
from datetime import date, datetime, timedelta
from collections import defaultdict

backup = '/home/atlantareciclajes/apps/egarage/shared/db/db.sqlite3'
suscriptores = {}

print("Conectando a la base de datos...")
conn = sqlite3.connect(backup)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

print("Verificando estructura de la tabla...")
cursor.execute("PRAGMA table_info(taller_empresa)")
columnas = [row[1] for row in cursor.fetchall()]
tiene_user_id = 'user_id' in columnas
print(f"Usando columna: {'user_id' if tiene_user_id else 'usuario_id'}")

print("\nProcesando suscripciones existentes...")
cursor.execute("""
    SELECT s.*, u.email, u.username, u.date_joined, u.is_active, u.is_staff
    FROM taller_suscripcion s
    LEFT JOIN auth_user u ON s.user_id = u.id
""")
suscripciones_existentes = cursor.fetchall()
print(f"Encontradas {len(suscripciones_existentes)} suscripciones existentes")

for row in suscripciones_existentes:
    email = row['email'] or row['username'] or f"user_{row['user_id']}"
    clave = email.lower().strip()
    
    # Buscar empresa
    if tiene_user_id:
        cursor.execute("SELECT * FROM taller_empresa WHERE user_id = ? LIMIT 1", (row['user_id'],))
    else:
        cursor.execute("SELECT * FROM taller_empresa WHERE usuario_id = ? LIMIT 1", (row['user_id'],))
    empresa = cursor.fetchone()
    
    suscriptores[clave] = {
        'user_email': row['email'],
        'user_username': row['username'],
        'user_id_original': row['user_id'],
        'tipo': row['tipo'],
        'fecha_inicio': row['fecha_inicio'],
        'fecha_fin': row['fecha_fin'],
        'activa': bool(row['activa']),
        'empresa': dict(empresa) if empresa else None,
        'tiene_suscripcion_original': True,
    }

print("\nBuscando usuarios con empresas pero sin suscripciones...")
if tiene_user_id:
    cursor.execute("""
        SELECT DISTINCT u.*, e.nombre_taller, e.pais, e.telefono, e.email as empresa_email
        FROM auth_user u
        INNER JOIN taller_empresa e ON e.user_id = u.id
        WHERE u.id NOT IN (SELECT user_id FROM taller_suscripcion)
    """)
else:
    cursor.execute("""
        SELECT DISTINCT u.*, e.nombre_taller, e.pais, e.telefono, e.email as empresa_email
        FROM auth_user u
        INNER JOIN taller_empresa e ON e.usuario_id = u.id
        WHERE u.id NOT IN (SELECT user_id FROM taller_suscripcion)
    """)

usuarios_sin_suscripcion = cursor.fetchall()
print(f"Encontrados {len(usuarios_sin_suscripcion)} usuarios con empresas pero sin suscripción")

for row in usuarios_sin_suscripcion:
    email = row['email'] or row['username'] or f"user_{row['id']}"
    clave = email.lower().strip()
    if clave in suscriptores:
        continue
    
    # Crear suscripción trial de 30 días desde fecha de registro
    fecha_reg = row['date_joined']
    if isinstance(fecha_reg, str):
        try:
            fecha_reg = datetime.fromisoformat(fecha_reg.replace('Z', '+00:00'))
        except:
            fecha_reg = datetime.now()
    fecha_inicio = fecha_reg.date() if isinstance(fecha_reg, datetime) else date.today()
    fecha_fin = fecha_inicio + timedelta(days=30)
    
    suscriptores[clave] = {
        'user_email': row['email'],
        'user_username': row['username'],
        'user_id_original': row['id'],
        'tipo': 'trial',
        'fecha_inicio': fecha_inicio.isoformat(),
        'fecha_fin': fecha_fin.isoformat(),
        'activa': True,
        'empresa': {
            'nombre_taller': row['nombre_taller'],
            'pais': row['pais'],
        },
        'tiene_suscripcion_original': False,
    }
    print(f"  Creada suscripción para: {email} | {row['nombre_taller']} | {row['pais']}")

conn.close()

# Agrupar por país
por_pais = defaultdict(int)
for s in suscriptores.values():
    pais = s.get('empresa', {}).get('pais', 'SIN_PAIS') if s.get('empresa') else 'SIN_PAIS'
    por_pais[pais] += 1

# Generar resultado
resultado = {
    'total_suscriptores_unicos': len(suscriptores),
    'fecha_consolidacion': date.today().isoformat(),
    'por_pais': dict(por_pais),
    'suscripciones': list(suscriptores.values())
}

# Guardar archivo
archivo_salida = 'suscripciones_consolidadas.json'
with open(archivo_salida, 'w', encoding='utf-8') as f:
    json.dump(resultado, f, indent=2, ensure_ascii=False)

print("\n" + "="*80)
print("RESUMEN")
print("="*80)
print(f"Total suscriptores: {len(suscriptores)}")
print(f"Por país:")
for pais, count in sorted(por_pais.items(), key=lambda x: x[1], reverse=True):
    print(f"  {pais}: {count}")
print(f"\nArchivo guardado: {archivo_salida}")
