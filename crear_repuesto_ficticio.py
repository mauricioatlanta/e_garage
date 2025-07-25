#!/usr/bin/env python
"""
Script para crear un repuesto ficticio usando SQLite directamente
"""
import os
import sys
import django

# Configurar Django con SQLite en lugar de PostgreSQL
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'e_garage.settings')

# Configurar SQLite como base de datos temporal
os.environ['USE_SQLITE'] = '1'

# Configurar Django
django.setup()

def crear_repuesto_ficticio():
    print("🔧 CREANDO REPUESTO FICTICIO")
    print("=" * 40)
    
    # Importar después de configurar Django
    from taller.models.repuesto import Repuesto
    from taller.models.empresa import Empresa  
    from taller.models.tienda import Tienda
    from taller.forms.repuesto import RepuestoForm
    
    try:
        # Verificar empresas existentes
        empresas = Empresa.objects.all()
        print(f"📊 Empresas en BD: {empresas.count()}")
        
        if empresas.exists():
            empresa = empresas.first()
            print(f"✓ Usando empresa existente: {empresa.nombre_taller}")
        else:
            print("⚠️ No hay empresas en la BD. Necesitas crear una empresa primero.")
            return
            
        # Verificar tiendas existentes  
        tiendas = Tienda.objects.all()
        print(f"📊 Tiendas en BD: {tiendas.count()}")
        
        if tiendas.exists():
            tienda = tiendas.first()
            print(f"✓ Usando tienda existente: {tienda.nombre}")
        else:
            print("⚠️ No hay tiendas en la BD. Necesitas crear una tienda primero.")
            return

        # Datos del repuesto ficticio
        datos_repuesto = {
            'tienda': tienda.pk,
            'nombre_repuesto': 'Filtro de Aceite Premium',
            'part_number': 'FILT-001',
            'precio_compra': '$8.500',    # $8,500
            'precio_venta': '$12.900',    # $12,900
            'stock': 15,
        }
        
        print(f"\n📝 Datos del repuesto a crear:")
        for key, value in datos_repuesto.items():
            print(f"   {key}: {value}")
        
        # Crear formulario
        print(f"\n🔄 Validando formulario...")
        form = RepuestoForm(datos_repuesto)
        
        if form.is_valid():
            print("✅ Formulario válido")
            print(f"📊 Datos limpios: {form.cleaned_data}")
            
            # Guardar repuesto
            print(f"\n💾 Guardando repuesto...")
            repuesto = form.save(commit=False)
            repuesto.empresa = empresa
            repuesto.save()
            
            print(f"\n🎉 ¡REPUESTO CREADO EXITOSAMENTE!")
            print(f"   ID: {repuesto.id}")
            print(f"   Nombre: {repuesto.nombre_repuesto}")
            print(f"   Part Number: {repuesto.part_number}")
            print(f"   Precio Compra: ${repuesto.precio_compra:,}")
            print(f"   Precio Venta: ${repuesto.precio_venta:,}")
            print(f"   Stock: {repuesto.stock}")
            print(f"   Tienda: {repuesto.tienda.nombre}")
            print(f"   Empresa: {repuesto.empresa.nombre_taller}")
            
            # Verificar que se guardó correctamente
            repuesto_verificado = Repuesto.objects.get(id=repuesto.id)
            print(f"\n✅ Verificación: Repuesto encontrado en BD con ID {repuesto_verificado.id}")
            
        else:
            print("❌ Errores en el formulario:")
            for field, errors in form.errors.items():
                print(f"   {field}: {', '.join(errors)}")
                
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        print(f"Detalles: {traceback.format_exc()}")

if __name__ == "__main__":
    crear_repuesto_ficticio()
