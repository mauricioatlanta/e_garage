# -*- coding: utf-8 -*-
"""
Validadores y normalizadores para datos sensibles.

Convenciones:
- tax_id es dato sensible (no mostrar en listados)
- Validación específica por tipo (RUT, CPF, CNPJ, RUC, RIF, EIN, SSN)
- Normalización automática (sin puntos, con guion si corresponde)
- Teléfonos con libphonenumber (opcional)
"""

import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def _alias_tax_id_type(tipo: str) -> str:
    """Normaliza los identificadores de tipo de tax ID para reutilizar validadores."""
    if not tipo:
        return ""
    mapping = {
        "CL_RUT": "RUT_CL",
        "US_EIN": "EIN",
        "US_SSN": "SSN",
        "BR_CPF": "CPF",
        "BR_CNPJ": "CNPJ",
        "PE_RUC": "RUC",
        "VE_RIF": "RIF",
        "MX_RFC": "RFC_MX",
        "AR_CUIT": "CUIT",
        "UY_CI": "CI_UY",
    }
    return mapping.get(tipo, tipo)


# ============================================================================
# VALIDADORES DE TAX ID POR PAÍS
# ============================================================================


def normalizar_tax_id(tax_id, tipo):
    """
    Normalizar tax_id según el tipo.

    Reglas:
    - Remover espacios, puntos, comas
    - Convertir a uppercase
    - Agregar guion si corresponde según formato estándar

    Args:
        tax_id (str): Tax ID sin normalizar
        tipo (str): Tipo de tax ID (RUT, CPF, CNPJ, etc.)

    Returns:
        str: Tax ID normalizado

    Ejemplos:
        >>> normalizar_tax_id('12.345.678-9', 'RUT_CL')
        '12345678-9'
        >>> normalizar_tax_id('123.456.789-01', 'CPF')
        '12345678901'
        >>> normalizar_tax_id('12-3456789', 'EIN')
        '12-3456789'
    """
    if not tax_id:
        return ""

    # Limpiar: remover espacios, puntos, comas
    tax_id = str(tax_id).strip().upper()
    tax_id_limpio = re.sub(r"[.\s,]", "", tax_id)

    tipo_normalizado = _alias_tax_id_type(tipo)

    # Normalización específica por tipo
    if tipo_normalizado == "RUT_CL":
        # RUT Chile: 12345678-9 (sin puntos, con guion)
        tax_id_limpio = re.sub(r"[-]", "", tax_id_limpio)  # Remover guiones existentes
        if len(tax_id_limpio) >= 2:
            # Agregar guion antes del dígito verificador
            tax_id_limpio = f"{tax_id_limpio[:-1]}-{tax_id_limpio[-1]}"

    elif tipo_normalizado == "EIN":
        # EIN USA: 12-3456789 (formato XX-XXXXXXX)
        tax_id_limpio = re.sub(r"[-]", "", tax_id_limpio)
        if len(tax_id_limpio) == 9:
            tax_id_limpio = f"{tax_id_limpio[:2]}-{tax_id_limpio[2:]}"

    elif tipo_normalizado == "SSN":
        # SSN USA: 123-45-6789 (formato XXX-XX-XXXX)
        tax_id_limpio = re.sub(r"[-]", "", tax_id_limpio)
        if len(tax_id_limpio) == 9:
            tax_id_limpio = f"{tax_id_limpio[:3]}-{tax_id_limpio[3:5]}-{tax_id_limpio[5:]}"

    elif tipo_normalizado == "CUIT":
        # CUIT Argentina: XX-XXXXXXXX-X (formato con guiones)
        tax_id_limpio = re.sub(r"[-]", "", tax_id_limpio)
        if len(tax_id_limpio) == 11:
            tax_id_limpio = f"{tax_id_limpio[:2]}-{tax_id_limpio[2:10]}-{tax_id_limpio[10]}"

    elif tipo_normalizado == "CI_UY":
        # CI Uruguay: X.XXX.XXX-X (formato con puntos y guion)
        # La CI uruguaya puede tener 7 u 8 dígitos
        # Normalizar: remover puntos y guiones, luego formatear
        tax_id_limpio = re.sub(r"[.\s-]", "", tax_id_limpio)
        # Formatear: X.XXX.XXX-X (7 dígitos) o XX.XXX.XXX-X (8 dígitos)
        if len(tax_id_limpio) == 7:
            # 7 dígitos: X.XXX.XXX-X
            tax_id_limpio = (
                f"{tax_id_limpio[0]}.{tax_id_limpio[1:4]}.{tax_id_limpio[4:7]}-{tax_id_limpio[6]}"
            )
        elif len(tax_id_limpio) == 8:
            # 8 dígitos: XX.XXX.XXX-X
            tax_id_limpio = (
                f"{tax_id_limpio[0:2]}.{tax_id_limpio[2:5]}.{tax_id_limpio[5:8]}-{tax_id_limpio[7]}"
            )

    # CPF, CNPJ, RUC, RIF: Solo dígitos (sin guiones)
    # Ya están limpios

    return tax_id_limpio


