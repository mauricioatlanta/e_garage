from pathlib import Path

p = Path("taller/views.py")
lines = p.read_text(encoding="utf-8").splitlines()

lines[117] = '    return render(request, "taller/configuracion.html", context)'
lines[118] = ""
lines[119] = "# View simple para probar el formulario de documento"

lines[151] = '    return render(request, "taller/documentos/create.html")'
lines[152] = ""
lines[153] = "# View simple para probar el formulario de documento"

p.write_text("\n".join(lines) + "\n", encoding="utf-8")
print("REBUILD_FIX_APPLIED")
