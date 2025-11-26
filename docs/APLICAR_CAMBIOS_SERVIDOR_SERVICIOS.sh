#!/bin/bash
# ============================================
# SCRIPT PARA APLICAR CAMBIOS EN EL SERVIDOR
# Ejecutar en PythonAnywhere
# ============================================

cd ~/apps/egarage/current

# Backup de archivos antes de modificar
cp taller/servicios/views.py taller/servicios/views.py.backup
cp templates/taller/us/en/servicios/servicios_menu.html templates/taller/us/en/servicios/servicios_menu.html.backup

echo "✅ Backups creados"

# Aplicar cambios usando Python
python3.10 << 'ENDPYTHON'
import re

# 1. Modificar taller/servicios/views.py
views_file = 'taller/servicios/views.py'
with open(views_file, 'r', encoding='utf-8') as f:
    content = f.read()

# Reemplazar la sección de obtención de servicios
old_services = '''    # Obtener servicios con filtros básicos
    if empresa:
        servicios = Servicio.objects.filter(empresa=empresa)
        if not servicios.exists():
            servicios = Servicio.objects.all()
    else:
        servicios = Servicio.objects.all()

    servicios_qs = (
        servicios.select_related("categoria", "subcategoria")
        .prefetch_related("names", "categoria__names", "subcategoria__names")
        .order_by("nombre")
    )
    if language:
        servicios_qs = servicios_qs.filter(names__language=language).distinct()
    servicios_list = list(servicios_qs)'''

new_services = '''    # Obtener servicios con filtros básicos
    # Primero filtrar por país (importante para mostrar servicios correctos)
    servicios = Servicio.objects.filter(categoria__country=country_code)
    
    # Si el usuario tiene empresa, priorizar servicios de su empresa
    if empresa:
        servicios_empresa = servicios.filter(empresa=empresa)
        if servicios_empresa.exists():
            servicios = servicios_empresa
        # Si no tiene servicios en su empresa, mostrar todos del país
        # (ya está filtrado por país arriba)
    
    servicios_qs = (
        servicios.select_related("categoria", "subcategoria")
        .prefetch_related("names", "categoria__names", "subcategoria__names")
        .order_by("nombre")
    )
    if language:
        servicios_qs = servicios_qs.filter(names__language=language).distinct()
    servicios_list = list(servicios_qs)'''

if old_services in content:
    content = content.replace(old_services, new_services)
    print("✅ Sección de servicios actualizada")
else:
    print("⚠️ No se encontró la sección exacta de servicios, buscando variante...")
    # Intentar con una búsqueda más flexible
    pattern = r'(# Obtener servicios con filtros básicos.*?servicios_list = list\(servicios_qs\))'
    if re.search(pattern, content, re.DOTALL):
        content = re.sub(pattern, new_services, content, flags=re.DOTALL)
        print("✅ Sección de servicios actualizada (patrón flexible)")
    else:
        print("❌ No se pudo encontrar la sección a reemplazar")

# Reemplazar sección de categorías
old_categorias = '''    categorias = list(
        CategoriaServicio.objects.filter(
            country=country_code,
            names__language=language,
            names__is_default=True,
        )
        .prefetch_related("names")
        .order_by("code")
        .distinct()
    )
    for categoria in categorias:
        categoria.label_localizado = categoria.get_label(language)'''

new_categorias = '''    # Obtener categorías del país, asegurando que tengan nombres en el idioma correcto
    categorias_qs = CategoriaServicio.objects.filter(
        country=country_code
    ).prefetch_related("names").order_by("code").distinct()
    
    categorias = []
    for categoria in categorias_qs:
        # Verificar que tenga nombre en el idioma solicitado
        nombre = categoria.get_label(language)
        if nombre and nombre != categoria.code:  # Si tiene nombre válido
            categoria.label_localizado = nombre
            categorias.append(categoria)'''

if old_categorias in content:
    content = content.replace(old_categorias, new_categorias)
    print("✅ Sección de categorías actualizada")
