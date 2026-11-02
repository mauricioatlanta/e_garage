#!/usr/bin/env python
"""
Script de verificación manual de las correcciones multi-tenant
"""

import os
import sys
from pathlib import Path

import django

# Configurar Django
sys.path.append(str(Path(__file__).parent))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "e_garage.settings")
django.setup()


def main():
    print("🔍 VERIFICACIÓN CORRECCIONES MULTI-TENANT")
    print("=" * 50)

    try:
        from taller.models.clientes import Cliente
        from taller.models.empresa import Empresa
        from taller.models.vehiculos import Vehiculo

        # Verificar empresas
        empresas = Empresa.objects.all()
        print(f"📊 Total empresas: {empresas.count()}")

        # Verificar clientes sin empresa
        clientes_sin_empresa = Cliente.objects.filter(empresa__isnull=True)
        print(f"❌ Clientes sin empresa: {clientes_sin_empresa.count()}")

        # Verificar vehículos sin empresa
        vehiculos_sin_empresa = Vehiculo.objects.filter(empresa__isnull=True)
        print(f"❌ Vehículos sin empresa: {vehiculos_sin_empresa.count()}")

        # Verificar distribución por empresa
        print("\n📈 DISTRIBUCIÓN POR EMPRESA:")
        for empresa in empresas:
            clientes_count = Cliente.objects.filter(empresa=empresa).count()
            vehiculos_count = Vehiculo.objects.filter(empresa=empresa).count()
            print(
                f"  🏢 {empresa.nombre_taller}: {clientes_count} clientes, {vehiculos_count} vehículos"
            )

        # Estado final
        if clientes_sin_empresa.count() == 0 and vehiculos_sin_empresa.count() == 0:
            print("\n✅ RESULTADO: BLINDAJE MULTI-TENANT CORRECTO")
            print("   Todos los datos están correctamente asignados a empresas")
        else:
            print("\n⚠️  RESULTADO: AÚN HAY PROBLEMAS")
            print("   Se requiere corrección adicional")

    except Exception as e:
        print(f"❌ Error durante verificación: {e}")
        return False

    return True


if __name__ == "__main__":
    main()