def validar_rut_chile(rut):
    """
    Validar RUT chileno con dígito verificador.

    Formato esperado: 12345678-9 o 123456789

    Args:
        rut (str): RUT a validar

    Raises:
        ValidationError: Si el RUT es inválido

    Ejemplos:
        >>> validar_rut_chile('12345678-5')  # Válido
        >>> validar_rut_chile('12345678-0')  # Inválido (dígito verificador incorrecto)
    """
    if not rut:
        return

    # Normalizar
    rut = normalizar_tax_id(rut, "RUT_CL")

    # Separar número y dígito verificador
    match = re.match(r"^(\d+)-([0-9K])$", rut)
    if not match:
        raise ValidationError(_("RUT debe tener formato: 12345678-9"))

    numero = match.group(1)
    dv = match.group(2)

    # Calcular dígito verificador
    suma = 0
    multiplo = 2

    for digit in reversed(numero):
        suma += int(digit) * multiplo
        multiplo += 1
        if multiplo == 8:
            multiplo = 2

    resto = suma % 11
    dv_calculado = 11 - resto

    if dv_calculado == 11:
        dv_esperado = "0"
    elif dv_calculado == 10:
        dv_esperado = "K"
    else:
        dv_esperado = str(dv_calculado)

    if dv != dv_esperado:
        raise ValidationError(
            _(f"RUT inválido. Dígito verificador incorrecto. Esperado: {dv_esperado}")
        )


def validar_cpf_brasil(cpf):
    """
    Validar CPF brasileño (11 dígitos).

    Formato esperado: 12345678901 (solo dígitos)

    Args:
        cpf (str): CPF a validar

    Raises:
        ValidationError: Si el CPF es inválido
    """
    if not cpf:
        return

    # Normalizar (solo dígitos)
    cpf = re.sub(r"\D", "", str(cpf))

    if len(cpf) != 11:
        raise ValidationError(_("CPF debe tener 11 dígitos"))

    # Verificar CPFs inválidos conocidos (todos iguales)
    if cpf == cpf[0] * 11:
        raise ValidationError(_("CPF inválido"))

    # Calcular dígitos verificadores
    def calcular_dv(digitos):
        soma = sum((i + 1) * int(d) for i, d in enumerate(reversed(digitos)))
        resto = soma % 11
        return 0 if resto < 2 else 11 - resto

    dv1 = calcular_dv(cpf[:9])
    dv2 = calcular_dv(cpf[:10])

    if cpf[-2:] != f"{dv1}{dv2}":
        raise ValidationError(_("CPF inválido. Dígitos verificadores incorrectos."))


