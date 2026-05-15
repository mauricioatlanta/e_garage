from pathlib import Path

p = Path("templates/taller/common/documentos/document_form.html")
txt = p.read_text(encoding="utf-8")

txt = txt.replace("â€”", "—")
txt = txt.replace("Â·", "·")

p.write_text(txt, encoding="utf-8")

print("? encoding corregido")
