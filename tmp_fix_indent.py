from pathlib import Path

p = Path("taller/views.py")
lines = p.read_text(encoding="utf-8").splitlines()

fixed = []

for line in lines:
    # FIX: eliminar indentación extra en bloque POST
    if line.strip().startswith('if "datos_form" in request.POST:'):
        fixed.append('    if "datos_form" in request.POST:')
        continue
    if line.strip().startswith('elif "empresa_form" in request.POST:'):
        fixed.append('    elif "empresa_form" in request.POST:')
        continue
    if line.strip().startswith('elif "crear_tecnico_rapido" in request.POST'):
        fixed.append('    elif "crear_tecnico_rapido" in request.POST and Tecnico and empresa:')
        continue
    if line.strip().startswith('elif "toggle_tecnico" in request.POST'):
        fixed.append('    elif "toggle_tecnico" in request.POST and Tecnico and empresa:')
        continue

    fixed.append(line)

p.write_text("\n".join(fixed) + "\n", encoding="utf-8")

print("INDENT_FIX_APPLIED")
