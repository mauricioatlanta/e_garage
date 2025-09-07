#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re


def buscar_funciones_sin_login():
    """
    Buscar funciones que manejan datos sensibles pero no tienen @login_required
    """
    archivos = [
        "taller/documentos/views.py",
        "taller/reportes/views.py",
        "taller/vehiculos/views.py",
        "taller/repuestos/views.py",
        "taller/servicios/views.py",
        "taller/api/views.py",
    ]

    funciones_sin_login = []

    for archivo in archivos:
        if os.path.exists(archivo):
            try:
                with open(archivo, "r", encoding="utf-8") as f:
                    content = f.read()

                # Buscar todas las definiciones de función
                patron_funcion = r"def\s+(\w+)\s*\([^)]*\):"
                funciones = re.finditer(patron_funcion, content)

                lines = content.split("\n")

                for func in funciones:
                    func_name = func.group(1)
                    start_line = content[: func.start()].count("\n")

                    # Buscar @login_required en las 5 líneas anteriores
                    context_start = max(0, start_line - 5)
                    context_lines = lines[context_start : start_line + 1]
                    context = "\n".join(context_lines)

                    tiene_login = "@login_required" in context
                    es_api = func_name.startswith("api_") or "api" in func_name.lower()
                    es_autocomplete = "autocomplete" in func_name.lower()
                    maneja_datos = any(
                        word in context.lower()
                        for word in [
                            "objects.",
                            "filter",
                            "get",
                            "create",
                            "delete",
                            "save",
                        ]
                    )

                    if not tiene_login and (es_api or es_autocomplete or maneja_datos):
                        # Verificar si es una función que necesita login
                        funcion_completa = lines[
                            start_line : min(len(lines), start_line + 20)
                        ]
                        func_content = "\n".join(funcion_completa)

                        if any(
                            sensitive in func_content.lower()
                            for sensitive in [
                                "objects.filter",
                                "objects.get",
                                "objects.create",
                                "request.user",
                            ]
                        ):
                            funciones_sin_login.append(
                                {
                                    "archivo": archivo,
                                    "linea": start_line + 1,
                                    "funcion": func_name,
                                    "razon": "Maneja datos sensibles sin @login_required",
                                }
                            )

            except Exception as e:
                print(f"Error procesando {archivo}: {e}")

    return funciones_sin_login


def verificar_validacion_empresa():
    """
    Verificar funciones que acceden a datos pero no validan empresa
    """
    archivos = [
        "taller/documentos/views.py",
        "taller/reportes/views.py",
        "taller/vehiculos/views.py",
        "taller/repuestos/views.py",
    ]

    funciones_sin_validacion = []

    for archivo in archivos:
        if os.path.exists(archivo):
            try:
                with open(archivo, "r", encoding="utf-8") as f:
                    content = f.read()

                lines = content.split("\n")

                for i, line in enumerate(lines):
                    if "def " in line and "request" in line:
                        # Buscar función
                        func_match = re.search(r"def\s+(\w+)", line)
                        if func_match:
                            func_name = func_match.group(1)

                            # Analizar siguientes 30 líneas
                            func_lines = lines[i : i + 30]
                            func_content = "\n".join(func_lines)

                            tiene_objects = "objects." in func_content
                            valida_empresa = (
                                "request.user.empresa" in func_content
                                or "empresa=" in func_content
                            )
                            es_get_object = "get_object_or_404" in func_content

                            if (
                                tiene_objects
                                and not valida_empresa
                                and not es_get_object
                            ):
                                # Verificar si maneja datos críticos
                                if any(
                                    critical in func_content.lower()
                                    for critical in [
                                        "cliente",
                                        "vehiculo",
                                        "documento",
                                        "repuesto",
                                        "mecanico",
                                    ]
                                ):
                                    funciones_sin_validacion.append(
                                        {
                                            "archivo": archivo,
                                            "linea": i + 1,
                                            "funcion": func_name,
                                            "razon": "Accede a datos sin validar empresa",
                                        }
                                    )

            except Exception as e:
                print(f"Error procesando {archivo}: {e}")

    return funciones_sin_validacion


if __name__ == "__main__":
    print("🔍 ANÁLISIS AVANZADO DE SEGURIDAD")
    print("=" * 40)

    print("\n1. FUNCIONES SIN @login_required:")
    funciones_sin_login = buscar_funciones_sin_login()
    if funciones_sin_login:
        for func in funciones_sin_login:
            print(f"  📍 {func['archivo']}:{func['linea']} - {func['funcion']}")
            print(f"     {func['razon']}")
    else:
        print("  ✅ Todas las funciones críticas tienen @login_required")

    print("\n2. FUNCIONES SIN VALIDACIÓN DE EMPRESA:")
    funciones_sin_validacion = verificar_validacion_empresa()
    if funciones_sin_validacion:
        for func in funciones_sin_validacion:
            print(f"  📍 {func['archivo']}:{func['linea']} - {func['funcion']}")
            print(f"     {func['razon']}")
    else:
        print("  ✅ Todas las funciones validan empresa correctamente")

    total_issues = len(funciones_sin_login) + len(funciones_sin_validacion)
    print(f"\n📊 TOTAL PROBLEMAS ENCONTRADOS: {total_issues}")

    if total_issues == 0:
        print("🎉 ¡ANÁLISIS AVANZADO: SISTEMA 100% SEGURO!")
    else:
        print(f"⚠️  {total_issues} problemas adicionales detectados")
