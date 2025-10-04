#!/usr/bin/env python
"""
Script para verificar y corregir inconsistencias en datos Cliente ↔ Vehículo ↔ Empresa

Uso:
    python check_data_consistency.py --check    # Solo verificar
    python check_data_consistency.py --fix      # Verificar y corregir
    python check_data_consistency.py --dry-run  # Simular correcciones sin aplicar
"""

import os
import sys
import django
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'egarage.settings')
django.setup()

from taller.models.clientes import Cliente
from taller.models.vehiculos import Vehiculo
from taller.models.documento import Documento
from taller.models.empresa import Empresa


def check_inconsistencies():
    """Verifica inconsistencias en los datos"""
    print("🔍 VERIFICANDO INCONSISTENCIAS EN DATOS...")
    print("=" * 60)
    
    issues = []
    
    # 1. Vehículos sin empresa
    vehiculos_sin_empresa = Vehiculo.objects.filter(empresa__isnull=True)
    if vehiculos_sin_empresa.exists():
        count = vehiculos_sin_empresa.count()
        issues.append(f"❌ {count} vehículos sin empresa asignada")
        print(f"   Vehículos sin empresa: {count}")
        
        # Mostrar algunos ejemplos
        for v in vehiculos_sin_empresa[:5]:
            print(f"     - Vehículo ID {v.id}: {v.patente} (Cliente: {v.cliente})")
    
    # 2. Vehículos con empresa diferente a la del cliente
    vehiculos_empresa_inconsistente = Vehiculo.objects.exclude(empresa=F('cliente__empresa'))
    if vehiculos_empresa_inconsistente.exists():
        count = vehiculos_empresa_inconsistente.count()
        issues.append(f"❌ {count} vehículos con empresa diferente a la del cliente")
        print(f"   Vehículos con empresa inconsistente: {count}")
        
        # Mostrar algunos ejemplos
        for v in vehiculos_empresa_inconsistente[:5]:
            print(f"     - Vehículo ID {v.id}: {v.patente}")
            print(f"       Vehículo empresa: {v.empresa}")
            print(f"       Cliente empresa: {v.cliente.empresa}")
    
    # 3. Clientes sin empresa
    clientes_sin_empresa = Cliente.objects.filter(empresa__isnull=True)
    if clientes_sin_empresa.exists():
        count = clientes_sin_empresa.count()
        issues.append(f"❌ {count} clientes sin empresa asignada")
        print(f"   Clientes sin empresa: {count}")
        
        # Mostrar algunos ejemplos
        for c in clientes_sin_empresa[:5]:
            print(f"     - Cliente ID {c.id}: {c.nombre} {c.apellido}")
    
    # 4. Documentos con inconsistencias
    documentos_problematicos = []
    for doc in Documento.objects.select_related('cliente', 'vehiculo', 'empresa'):
        has_issue = False
        
        # Cliente no pertenece a la empresa del documento
        if doc.cliente and doc.empresa and doc.cliente.empresa != doc.empresa:
            has_issue = True
        
        # Vehículo no pertenece a la empresa del documento
        if doc.vehiculo and doc.empresa and doc.vehiculo.empresa != doc.empresa:
            has_issue = True
        
        # Vehículo no pertenece al cliente del documento
        if doc.vehiculo and doc.cliente and doc.vehiculo.cliente != doc.cliente:
            has_issue = True
        
        if has_issue:
            documentos_problematicos.append(doc)
    
    if documentos_problematicos:
        issues.append(f"❌ {len(documentos_problematicos)} documentos con inconsistencias")
        print(f"   Documentos problemáticos: {len(documentos_problematicos)}")
        
        # Mostrar algunos ejemplos
        for doc in documentos_problematicos[:3]:
            print(f"     - Documento ID {doc.id}: {doc.tipo} #{doc.numero}")
            print(f"       Empresa doc: {doc.empresa}")
            print(f"       Cliente: {doc.cliente} (empresa: {doc.cliente.empresa if doc.cliente else 'N/A'})")
            print(f"       Vehículo: {doc.vehiculo} (empresa: {doc.vehiculo.empresa if doc.vehiculo else 'N/A'})")
    
    # Resumen
    print("\n" + "=" * 60)
    if issues:
        print(f"🚨 ENCONTRADAS {len(issues)} INCONSISTENCIAS:")
        for issue in issues:
            print(f"   {issue}")
    else:
        print("✅ NO SE ENCONTRARON INCONSISTENCIAS")
    
    return issues


