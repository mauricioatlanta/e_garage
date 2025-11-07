#!/usr/bin/env python
"""
Auditoría de archivos estáticos - Detecta duplicados, nombres problemáticos, etc.
"""
import os
import hashlib
import csv
import argparse
from pathlib import Path
import mimetypes

def get_file_hash(filepath):
    """Calcula SHA1 de un archivo"""
    hash_sha1 = hashlib.sha1()
    try:
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha1.update(chunk)
        return hash_sha1.hexdigest()
    except Exception as e:
        return f"ERROR: {e}"

def analyze_filename(filename):
    """Analiza problemas en el nombre del archivo"""
    issues = []
    
    # Espacios
    if ' ' in filename:
        issues.append("SPACES")
    
    # Mayúsculas
    if any(c.isupper() for c in filename):
        issues.append("UPPERCASE")
    
    # Acentos y caracteres especiales
    special_chars = "áéíóúñüçàèìòù"
    if any(char in filename.lower() for char in special_chars):
        issues.append("ACCENTS")
    
    # Caracteres problemáticos
    problematic = "()[]{}!@#$%^&*+=|\\:;\"'<>?/~`"
    if any(char in filename for char in problematic):
        issues.append("SPECIAL_CHARS")
    
    # Nombres muy largos
    if len(filename) > 50:
        issues.append("LONG_NAME")
    
    return issues

def get_file_type(filepath):
    """Determina el tipo de archivo"""
    mime_type, _ = mimetypes.guess_type(filepath)
    if mime_type:
        if mime_type.startswith('text/css'):
            return 'CSS'
        elif mime_type.startswith('application/javascript') or mime_type.startswith('text/javascript'):
            return 'JS'
        elif mime_type.startswith('image/'):
            return 'IMG'
        elif mime_type.startswith('font/'):
            return 'FONT'
        elif mime_type.startswith('video/'):
            return 'VIDEO'
        elif mime_type.startswith('audio/'):
            return 'AUDIO'
    
    # Fallback por extensión
    ext = Path(filepath).suffix.lower()
    if ext in ['.css']:
        return 'CSS'
    elif ext in ['.js']:
        return 'JS'
    elif ext in ['.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp', '.ico']:
        return 'IMG'
    elif ext in ['.woff', '.woff2', '.ttf', '.otf', '.eot']:
        return 'FONT'
    elif ext in ['.mp4', '.webm', '.avi', '.mov']:
        return 'VIDEO'
    elif ext in ['.mp3', '.wav', '.ogg']:
        return 'AUDIO'
    
    return 'OTHER'

def audit_static_directory(base_path, output_csv):
    """Audita directorio de archivos estáticos"""
    base_path = Path(base_path)
    
    if not base_path.exists():
        print(f"❌ Directorio no existe: {base_path}")
        return
    
    print(f"🔍 Auditando directorio: {base_path}")
    
    # Recopilar información de archivos
    files_data = []
    hash_map = {}
    
    for file_path in base_path.rglob('*'):
        if file_path.is_file():
            relative_path = file_path.relative_to(base_path)
            
            # Información básica
            file_size = file_path.stat().st_size
            file_hash = get_file_hash(file_path)
            file_type = get_file_type(file_path)
            filename_issues = analyze_filename(file_path.name)
            
            # Detectar duplicados
            if file_hash in hash_map:
                hash_map[file_hash].append(str(relative_path))
            else:
                hash_map[file_hash] = [str(relative_path)]
            
            files_data.append({
                'path': str(relative_path),
                'name': file_path.name,
                'size_bytes': file_size,
                'size_mb': round(file_size / (1024 * 1024), 2),
                'sha1': file_hash,
                'type': file_type,
                'issues': '; '.join(filename_issues) if filename_issues else '',
                'has_issues': len(filename_issues) > 0,
                'is_duplicate': False  # Se actualizará después
            })
    
    # Marcar duplicados
    for file_data in files_data:
        if len(hash_map[file_data['sha1']]) > 1:
            file_data['is_duplicate'] = True
    
    # Escribir CSV
    with open(output_csv, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['path', 'name', 'size_bytes', 'size_mb', 'sha1', 'type', 'issues', 'has_issues', 'is_duplicate']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(files_data)
    
    # Estadísticas
    total_files = len(files_data)
    files_with_issues = sum(1 for f in files_data if f['has_issues'])
    duplicate_files = sum(1 for f in files_data if f['is_duplicate'])
    total_size_mb = sum(f['size_mb'] for f in files_data)
    
    print(f"\n📊 ESTADÍSTICAS:")
    print(f"   Total archivos: {total_files}")
    print(f"   Archivos con problemas: {files_with_issues}")
    print(f"   Archivos duplicados: {duplicate_files}")
    print(f"   Tamaño total: {total_size_mb:.2f} MB")
    print(f"   Reporte guardado en: {output_csv}")
    
    # Mostrar problemas más comunes
    if files_with_issues > 0:
        print(f"\n⚠️  PROBLEMAS DETECTADOS:")
        issue_counts = {}
        for file_data in files_data:
            if file_data['issues']:
                for issue in file_data['issues'].split('; '):
                    issue_counts[issue] = issue_counts.get(issue, 0) + 1
        
        for issue, count in sorted(issue_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"   {issue}: {count} archivos")

def main():
    parser = argparse.ArgumentParser(description='Audita archivos estáticos')
    parser.add_argument('--base', required=True, help='Directorio base de archivos estáticos')
    parser.add_argument('--out', required=True, help='Archivo CSV de salida')
    
    args = parser.parse_args()
    audit_static_directory(args.base, args.out)

if __name__ == '__main__':
    main()