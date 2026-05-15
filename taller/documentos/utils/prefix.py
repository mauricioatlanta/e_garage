def doc_prefix(tipo: str) -> str:
    """
    Prefijo de numeración por tipo de documento.
    Incluye REC (Recibo/Boleta).
    """
    return {
        "OT": "OT",
        "FAC": "F",
        "PRES": "P",
        "REC": "R",
    }.get((tipo or "").upper(), "D")