def fix_inconsistencies(dry_run=False):
    """Corrige las inconsistencias encontradas"""
    print(f"\n🔧 {'SIMULANDO' if dry_run else 'APLICANDO'} CORRECCIONES...")
    print("=" * 60)
    
    fixed_count = 0
    
    # 1. Asignar empresa a vehículos sin empresa (basado en el cliente)
    vehiculos_sin_empresa = Vehiculo.objects.filter(empresa__isnull=True)
    for v in vehiculos_sin_empresa:
        if v.cliente and v.cliente.empresa:
            if not dry_run:
                v.empresa = v.cliente.empresa
                v.save()
            print(f"   ✅ Vehículo {v.id} ({v.patente}): empresa = {v.cliente.empresa}")
            fixed_count += 1
    
    # 2. Corregir vehículos con empresa inconsistente
    vehiculos_empresa_inconsistente = Vehiculo.objects.exclude(empresa=F('cliente__empresa'))
    for v in vehiculos_empresa_inconsistente:
        if v.cliente and v.cliente.empresa:
            old_empresa = v.empresa
            if not dry_run:
                v.empresa = v.cliente.empresa
                v.save()
            print(f"   ✅ Vehículo {v.id} ({v.patente}): {old_empresa} → {v.cliente.empresa}")
            fixed_count += 1
    
    # 3. Asignar empresa a clientes sin empresa (basado en los vehículos)
    clientes_sin_empresa = Cliente.objects.filter(empresa__isnull=True)
    for c in clientes_sin_empresa:
        # Buscar la empresa más común entre los vehículos del cliente
        vehiculos_empresas = Vehiculo.objects.filter(cliente=c, empresa__isnull=False).values_list('empresa', flat=True).distinct()
        if vehiculos_empresas:
            # Usar la primera empresa encontrada
            empresa_comun = vehiculos_empresas[0]
            if not dry_run:
                c.empresa_id = empresa_comun
                c.save()
            print(f"   ✅ Cliente {c.id} ({c.nombre} {c.apellido}): empresa = {empresa_comun}")
            fixed_count += 1
    
    print(f"\n📊 TOTAL CORRECCIONES {'SIMULADAS' if dry_run else 'APLICADAS'}: {fixed_count}")
    
    return fixed_count


def main():
    """Función principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Verificar y corregir inconsistencias en datos')
    parser.add_argument('--check', action='store_true', help='Solo verificar inconsistencias')
    parser.add_argument('--fix', action='store_true', help='Verificar y corregir inconsistencias')
    parser.add_argument('--dry-run', action='store_true', help='Simular correcciones sin aplicar')
    
    args = parser.parse_args()
    
    if not any([args.check, args.fix, args.dry_run]):
        print("❌ Debe especificar --check, --fix o --dry-run")
        parser.print_help()
        return
    
    # Siempre verificar primero
    issues = check_inconsistencies()
    
    # Aplicar correcciones si se solicita
    if args.fix or args.dry_run:
        if issues:
            print(f"\n⚠️  {'SIMULANDO' if args.dry_run else 'APLICANDO'} CORRECCIONES...")
            fixed_count = fix_inconsistencies(dry_run=args.dry_run)
            
            if args.dry_run:
                print(f"\n💡 Para aplicar las correcciones, ejecuta: python {sys.argv[0]} --fix")
            else:
                print(f"\n✅ Correcciones aplicadas exitosamente")
        else:
            print(f"\n✅ No hay correcciones necesarias")


if __name__ == "__main__":
    main()
