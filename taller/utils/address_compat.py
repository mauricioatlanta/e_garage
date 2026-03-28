# -*- coding: utf-8 -*-
"""
Utilidades de compatibilidad para Address v2

Permite migración gradual desde campos legacy (direccion, region, ciudad)
hacia el nuevo modelo Address estructurado.

Feature Flag: ConfiguracionEmpresa.use_address_v2

Uso:
    from taller.utils.address_compat import should_use_address_v2, get_company_address

    if should_use_address_v2(empresa):
        address = get_company_address(empresa)
        direccion = address.full_address
    else:
        direccion = empresa.configuracion.direccion  # Legacy
"""
from typing import Optional, Tuple


def should_use_address_v2(empresa) -> bool:
    """
    Determina si una empresa debe usar Address v2 o campos legacy.

    Args:
        empresa: Instancia de Empresa

    Returns:
        bool: True si debe usar Address v2, False para campos legacy

    Ejemplo:
        if should_use_address_v2(request.user.empresa):
            # Usar Address v2
            address = empresa.configuracion.legal_address
        else:
            # Usar campos legacy
            direccion = empresa.configuracion.direccion
    """
    if not empresa:
        return False

    try:
        config = empresa.configuracion if hasattr(empresa, "configuracion") else empresa.config
        return getattr(config, "use_address_v2", False)
    except:
        return False


def get_company_address(empresa) -> Optional["Address"]:
    """
    Obtiene la dirección de una empresa (v2 o None).

    Args:
        empresa: Instancia de Empresa

    Returns:
        Address o None

    Ejemplo:
        address = get_company_address(empresa)
        if address:
            print(address.full_address)
            print(address.sales_tax)
    """
    if not empresa:
        return None

    try:
        config = empresa.configuracion if hasattr(empresa, "configuracion") else empresa.config
        if should_use_address_v2(empresa):
            return config.legal_address
        return None
    except:
        return None


def get_company_address_text(empresa) -> str:
    """
    Obtiene la dirección de una empresa como texto (v2 o legacy).

    Retorna el texto de la dirección, sea desde Address v2 o campo legacy.

    Args:
        empresa: Instancia de Empresa

    Returns:
        str: Dirección como texto

    Ejemplo:
        direccion = get_company_address_text(empresa)
        print(f"Dirección: {direccion}")
    """
    if not empresa:
        return ""

    try:
        config = empresa.configuracion if hasattr(empresa, "configuracion") else empresa.config

        # Intentar Address v2 primero si está activado
        if should_use_address_v2(empresa):
            address = config.legal_address
            if address:
                return address.full_address

        # Fallback a campo legacy
        return config.direccion or ""
    except:
        return ""


def get_cliente_address_text(cliente) -> str:
    """
    Obtiene la dirección de un cliente como texto (v2 o legacy).

    Args:
        cliente: Instancia de Cliente

    Returns:
        str: Dirección como texto

    Ejemplo:
        direccion = get_cliente_address_text(cliente)
    """
    if not cliente:
        return ""

    try:
        # Verificar si la empresa del cliente usa Address v2
        empresa = cliente.empresa
        if should_use_address_v2(empresa):
            address = cliente.billing_address
            if address:
                return address.full_address

        # Fallback a campo legacy
        if hasattr(cliente, "direccion"):
            return cliente.direccion or ""

        return ""
    except:
        return ""


def get_sales_tax_for_cliente(cliente) -> Tuple[float, float]:
    """
    Obtiene sales tax para un cliente (v2 o legacy).

    Args:
        cliente: Instancia de Cliente

    Returns:
        Tuple[float, float]: (state_tax, local_tax)

    Ejemplo:
        state_tax, local_tax = get_sales_tax_for_cliente(cliente)
        total_tax = state_tax + local_tax
    """
    if not cliente:
        return (0.0, 0.0)

    try:
        # Verificar si la empresa del cliente usa Address v2
        empresa = cliente.empresa
        if should_use_address_v2(empresa):
            address = cliente.billing_address
            if address and address.city:
                state_tax = float(address.city.estado.sales_tax or 0)
                local_tax = float(address.city.sales_tax_local or 0)
                return (state_tax, local_tax)

        # Fallback a campos legacy
        # Si tiene ciudad_usa (nuevo modelo unificado pero no Address)
        if hasattr(cliente, "ciudad_usa") and cliente.ciudad_usa:
            ciudad = cliente.ciudad_usa
            state_tax = float(ciudad.estado.sales_tax or 0)
            local_tax = float(ciudad.sales_tax_local or 0)
            return (state_tax, local_tax)

        # Si tiene ciudad legacy (Chile)
        if hasattr(cliente, "ciudad") and cliente.ciudad:
            # TallerCiudad no tiene sales_tax
            return (0.0, 0.0)

        return (0.0, 0.0)
    except:
        return (0.0, 0.0)