def validar_cnpj_brasil(cnpj):
    """
    Validar CNPJ brasileño (14 dígitos).

    Formato esperado: 12345678901234 (solo dígitos)

    Args:
        cnpj (str): CNPJ a validar

    Raises:
        ValidationError: Si el CNPJ es inválido
    """
    if not cnpj:
        return

    # Normalizar (solo dígitos)
    cnpj = re.sub(r"\D", "", str(cnpj))

    if len(cnpj) != 14:
        raise ValidationError(_("CNPJ debe tener 14 dígitos"))

    # Verificar CNPJs inválidos conocidos
    if cnpj == cnpj[0] * 14:
        raise ValidationError(_("CNPJ inválido"))

    # Calcular dígitos verificadores
    def calcular_dv(digitos, pesos):
        soma = sum(int(d) * p for d, p in zip(digitos, pesos))
        resto = soma % 11
        return 0 if resto < 2 else 11 - resto

    pesos1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    pesos2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]

    dv1 = calcular_dv(cnpj[:12], pesos1)
    dv2 = calcular_dv(cnpj[:13], pesos2)

    if cnpj[-2:] != f"{dv1}{dv2}":
        raise ValidationError(_("CNPJ inválido. Dígitos verificadores incorrectos."))


def validar_ruc_peru(ruc):
    """
    Validar RUC peruano (11 dígitos).

    Formato esperado: 20123456789 (solo dígitos)

    Args:
        ruc (str): RUC a validar

    Raises:
        ValidationError: Si el RUC es inválido
    """
    if not ruc:
        return

    # Normalizar (solo dígitos)
    ruc = re.sub(r"\D", "", str(ruc))

    if len(ruc) != 11:
        raise ValidationError(_("RUC debe tener 11 dígitos"))

    # Verificar que empiece con 10, 15, 16, 17, o 20
    prefijo = ruc[:2]
    if prefijo not in ["10", "15", "16", "17", "20"]:
        raise ValidationError(_("RUC debe empezar con 10, 15, 16, 17, o 20"))

    # Validación básica (RUC tiene algoritmo de dígito verificador complejo)
    # Por ahora solo verificar longitud y prefijo
    # TODO: Implementar validación completa si es crítico


def validar_rif_venezuela(rif):
    """
    Validar RIF venezolano.

    Formato esperado: J123456789 (letra + 9 dígitos)

    Args:
        rif (str): RIF a validar

    Raises:
        ValidationError: Si el RIF es inválido
    """
    if not rif:
        return

    # Normalizar
    rif = str(rif).strip().upper()
    rif = re.sub(r"[-\s]", "", rif)

    # Formato: 1 letra + 9 dígitos
    if not re.match(r"^[VEJPGC]\d{9}$", rif):
        raise ValidationError(
            _("RIF debe tener formato: J123456789 (letra V/E/J/P/G/C + 9 dígitos)")
        )


def validar_rfc_mexico(rfc):
    """
    Validar RFC mexicano.

    Formato:
      - Personas físicas: 4 letras + 6 dígitos (fecha) + 3 alfanuméricos
      - Personas morales: 3 letras + 6 dígitos + 3 alfanuméricos
    """
    if not rfc:
        return

    rfc = str(rfc).strip().upper()
    rfc = re.sub(r"[-\s]", "", rfc)

    if not re.match(r"^[A-ZÑ&]{3,4}\d{6}[A-Z0-9]{3}$", rfc):
        raise ValidationError(_("RFC debe tener formato válido: AAAAYYMMDDXXX o AAAYYMMDDXXX"))


