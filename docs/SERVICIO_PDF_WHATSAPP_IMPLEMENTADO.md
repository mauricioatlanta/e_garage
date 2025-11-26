# 📄 Servicio de Salida de Documentos (PDF + WhatsApp) - Implementación Completa

## 📋 Resumen

Implementación completa del servicio de generación de PDFs y enlaces de WhatsApp para documentos. Cierra el ciclo de venta ("The Fulfillment Loop") - el cliente recibe su comprobante de forma digital.

**Features:**
- ✅ Generación de PDFs con WeasyPrint (HTML/CSS a PDF)
- ✅ Multi-tenant seguro (usa logo, colores y datos de la empresa)
- ✅ Formato de moneda según país (CL/US/MX)
- ✅ Enlaces de WhatsApp pre-llenados
- ✅ Templates HTML profesionales

## 🎯 Problema Resuelto

**Antes:**
- ❌ No había forma automática de generar PDFs profesionales
- ❌ No había integración con WhatsApp
- ❌ No había servicio dedicado para salida de documentos

**Ahora:**
- ✅ PDFs generados automáticamente con diseño profesional
- ✅ Enlaces de WhatsApp con mensaje pre-llenado
- ✅ Servicio dedicado y reutilizable
- ✅ Multi-tenant seguro

## 📁 Archivos Creados

### 1. Servicio de Salida de Documentos
**Archivo**: `taller/services/document_output_service.py`

Servicio dedicado que maneja toda la lógica de generación de PDFs y enlaces de WhatsApp:

```python
class DocumentOutputService:
    @staticmethod
    def generate_pdf(documento, request=None):
        """Genera PDF en memoria (bytes)"""
    
    @staticmethod
    def generate_whatsapp_link(documento, request=None, pdf_url=None):
        """Genera enlace de WhatsApp pre-llenado"""
```

### 2. Vistas de PDF y WhatsApp
**Archivo**: `taller/documentos/views_pdf.py`

Vistas para descargar PDFs y enviar por WhatsApp:

- `descargar_pdf_documento()` - Genera y descarga PDF
- `generar_enlace_whatsapp()` - API para obtener enlace de WhatsApp
- `enviar_por_whatsapp()` - Redirige al enlace de WhatsApp

### 3. Template HTML para PDF
**Archivo**: `templates/taller/documentos/pdf/invoice_template.html`

Template HTML profesional optimizado para PDF con:
- Diseño limpio y profesional
- Multi-tenant (logo, colores, datos de empresa)
- Formato de moneda según país
- Todos los detalles del documento

### 4. URLs Agregadas
**Archivo**: `taller/documentos/urls.py`

URLs agregadas:
- `/documentos/<pk>/pdf/` - Ver PDF en navegador
- `/documentos/<pk>/pdf/descargar/` - Descargar PDF
- `/documentos/<pk>/whatsapp/` - Enviar por WhatsApp
- `/documentos/<pk>/whatsapp/enlace/` - API: Obtener enlace WhatsApp

## 🔧 Configuración

### 1. Instalar WeasyPrint

```bash
pip install weasyprint
```

### 2. Servicio Disponible

Ya está exportado en `taller/services/__init__.py`:

```python
from taller.services import DocumentOutputService
```

## 🎨 Uso

### Generar PDF

```python
from taller.services import DocumentOutputService

# Generar PDF
pdf_bytes, filename = DocumentOutputService.generate_pdf(documento, request)

# Crear respuesta HTTP
response = HttpResponse(pdf_bytes, content_type='application/pdf')
response['Content-Disposition'] = f'inline; filename="{filename}"'
return response
```

### Generar Enlace de WhatsApp

```python
from taller.services import DocumentOutputService

# Generar enlace
whatsapp_url = DocumentOutputService.generate_whatsapp_link(
    documento,
    request=request,
    pdf_url=None  # Opcional: URL pública del PDF
)

# Redirigir al usuario
return redirect(whatsapp_url)
```

### Desde Templates

```html
<!-- Botón para descargar PDF -->
<a href="{% url 'documentos:descargar_pdf' documento.pk %}" 
   class="btn btn-primary" 
   target="_blank">
    📄 Ver PDF
</a>

<!-- Botón para enviar por WhatsApp -->
<form method="post" action="{% url 'documentos:enviar_whatsapp' documento.pk %}">
    {% csrf_token %}
    <button type="submit" class="btn btn-success">
        💬 Enviar por WhatsApp
    </button>
</form>

<!-- API: Obtener enlace WhatsApp (para uso con JavaScript) -->
<button onclick="enviarWhatsApp({{ documento.pk }})">
    💬 Enviar por WhatsApp
</button>

<script>
function enviarWhatsApp(documentoId) {
    fetch(`/documentos/${documentoId}/whatsapp/enlace/`)
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                window.open(data.whatsapp_url, '_blank');
            } else {
                alert('Error: ' + data.error);
            }
        });
}
</script>
```

## 📊 Características

### 1. Multi-Tenant Seguro

El servicio obtiene configuración de la empresa con fallbacks:

1. **CompanySettings** (sistema nuevo)
2. **ConfiguracionEmpresa** (legacy)
3. **Datos directos de Empresa** (fallback)

