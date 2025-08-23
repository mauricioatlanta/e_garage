#!/usr/bin/env python
"""Script para verificar datos de mecánicos y documentos"""
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_taller.settings')
django.setup()

from taller.models.tecnico import Mecanico
from taller.models.documento import Documento
from taller.models.empresa import Empresa

print("🔍 VERIFICANDO DATOS DEL SISTEMA...")
print(f"📊 Empresas: {Empresa.objects.count()}")
print(f"🔧 Mecánicos: {Tecnico.objects.count()}")
print(f"📄 Documentos: {Documento.objects.count()}")

if Tecnico.objects.exists():
    print("\n👨‍🔧 MECÁNICOS ENCONTRADOS:")
    for mecanico in Tecnico.objects.all()[:5]:
        print(f"  - {mecanico.nombre} (Empresa: {mecanico.empresa.nombre_taller if mecanico.empresa else 'Sin empresa'})")

if Documento.objects.exists():
    print("\n📋 DOCUMENTOS RECIENTES:")
    for doc in Documento.objects.all()[:5]:
        print(f"  - {doc.numero_documento} - {doc.tipo_documento} (Mecánico: {doc.mecanico.nombre if doc.mecanico else 'Sin mecánico'})")
else:
    print("\n⚠️  No se encontraron documentos. El reporte estará vacío.")
    
print("\n✅ Verificación completada.")