def validar_cuit_argentina(cuit):
    """
    Validar CUIT argentino (Clave Única de Identificación Tributaria).

    Formato esperado: XX-XXXXXXXX-X (11 dígitos con guiones)
    Los primeros 2 dígitos indican el tipo de contribuyente:
    - 20: Persona física
    - 27: Persona física (monotributo)
    - 30: Empresa
    - 33: Empresa (IVA exento)
    - 34: Empresa (IVA no responsable)

    Args:
        cuit (str): CUIT a validar

    Raises:
        ValidationError: Si el CUIT es inválido
    """
    if not cuit:
        return

    # Normalizar
    cuit_limpio = re.sub(r"[^0-9]", "", str(cuit))

    if len(cuit_limpio) != 11:
        raise ValidationError(_("CUIT debe tener 11 dígitos"))

    # Verificar que los primeros 2 dígitos sean válidos
    tipo_contribuyente = int(cuit_limpio[:2])
    tipos_validos = [20, 23, 24, 27, 30, 33, 34]

    if tipo_contribuyente not in tipos_validos:
        raise ValidationError(
            _(
                "CUIT con tipo de contribuyente inválido. Debe empezar con 20, 23, 24, 27, 30, 33 o 34"
            )
        )

    # Calcular dígito verificador
    multiplicadores = [5, 4, 3, 2, 7, 6, 5, 4, 3, 2]
    suma = sum(int(cuit_limpio[i]) * multiplicadores[i] for i in range(10))
    resto = suma % 11

    if resto < 2:
        dv_esperado = resto
    else:
        dv_esperado = 11 - resto

    dv_ingresado = int(cuit_limpio[10])

    if dv_ingresado != dv_esperado:
        raise ValidationError(
            _(f"CUIT inválido. Dígito verificador incorrecto. Esperado: {dv_esperado}")
        )


def validar_ci_uruguay(ci):
    """
    Validar CI uruguayo (Cédula de Identidad).

    Formato esperado: X.XXX.XXX-X o XX.XXX.XXX-X (7-8 dígitos con puntos y guion)
    La CI puede tener 7 u 8 dígitos.

    Args:
        ci (str): CI a validar

    Raises:
        ValidationError: Si la CI es inválida
    """
    if not ci:
        return

    # Normalizar (remover puntos, guiones y espacios)
    ci_limpio = re.sub(r"[.\s-]", "", str(ci))

    if len(ci_limpio) < 7 or len(ci_limpio) > 8:
        raise ValidationError(_("CI debe tener entre 7 y 8 dígitos"))

    # Validación básica: solo dígitos
    if not ci_limpio.isdigit():
        raise ValidationError(_("CI debe contener solo dígitos"))

    # Nota: La CI uruguaya no tiene un algoritmo de dígito verificador estándar
    # como el RUT chileno o el CUIT argentino. Se valida solo el formato y longitud.


def validar_ein_usa(ein):
    """
    Validar EIN estadounidense (Employer Identification Number).

    Formato esperado: 12-3456789

    Args:
        ein (str): EIN a validar

    Raises:
        ValidationError: Si el EIN es inválido
    """
    if not ein:
        return

    # Normalizar
    ein_limpio = re.sub(r"[^0-9]", "", str(ein))

    if len(ein_limpio) != 9:
        raise ValidationError(_("EIN debe tener 9 dígitos"))

    # Verificar formato válido (primeros 2 dígitos no pueden ser 00, 07, 08, 09, etc.)
    prefijo = int(ein_limpio[:2])

    if prefijo in [0, 7, 8, 9, 17, 18, 19, 28, 29, 49, 69, 70, 78, 79, 89]:
        raise ValidationError(_("EIN con prefijo inválido"))


def validar_ssn_usa(ssn):
    """
    Validar SSN estadounidense (Social Security Number).

    Formato esperado: 123-45-6789

    Args:
        ssn (str): SSN a validar

    Raises:
        ValidationError: Si el SSN es inválido
    """
    if not ssn:
        return

    # Normalizar
    ssn_limpio = re.sub(r"[^0-9]", "", str(ssn))

    if len(ssn_limpio) != 9:
        raise ValidationError(_("SSN debe tener 9 dígitos"))

    # Verificar que no sea todo ceros o secuencias inválidas
    if ssn_limpio in [
        "000000000",
        "111111111",
        "222222222",
        "333333333",
        "444444444",
        "555555555",
        "666666666",
        "777777777",
        "888888888",
        "999999999",
    ]:
        raise ValidationError(_("SSN inválido"))

    # Primeros 3 dígitos no pueden ser 000, 666, o 900-999
    area = int(ssn_limpio[:3])
    if area == 0 or area == 666 or area >= 900:
        raise ValidationError(_("SSN con área inválida"))


