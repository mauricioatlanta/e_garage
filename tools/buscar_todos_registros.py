#!/usr/bin/env python
"""
Script para buscar TODOS los registros relacionados con suscripciones
Incluye: usuarios, empresas, suscripciones, trials, embudo, etc.
"""

import os
import sys
import django
from collections import defaultdict

sys.path.insert(0, '/home/atlantareciclajes/apps/egarage/current')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_taller.settings')
django.setup()

from django.contrib.auth.models import User
from taller.models.suscripcion import Suscripcion
from taller.models.empresa import Empresa

# Intentar importar otros modelos relacionados
try:
    from taller.models.trial import TrialRegistro
    tiene_trial = True
except:
    tiene_trial = False
    TrialRegistro = None

try:
    from taller.models.registro_embudo import RegistroEmbudoSuscriptor
    tiene_embudo = True
except:
    tiene_embudo = False
    RegistroEmbudoSuscriptor = None

print("="*80)
print("BÚSQUEDA COMPLETA DE REGISTROS")
print("="*80)
print()

# 1. Usuarios
print("1. USUARIOS:")
print("-"*80)
usuarios = User.objects.all()
print(f"Total usuarios: {usuarios.count()}")
for user in usuarios:
    print(f"  - ID: {user.id} | Email: {user.email} | Username: {user.username} | Fecha: {user.date_joined}")
print()

# 2. Empresas
print("2. EMPRESAS:")
print("-"*80)
empresas = Empresa.objects.all()
print(f"Total empresas: {empresas.count()}")
por_pais_empresas = defaultdict(list)
for empresa in empresas:
    por_pais_empresas[empresa.pais].append(empresa)
    print(f"  - ID: {empresa.id} | Nombre: {empresa.nombre_taller} | País: {empresa.pais} | User ID: {empresa.user.id if empresa.user else 'None'}")
print()

# 3. Suscripciones
print("3. SUSCRIPCIONES:")
print("-"*80)
suscripciones = Suscripcion.objects.all()
print(f"Total suscripciones: {suscripciones.count()}")
for suscripcion in suscripciones:
    print(f"  - User: {suscripcion.user.email} | Tipo: {suscripcion.tipo} | Activa: {suscripcion.activa} | Fin: {suscripcion.fecha_fin}")
print()

# 4. Trials (si existe)
if tiene_trial and TrialRegistro:
    print("4. REGISTROS DE TRIAL:")
    print("-"*80)
    trials = TrialRegistro.objects.all()
    print(f"Total trials: {trials.count()}")
    for trial in trials:
        print(f"  - Email: {trial.email} | Nombre: {trial.nombre} | Activa: {trial.prueba_activa} | Fecha: {trial.fecha_registro}")
    print()

# 5. Embudo (si existe)
if tiene_embudo and RegistroEmbudoSuscriptor:
    print("5. REGISTROS DE EMBUDO:")
    print("-"*80)
    embudos = RegistroEmbudoSuscriptor.objects.all()
    print(f"Total registros embudo: {embudos.count()}")
    for embudo in embudos:
        print(f"  - User: {embudo.user.email} | País: {embudo.pais} | Trial: {embudo.obtuvo_trial} | Fecha: {embudo.fecha_registro}")
    print()

# 6. Resumen por país
print("="*80)
print("RESUMEN POR PAÍS (EMPRESAS)")
print("="*80)
for pais in sorted(por_pais_empresas.keys()):
    print(f"{pais}: {len(por_pais_empresas[pais])} empresas")
print()

# 7. Usuarios con empresa vs sin empresa
print("="*80)
print("USUARIOS CON/SIN EMPRESA")
print("="*80)
usuarios_con_empresa = []
usuarios_sin_empresa = []

for user in usuarios:
    tiene_empresa = False
    try:
        empresa = Empresa.objects.get(user=user)
        tiene_empresa = True
    except:
        try:
            empresa = Empresa.objects.filter(usuario=user).first()
            if empresa:
                tiene_empresa = True
        except:
            pass
    
    if tiene_empresa:
        usuarios_con_empresa.append(user)
    else:
        usuarios_sin_empresa.append(user)

print(f"Usuarios con empresa: {len(usuarios_con_empresa)}")
for user in usuarios_con_empresa:
    try:
        empresa = Empresa.objects.get(user=user)
        print(f"  - {user.email} → {empresa.nombre_taller} ({empresa.pais})")
    except:
        print(f"  - {user.email} → (empresa encontrada pero error al obtener)")
print()

print(f"Usuarios sin empresa: {len(usuarios_sin_empresa)}")
for user in usuarios_sin_empresa:
    print(f"  - {user.email}")
print()

# 8. Verificar si hay datos en otras bases de datos
print("="*80)
print("VERIFICACIÓN DE BASES DE DATOS")
print("="*80)
from django.conf import settings
print(f"Base de datos configurada: {settings.DATABASES['default'].get('NAME', 'N/A')}")
print()
