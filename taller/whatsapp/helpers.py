"""
Helpers para WhatsApp (click-to-WhatsApp wa.me)
Para uso en templates y vistas
"""
import logging
from urllib.parse import quote
from typing import Optional

logger = logging.getLogger(__name__)


# Longitudes mínimas de teléfono por país (sin código de país)
PHONE_MIN_LENGTHS = {
    "CL": 9,   # Chile: 9 dígitos (ej: 912345678)
    "US": 10,  # USA: 10 dígitos (ej: 1234567890)
    "MX": 10,  # México: 10 dígitos
    "BR": 10,  # Brasil: 10-11 dígitos (celular)
    "PE": 9,   # Perú: 9 dígitos
    "CO": 10,  # Colombia: 10 dígitos
    "EC": 9,   # Ecuador: 9 dígitos
    "VE": 10,  # Venezuela: 10 dígitos
    "AR": 10,  # Argentina: 10 dígitos
    "UY": 8,   # Uruguay: 8 dígitos
}

# Longitudes mínimas con código de país (E.164 sin +)
PHONE_MIN_LENGTHS_WITH_COUNTRY = {
    "CL": 11,  # 56 + 9 dígitos
    "US": 11,  # 1 + 10 dígitos
    "MX": 12,  # 52 + 10 dígitos
    "BR": 12,  # 55 + 10-11 dígitos
    "PE": 11,  # 51 + 9 dígitos
    "CO": 12,  # 57 + 10 dígitos
    "EC": 12,  # 593 + 9 dígitos
    "VE": 12,  # 58 + 10 dígitos
    "AR": 12,  # 54 + 10 dígitos
    "UY": 11,  # 598 + 8 dígitos
}


def validate_phone_by_country(phone: str, country_code: str = "CL") -> bool:
    """
    Valida teléfono por país (longitud mínima/máxima)
    
    Args:
        phone: Número de teléfono (puede venir en cualquier formato)
        country_code: Código de país de 2 letras (ej: "CL", "US", "MX")
        
    Returns:
        True si es válido, False en caso contrario
    """
    if not phone:
        return False
    
    # Normalizar primero
    normalized = normalize_phone(phone, country_code)
    if not normalized:
        return False
    
    # Validar longitud
    return validate_phone_length(normalized, country_code)


def validate_phone_length(phone: str, country_code: str = "CL") -> bool:
    """
    Valida que el teléfono tenga longitud mínima según el país
    
    Args:
        phone: Número de teléfono normalizado (sin +, solo dígitos)
        country_code: Código de país (ej: "CL", "US")
        
    Returns:
        True si cumple longitud mínima, False en caso contrario
    """
    if not phone:
        return False
    
    # Remover caracteres no numéricos
    clean = "".join(filter(str.isdigit, str(phone)))
    
    if not clean:
        return False
    
    # Obtener longitud mínima según país
    min_length = PHONE_MIN_LENGTHS.get(country_code, 9)  # Default 9
    min_length_with_country = PHONE_MIN_LENGTHS_WITH_COUNTRY.get(country_code, 11)  # Default 11
    
    # Verificar si tiene código de país o no
    # Si tiene más de 10 dígitos, probablemente tiene código de país
    if len(clean) >= min_length_with_country:
        return len(clean) >= min_length_with_country
    else:
        return len(clean) >= min_length


def normalize_phone(phone: str, country_code: str = "56") -> str:
    """
    Normalizar número de teléfono a formato E.164 sin + para wa.me
    
    Maneja múltiples formatos:
    - +56912345678
    - 0056912345678 (prefijo 00)
    - 56912345678
    - 912345678 (local sin código)
    - (56) 9 1234 5678 (con espacios/paréntesis)
    
    Args:
        phone: Número de teléfono (puede venir con +, espacios, guiones, paréntesis, 00)
        country_code: Código de país por defecto si no tiene (ej: "56" para Chile)
        
    Returns:
        Número limpio sin + ni espacios (ej: "56912345678")
    """
    if not phone:
        return ""
    
    # Convertir a string y remover espacios
    phone_str = str(phone).strip()
    
    # Remover prefijo 00 (formato internacional alternativo)
    if phone_str.startswith("00"):
        phone_str = phone_str[2:]
    
    # Remover + al inicio
    if phone_str.startswith("+"):
        phone_str = phone_str[1:]
    
    # Remover todos los caracteres no numéricos (espacios, guiones, paréntesis, etc.)
    clean = "".join(filter(str.isdigit, phone_str))
    
    if not clean:
        return ""
    
    # Si ya tiene código de país (más de 10 dígitos o empieza con código conocido), usarlo
    # Códigos de país comunes: 1 (US/CA), 52 (MX), 55 (BR), 56 (CL), 51 (PE), 57 (CO), 58 (VE), 593 (EC), 54 (AR), 598 (UY)
    known_country_codes = ["1", "52", "55", "56", "51", "57", "58", "593", "54", "598"]
    has_country_code = any(clean.startswith(code) for code in known_country_codes)
    
    if has_country_code:
        # Ya tiene código de país, retornar tal cual
        return clean
    
    # Si no tiene código de país, agregarlo según formato local
    # Detectar formato local por longitud y patrón
    if len(clean) == 9 and clean.startswith("9"):
        # Formato chileno: 9 dígitos que empiezan con 9
        clean = country_code + clean
    elif len(clean) >= 8 and len(clean) <= 10:
        # Formato local genérico (8-10 dígitos), agregar código de país
        clean = country_code + clean
    # Si tiene más de 10 dígitos, asumir que ya tiene código de país aunque no lo reconozcamos
    
    return clean


