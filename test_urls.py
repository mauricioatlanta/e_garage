"""
Archivo temporal para agregar la URL de prueba
"""

# URL de prueba para el formulario de documento
urlpatterns = [
    # ... existing URLs ...
    # URL de prueba para el formulario de documento
    path("test-doc/", crear_documento_test, name="test_document_form"),
    # ... rest of URLs ...
]