```python
config = DocumentOutputService._get_empresa_config(empresa, request)
# Retorna: logo, nombre, tagline, direccion, telefono, email, etc.
```

### 2. Formato de Moneda Según País

```python
# Chile (CL)
currency = {
    'symbol': '$',
    'code': 'CLP',
    'decimals': 0,
    'thousands_separator': '.',
    'decimal_separator': ',',
}

# USA (US)
currency = {
    'symbol': 'US$',
    'code': 'USD',
    'decimals': 2,
    'thousands_separator': ',',
    'decimal_separator': '.',
}

# México (MX)
currency = {
    'symbol': 'MX$',
    'code': 'MXN',
    'decimals': 2,
    'thousands_separator': ',',
    'decimal_separator': '.',
}
```

### 3. Template HTML Profesional

El template incluye:
- Header con logo y datos de empresa
- Información del documento (tipo, número, fecha, estado)
- Información del cliente y vehículo
- Tabla de líneas (repuestos, servicios)
- Totales (netos, impuestos, descuentos, total final)
- Footer con información legal

### 4. Enlace de WhatsApp Inteligente

El enlace incluye:
- Mensaje personalizado con nombre del cliente
- Tipo y número de documento
- Total formateado según moneda
- URL de descarga del PDF (si está disponible)

Ejemplo de mensaje:
```
Hola Juan Pérez,

Adjunto Factura N°FAC001
de Mi Taller
por un total de $50.000.

Gracias por su preferencia.

Descargar: https://tugarage.com/documentos/123/pdf/
```

## 🔒 Seguridad

### Multi-Tenant

```python
# ✅ Siempre filtrar por empresa
documento = get_object_or_404(
    Documento,
    pk=pk,
    empresa=request.user.empresa  # 🔒 Multi-tenant
)
```

### Validación de Acceso

```python
# Solo usuarios autenticados pueden generar PDFs
@login_required
@require_GET
def descargar_pdf_documento(request, pk):
    # ...
```

## 🎨 Personalización

### Logo y Colores

El PDF usa automáticamente:
- Logo de la empresa (si está configurado)
- Colores primarios de la empresa
- Nombre y datos de contacto

### Formato de Moneda

El formato se ajusta automáticamente según `empresa.pais`:
- Chile: `$50.000` (sin decimales)
- USA: `US$50.00` (2 decimales)
- México: `MX$50.00` (2 decimales)

## ⚠️ Notas Importantes

### 1. WeasyPrint

El servicio requiere WeasyPrint instalado. Si no está disponible, se lanza `ImportError`:

```python
try:
    pdf_bytes, filename = DocumentOutputService.generate_pdf(documento, request)
except ImportError:
    # WeasyPrint no está disponible
    messages.error(request, "WeasyPrint no está disponible. Instala con: pip install weasyprint")
```

### 2. Base URL para Imágenes

El servicio necesita `base_url` para cargar imágenes/logos:

```python
# Se obtiene automáticamente del request
base_url = request.build_absolute_uri('/')

# O se puede configurar en settings
BASE_URL = 'https://tugarage.com'
```

### 3. Servidores Compartidos (PythonAnywhere)

En servidores compartidos, asegúrate de:
1. Instalar WeasyPrint correctamente
2. Configurar `BASE_URL` en settings
3. Verificar permisos de lectura de imágenes

## ✅ Ventajas

| Aspecto | Antes | Ahora |
|---------|-------|-------|
| **Generación de PDF** | Manual | Automática |
| **Diseño** | Básico | Profesional |
| **Multi-tenant** | No | Sí |
| **WhatsApp** | No | Sí |
| **Formato de Moneda** | Manual | Automático |
| **Reutilización** | No | Servicio dedicado |

## 🚀 Próximos Pasos Opcionales

1. **Envío Automático por Email**
   - Enviar PDF adjunto al email del cliente automáticamente

2. **Firma Digital**
   - Agregar firma digital al PDF

3. **Código QR**
   - Generar código QR para verificación

4. **Plantillas Personalizadas**
   - Permitir a empresas crear plantillas personalizadas

5. **Historial de Envíos**
   - Registrar cada envío de PDF/WhatsApp

## ✅ Checklist de Implementación

- [x] Servicio DocumentOutputService creado
- [x] Vistas de PDF y WhatsApp creadas
- [x] Template HTML para PDF creado
- [x] URLs agregadas
- [x] Multi-tenant seguro
- [x] Formato de moneda por país
- [x] Logging de operaciones
- [ ] Instalar WeasyPrint en servidor
- [ ] Probar generación de PDFs
- [ ] Probar enlaces de WhatsApp

## 🎉 Resultado

Con este servicio, tu sistema ahora:
- ✅ Genera PDFs profesionales automáticamente
- ✅ Crea enlaces de WhatsApp pre-llenados
- ✅ Usa logo y colores de la empresa (multi-tenant)
- ✅ Formatea moneda según país automáticamente
- ✅ Es reutilizable y fácil de mantener

**¡The Fulfillment Loop completo!** 🎊

El cliente ahora recibe su comprobante de forma digital, cerrando el ciclo de venta de manera profesional y moderna.

