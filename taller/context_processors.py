def empresa_context(request):
    empresa = getattr(request, "empresa", None)
    cfg = None
    if empresa and hasattr(empresa, "configuracionempresa"):
        cfg = empresa.configuracionempresa
    return {"empresa_cfg": cfg}
