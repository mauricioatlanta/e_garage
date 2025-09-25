#!/usr/bin/env python3
# split_zip.py
# Crea múltiples ZIPs ("partes") de una carpeta grande, manteniendo rutas relativas.
# Genera manifest.json y checksums SHA256 de cada ZIP.
#
# Uso:
#   python split_zip.py <carpeta_origen> --out <carpeta_salida> --part-mb 90 --exclude ".git" "__pycache__"

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def human(n: int) -> str:
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if n < 1024 or unit == "TB":
            return f"{n:.2f} {unit}" if unit != "B" else f"{n} {unit}"
        n /= 1024


def should_exclude(path: Path, exclude_terms) -> bool:
    p_str = str(path).replace("\\", "/").lower()
    for term in exclude_terms:
        t = term.lower()
        if t in p_str.split("/"):  # excluye si coincide como segmento (carpeta/archivo)
            return True
        if p_str.endswith(t):  # o si termina con el patrón
            return True
    return False


def collect_files(root: Path, exclude_terms):
    files = []
    for dirpath, dirnames, filenames in os.walk(root):
        dpath = Path(dirpath)
        # Filtra dirnames in-place para acelerar (no descender en dirs excluidas)
        dirnames[:] = [
            d for d in dirnames if not should_exclude(dpath / d, exclude_terms)
        ]
        for fn in filenames:
            fpath = dpath / fn
            if should_exclude(fpath, exclude_terms):
                continue
            try:
                if fpath.is_symlink():
                    continue
                size = fpath.stat().st_size
            except (FileNotFoundError, PermissionError):
                continue
            rel = fpath.relative_to(root)
            files.append((fpath, rel, size))
    return files


def plan_parts(files, part_bytes: int):
    """
    Agrupa archivos en partes intentando no pasar de part_bytes (usando tamaño sin comprimir).
    Si un archivo > part_bytes, lo deja solo en una parte.
    """
    parts = []
    current = []
    current_size = 0

    for fpath, rel, size in files:
        if size > part_bytes:
            # cierra parte actual si tiene algo
            if current:
                parts.append(current)
                current = []
                current_size = 0
            # parte “gigante” con un solo archivo
            parts.append([(fpath, rel, size)])
            continue

        if current_size + size > part_bytes and current:
            parts.append(current)
            current = [(fpath, rel, size)]
            current_size = size
        else:
            current.append((fpath, rel, size))
            current_size += size

    if current:
        parts.append(current)
    return parts


def main():
    ap = argparse.ArgumentParser(
        description="Divide una carpeta en varios ZIPs con límite de tamaño."
    )
    ap.add_argument("source", help="Carpeta origen (proyecto grande)")
    ap.add_argument(
        "--out", default="export_parts", help="Carpeta de salida para los ZIPs"
    )
    ap.add_argument(
        "--part-mb", type=int, default=90, help="Tamaño objetivo por ZIP (MB)"
    )
    ap.add_argument(
        "--prefix", default="eg_app_part_", help="Prefijo del nombre de las partes"
    )
    ap.add_argument(
        "--exclude",
        nargs="*",
        default=[".git", "__pycache__", "node_modules", "venv"],
        help="Patrones/carpetas a excluir (segmentos)",
    )
    args = ap.parse_args()

    root = Path(args.source).resolve()
    outdir = Path(args.out).resolve()
    outdir.mkdir(parents=True, exist_ok=True)

    if not root.exists() or not root.is_dir():
        print(
            f"ERROR: Carpeta origen no existe o no es carpeta: {root}", file=sys.stderr
        )
        sys.exit(1)

    part_bytes_target = args.part_mb * 1024 * 1024

    print(f"📦 Origen: {root}")
    print(f"📤 Salida: {outdir}")
    print(f"🎯 Límite por ZIP: {args.part_mb} MB (~{human(part_bytes_target)})")
    print(f"🚫 Exclusiones: {args.exclude}")
    print("🔎 Recolectando archivos...")

    files = collect_files(root, args.exclude)
    total_size = sum(sz for _, _, sz in files)
    print(
        f"✅ Archivos: {len(files)} | Tamaño total (sin comprimir): {human(total_size)}"
    )

    if not files:
        print("No se encontraron archivos para empaquetar (verifica exclusiones).")
        sys.exit(0)

    print("🧠 Planificando partes...")
    parts = plan_parts(files, part_bytes_target)
    print(f"📚 Partes planificadas: {len(parts)}")

    manifest = {
        "created_at": datetime.utcnow().isoformat() + "Z",
        "source": str(root),
        "output_dir": str(outdir),
        "part_mb_target": args.part_mb,
        "prefix": args.prefix,
        "exclude": args.exclude,
        "total_files": len(files),
        "total_size_uncompressed": total_size,
        "parts": [],
    }

    ndigits = max(3, len(str(len(parts))))
    warnings = []
    for idx, group in enumerate(parts, start=1):
        part_name = f"{args.prefix}{str(idx).zfill(ndigits)}.zip"
        part_path = outdir / part_name
        part_size_uncompressed = sum(sz for _, _, sz in group)

        print(
            f"➡️  Creando {part_name} con {len(group)} archivos ({human(part_size_uncompressed)}) …"
        )
        with ZipFile(part_path, "w", compression=ZIP_DEFLATED) as zf:
            for fpath, rel, _sz in group:
                zf.write(fpath, arcname=str(rel))

        digest = sha256_file(part_path)
        written = part_path.stat().st_size
        print(f"   ✔️ Escrito: {human(written)} | SHA256: {digest[:16]}…")

        # Advertir si alguna parte quedó muy grande
        if written > (args.part_mb + 5) * 1024 * 1024:
            warnings.append(
                f"⚠️  {part_name} supera {args.part_mb+5} MB ({human(written)}). "
                f"Considera bajar --part-mb o excluir archivos pesados."
            )

        manifest["parts"].append(
            {
                "index": idx,
                "zip": part_name,
                "files": [str(rel) for _f, rel, _s in group],
                "size_uncompressed": part_size_uncompressed,
                "size_zip_bytes": written,
                "sha256": digest,
            }
        )

    manifest_path = outdir / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"📝 Manifest: {manifest_path}")

    if warnings:
        print("\n".join(warnings))

    print(
        "\n✅ Listo. Sube cada ZIP (y opcionalmente el manifest.json). "
        "Para reconstruir, descomprime todas las partes en la misma carpeta destino."
    )


if __name__ == "__main__":
    main()