def build_wa_link(phone: str, message: str, country_code: str = "56", validate_length: bool = True) -> Optional[str]:
    """
    Construir link de WhatsApp (wa.me) con mensaje pre-llenado
    
    🔒 VALIDACIÓN: Verifica longitud mínima según país antes de construir el link.
    
    Args:
        phone: Número de teléfono del destinatario
        message: Mensaje a pre-llenar
        country_code: Código de país por defecto (numérico: "56", "1", etc.)
        validate_length: Si True, valida longitud mínima según país
        
    Returns:
        URL de wa.me o None si no hay teléfono o no cumple validación
    """
    if not phone:
        return None
    
    # Normalizar teléfono
    phone_clean = normalize_phone(phone, country_code)
    
    if not phone_clean:
        return None
    
    # 🔒 VALIDACIÓN: Verificar longitud mínima según país
    if validate_length:
        # Mapear código numérico a código de 2 letras para validación
        country_map = {
            "56": "CL", "1": "US", "52": "MX", "55": "BR",
            "51": "PE", "57": "CO", "593": "EC", "58": "VE",
            "54": "AR", "598": "UY"
        }
        country_code_2letter = country_map.get(country_code, "CL")
        
        if not validate_phone_length(phone_clean, country_code_2letter):
            logger.warning(
                f"Teléfono no cumple longitud mínima: {phone} "
                f"(normalizado: {phone_clean}, país: {country_code_2letter})"
            )
            return None
    
    # Codificar mensaje para URL
    message_encoded = quote(message)
    
    # Construir URL
    url = f"https://wa.me/{phone_clean}?text={message_encoded}"
    
    return url


def build_document_wa_message(
    documento,
    cliente_nombre: str,
    tipo_doc: str,
    numero_doc: str,
    total: float,
    empresa_nombre: str,
    url_documento: Optional[str] = None,
    vehiculo_info: Optional[str] = None,
    language: str = "es",
) -> str:
    """
    Construir mensaje de WhatsApp para enviar documento a cliente
    
    Args:
        documento: Instancia de Documento
        cliente_nombre: Nombre del cliente
        tipo_doc: Tipo de documento (ej: "Presupuesto", "Orden de Trabajo")
        numero_doc: Número del documento
        total: Total del documento
        empresa_nombre: Nombre de la empresa/taller
        url_documento: URL del documento o PDF (opcional)
        vehiculo_info: Información del vehículo (opcional)
        language: Idioma del mensaje ("es" o "en")
        
    Returns:
        Mensaje formateado para WhatsApp
    """
    if language == "en":
        message_parts = [
            f"Hello {cliente_nombre}! 👋",
            "",
            f"We're sending you your *{tipo_doc} #{numero_doc}* from *{empresa_nombre}*.",
            "",
            f"💰 Total: *${total:,.2f}*",
        ]
        
        if vehiculo_info:
            message_parts.append(f"🚗 Vehicle: {vehiculo_info}")
            message_parts.append("")
        
        if url_documento:
            message_parts.append("📄 You can review it here:")
            message_parts.append(url_documento)
            message_parts.append("")
        
        message_parts.append("Thank you for trusting us! 🚗✨")
    else:
        # Español (default)
        message_parts = [
            f"¡Hola {cliente_nombre}! 👋",
            "",
            f"Te enviamos tu *{tipo_doc} N°{numero_doc}* de *{empresa_nombre}*.",
            "",
            f"💰 Total: *${total:,.2f}*",
        ]
        
        if vehiculo_info:
            message_parts.append(f"🚗 Vehículo: {vehiculo_info}")
            message_parts.append("")
        
        if url_documento:
            message_parts.append("📄 Puedes revisarlo aquí:")
            message_parts.append(url_documento)
            message_parts.append("")
        
        message_parts.append("¡Gracias por confiar en nosotros! 🚗✨")
    
    return "\n".join(message_parts)
