#!/usr/bin/env python
"""
Script de verificación de modelos para "Otros Servicios"
"""

import os

import django

# Configurar Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
django.setup()


from taller.servicios.models import Servicio, ServicioName


def verificar_modelo_servicio():
    print("=" * 50)
    print("VERIFICACIÓN MODELO SERVICIO")
    print("=" * 50)

    # 1. Verificar campos del modelo
    print("\n1. CAMPOS DEL MODELO SERVICIO:")
    campos = [field.name for field in Servicio._meta.get_fields()]
    for campo in sorted(campos):
        print(f"   - {campo}")

    # 2. Verificar campos específicos para "Otros Servicios"
    print("\n2. ANÁLISIS CAMPOS REQUERIDOS:")
    campos_encontrados = {
        "tipo": "tipo" in campos,
        "country": "country" in campos,
        "code": "code" in campos,
    }

    for campo, existe in campos_encontrados.items():
        if existe:
            field = Servicio._meta.get_field(campo)
            choices = getattr(field, "choices", None)
            print(f"   ✅ {campo}: {field.__class__.__name__}")
            if choices:
                print(f"      Choices: {choices}")
        else:
            print(f"   ❌ {campo}: NO EXISTE")

    # 3. Verificar instancias existentes
    print(f"\n3. TOTAL SERVICIOS EXISTENTES: {Servicio.objects.count()}")

    if Servicio.objects.exists():
        primer_servicio = Servicio.objects.first()
        print("\nEjemplo de servicio:")
        print(f"   ID: {primer_servicio.id}")
        print(f"   Code: {primer_servicio.code}")
        print(f"   Country: {primer_servicio.country}")
        print(f"   Activo: {primer_servicio.activo}")

        # Verificar si tiene campo tipo
        if hasattr(primer_servicio, "tipo"):
            print(f"   Tipo: {primer_servicio.tipo}")
        else:
            print("   Tipo: ❌ NO DEFINIDO (necesario para interno/externo)")


def verificar_modelo_servicioname():
    print("\n" + "=" * 50)
    print("VERIFICACIÓN MODELO SERVICIONAME (MULTILENGUAJE)")
    print("=" * 50)

    campos = [field.name for field in ServicioName._meta.get_fields()]
    print("\nCampos de ServicioName:")
    for campo in sorted(campos):
        print(f"   - {campo}")

    print(f"\nTotal traducciones: {ServicioName.objects.count()}")

    if ServicioName.objects.exists():
        ejemplo = ServicioName.objects.first()
        print("\nEjemplo de traducción:")
        print(f"   Servicio: {ejemplo.servicio}")
        print(f"   Language: {ejemplo.language}")
        print(f"   Label: {ejemplo.label}")
        if hasattr(ejemplo, "aliases"):
            print(f"   Aliases: {ejemplo.aliases}")


def verificar_modelo_otroservicio():
    print("\n" + "=" * 50)
    print("VERIFICACIÓN MODELO OTROSERVICIODOCUMENTO")
    print("=" * 50)

    campos = [field.name for field in LineaOtroServicio._meta.get_fields()]
    print("\nCampos de OtroServicioDocumento:")
    for campo in sorted(campos):
        print(f"   - {campo}")

    print(f"\nTotal otros servicios: {LineaOtroServicio.objects.count()}")

    if LineaOtroServicio.objects.exists():
        ejemplo = LineaOtroServicio.objects.first()
        print("\nEjemplo de otro servicio:")
        print(f"   Nombre: {ejemplo.nombre}")
        print(f"   Empresa Externa: {ejemplo.empresa_externa}")
        print(f"   Costo: {ejemplo.costo_interno}")
        print(f"   Precio: {ejemplo.precio_cliente}")
        print(f"   Ganancia: {ejemplo.ganancia}")


def verificar_necesidades_implementacion():
    print("\n" + "=" * 60)
    print("ANÁLISIS DE NECESIDADES DE IMPLEMENTACIÓN")
    print("=" * 60)

    # Verificar si Servicio tiene campo tipo
    servicio_tiene_tipo = hasattr(Servicio._meta.get_field("id"), "choices")  # Dummy check
    try:
        Servicio._meta.get_field("tipo")
        servicio_tiene_tipo = True
    except:
        servicio_tiene_tipo = False

    if not servicio_tiene_tipo:
        print("\n❌ FALTA: Campo 'tipo' en modelo Servicio")
        print("   Necesario agregar:")
        print("   tipo = models.CharField(")
        print("       max_length=20,")
        print("       choices=[('interno','Interno'), ('externo','Externo')],")
        print("       default='interno'")
        print("   )")

    # Verificar unique_together
    meta = Servicio._meta
    unique_together = getattr(meta, "unique_together", [])
    print(f"\nUnique together actual: {unique_together}")

    if ("country", "tipo", "code") not in unique_together:
        print("❌ FALTA: unique_together = ('country', 'tipo', 'code')")
    else:
        print("✅ unique_together correcto")


if __name__ == "__main__":
    verificar_modelo_servicio()
    verificar_modelo_servicioname()
    verificar_modelo_otroservicio()
    verificar_necesidades_implementacion()
