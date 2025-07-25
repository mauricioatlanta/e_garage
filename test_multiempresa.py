import os
import django
import sys
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings_sqlite')
django.setup()

from django.contrib.auth.models import User
from taller.models.empresa import Empresa
from taller.models.clientes import Cliente
from taller.models.vehiculos import Vehiculo

def test_multiempresa_filtrado():
    """Test del filtrado multiempresa para clientes y vehículos"""
    
    print("🔍 TEST: Filtrado Multiempresa")
    print("=" * 50)
    
    # 1. Verificar usuarios y empresas
    usuarios = User.objects.all()
    empresas = Empresa.objects.all()
    
    print(f"👤 Total usuarios: {usuarios.count()}")
    print(f"🏢 Total empresas: {empresas.count()}")
    
    # 2. Mostrar distribución de clientes por empresa
    print(f"\n📊 DISTRIBUCIÓN DE CLIENTES:")
    for empresa in empresas:
        clientes_empresa = Cliente.objects.filter(empresa=empresa)
        print(f"   🏢 {empresa.nombre_taller}: {clientes_empresa.count()} clientes")
        for cliente in clientes_empresa[:3]:  # Mostrar solo los primeros 3
            print(f"      - {cliente.nombre} {cliente.apellido or ''}")
        if clientes_empresa.count() > 3:
            print(f"      ... y {clientes_empresa.count() - 3} más")
    
    # 3. Mostrar distribución de vehículos por empresa
    print(f"\n🚗 DISTRIBUCIÓN DE VEHÍCULOS:")
    for empresa in empresas:
        vehiculos_empresa = Vehiculo.objects.filter(empresa=empresa)
        print(f"   🏢 {empresa.nombre_taller}: {vehiculos_empresa.count()} vehículos")
        for vehiculo in vehiculos_empresa[:3]:  # Mostrar solo los primeros 3
            cliente = vehiculo.cliente
            print(f"      - {vehiculo.patente} (Cliente: {cliente.nombre})")
        if vehiculos_empresa.count() > 3:
            print(f"      ... y {vehiculos_empresa.count() - 3} más")
    
    # 4. Verificar si hay filtros cruzados (problema de seguridad)
    print(f"\n🔒 VERIFICACIÓN DE SEGURIDAD:")
    
    total_clientes = Cliente.objects.count()
    total_vehiculos = Vehiculo.objects.count()
    
    clientes_por_empresa = sum(Cliente.objects.filter(empresa=emp).count() for emp in empresas)
    vehiculos_por_empresa = sum(Vehiculo.objects.filter(empresa=emp).count() for emp in empresas)
    
    print(f"   📊 Clientes totales: {total_clientes}")
    print(f"   📊 Clientes por empresa: {clientes_por_empresa}")
    print(f"   {'✅' if total_clientes == clientes_por_empresa else '❌'} Consistencia clientes")
    
    print(f"   📊 Vehículos totales: {total_vehiculos}")
    print(f"   📊 Vehículos por empresa: {vehiculos_por_empresa}")
    print(f"   {'✅' if total_vehiculos == vehiculos_por_empresa else '❌'} Consistencia vehículos")
    
    # 5. Buscar registros sin empresa (problema potencial)
    clientes_sin_empresa = Cliente.objects.filter(empresa__isnull=True)
    vehiculos_sin_empresa = Vehiculo.objects.filter(empresa__isnull=True)
    
    if clientes_sin_empresa.exists():
        print(f"   ⚠️ {clientes_sin_empresa.count()} clientes sin empresa asignada")
    else:
        print(f"   ✅ Todos los clientes tienen empresa asignada")
    
    if vehiculos_sin_empresa.exists():
        print(f"   ⚠️ {vehiculos_sin_empresa.count()} vehículos sin empresa asignada")
    else:
        print(f"   ✅ Todos los vehículos tienen empresa asignada")
    
    # 6. URLs de testing
    print(f"\n🌐 URLs PARA TESTING:")
    print(f"   🔧 Crear documento: http://127.0.0.1:8000/documentos/nuevo/")
    print(f"   📋 Autocomplete cliente: http://127.0.0.1:8000/autocomplete/cliente/")
    print(f"   🚗 Autocomplete vehículo: http://127.0.0.1:8000/autocomplete/vehiculo/")
    
    print(f"\n🎯 ESTADO FINAL:")
    if total_clientes == clientes_por_empresa and total_vehiculos == vehiculos_por_empresa:
        print(f"   ✅ Filtrado multiempresa funcionando correctamente")
    else:
        print(f"   ❌ Hay problemas en el filtrado multiempresa")

def crear_datos_test_multiempresa():
    """Crear datos de prueba para múltiples empresas"""
    print("\n🧪 CREANDO DATOS TEST MULTIEMPRESA")
    
    # Obtener usuarios existentes
    usuarios = User.objects.all()[:2]  # Tomar los primeros 2 usuarios
    
    if len(usuarios) < 2:
        print("❌ Se necesitan al menos 2 usuarios para el test multiempresa")
        return
    
    contador_clientes = Cliente.objects.count()
    contador_vehiculos = Vehiculo.objects.count()
    
    for i, user in enumerate(usuarios):
        # Obtener o crear empresa
        try:
            empresa = user.empresa_usuario
        except:
            empresa, created = Empresa.objects.get_or_create(
                usuario=user,
                defaults={'nombre_taller': f'Taller {user.username}'}
            )
        
        # Crear cliente para esta empresa
        cliente = Cliente.objects.create(
            empresa=empresa,
            nombre=f"Cliente Test {i+1}",
            apellido=f"Empresa {empresa.nombre_taller}",
            telefono=f"12345678{i}",
            email=f"cliente{i}@{empresa.nombre_taller.lower().replace(' ', '')}.com"
        )
        
        print(f"   ✅ Cliente creado: {cliente.nombre} para {empresa.nombre_taller}")
    
    print(f"   📊 Clientes antes: {contador_clientes}, después: {Cliente.objects.count()}")

if __name__ == "__main__":
    test_multiempresa_filtrado()
    crear_datos_test_multiempresa()
    print("\n" + "="*50)
    test_multiempresa_filtrado()  # Ejecutar nuevamente para ver cambios
