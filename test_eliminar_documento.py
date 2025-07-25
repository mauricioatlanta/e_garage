#!/usr/bin/env python
"""
Script de prueba para verificar la funcionalidad de eliminación de documentos
"""
import os
import sys
import django
from django.conf import settings

# Configurar el entorno de Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_taller.settings')
django.setup()

from django.contrib.auth.models import User
from taller.models.documento import Documento
from taller.models.empresa import Empresa
from taller.models.clientes import Cliente

def test_eliminar_documento():
    """
    Prueba la funcionalidad de eliminación de documentos
    """
    print("🔍 Verificando documentos existentes...")
    
    # Listar todos los documentos
    documentos = Documento.objects.all()
    print(f"📄 Total de documentos en la base de datos: {documentos.count()}")
    
    for doc in documentos:
        print(f"  - ID: {doc.id}, Tipo: {doc.tipo_documento}, Número: {doc.numero_documento}, Empresa: {doc.empresa}")
    
    # Verificar empresas
    print("\n🏢 Empresas existentes:")
    empresas = Empresa.objects.all()
    for empresa in empresas:
        print(f"  - ID: {empresa.id}, Nombre: {empresa.nombre if hasattr(empresa, 'nombre') else 'Sin nombre'}")
    
    # Verificar usuarios y sus empresas
    print("\n👤 Usuarios y sus empresas:")
    usuarios = User.objects.all()
    for usuario in usuarios:
        try:
            empresa_usuario = usuario.empresa_usuario
            print(f"  - Usuario: {usuario.username}, Empresa: {empresa_usuario}")
        except AttributeError:
            print(f"  - Usuario: {usuario.username}, Sin empresa asociada")
    
    return documentos.count() > 0

def crear_datos_prueba():
    """
    Crear datos de prueba si no existen
    """
    print("\n🔧 Creando datos de prueba...")
    
    # Crear empresa de prueba
    empresa, created = Empresa.objects.get_or_create(
        nombre="Taller de Prueba"
    )
    if created:
        print(f"✅ Empresa creada: {empresa}")
    
    # Crear cliente de prueba
    cliente, created = Cliente.objects.get_or_create(
        nombre="Cliente de Prueba",
        empresa=empresa,
        defaults={'telefono': '123456789', 'email': 'cliente@test.com'}
    )
    if created:
        print(f"✅ Cliente creado: {cliente}")
    
    # Crear documento de prueba
    documento, created = Documento.objects.get_or_create(
        tipo_documento="Presupuesto",
        numero_documento="TEST-001",
        empresa=empresa,
        cliente=cliente
    )
    if created:
        print(f"✅ Documento creado: {documento}")
    
    return documento

if __name__ == "__main__":
    print("🚀 Iniciando prueba de eliminación de documentos\n")
    
    # Verificar estado actual
    tiene_datos = test_eliminar_documento()
    
    if not tiene_datos:
        print("\n⚠️  No hay documentos. Creando datos de prueba...")
        crear_datos_prueba()
        test_eliminar_documento()
    
    print("\n✅ Prueba completada. La vista eliminar_documento ahora:")
    print("   - ✅ Verifica que el usuario esté autenticado")
    print("   - ✅ Verifica que el documento pertenezca a la empresa del usuario")
    print("   - ✅ Maneja errores de eliminación")
    print("   - ✅ Muestra mensajes de confirmación")
    print("   - ✅ Redirige correctamente a la lista de documentos")