# ============================================================================
# VALIDADOR GENÉRICO POR TIPO
# ============================================================================


def validar_tax_id(tax_id, tax_id_type):
    """
    Validar y normalizar tax_id según el tipo.

    Args:
        tax_id (str): Tax ID a validar
        tax_id_type (str): Tipo (RUT_CL, CPF, CNPJ, RUC, RIF, EIN, SSN)

    Returns:
        str: Tax ID normalizado

    Raises:
        ValidationError: Si el tax_id es inválido

    Ejemplos:
        >>> validar_tax_id('12.345.678-9', 'RUT_CL')
        '12345678-9'
        >>> validar_tax_id('123.456.789-01', 'CPF')
        '12345678901'
    """
    if not tax_id:
        return ""

    # Normalizar primero
    tipo = _alias_tax_id_type(tax_id_type)
    tax_id_normalizado = normalizar_tax_id(tax_id, tipo)

    # Validar según tipo
    if tipo == "RUT_CL":
        validar_rut_chile(tax_id_normalizado)
    elif tipo == "CPF":
        validar_cpf_brasil(tax_id_normalizado)
    elif tipo == "CNPJ":
        validar_cnpj_brasil(tax_id_normalizado)
    elif tipo == "RUC":
        validar_ruc_peru(tax_id_normalizado)
    elif tipo == "RIF":
        validar_rif_venezuela(tax_id_normalizado)
    elif tipo == "EIN":
        validar_ein_usa(tax_id_normalizado)
    elif tipo == "SSN":
        validar_ssn_usa(tax_id_normalizado)
    elif tipo == "RFC_MX":
        validar_rfc_mexico(tax_id_normalizado)
    elif tipo == "CUIT":
        validar_cuit_argentina(tax_id_normalizado)
    elif tipo == "CI_UY":
        validar_ci_uruguay(tax_id_normalizado)

    return tax_id_normalizado


# ============================================================================
# ENMASCARAR DATOS SENSIBLES
# ============================================================================


def enmascarar_tax_id(tax_id, tax_id_type=None):
    """
    Enmascarar tax_id para mostrar en listados (dato sensible).

    Args:
        tax_id (str): Tax ID completo
        tax_id_type (str, optional): Tipo de tax ID

    Returns:
        str: Tax ID enmascarado

    Ejemplos:
        >>> enmascarar_tax_id('12345678-9', 'RUT_CL')
        '****5678-9'
        >>> enmascarar_tax_id('12345678901', 'CPF')
        '*******8901'
        >>> enmascarar_tax_id('12-3456789', 'EIN')
        '**-***6789'

    IMPORTANTE:
        Usar en listados, NO en formularios de edición.
        En formularios, mostrar completo para editar.
    """
    if not tax_id:
        return ""

    tax_id = str(tax_id)

    # Mostrar solo últimos 4 caracteres (o últimos dígitos si tiene guion)
    if "-" in tax_id:
        partes = tax_id.split("-")
        if len(partes) == 2:
            # Formato con guion (RUT, EIN, SSN)
            primera = "*" * len(partes[0])
            segunda = partes[1]
            return f"{primera}-{segunda}"
        elif len(partes) == 3:
            # SSN: 123-45-6789 → ***-**-6789
            return f"***-**-{partes[2]}"

    # Sin guion: mostrar últimos 4 dígitos
    if len(tax_id) > 4:
        return "*" * (len(tax_id) - 4) + tax_id[-4:]
    else:
        return tax_id