def migrate_cliente_to_address_v2(cliente, create_address: bool = True) -> bool:
    """
    Migra un cliente de campos legacy a Address v2.

    Args:
        cliente: Instancia de Cliente
        create_address: Si True, crea Address automáticamente desde campos legacy

    Returns:
        bool: True si se migró exitosamente

    Ejemplo:
        from taller.utils.address_compat import migrate_cliente_to_address_v2

        # Migrar cliente
        if migrate_cliente_to_address_v2(cliente):
            print("Cliente migrado a Address v2")
    """
    if not cliente:
        return False

    try:
        # Si ya tiene billing_address, no hacer nada
        if cliente.billing_address:
            return True

        # Si no se debe crear, retornar False
        if not create_address:
            return False

        # Intentar crear desde ciudad_usa (nuevo modelo unificado)
        if hasattr(cliente, "ciudad_usa") and cliente.ciudad_usa:
            from ubicacion.models import Address

            # Crear Address
            address = Address.objects.create(
                line1=getattr(cliente, "direccion", "") or "N/A",
                line2="",
                city=cliente.ciudad_usa,
                postal_code=getattr(cliente, "zipcode", "") or "",
                company=cliente.empresa,
            )

            # Asignar a cliente
            cliente.billing_address = address
            cliente.save(update_fields=["billing_address"])

            return True

        return False
    except Exception as e:
        print(f"Error migrando cliente a Address v2: {e}")
        return False


def enable_address_v2_for_company(empresa, enable: bool = True) -> bool:
    """
    Activa o desactiva Address v2 para una empresa.

    Args:
        empresa: Instancia de Empresa
        enable: True para activar, False para desactivar

    Returns:
        bool: True si se actualizó exitosamente

    Ejemplo:
        from taller.utils.address_compat import enable_address_v2_for_company

        # Activar Address v2
        enable_address_v2_for_company(empresa, True)
    """
    if not empresa:
        return False

    try:
        config = empresa.configuracion if hasattr(empresa, "configuracion") else empresa.config
        config.use_address_v2 = enable
        config.save(update_fields=["use_address_v2"])
        return True
    except Exception as e:
        print(f"Error actualizando feature flag: {e}")
        return False


# Decorador para views que requieren Address v2
def requires_address_v2(view_func):
    """
    Decorador para views que requieren Address v2 activado.

    Si Address v2 no está activado, muestra un mensaje y redirige.

    Uso:
        from taller.utils.address_compat import requires_address_v2

        @requires_address_v2
        def mi_view(request):
            # Esta view solo funciona con Address v2
            pass
    """
    from functools import wraps
    from django.shortcuts import redirect
    from django.contrib import messages

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not hasattr(request, "user") or not request.user.is_authenticated:
            return redirect("login")

        empresa = getattr(request.user, "empresa", None)
        if not should_use_address_v2(empresa):
            messages.warning(
                request,
                "Esta funcionalidad requiere activar Address v2 en la configuración de la empresa.",
            )
            try:
                return redirect("taller:configuracion")
            except:
                return redirect("/configuracion/")

        return view_func(request, *args, **kwargs)

    return wrapper


# Context processor para templates
def address_v2_context(request):
    """
    Context processor para agregar información de Address v2 a templates.

    Agregar en settings.py:
        TEMPLATES = [{
            'OPTIONS': {
                'context_processors': [
                    ...
                    'taller.utils.address_compat.address_v2_context',
                ],
            },
        }]

    Uso en template:
        {% if use_address_v2 %}
            <!-- Mostrar formulario Address v2 -->
        {% else %}
            <!-- Mostrar formulario legacy -->
        {% endif %}
    """
    use_v2 = False

    if hasattr(request, "user") and request.user.is_authenticated:
        empresa = getattr(request.user, "empresa", None)
        use_v2 = should_use_address_v2(empresa)

    return {
        "use_address_v2": use_v2,
        "address_v2_enabled": use_v2,
    }
