#!/usr/bin/env python
"""
Sugiere reorganización de archivos estáticos - Normaliza nombres y estructura
"""
import os
import json
import argparse
import shutil
from pathlib import Path
import unicodedata
import re

def normalize_filename(filename):
    """Normaliza nombre de archivo: minúsculas, sin acentos, kebab-case"""
    # Remover acentos
    filename = unicodedata.normalize('NFD', filename)
    filename = ''.join(c for c in filename if unicodedata.category(c) != 'Mn')
    
    # Convertir a minúsculas
    filename = filename.lower()
    
    # Reemplazar espacios y caracteres especiales con guiones
    filename = re.sub(r'[^\w\-\.]', '-', filename)
    
    # Limpiar múltiples guiones
    filename = re.sub(r'-+', '-', filename)
    
    # Remover guiones al inicio y final
    filename = filename.strip('-')
    
    return filename

def get_target_directory(file_type, current_path):
    """Determina el directorio objetivo basado en el tipo y contexto"""
    path_str = str(current_path).lower()
    
    # Archivos específicos por país/idioma
    if '/cl/' in path_str or 'chile' in path_str:
        country = 'cl'
    elif '/us/' in path_str or 'usa' in path_str or 'united' in path_str:
        country = 'us'
    else:
        country = 'common'
    
    # Mapeo de tipos a directorios
    type_mapping = {
        'CSS': f'taller/{country}/css',
        'JS': f'taller/{country}/js',
        'IMG': f'taller/{country}/img',
        'FONT': f'taller/{country}/fonts',
        'VIDEO': f'taller/{country}/media',
        'AUDIO': f'taller/{country}/media',
        'OTHER': f'taller/{country}/media'
    }
    
    # Archivos de terceros van a vendor/
    if any(vendor in path_str for vendor in ['jquery', 'select2', 'bootstrap', 'vendor']):
        if file_type in ['CSS', 'JS']:
            return f'vendor/{current_path.parts[-2] if len(current_path.parts) > 1 else "unknown"}/{file_type.lower()}'
        else:
            return f'vendor/{current_path.parts[-2] if len(current_path.parts) > 1 else "unknown"}'
    
    return type_mapping.get(file_type, f'taller/{country}/media')

def suggest_moves(base_path, manifest_file, apply_changes=False):
    """Sugiere movimientos y reorganización de archivos"""
    base_path = Path(base_path)
    
    if not base_path.exists():
        print(f"❌ Directorio no existe: {base_path}")
        return
    
    print(f"🔍 Analizando estructura en: {base_path}")
    
    # Cargar datos de auditoría si existe
    audit_csv = Path('tools/reports/audit_static.csv')
    if not audit_csv.exists():
        print("❌ No se encontró audit_static.csv. Ejecuta primero audit_static.py")
        return
    
    # Leer datos de auditoría
    import csv
    files_data = []
    with open(audit_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        files_data = list(reader)
    
    # Generar sugerencias de movimiento
    moves = []
    manifest = {}
    
    for file_data in files_data:
        current_path = Path(file_data['path'])
        file_type = file_data['type']
        
        # Saltar duplicados (se manejarán por separado)
        if file_data['is_duplicate'] == 'True':
            continue
        
        # Determinar directorio objetivo
        target_dir = get_target_directory(file_type, current_path)
        
        # Normalizar nombre de archivo
        normalized_name = normalize_filename(current_path.name)
        
        # Crear nuevo path
        new_path = Path(target_dir) / normalized_name
        
        # Evitar colisiones
        counter = 1
        original_new_path = new_path
        while str(new_path) in [move['new_path'] for move in moves]:
            stem = original_new_path.stem
            suffix = original_new_path.suffix
            new_path = original_new_path.parent / f"{stem}-{counter}{suffix}"
            counter += 1
        
        # Agregar a movimientos
        move = {
            'old_path': str(current_path),
            'new_path': str(new_path),
            'file_type': file_type,
            'size_mb': float(file_data['size_mb']),
            'has_issues': file_data['has_issues'] == 'True',
            'issues': file_data['issues']
        }
        moves.append(move)
        
        # Agregar al manifest
        manifest[str(current_path)] = str(new_path)
    
    # Guardar manifest
    with open(manifest_file, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    
    # Mostrar resumen
    print(f"\n📋 RESUMEN DE MOVIMIENTOS:")
    print(f"   Total archivos a mover: {len(moves)}")
    print(f"   Archivos con problemas: {sum(1 for m in moves if m['has_issues'])}")
    print(f"   Manifest guardado en: {manifest_file}")
    
    # Mostrar algunos ejemplos
    print(f"\n📝 EJEMPLOS DE MOVIMIENTOS:")
    for i, move in enumerate(moves[:10]):
        status = "⚠️" if move['has_issues'] else "✅"
        print(f"   {status} {move['old_path']} → {move['new_path']}")
    
    if len(moves) > 10:
        print(f"   ... y {len(moves) - 10} más")
    
    # Aplicar cambios si se solicita
    if apply_changes:
        print(f"\n🔄 APLICANDO CAMBIOS...")
        applied = 0
        errors = 0
        
        for move in moves:
            try:
                old_path = base_path / move['old_path']
                new_path = base_path / move['new_path']
                
                # Crear directorio padre si no existe
                new_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Mover archivo
                shutil.move(str(old_path), str(new_path))
                applied += 1
                
            except Exception as e:
                print(f"   ❌ Error moviendo {move['old_path']}: {e}")
                errors += 1
        
        print(f"   ✅ Archivos movidos: {applied}")
        print(f"   ❌ Errores: {errors}")
    else:
        print(f"\n💡 Para aplicar los cambios, ejecuta:")
        print(f"   python suggest_moves.py --base {base_path} --manifest {manifest_file} --apply")

def main():
    parser = argparse.ArgumentParser(description='Sugiere reorganización de archivos estáticos')
    parser.add_argument('--base', required=True, help='Directorio base de archivos estáticos')
    parser.add_argument('--manifest', required=True, help='Archivo JSON de manifest')
    parser.add_argument('--apply', action='store_true', help='Aplicar los cambios')
    
    args = parser.parse_args()
    suggest_moves(args.base, args.manifest, args.apply)

if __name__ == '__main__':
    main()
