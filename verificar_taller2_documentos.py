#!/usr/bin/env python
"""
Script para verificar el problema de taller2 con documentos
"""
import os
import django

# Configurar Django
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'e_garage.settings')

# Configurar temporalmente SQLite
import django
from django.conf import settings

# Sobrescribir configuración de base de datos
settings.DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

django.setup()

from django.contrib.auth.models import User
from taller.models.perfilusuario import PerfilUsuario
from taller.models.empresa import Empresa
from taller.models.documento import Documento, RepuestoDocumento, ServicioDocumento

def verificar_taller2():
    print("=== VERIFICACIÓN TALLER2 - PROBLEMA DOCUMENTOS ===\n")
    
    try:
        # 1. Verificar usuario
        user = User.objects.get(username='taller2')
        print(f"✅ Usuario encontrado: {user.username}")
        print(f"   Email: {user.email}")
        print(f"   Activo: {user.is_active}")
        print(f"   Staff: {user.is_staff}")
        print(f"   Superuser: {user.is_superuser}")
        
        # 2. Verificar PerfilUsuario
        try:
            perfil = PerfilUsuario.objects.get(user=user)
            print(f"\n✅ PerfilUsuario encontrado:")
            print(f"   ID: {perfil.pk}")
            print(f"   Empresa: {perfil.empresa}")
            print(f"   Empresa ID: {perfil.empresa.pk if perfil.empresa else 'NULL'}")
            print(f"   Rol: {perfil.rol}")
            
            if perfil.empresa:
                print(f"\n📋 Información de la Empresa:")
                print(f"   Nombre: {perfil.empresa.nombre_taller}")
                print(f"   Suscripción activa: {perfil.empresa.suscripcion_activa}")
                print(f"   Fecha inicio: {perfil.empresa.fecha_inicio}")
            else:
                print("\n❌ PROBLEMA: No hay empresa asociada al PerfilUsuario")
                
        except PerfilUsuario.DoesNotExist:
            print("\n❌ PROBLEMA CRÍTICO: PerfilUsuario NO ENCONTRADO para taller2")
            return
        
        # 3. Verificar documentos
        docs = Documento.objects.filter(empresa=perfil.empresa).order_by('-fecha')
        print(f"\n📄 Documentos de la empresa: {docs.count()}")
        
        if docs.exists():
            print("\n🔍 Últimos 5 documentos:")
            for i, doc in enumerate(docs[:5], 1):
                print(f"   {i}. Doc #{doc.numero_documento} ({doc.tipo_documento})")
                print(f"      Empresa: {doc.empresa.nombre_taller}")
                print(f"      Cliente: {doc.cliente}")
                print(f"      Fecha: {doc.fecha}")
                
                # Verificar items del documento
                repuestos = RepuestoDocumento.objects.filter(documento=doc)
                servicios = ServicioDocumento.objects.filter(documento=doc)
                print(f"      Repuestos: {repuestos.count()}")
                print(f"      Servicios: {servicios.count()}")
                if repuestos.exists():
                    for rep in repuestos[:3]:
                        print(f"        - Repuesto: {rep.nombre} (${rep.precio:,.0f})")
                if servicios.exists():
                    for serv in servicios[:3]:
                        print(f"        - Servicio: {serv.nombre} (${serv.precio:,.0f})")
                print()
        
        # 4. Verificar último documento con problemas
        ultimo_doc = docs.first()
        if ultimo_doc:
            print(f"\n🔎 ANÁLISIS DETALLADO DEL ÚLTIMO DOCUMENTO:")
            print(f"   Documento #{ultimo_doc.numero_documento}")
            print(f"   Tipo: {ultimo_doc.tipo_documento}")
            print(f"   Cliente: {ultimo_doc.cliente}")
            print(f"   Vehículo: {ultimo_doc.vehiculo}")
            
            repuestos_bd = RepuestoDocumento.objects.filter(documento=ultimo_doc)
            servicios_bd = ServicioDocumento.objects.filter(documento=ultimo_doc)
            print(f"\n   Items en base de datos:")
            print(f"     Repuestos: {repuestos_bd.count()}")
            print(f"     Servicios: {servicios_bd.count()}")
            
            for rep in repuestos_bd:
                print(f"     - Repuesto: {rep.nombre}")
                print(f"       Precio: ${rep.precio:,.0f}")
                print(f"       Cantidad: {rep.cantidad}")
                print(f"       Total: ${rep.total:,.0f}")
                
            for serv in servicios_bd:
                print(f"     - Servicio: {serv.nombre}")
                print(f"       Precio: ${serv.precio:,.0f}")
        
    except User.DoesNotExist:
        print("❌ PROBLEMA CRÍTICO: Usuario taller2 no encontrado")
    
    except Exception as e:
        print(f"❌ ERROR INESPERADO: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verificar_taller2()
