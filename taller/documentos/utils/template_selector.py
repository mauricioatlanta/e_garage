def template_crear(country: str) -> str:
    c = (country or "CL").upper()
    return (
        "taller/us/en/documentos/crear_documento.html"
        if c == "US"
        else "taller/cl/es/documentos/crear_documento.html"
    )
