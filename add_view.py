#!/usr/bin/env python
"""
Script para agregar la view de prueba al archivo views.py
"""

import os

# Leer el archivo views.py
with open("taller/views.py", "r", encoding="utf-8") as f:
    content = f.read()

# Eliminar el comentario incompleto al final
if "# ... existing code ..." in content:
    content = content.split("# ... existing code ...")[0].strip()

# Agregar la nueva función
new_function = '''# View simple para probar el formulario de documento
def crear_documento_test(request):
    """View simple para probar el formulario de creación de documentos"""
    if request.method == "POST":
        print("=== DATOS RECIBIDOS EN POST ===")
        print("POST data:", dict(request.POST))
        
        # Mostrar datos específicos
        repuestos_json = request.POST.get('repuestos_json', '[]')
        servicios_json = request.POST.get('servicios_json', '[]')
        
        print("\\n=== REPUESTOS JSON ===")
        print(repuestos_json)
        
        print("\\n=== SERVICIOS JSON ===")
        print(servicios_json)
        
        print("\\n=== OTROS DATOS ===\\n")
        print("Cliente ID:", request.POST.get('cliente_id'))
        print("Vehiculo ID:", request.POST.get('vehiculo_id'))
        print("Observaciones:", request.POST.get('observaciones'))
        print("Fecha:", request.POST.get('fecha'))
        print("Total:", request.POST.get('total'))
        
        # Retornar un mensaje simple
        from django.http import JsonResponse
        return JsonResponse({
            'status': 'success',
            'message': 'Datos recibidos correctamente',
            'repuestos': repuestos_json,
            'servicios': servicios_json
        })
    
    # Si es GET, mostrar el template
    return render(request, "taller/documentos/create.html")'''

# Escribir el archivo actualizado
with open("taller/views.py", "w", encoding="utf-8") as f:
    f.write(content + "\\n\\n" + new_function)

print("OK: Funcion agregada exitosamente!")
