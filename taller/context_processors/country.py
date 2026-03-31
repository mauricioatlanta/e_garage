<<<<<<< HEAD
def country_context(request):
    return {
        "country_code": getattr(request, "country_code", None),
        "lang_code": getattr(request, "lang_code", None),
=======
﻿def country_context(request):
    return {
        "country_code": getattr(request, "country_code", "cl"),
        "lang_code": getattr(request, "lang_code", "es"),
>>>>>>> 0fe6b08f (Fix: Sincronización total de archivos, context processors y limpieza Black)
    }
