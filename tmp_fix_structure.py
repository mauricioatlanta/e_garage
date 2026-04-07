from pathlib import Path

p = Path("taller/views.py")
lines = p.read_text(encoding="utf-8").splitlines()

new_lines = []
inside_bad_block = False

for i, line in enumerate(lines):
    # Detectar bloque corrupto después del render
    if 'return render(request, "taller/configuracion.html", context)' in line:
        new_lines.append(line)
        new_lines.append("")  # línea en blanco
        continue

    # Eliminar bloque corrupto que quedó dentro
    if 'if request.method == "POST":' in line and i < 160:
        continue
    if "DATOS RECIBIDOS EN POST" in line:
        continue
    if "repuestos_json" in line and i < 160:
        continue

    new_lines.append(line)

p.write_text("\n".join(new_lines) + "\n", encoding="utf-8")

print("STRUCTURE_FIX_APPLIED")
