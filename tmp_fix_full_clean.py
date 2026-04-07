from pathlib import Path

p = Path("taller/views.py")
s = p.read_text(encoding="utf-8")

# 1. Cortar todo lo que está después del render de configuracion
cut_marker = 'return render(request, "taller/configuracion.html", context)'
before, _, after = s.partition(cut_marker)

clean = before + cut_marker + "\n\n"

# 2. Recrear view limpia correctamente
clean += '''
def crear_documento_test(request):
    """View simple para probar el formulario de creación de documentos"""
    from django.http import JsonResponse

    if request.method == "POST":
        print("=== DATOS RECIBIDOS EN POST ===")
        print("POST data:", dict(request.POST))

        repuestos_json = request.POST.get("repuestos_json", "[]")
        servicios_json = request.POST.get("servicios_json", "[]")

        print("\\n=== REPUESTOS JSON ===")
        print(repuestos_json)

        print("\\n=== SERVICIOS JSON ===")
        print(servicios_json)

        return JsonResponse({
            "status": "success",
            "message": "Datos recibidos correctamente",
            "repuestos": repuestos_json,
            "servicios": servicios_json
        })

    return render(request, "taller/documentos/create.html")
'''

p.write_text(clean, encoding="utf-8")

print("FULL_CLEAN_REBUILD_DONE")
