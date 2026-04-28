from pathlib import Path

files = [
    Path("templates/taller/cl/es/documentos/document_form.html"),
    Path("templates/taller/common/documentos/document_form.html"),
]

for p in files:
    data = p.read_bytes()

    if data.startswith(b"\xff\xfe") or data.startswith(b"\xfe\xff"):
        text = data.decode("utf-16")
    else:
        text = data.decode("cp1252")

    p.write_text(text, encoding="utf-8", newline="\n")
    print("FIXED_UTF8:", p)

for p in files:
    p.read_text(encoding="utf-8")
    print("UTF8_OK:", p)