def enmascarar_email(email):
    """
    Enmascarar email para mostrar en listados.

    Args:
        email (str): Email completo

    Returns:
        str: Email enmascarado

    Ejemplos:
        >>> enmascarar_email('juan.perez@example.com')
        'ju***@example.com'
        >>> enmascarar_email('a@b.com')
        'a@b.com'
    """
    if not email or "@" not in email:
        return email

    local, domain = email.split("@", 1)

    if len(local) <= 2:
        return email

    # Mostrar primeros 2 caracteres + *** + @domain
    return f"{local[:2]}***@{domain}"


# ============================================================================
# VALIDACIÓN DE TELÉFONOS (OPCIONAL - REQUIERE libphonenumber)
# ============================================================================


def validar_telefono(telefono, pais_code="CL"):
    """
    Validar y formatear teléfono usando libphonenumber.

    OPCIONAL: Requiere instalar phonenumbers
    pip install phonenumbers

    Args:
        telefono (str): Teléfono a validar
        pais_code (str): Código de país ISO 3166-1 alpha-2

    Returns:
        str: Teléfono en formato E164 (+56912345678)

    Raises:
        ValidationError: Si el teléfono es inválido

    Ejemplos:
        >>> validar_telefono('+56912345678', 'CL')
        '+56912345678'
        >>> validar_telefono('912345678', 'CL')
        '+56912345678'
        >>> validar_telefono('(555) 123-4567', 'US')
        '+15551234567'
    """
    if not telefono:
        return ""

    try:
        import phonenumbers
        from phonenumbers import NumberParseException
    except ImportError:
        # Si no está instalado, solo validar formato básico
        telefono_limpio = re.sub(r"[^0-9+]", "", str(telefono))
        if len(telefono_limpio) < 8:
            raise ValidationError(_("Teléfono debe tener al menos 8 dígitos"))
        return telefono_limpio

    try:
        # Parsear teléfono
        parsed = phonenumbers.parse(telefono, pais_code)

        # Validar
        if not phonenumbers.is_valid_number(parsed):
            raise ValidationError(_("Número de teléfono inválido"))

        # Formatear a E164 (+56912345678)
        return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)

    except NumberParseException as e:
        raise ValidationError(_(f"Error al parsear teléfono: {e}"))


def formatear_telefono_nacional(telefono, pais_code="CL"):
    """
    Formatear teléfono para mostrar en formato nacional.

    Args:
        telefono (str): Teléfono en formato E164
        pais_code (str): Código de país

    Returns:
        str: Teléfono en formato nacional

    Ejemplos:
        >>> formatear_telefono_nacional('+56912345678', 'CL')
        '9 1234 5678'
        >>> formatear_telefono_nacional('+15551234567', 'US')
        '(555) 123-4567'
    """
    if not telefono:
        return ""

    try:
        import phonenumbers
    except ImportError:
        return telefono

    try:
        parsed = phonenumbers.parse(telefono, pais_code)
        return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.NATIONAL)
    except:
        return telefono


# ============================================================================
# HELPER: DATOS SENSIBLES
# ============================================================================

CAMPOS_SENSIBLES = [
    "tax_id",
    "rut",
    "cpf",
    "cnpj",
    "ruc",
    "rif",
    "ein",
    "ssn",
    "password",
    "card_number",
    "cvv",
    "account_number",
]


def es_campo_sensible(nombre_campo):
    """
    Verificar si un campo es sensible (no mostrar en listados).

    Args:
        nombre_campo (str): Nombre del campo

    Returns:
        bool: True si es sensible

    Ejemplos:
        >>> es_campo_sensible('tax_id')
        True
        >>> es_campo_sensible('nombre')
        False
    """
    nombre_lower = nombre_campo.lower()
    return any(sensible in nombre_lower for sensible in CAMPOS_SENSIBLES)
