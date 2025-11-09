import json, pathlib

files = [
    "fixtures/marcas_modelos.json",
    "fixtures/catalogo_modelos.json",
    "fixtures/ubicacion_cl.json",
    "fixtures/ubicacion_us.json",
]


def smart_read_bytes(p: pathlib.Path) -> str:
    data = p.read_bytes()
    # Prueba varios encodings comunes (UTF-16 causa tu error)
    for enc in ("utf-8", "utf-16", "utf-16-le", "utf-16-be", "latin-1"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    raise UnicodeDecodeError("decode", data, 0, 1, "unknown encoding")


for f in files:
    p = pathlib.Path(f)
    if not p.exists():
        print(f"⚠️  {f} no existe, salto.")
        continue

    try:
        text = smart_read_bytes(p).strip()
    except Exception as e:
        print(f"❌ {f}: no se pudo decodificar ({e}). Se escribirá [] temporal.")
        obj = []
    else:
        if not text:
            print(f"⚠️  {f}: vacío. Se escribirá [] temporal.")
            obj = []
        else:
            try:
                obj = json.loads(text)
            except Exception as e:
                # Intento extra: NDJSON (JSON por línea)
                lines = [ln for ln in text.splitlines() if ln.strip()]
                ok = []
                ndjson_ok = True
                for ln in lines:
                    try:
                        ok.append(json.loads(ln))
                    except Exception:
                        ndjson_ok = False
                        break
                if ndjson_ok and ok:
                    obj = ok
                    print(f"ℹ️  {f}: interpretado como NDJSON ({len(ok)} líneas).")
                else:
                    print(f"❌ {f}: JSON inválido ({e}). Se escribirá [] temporal.")
                    obj = []

    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✅ Normalizado UTF-8 + JSON válido: {f}")
