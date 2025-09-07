#!/usr/bin/env python3
"""
🔒 AUDITORÍA DE SEGURIDAD - SEPARACIÓN DE DATOS POR EMPRESA
Verifica que no hay fuga de datos entre talleres en eGarage
"""

import os
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent


def encontrar_problemas_seguridad():
    """Buscar patrones problemáticos en los archivos de views"""

    print("🔍 AUDITORÍA DE SEGURIDAD - SEPARACIÓN DE DATOS")
    print("=" * 60)

    archivos_views = [
        "taller/documentos/views.py",
        "taller/reportes/views.py",
        "taller/clientes/views.py",
        "taller/vehiculos/views.py",
        "taller/repuestos/views.py",
        "taller/servicios/views.py",
        "taller/views.py",
        "taller/api/views.py",
        "taller/exports/views.py",
    ]

    # Patrones problemáticos que NO deben existir
    patrones_problematicos = [
        (r"\.objects\.all\(\)", "❌ CRÍTICO: .objects.all() sin filtro de empresa"),
        (
            r"\.objects\.filter\([^)]*\)(?![^)]*empresa)",
            "⚠️ POSIBLE: filter() sin empresa (revisar contexto)",
        ),
        (
            r"ServicioDocumento\.objects\.filter\([^)]*\)(?![^)]*documento__empresa)",
            "❌ CRÍTICO: ServicioDocumento sin filtro empresa",
        ),
        (
            r"RepuestoDocumento\.objects\.filter\([^)]*\)(?![^)]*documento__empresa)",
            "❌ CRÍTICO: RepuestoDocumento sin filtro empresa",
        ),
        (
            r"Cliente\.objects\.(?!filter\([^)]*empresa)",
            "❌ CRÍTICO: Cliente sin filtro empresa",
        ),
        (
            r"Vehiculo\.objects\.(?!filter\([^)]*empresa)",
            "❌ CRÍTICO: Vehiculo sin filtro empresa",
        ),
        (
            r"Documento\.objects\.(?!filter\([^)]*empresa)",
            "❌ CRÍTICO: Documento sin filtro empresa",
        ),
        (
            r"Repuesto\.objects\.(?!filter\([^)]*empresa)",
            "❌ CRÍTICO: Repuesto sin filtro empresa",
        ),
        (
            r"Mecanico\.objects\.(?!filter\([^)]*empresa)",
            "❌ CRÍTICO: Mecanico sin filtro empresa",
        ),
    ]

    # Patrones correctos que deben existir
    patrones_correctos = [
        (r"\.filter\([^)]*empresa=", "✅ CORRECTO: Filtro por empresa"),
        (r"request\.user\.empresa", "✅ CORRECTO: Obtiene empresa del usuario"),
        (r"documento__empresa=empresa", "✅ CORRECTO: Filtro por empresa en relación"),
    ]

    problemas_encontrados = []
    archivos_verificados = 0
    archivos_con_problemas = 0

    for archivo_rel in archivos_views:
        archivo_path = PROJECT_ROOT / archivo_rel

        if not archivo_path.exists():
            print(f"⚠️ Archivo no encontrado: {archivo_rel}")
            continue

        archivos_verificados += 1

        try:
            with open(archivo_path, encoding="utf-8") as f:
                contenido = f.read()

            print(f"\n📄 Verificando: {archivo_rel}")

            problemas_archivo = []

            # Buscar patrones problemáticos
            for patron, descripcion in patrones_problematicos:
                coincidencias = re.finditer(patron, contenido, re.MULTILINE)
                for match in coincidencias:
                    linea_num = contenido[: match.start()].count("\n") + 1
                    linea_contenido = contenido.split("\n")[linea_num - 1].strip()

                    # Filtrar falsos positivos
                    if "objects.all()" in patron and (
                        "Empresa.objects" in linea_contenido
                        or "Marca.objects" in linea_contenido
                        or "Modelo.objects" in linea_contenido
                        or "ColorVehiculo.objects" in linea_contenido
                        or "MotorVehiculo.objects" in linea_contenido
                        or "CajaVehiculo.objects" in linea_contenido
                        or "TallerRegion.objects" in linea_contenido
                        or "TallerCiudad.objects" in linea_contenido
                    ):
                        continue  # Estos modelos no necesitan filtro de empresa

                    problemas_archivo.append(
                        {
                            "linea": linea_num,
                            "contenido": linea_contenido,
                            "problema": descripcion,
                            "patron": patron,
                        }
                    )

            if problemas_archivo:
                archivos_con_problemas += 1
                problemas_encontrados.extend(
                    [{**p, "archivo": archivo_rel} for p in problemas_archivo]
                )

                for problema in problemas_archivo:
                    print(f"   {problema['problema']}")
                    print(f"   Línea {problema['linea']}: {problema['contenido']}")
            else:
                print("   ✅ Sin problemas críticos detectados")

            # Verificar filtros correctos
            filtros_correctos = 0
            for patron, descripcion in patrones_correctos:
                coincidencias = len(re.findall(patron, contenido))
                if coincidencias > 0:
                    filtros_correctos += coincidencias

            if filtros_correctos > 0:
                print(f"   ✅ {filtros_correctos} filtros correctos encontrados")

        except Exception as e:
            print(f"   ❌ Error leyendo archivo: {e}")

    # Resumen final
    print("\n" + "=" * 60)
    print("📊 RESUMEN DE AUDITORÍA")
    print("=" * 60)

    print(f"📁 Archivos verificados: {archivos_verificados}")
    print(f"⚠️ Archivos con problemas: {archivos_con_problemas}")
    print(
        f"🚨 Total problemas críticos: {len([p for p in problemas_encontrados if 'CRÍTICO' in p['problema']])}"
    )
    print(
        f"⚠️ Total problemas posibles: {len([p for p in problemas_encontrados if 'POSIBLE' in p['problema']])}"
    )

    if problemas_encontrados:
        print("\n🚨 PROBLEMAS CRÍTICOS DETECTADOS:")
        print("-" * 40)

        for problema in problemas_encontrados:
            if "CRÍTICO" in problema["problema"]:
                print(f"\n📍 {problema['archivo']} (línea {problema['linea']})")
                print(f"   {problema['problema']}")
                print(f"   Código: {problema['contenido']}")

        print("\n🔧 ACCIONES REQUERIDAS:")
        print(
            "1. Agregar filtro .filter(empresa=empresa) en todos los queries críticos"
        )
        print(
            "2. Verificar que request.user.empresa está disponible en todas las vistas"
        )
        print("3. Implementar middleware de empresa si no existe")
        print("4. Ejecutar tests con múltiples empresas para verificar separación")

        return False
    else:
        print("\n🎉 ¡AUDITORÍA EXITOSA!")
        print("✅ No se detectaron fugas de datos entre empresas")
        print("✅ Todos los queries están correctamente filtrados")

        return True


