# Comandos PDF - WeasyPrint y wkhtmltopdf

## 🖨️ WeasyPrint (Recomendado)

### Instalación:
```bash
pip install weasyprint
```

### Uso en Django:
```python
from weasyprint import HTML
from django.template.loader import render_to_string
from django.http import HttpResponse

def documento_pdf_weasyprint(request, pk):
    obj = get_object_or_404(Documento, pk=pk, empresa=request.user.empresa)

    context = {
        "obj": obj,
        "pdf_mode": True,
        "empresa_nombre": empresa.nombre_taller,
        # ... más contexto
    }

    # Generar HTML
    html = render_to_string("taller/documentos/pdf_base.html", context)

    # Convertir a PDF
    pdf = HTML(string=html).write_pdf()

    # Retornar como descarga
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="documento_{pk}.pdf"'
    return response
```

### Características WeasyPrint:
- ✅ **CSS moderno** - Soporta @page, element(), counter(pages)
- ✅ **Headers/footers automáticos** - Con running elements
- ✅ **Numeración de páginas** - Automática con counter(pages)
- ✅ **Márgenes configurables** - @page margin
- ✅ **Alto contraste** - Optimizado para impresión

## 🖨️ wkhtmltopdf (Alternativa)

### Instalación:
```bash
# Ubuntu/Debian
sudo apt-get install wkhtmltopdf

# macOS
brew install wkhtmltopdf

# Windows
# Descargar desde: https://wkhtmltopdf.org/downloads.html
```

### Comando básico:
```bash
wkhtmltopdf \
  --page-size A4 \
  --margin-top 28mm --margin-bottom 22mm \
  --margin-left 14mm --margin-right 14mm \
  --header-html "https://tu-dominio.com/pdf/header/123/" \
  --footer-html "https://tu-dominio.com/pdf/footer/123/" \
  "https://tu-dominio.com/documentos/123/pdf-html/" \
  "/tmp/documento_123.pdf"
```

### Uso en Django:
```python
import subprocess
from django.conf import settings

def documento_pdf_wkhtmltopdf(request, pk):
    obj = get_object_or_404(Documento, pk=pk, empresa=request.user.empresa)

    # URLs absolutas
    base_url = request.build_absolute_uri('/')
    header_url = request.build_absolute_uri(reverse('pdf:header', args=[pk]))
    footer_url = request.build_absolute_uri(reverse('pdf:footer', args=[pk]))
    content_url = request.build_absolute_uri(reverse('documentos:pdf_html', args=[pk]))

    # Comando wkhtmltopdf
    cmd = [
        'wkhtmltopdf',
        '--page-size', 'A4',
        '--margin-top', '28mm',
        '--margin-bottom', '22mm',
        '--margin-left', '14mm',
        '--margin-right', '14mm',
        '--header-html', header_url,
        '--footer-html', footer_url,
        content_url,
        f'/tmp/documento_{pk}.pdf'
    ]

    # Ejecutar comando
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        with open(f'/tmp/documento_{pk}.pdf', 'rb') as f:
            pdf_content = f.read()

        response = HttpResponse(pdf_content, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="documento_{pk}.pdf"'
        return response
    else:
        return HttpResponse(f"Error: {result.stderr}", status=500)
```

### Características wkhtmltopdf:
- ✅ **WebKit engine** - Motor de navegador real
- ✅ **Headers/footers externos** - Via URLs
- ✅ **Variables de página** - [page], [toPage]
- ✅ **JavaScript** - Soporte limitado
- ⚠️ **CSS limitado** - No soporta CSS moderno

## 📋 Comparación

| Característica | WeasyPrint | wkhtmltopdf |
|---|---|---|
| **CSS moderno** | ✅ Completo | ⚠️ Limitado |
| **Headers/footers** | ✅ @page element() | ✅ URLs externas |
| **Numeración** | ✅ counter(pages) | ✅ [page]/[toPage] |
| **Márgenes** | ✅ @page margin | ✅ --margin-* |
| **JavaScript** | ❌ No | ⚠️ Limitado |
| **Instalación** | ✅ pip install | ⚠️ Binario externo |
| **Rendimiento** | ✅ Rápido | ⚠️ Más lento |

## 🎯 Recomendación

**Usar WeasyPrint** para la mayoría de casos:
- CSS moderno y fiel
- Headers/footers automáticos
- Numeración de páginas nativa
- Instalación simple con pip
- Mejor rendimiento

**Usar wkhtmltopdf** solo si necesitas:
- JavaScript específico
- Compatibilidad con sistemas existentes
- Headers/footers muy complejos

## 🔧 URLs de Ejemplo

```python
# Incluir en tu urls.py principal
urlpatterns = [
    path("documentos/", include("taller.documentos.urls_ejemplo")),
    path("pdf/", include("taller.pdf.urls")),
]

# URLs disponibles:
# /documentos/crear/                    - Crear documento
# /documentos/123/editar/              - Editar documento
# /documentos/123/pdf/                 - Ver PDF (preview)
# /documentos/123/pdf-html/            - HTML para PDF
# /documentos/123/pdf-weasyprint/      - PDF con WeasyPrint
# /documentos/123/pdf-wkhtmltopdf/     - PDF con wkhtmltopdf
# /pdf/header/123/                     - Header para wkhtmltopdf
# /pdf/footer/123/                     - Footer para wkhtmltopdf
```