else:
    print("⚠️ No se encontró la sección exacta de categorías")

# Reemplazar sección de subcategorías
old_subcategorias = '''    subcategorias = list(
        SubcategoriaServicio.objects.filter(
            country=country_code,
            names__language=language,
            names__is_default=True,
        )
        .prefetch_related("names")
        .order_by("code")
        .distinct()
    )
    for subcategoria in subcategorias:
        subcategoria.label_localizado = subcategoria.get_label(language)'''

new_subcategorias = '''    # Obtener subcategorías del país, asegurando que tengan nombres en el idioma correcto
    subcategorias_qs = SubcategoriaServicio.objects.filter(
        country=country_code
    ).prefetch_related("names").order_by("code").distinct()
    
    subcategorias = []
    for subcategoria in subcategorias_qs:
        # Verificar que tenga nombre en el idioma solicitado
        nombre = subcategoria.get_label(language)
        if nombre and nombre != subcategoria.code:  # Si tiene nombre válido
            subcategoria.label_localizado = nombre
            subcategorias.append(subcategoria)'''

if old_subcategorias in content:
    content = content.replace(old_subcategorias, new_subcategorias)
    print("✅ Sección de subcategorías actualizada")
else:
    print("⚠️ No se encontró la sección exacta de subcategorías")

# Reemplazar servicios_por_categoria
old_servicios_por_cat = '''    servicios_por_categoria = defaultdict(list)
    for servicio in servicios_list:
        if servicio.categoria:
            servicios_por_categoria[servicio.categoria].append(servicio)'''

new_servicios_por_cat = '''    servicios_por_categoria = defaultdict(list)
    for servicio in servicios_list:
        if servicio.categoria and servicio.categoria.country == country_code:
            servicios_por_categoria[servicio.categoria].append(servicio)'''

if old_servicios_por_cat in content:
    content = content.replace(old_servicios_por_cat, new_servicios_por_cat)
    print("✅ Sección servicios_por_categoria actualizada")

# Guardar archivo
with open(views_file, 'w', encoding='utf-8') as f:
    f.write(content)
print(f"✅ Archivo {views_file} actualizado")

# 2. Modificar template
template_file = 'templates/taller/us/en/servicios/servicios_menu.html'
with open(template_file, 'r', encoding='utf-8') as f:
    template_content = f.read()

# Reemplazos en el template
replacements = [
    ('{{ servicio.nombre }}', '{{ servicio.nombre_localizado|default:servicio.nombre }}'),
    ('{{ servicio.subcategoria.get_label }}', '{{ servicio.subcategoria_label|default:servicio.subcategoria.get_label }}'),
    ('{{ categoria.get_label }}', '{{ categoria.label_localizado|default:categoria.get_label }}'),
    ('{{ subcategoria.get_label }}', '{{ subcategoria.label_localizado|default:subcategoria.get_label }}'),
    ('{{ servicio.categoria.get_label|default:\'\' }}', '{{ servicio.categoria_label|default:servicio.categoria.get_label|default:\'\' }}'),
    ('{{ servicio.subcategoria.get_label|default:\'\' }}', '{{ servicio.subcategoria_label|default:servicio.subcategoria.get_label|default:\'\' }}'),
    ('{{ servicio.nombre|default:\'\' }}', '{{ servicio.nombre_localizado|default:servicio.nombre|default:\'\' }}'),
    ('{{ servicios_cat.count }}', '{{ servicios_cat|length }}'),
]

for old, new in replacements:
    if old in template_content:
        template_content = template_content.replace(old, new)
        print(f"✅ Reemplazado en template: {old[:30]}...")

# Guardar template
with open(template_file, 'w', encoding='utf-8') as f:
    f.write(template_content)
print(f"✅ Archivo {template_file} actualizado")

print("\n✅ ¡Todos los cambios aplicados!")
print("📝 Reinicia la aplicación web en PythonAnywhere")
ENDPYTHON

echo ""
echo "✅ Script completado"
echo "📝 Ahora reinicia la aplicación web en PythonAnywhere"

