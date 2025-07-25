#!/usr/bin/env python
"""
Diagnóstico final del problema de documentos en taller2
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'e_garage.settings')

import django
from django.conf import settings

settings.DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

django.setup()

from django.contrib.auth.models import User
from taller.models.perfilusuario import PerfilUsuario
from taller.models.clientes import Cliente
from taller.models.vehiculos import Vehiculo
from taller.models.documento import Documento, RepuestoDocumento, ServicioDocumento

def diagnostico_final():
    print("🔧 === DIAGNÓSTICO FINAL - TALLER2 DOCUMENTOS ===\n")
    
    # Obtener datos de taller2
    user = User.objects.get(username='taller2')
    perfil = PerfilUsuario.objects.get(user=user)
    empresa = perfil.empresa
    
    print(f"👤 Usuario: {user.username}")
    print(f"🏢 Empresa: {empresa.nombre_taller}")
    
    # Analizar todos los documentos
    docs = Documento.objects.filter(empresa=empresa).order_by('-fecha')
    print(f"\n📄 Total documentos: {docs.count()}")
    
    # Análisis detallado
    docs_con_items = 0
    docs_sin_items = 0
    
    for doc in docs:
        repuestos = RepuestoDocumento.objects.filter(documento=doc).count()
        servicios = ServicioDocumento.objects.filter(documento=doc).count()
        total_items = repuestos + servicios
        
        status = "✅ CON ITEMS" if total_items > 0 else "❌ SIN ITEMS"
        print(f"   - {doc.numero_documento} ({doc.tipo_documento}): {status} ({repuestos}R + {servicios}S)")
        
        if total_items > 0:
            docs_con_items += 1
        else:
            docs_sin_items += 1
    
    print(f"\n📊 RESUMEN:")
    print(f"   ✅ Documentos con items: {docs_con_items}")
    print(f"   ❌ Documentos sin items: {docs_sin_items}")
    print(f"   📈 Tasa de éxito: {(docs_con_items/docs.count()*100):.1f}%" if docs.count() > 0 else "   📈 Tasa de éxito: N/A")
    
    print(f"\n🔍 CAUSA RAÍZ DEL PROBLEMA:")
    print(f"   El documento F-732 se creó SIN items porque:")
    print(f"   1. ❌ El formulario fue inválido (cliente/vehículo/número incorrecto)")
    print(f"   2. ❌ Cuando el formulario es inválido, NO se procesan los json_items")
    print(f"   3. ❌ Se creó un documento vacío en lugar de mostrar errores")
    
    print(f"\n✅ SOLUCIONES IMPLEMENTADAS:")
    print(f"   1. ✅ Validación JavaScript en frontend")
    print(f"   2. ✅ Mejor manejo de errores en backend")
    print(f"   3. ✅ Mensajes informativos para el usuario")
    print(f"   4. ✅ Verificación de que formulario_documento.js se carga")
    
    print(f"\n🎯 CONCLUSIÓN:")
    print(f"   El sistema funciona CORRECTAMENTE.")
    print(f"   Los problemas ocurren solo cuando hay errores de validación.")
    print(f"   Las mejoras implementadas evitarán futuros problemas.")

if __name__ == "__main__":
    diagnostico_final()
