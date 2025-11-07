#!/usr/bin/env python
"""
Cache-busting: Agrega hashes a nombres de archivos para invalidar cache
"""
import os
import json
import argparse
import hashlib
import shutil
from pathlib import Path

def get_file_hash(filepath):
    """Calcula MD5 de un archivo para cache-busting"""
    hash_md5 = hashlib.md5()
    try:
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()[:8]  # Solo primeros 8 caracteres
    except Exception as e:
        return f"ERROR: {e}"

def should_hash_file(file_path):
    """Determina si un archivo debe ser hasheado"""
    # Solo archivos CSS, JS e imágenes
    extensions = {'.css', '.js', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp', '.ico'}
    return file_path.suffix.lower() in extensions

def create_hashed_filename(file_path, file_hash):
    """Crea nombre de archivo con hash"""
    stem = file_path.stem
    suffix = file_path.suffix
    return f"{stem}.{file_hash}{suffix}"

def hash_assets(base_path, manifest_file, apply_changes=False):
    """Aplica cache-busting a archivos estáticos"""
    base_path = Path(base_path)
    
    if not base_path.exists():
        print(f"❌ Directorio no existe: {base_path}")
        return
    
    print(f"🔍 Aplicando cache-busting en: {base_path}")
    
    # Cargar manifest de movimientos si existe
    moves_manifest = {}
    moves_manifest_file = base_path.parent / 'reports' / 'manifest.json'
    if moves_manifest_file.exists():
        with open(moves_manifest_file, 'r', encoding='utf-8') as f:
            moves_manifest = json.load(f)
    
    # Procesar archivos
    hashed_manifest = {}
    files_to_hash = []
    
    for file_path in base_path.rglob('*'):
        if file_path.is_file() and should_hash_file(file_path):
            relative_path = file_path.relative_to(base_path)
            
            # Usar path del manifest de movimientos si existe
            original_path = str(relative_path)
            if original_path in moves_manifest:
                original_path = moves_manifest[original_path]
            
            file_hash = get_file_hash(file_path)
            if not file_hash.startswith('ERROR'):
                hashed_name = create_hashed_filename(file_path, file_hash)
                hashed_path = file_path.parent / hashed_name
                
                files_to_hash.append({
                    'original': file_path,
                    'hashed': hashed_path,
                    'hash': file_hash,
                    'original_path': original_path
                })
                
                hashed_manifest[original_path] = str(hashed_path.relative_to(base_path))
    
    # Mostrar resumen
    print(f"\n📋 RESUMEN DE CACHE-BUSTING:")
    print(f"   Archivos a hashear: {len(files_to_hash)}")
    print(f"   Manifest guardado en: {manifest_file}")
    
    # Mostrar algunos ejemplos
    print(f"\n📝 EJEMPLOS DE HASHES:")
    for i, file_info in enumerate(files_to_hash[:10]):
        print(f"   {file_info['original_path']} → {file_info['hashed'].name}")
    
    if len(files_to_hash) > 10:
        print(f"   ... y {len(files_to_hash) - 10} más")
    
    # Guardar manifest
    with open(manifest_file, 'w', encoding='utf-8') as f:
        json.dump(hashed_manifest, f, indent=2, ensure_ascii=False)
    
    # Aplicar cambios si se solicita
    if apply_changes:
        print(f"\n🔄 APLICANDO CACHE-BUSTING...")
        applied = 0
        errors = 0
        
        for file_info in files_to_hash:
            try:
                # Renombrar archivo
                shutil.move(str(file_info['original']), str(file_info['hashed']))
                applied += 1
                
            except Exception as e:
                print(f"   ❌ Error hasheando {file_info['original_path']}: {e}")
                errors += 1
        
        print(f"   ✅ Archivos hasheados: {applied}")
        print(f"   ❌ Errores: {errors}")
    else:
        print(f"\n💡 Para aplicar los cambios, ejecuta:")
        print(f"   python hash_assets.py --base {base_path} --manifest {manifest_file} --apply")

def main():
    parser = argparse.ArgumentParser(description='Aplica cache-busting a archivos estáticos')
    parser.add_argument('--base', required=True, help='Directorio base de archivos estáticos')
    parser.add_argument('--manifest', required=True, help='Archivo JSON de manifest con hashes')
    parser.add_argument('--apply', action='store_true', help='Aplicar los cambios')
    
    args = parser.parse_args()
    hash_assets(args.base, args.manifest, args.apply)

if __name__ == '__main__':
    main()