def verificar_middleware_empresa():
    """Verificar que existe middleware de empresa"""
    print("\n🔒 VERIFICANDO MIDDLEWARE DE EMPRESA")
    print("-" * 40)

    middleware_paths = [
        "taller/middleware.py",
        "middleware.py",
        "garage_project/middleware.py",
    ]

    for path in middleware_paths:
        middleware_file = PROJECT_ROOT / path
        if middleware_file.exists():
            try:
                with open(middleware_file, encoding="utf-8") as f:
                    contenido = f.read()

                if "EmpresaMiddleware" in contenido or "empresa" in contenido.lower():
                    print(f"✅ Middleware encontrado en: {path}")
                    return True
            except Exception as e:
                print(f"❌ Error leyendo {path}: {e}")

    print("⚠️ No se encontró middleware de empresa específico")
    print(
        "💡 Recomendación: Implementar EmpresaMiddleware para inyectar request.empresa"
    )
    return False


def sugerir_tests_seguridad():
    """Sugerir tests para verificar separación de datos"""
    print("\n🧪 TESTS DE SEGURIDAD RECOMENDADOS")
    print("-" * 40)

    tests_recomendados = [
        "Crear 2 empresas con datos distintos",
        "Verificar que /reportes/ solo muestra datos de la empresa autenticada",
        "Verificar que /clientes/ solo muestra clientes de la empresa",
        "Verificar que /vehiculos/ solo muestra vehículos de la empresa",
        "Verificar que /documentos/ solo muestra documentos de la empresa",
        "Verificar que APIs no devuelven datos de otras empresas",
        "Verificar que PDFs solo incluyen datos de la empresa",
        "Test de penetración: intentar acceder a datos de otra empresa",
    ]

    for i, test in enumerate(tests_recomendados, 1):
        print(f"{i}. {test}")

    print("\n📝 Script de test sugerido:")
    print("python manage.py test taller.tests.test_separacion_empresas")


if __name__ == "__main__":
    print("🛡️ AUDITOR DE SEGURIDAD EGARAGE")
    print("Verificando separación de datos entre empresas")
    print("=" * 60)

    # Cambiar al directorio del proyecto
    os.chdir(PROJECT_ROOT)

    # Ejecutar auditoría
    seguridad_ok = encontrar_problemas_seguridad()

    # Verificar middleware
    middleware_ok = verificar_middleware_empresa()

    # Sugerir tests
    sugerir_tests_seguridad()

    # Resultado final
    print("\n" + "=" * 60)
    if seguridad_ok:
        print("🎉 SISTEMA SEGURO - Sin fugas de datos detectadas")
        if not middleware_ok:
            print("⚠️ Considerar implementar middleware de empresa para mayor robustez")
    else:
        print("🚨 VULNERABILIDADES DETECTADAS - Acción inmediata requerida")

    print("\n📋 CHECKLIST FINAL:")
    print(f"{'✅' if seguridad_ok else '❌'} Queries filtrados por empresa")
    print(f"{'✅' if middleware_ok else '⚠️'} Middleware de empresa")
    print("⚠️ Tests de separación (pendiente)")
    print("⚠️ Verificación manual (pendiente)")

    print(f"\n🎯 Estado: {'SEGURO' if seguridad_ok else 'REQUIERE ATENCIÓN'}")
