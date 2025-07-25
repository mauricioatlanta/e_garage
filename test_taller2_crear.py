"""
Script para simular login como taller2 y crear documento de prueba
"""
import os
import django
import sys
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings_sqlite')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from taller.models.empresa import Empresa
import json

def test_crear_documento_taller2():
    """Test de creación de documento como usuario taller2"""
    
    print("🧪 TEST: Crear documento como taller2")
    print("=" * 50)
    
    # Obtener usuario taller2
    try:
        user_taller2 = User.objects.get(username='taller2')
        print(f"👤 Usuario encontrado: {user_taller2.username}")
    except User.DoesNotExist:
        print("❌ Usuario taller2 no encontrado")
        return
    
    # Obtener empresa de taller2
    try:
        empresa_taller2 = user_taller2.empresa_usuario
        print(f"🏢 Empresa: {empresa_taller2.nombre_taller}")
    except AttributeError:
        print("❌ Usuario taller2 no tiene empresa asignada")
        return
    
    # Crear cliente de prueba para Django Test Client
    client = Client()
    
    # Hacer login
    client.force_login(user_taller2)
    print(f"🔑 Login realizado como: {user_taller2.username}")
    
    # Obtener clientes de esta empresa
    from taller.models.clientes import Cliente
    clientes_empresa = Cliente.objects.filter(empresa=empresa_taller2)
    print(f"👥 Clientes disponibles para esta empresa: {clientes_empresa.count()}")
    
    if not clientes_empresa.exists():
        print("⚠️ No hay clientes para esta empresa")
        return
    
    cliente = clientes_empresa.first()
    print(f"👤 Usando cliente: {cliente.nombre}")
    
    # Datos del documento a crear
    json_items = json.dumps([
        {
            "tipo": "repuesto",
            "partnumber": "TEST002",
            "nombre": "Filtro de aceite TEST-TALLER2",
            "cantidad": 1,
            "precio": 25000
        },
        {
            "tipo": "servicio", 
            "nombre": "Servicio TEST-TALLER2",
            "precio": 35000
        }
    ])
    
    # Datos del formulario
    form_data = {
        'tipo_documento': 'Presupuesto',
        'fecha': '2025-07-22',
        'cliente': cliente.id,
        'kilometraje': 150000,
        'json_items': json_items
    }
    
    print(f"📤 Enviando datos:")
    print(f"   Cliente: {cliente.nombre}")
    print(f"   JSON items: {json_items}")
    
    # Enviar petición POST
    response = client.post('/documentos/nuevo/', form_data)
    
    print(f"📊 Respuesta: Status {response.status_code}")
    
    if response.status_code == 302:  # Redirect después de crear
        print(f"✅ Documento creado (redirect)")
        
        # Verificar que el documento se creó con datos
        from taller.models.documento import Documento, RepuestoDocumento, ServicioDocumento
        documento_creado = Documento.objects.filter(empresa=empresa_taller2).order_by('-id').first()
        
        if documento_creado:
            print(f"📋 Documento creado: #{documento_creado.id} - {documento_creado.numero_documento}")
            
            repuestos = RepuestoDocumento.objects.filter(documento=documento_creado)
            servicios = ServicioDocumento.objects.filter(documento=documento_creado)
            
            print(f"🔩 Repuestos: {repuestos.count()}")
            for rep in repuestos:
                print(f"   - {rep.nombre}: ${rep.precio}")
            
            print(f"⚙️ Servicios: {servicios.count()}")
            for serv in servicios:
                print(f"   - {serv.nombre}: ${serv.precio}")
            
            if repuestos.exists() or servicios.exists():
                print(f"✅ ÉXITO: Documento tiene datos")
                print(f"🔗 URL: http://127.0.0.1:8000/documentos/{documento_creado.id}/")
            else:
                print(f"❌ PROBLEMA: Documento sin datos de repuestos/servicios")
        else:
            print(f"❌ No se encontró el documento creado")
    else:
        print(f"❌ Error en creación: {response.status_code}")
        if hasattr(response, 'content'):
            print(f"Response content: {response.content.decode()[:500]}")

if __name__ == "__main__":
    test_crear_documento_taller2()
