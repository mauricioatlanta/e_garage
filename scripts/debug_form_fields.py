#!/usr/bin/env python
"""
Script para debuggear los campos del formulario de vehículos
"""

import os

import django

# Configurar Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
django.setup()

from django.contrib.auth import get_user_model

from taller.vehiculos.forms import VehiculoForm

User = get_user_model()


def debug_form_fields():
    """Debuggear los campos del formulario"""

    print("🔍 DEBUGGEANDO CAMPOS DEL FORMULARIO")
    print("=" * 50)

    # Buscar usuario testuser_usa
    try:
        user = User.objects.get(username="testuser_usa")
        print(f"✅ Usuario encontrado: {user.username}")
        print(f"✅ Empresa: {user.empresa.nombre_taller}")
        print(f"✅ País: {user.empresa.pais}")

        # Crear formulario
        form = VehiculoForm(user=user)
        print("✅ Formulario creado")

        # Mostrar todos los campos del formulario
        print("\n📋 CAMPOS DEL FORMULARIO:")
        print("-" * 30)

        for field_name, field in form.fields.items():
            print(f"🔹 {field_name}:")
            print(f"   - Tipo: {type(field).__name__}")
            print(f"   - Label: {field.label}")
            print(f"   - Required: {field.required}")

            # Manejar choices de manera segura
            if hasattr(field, "choices"):
                try:
                    choices_list = list(field.choices)
                    print(f"   - Choices: {len(choices_list)}")

                    # Mostrar las primeras 5 opciones
                    if choices_list:
                        print("   - Primeras opciones:")
                        for i, (value, label) in enumerate(choices_list[:5]):
                            print(f"     {i+1}. {value} -> {label}")
                        if len(choices_list) > 5:
                            print(f"     ... y {len(choices_list) - 5} más")
                except Exception as e:
                    print(f"   - Choices: Error al procesar - {e}")
            else:
                print("   - Choices: N/A")
            print()

        # Verificar campos específicos
        campos_usa = ["marca_texto", "modelo_texto"]
        campos_chile = ["marca", "modelo"]

        print("🔍 VERIFICACIÓN DE CAMPOS:")
        print("-" * 30)

        for campo in campos_usa:
            if campo in form.fields:
                print(f"✅ {campo} encontrado")
            else:
                print(f"❌ {campo} NO encontrado")

        for campo in campos_chile:
            if campo in form.fields:
                print(f"✅ {campo} encontrado")
            else:
                print(f"❌ {campo} NO encontrado")

        # Verificar si hay campos duplicados
        print("\n🔍 VERIFICACIÓN DE DUPLICADOS:")
        print("-" * 30)

        if "marca" in form.fields and "marca_texto" in form.fields:
            print("⚠️  AMBOS campos marca están presentes (puede causar confusión)")
        elif "marca" in form.fields:
            print("🇨🇱 Solo campo marca (Chile)")
        elif "marca_texto" in form.fields:
            print("🇺🇸 Solo campo marca_texto (USA)")
        else:
            print("❌ No hay campos de marca")

    except User.DoesNotExist:
        print("❌ Usuario testuser_usa no encontrado")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()

    print("\n" + "=" * 50)
    print("🏁 DEBUG COMPLETADO")


if __name__ == "__main__":
    debug_form_fields()
