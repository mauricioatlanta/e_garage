# 🚀 BRANDING ENTERPRISE - MEJORAS FINALES

## 🎯 OBJETIVO: BRANDING WHITE-LABEL DE CLASE ENTERPRISE

### ✅ BASE SÓLIDA ACTUAL
- ✅ Branding personalizado completo (backend + frontend + PDF)
- ✅ Context processor con cache inteligente
- ✅ Interfaz Settings moderna con preview tiempo real
- ✅ Sistema multilenguaje/multipaís operativo

### 🔥 MEJORAS ENTERPRISE PROPUESTAS

## 1. 🌍 INTEGRACIÓN COMPLETA MULTILENGUAJE + BRANDING

### Problema a Resolver
Un suscriptor puede tener usuarios accediendo desde diferentes países/idiomas, pero debe mantener su branding corporativo consistente.

### Solución: Context Processor Unificado Inteligente

```python
# taller/context_processors/unified_context.py
from django.core.cache import cache
from django.conf import settings
from .country_context import get_country_from_request, get_language_from_request
from taller.models import CompanySettings

def unified_branding_context(request):
    """
    Context processor que combina branding personalizado con multilenguaje
    Prioridad: Branding del usuario > Defaults por país > Defaults globales
    """

    # Obtener contexto multilenguaje
    current_country = get_country_from_request(request)
    current_language = get_language_from_request(request)

    # Cache key único por usuario/país/idioma
    user_id = request.user.id if request.user.is_authenticated else 'anonymous'
    cache_key = f'unified_context_{user_id}_{current_country}_{current_language}'

    cached_context = cache.get(cache_key)
    if cached_context:
        return cached_context

    context = {
        # Contexto multilenguaje base
        'current_country': current_country,
        'current_language': current_language,
        'available_countries': get_available_countries(),
        'country_flag': get_country_flag(current_country),
        'language_name': get_language_display_name(current_language),
    }

    # Agregar branding personalizado si usuario autenticado
    if request.user.is_authenticated:
        try:
            company_settings = CompanySettings.objects.get(user=request.user)

            # Branding personalizado
            context.update({
                'company_name': company_settings.get_company_name(),
                'company_logo': company_settings.get_logo_url(),
                'company_tagline': company_settings.tagline,
                'primary_color': company_settings.primary_color,
                'secondary_color': company_settings.secondary_color,
                'accent_color': company_settings.accent_color,
                'background_color': company_settings.background_color,
                'text_color': company_settings.text_color,
                'font_family': company_settings.get_font_family(),
                'font_size_base': company_settings.font_size_base,
                'border_radius': company_settings.border_radius,
                'shadow_style': company_settings.shadow_style,

                # Datos de contacto localizados
                'company_address': company_settings.get_localized_address(current_country),
                'company_phone': company_settings.get_localized_phone(current_country),
                'company_email': company_settings.email,
                'company_website': company_settings.website,

                # Configuración regional
                'currency_symbol': company_settings.get_currency_for_country(current_country),
                'timezone': company_settings.get_timezone_for_country(current_country),
                'date_format': company_settings.get_date_format_for_country(current_country),

                # Branding flags
                'has_custom_branding': True,
                'branding_tier': company_settings.get_branding_tier(),
            })

        except CompanySettings.DoesNotExist:
            # Defaults globales por país
            context.update(get_default_branding_for_country(current_country))
            context['has_custom_branding'] = False
    else:
        # Usuario no autenticado - branding por defecto del país
        context.update(get_default_branding_for_country(current_country))
        context['has_custom_branding'] = False

    # Cache por 5 minutos
    cache.set(cache_key, context, 300)
    return context

def get_default_branding_for_country(country):
    """Branding por defecto según el país"""
    defaults = {
        'CL': {
            'company_name': 'eGarage Chile',
            'company_logo': '/static/img/egarage-cl-logo.png',
            'primary_color': '#d32f2f',  # Rojo chileno
            'secondary_color': '#1976d2',
            'currency_symbol': '$',
            'phone_format': '+56 X XXXX XXXX',
        },
        'US': {
            'company_name': 'eGarage USA',
            'company_logo': '/static/img/egarage-us-logo.png',
            'primary_color': '#1565c0',  # Azul americano
            'secondary_color': '#d32f2f',
            'currency_symbol': '$',
            'phone_format': '+1 (XXX) XXX-XXXX',
        }
    }

    return defaults.get(country, defaults['US'])
```

### Extensión del Modelo CompanySettings

```python
# taller/models/company_settings.py - Campos adicionales
class CompanySettings(models.Model):
    # ... campos existentes ...

    # NUEVOS CAMPOS - Personalización Avanzada
    accent_color = models.CharField(
        max_length=7,
        default='#ff9800',
        validators=[validate_hex_color],
        help_text="Color de acentos y highlights"
    )
    background_color = models.CharField(
        max_length=7,
        default='#ffffff',
        validators=[validate_hex_color],
        help_text="Color de fondo principal"
    )
    text_color = models.CharField(
        max_length=7,
        default='#212121',
        validators=[validate_hex_color],
        help_text="Color de texto principal"
    )

    # Tipografía
    FONT_CHOICES = [
        ('system', 'Fuente del Sistema'),
        ('roboto', 'Roboto (Moderna)'),
        ('open-sans', 'Open Sans (Limpia)'),
        ('lato', 'Lato (Profesional)'),
        ('montserrat', 'Montserrat (Elegante)'),
        ('poppins', 'Poppins (Friendly)'),
        ('source-sans', 'Source Sans Pro (Técnica)'),
    ]
    font_family = models.CharField(
        max_length=20,
        choices=FONT_CHOICES,
        default='system',
        help_text="Familia tipográfica principal"
    )
    font_size_base = models.IntegerField(
        default=14,
        validators=[MinValueValidator(12), MaxValueValidator(18)],
        help_text="Tamaño base de fuente (12-18px)"
    )

    # Estilo visual
    border_radius = models.IntegerField(
        default=4,
        validators=[MinValueValidator(0), MaxValueValidator(20)],
        help_text="Radio de bordes redondeados (0-20px)"
    )
    SHADOW_CHOICES = [
        ('none', 'Sin sombras'),
        ('subtle', 'Sombras sutiles'),
        ('medium', 'Sombras medianas'),
        ('strong', 'Sombras marcadas'),
    ]
    shadow_style = models.CharField(
        max_length=10,
        choices=SHADOW_CHOICES,
        default='subtle',
        help_text="Estilo de sombras"
    )

    # Localización multipaís
    address_cl = models.TextField(blank=True, help_text="Dirección en Chile")
    address_us = models.TextField(blank=True, help_text="Dirección en USA")
    phone_cl = models.CharField(max_length=20, blank=True, help_text="Teléfono Chile")
    phone_us = models.CharField(max_length=20, blank=True, help_text="Teléfono USA")

    # Métodos para localización
    def get_localized_address(self, country):
        """Dirección localizada por país"""
        if country == 'CL' and self.address_cl:
            return self.address_cl
        elif country == 'US' and self.address_us:
            return self.address_us
        return self.address  # Fallback a dirección principal

    def get_localized_phone(self, country):
        """Teléfono localizado por país"""
        if country == 'CL' and self.phone_cl:
            return self.phone_cl
        elif country == 'US' and self.phone_us:
            return self.phone_us
        return self.phone  # Fallback

    def get_currency_for_country(self, country):
        """Símbolo de moneda según país"""
        currencies = {
            'CL': '$',
            'US': '$',
            'MX': '$',
            'CO': '$',
            'AR': '$',
        }
        return currencies.get(country, '$')

    def get_font_family(self):
        """CSS para familia tipográfica"""
        fonts = {
            'system': '-apple-system, BlinkMacSystemFont, "Segoe UI", system-ui',
            'roboto': '"Roboto", sans-serif',
            'open-sans': '"Open Sans", sans-serif',
            'lato': '"Lato", sans-serif',
            'montserrat': '"Montserrat", sans-serif',
            'poppins': '"Poppins", sans-serif',
            'source-sans': '"Source Sans Pro", sans-serif',
        }
        return fonts.get(self.font_family, fonts['system'])

    def get_css_variables(self):
        """Variables CSS para personalización avanzada"""
        return {
            '--primary-color': self.primary_color,
            '--secondary-color': self.secondary_color,
            '--accent-color': self.accent_color,
            '--background-color': self.background_color,
            '--text-color': self.text_color,
            '--font-family': self.get_font_family(),
            '--font-size-base': f'{self.font_size_base}px',
            '--border-radius': f'{self.border_radius}px',
            '--shadow-style': self.get_shadow_css(),
        }

    def get_shadow_css(self):
        """CSS para sombras según estilo"""
        shadows = {
            'none': 'none',
            'subtle': '0 1px 3px rgba(0,0,0,0.1)',
            'medium': '0 2px 8px rgba(0,0,0,0.15)',
            'strong': '0 4px 16px rgba(0,0,0,0.2)',
        }
        return shadows.get(self.shadow_style, shadows['subtle'])
```

## 2. 🎨 INTERFAZ AVANZADA DE PERSONALIZACIÓN

### Template Settings Expandido

```html
<!-- templates/settings/company_settings_advanced.html -->
<div class="branding-customization">
    <!-- Tab de Personalización Avanzada -->
    <div class="tab-pane" id="advanced-customization">
        <div class="row">
            <!-- Paleta de Colores Completa -->
            <div class="col-md-6">
                <h5>🎨 Paleta de Colores</h5>
                <div class="color-palette-grid">
                    <div class="color-input-group">
                        <label>Color Primario</label>
                        <input type="color" name="primary_color" class="color-picker">
                        <span class="color-preview" data-color="primary"></span>
                    </div>
                    <div class="color-input-group">
                        <label>Color Secundario</label>
                        <input type="color" name="secondary_color" class="color-picker">
                        <span class="color-preview" data-color="secondary"></span>
                    </div>
                    <div class="color-input-group">
                        <label>Color de Acento</label>
                        <input type="color" name="accent_color" class="color-picker">
                        <span class="color-preview" data-color="accent"></span>
                    </div>
                    <div class="color-input-group">
                        <label>Color de Fondo</label>
                        <input type="color" name="background_color" class="color-picker">
                        <span class="color-preview" data-color="background"></span>
                    </div>
                    <div class="color-input-group">
                        <label>Color de Texto</label>
                        <input type="color" name="text_color" class="color-picker">
                        <span class="color-preview" data-color="text"></span>
                    </div>
                </div>

                <!-- Paletas Predefinidas -->
                <div class="preset-palettes">
                    <h6>Paletas Predefinidas</h6>
                    <div class="palette-options">
                        <div class="palette-option" data-palette="corporate">
                            <span class="palette-name">Corporativo</span>
                            <div class="palette-colors">
                                <span style="background: #1565c0"></span>
                                <span style="background: #424242"></span>
                                <span style="background: #ff9800"></span>
                            </div>
                        </div>
                        <div class="palette-option" data-palette="modern">
                            <span class="palette-name">Moderno</span>
                            <div class="palette-colors">
                                <span style="background: #6366f1"></span>
                                <span style="background: #ec4899"></span>
                                <span style="background: #10b981"></span>
                            </div>
                        </div>
                        <div class="palette-option" data-palette="automotive">
                            <span class="palette-name">Automotriz</span>
                            <div class="palette-colors">
                                <span style="background: #d32f2f"></span>
                                <span style="background: #212121"></span>
                                <span style="background: #ffc107"></span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Tipografía -->
            <div class="col-md-6">
                <h5>🔤 Tipografía</h5>
                <div class="typography-controls">
                    <div class="form-group">
                        <label>Familia Tipográfica</label>
                        <select name="font_family" class="form-control font-selector">
                            <option value="system">Sistema (Default)</option>
                            <option value="roboto">Roboto (Moderna)</option>
                            <option value="open-sans">Open Sans (Limpia)</option>
                            <option value="lato">Lato (Profesional)</option>
                            <option value="montserrat">Montserrat (Elegante)</option>
                            <option value="poppins">Poppins (Amigable)</option>
                        </select>
                        <div class="font-preview">
                            <p class="preview-text">Su empresa automotriz de confianza</p>
                        </div>
                    </div>

                    <div class="form-group">
                        <label>Tamaño Base</label>
                        <div class="size-slider">
                            <input type="range" name="font_size_base" min="12" max="18" value="14">
                            <span class="size-display">14px</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Estilo Visual -->
        <div class="row mt-4">
            <div class="col-md-6">
                <h5>🎯 Estilo Visual</h5>
                <div class="visual-style-controls">
                    <div class="form-group">
                        <label>Bordes Redondeados</label>
                        <div class="radius-slider">
                            <input type="range" name="border_radius" min="0" max="20" value="4">
                            <span class="radius-display">4px</span>
                            <div class="radius-preview"></div>
                        </div>
                    </div>

                    <div class="form-group">
                        <label>Estilo de Sombras</label>
                        <div class="shadow-options">
                            <label class="shadow-option">
                                <input type="radio" name="shadow_style" value="none">
                                <span class="shadow-preview shadow-none">Sin sombras</span>
                            </label>
                            <label class="shadow-option">
                                <input type="radio" name="shadow_style" value="subtle">
                                <span class="shadow-preview shadow-subtle">Sutiles</span>
                            </label>
                            <label class="shadow-option">
                                <input type="radio" name="shadow_style" value="medium">
                                <span class="shadow-preview shadow-medium">Medianas</span>
                            </label>
                            <label class="shadow-option">
                                <input type="radio" name="shadow_style" value="strong">
                                <span class="shadow-preview shadow-strong">Marcadas</span>
                            </label>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Preview en Tiempo Real -->
            <div class="col-md-6">
                <h5>👁️ Vista Previa</h5>
                <div class="live-preview-container">
                    <div class="preview-frame" id="advanced-preview">
                        <div class="preview-header">
                            <img src="" alt="Logo" class="preview-logo">
                            <span class="preview-company-name">Nombre Empresa</span>
                        </div>
                        <div class="preview-content">
                            <div class="preview-card">
                                <h6>Ejemplo de Tarjeta</h6>
                                <p>Texto de ejemplo con la tipografía seleccionada</p>
                                <button class="preview-button">Botón Ejemplo</button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>

<script>
// JavaScript para preview en tiempo real
document.addEventListener('DOMContentLoaded', function() {
    const colorPickers = document.querySelectorAll('.color-picker');
    const fontSelector = document.querySelector('.font-selector');
    const sizeSlider = document.querySelector('input[name="font_size_base"]');
    const radiusSlider = document.querySelector('input[name="border_radius"]');
    const shadowOptions = document.querySelectorAll('input[name="shadow_style"]');

    function updatePreview() {
        const preview = document.getElementById('advanced-preview');
        const styles = {
            '--primary-color': document.querySelector('[name="primary_color"]').value,
            '--secondary-color': document.querySelector('[name="secondary_color"]').value,
            '--accent-color': document.querySelector('[name="accent_color"]').value,
            '--background-color': document.querySelector('[name="background_color"]').value,
            '--text-color': document.querySelector('[name="text_color"]').value,
            '--font-family': getFontFamily(fontSelector.value),
            '--font-size-base': sizeSlider.value + 'px',
            '--border-radius': radiusSlider.value + 'px',
            '--shadow-style': getShadowStyle(),
        };

        Object.entries(styles).forEach(([prop, value]) => {
            preview.style.setProperty(prop, value);
        });
    }

    // Event listeners para actualización en tiempo real
    colorPickers.forEach(picker => picker.addEventListener('input', updatePreview));
    fontSelector.addEventListener('change', updatePreview);
    sizeSlider.addEventListener('input', updatePreview);
    radiusSlider.addEventListener('input', updatePreview);
    shadowOptions.forEach(option => option.addEventListener('change', updatePreview));

    // Paletas predefinidas
    document.querySelectorAll('.palette-option').forEach(option => {
        option.addEventListener('click', function() {
            const palette = this.dataset.palette;
            applyPalette(palette);
            updatePreview();
        });
    });
});
</script>
```

## 3. 📄 TESTING CROSS-BROWSER Y PDF

### Suite de Tests para PDFs

```python
# tests/test_pdf_cross_platform.py
import os
import base64
from io import BytesIO
from PIL import Image, ImageChops
from django.test import TestCase, Client
from django.contrib.auth.models import User
from taller.models import CompanySettings, Documento
from taller.utils.pdf_generator import DocumentoPDFGenerator

class PDFCrossPlatformTest(TestCase):
    """Tests para verificar PDFs en diferentes navegadores y dispositivos"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='test_pdf',
            password='test123'
        )
        self.company_settings = CompanySettings.objects.create(
            user=self.user,
            company_name='Test Auto Repair',
            primary_color='#e74c3c',
            secondary_color='#3498db'
        )

        # Logo de prueba (base64)
        self.test_logo = self._create_test_logo()
        self.company_settings.logo = self.test_logo
        self.company_settings.save()

    def _create_test_logo(self):
        """Crea logo de prueba para testing"""
        # Crear imagen de prueba 200x100px
        img = Image.new('RGB', (200, 100), color='#e74c3c')
        # Agregar texto simulado
        # En producción usarías PIL.ImageDraw para agregar texto

        buffer = BytesIO()
        img.save(buffer, format='PNG')
        return base64.b64encode(buffer.getvalue()).decode()

    def test_pdf_logo_scaling(self):
        """Test que logos se escalen correctamente en PDF"""
        documento = self._create_test_document()
        generator = DocumentoPDFGenerator(documento)

        # Generar PDF con diferentes tamaños de logo
        logo_sizes = [
            (50, 25),   # Pequeño
            (100, 50),  # Mediano
            (200, 100), # Grande
            (400, 200), # Extra grande
        ]

        for width, height in logo_sizes:
            with self.subTest(size=f"{width}x{height}"):
                # Redimensionar logo
                resized_logo = self._resize_logo(width, height)
                self.company_settings.logo = resized_logo
                self.company_settings.save()

                # Generar PDF
                pdf_content = generator.generate()
                self.assertIsNotNone(pdf_content)
                self.assertGreater(len(pdf_content), 1000)  # PDF mínimo

                # Verificar que PDF sea válido
                self.assertTrue(pdf_content.startswith(b'%PDF'))

    def test_pdf_color_consistency(self):
        """Test que colores se reproduzcan correctamente"""
        test_colors = [
            '#ff0000',  # Rojo puro
            '#00ff00',  # Verde puro
            '#0000ff',  # Azul puro
            '#ffffff',  # Blanco
            '#000000',  # Negro
            '#cccccc',  # Gris claro
            '#333333',  # Gris oscuro
        ]

        documento = self._create_test_document()

        for color in test_colors:
            with self.subTest(color=color):
                self.company_settings.primary_color = color
                self.company_settings.save()

                generator = DocumentoPDFGenerator(documento)
                pdf_content = generator.generate()

                # Verificar que PDF se genere sin errores
                self.assertIsNotNone(pdf_content)
                # En un test más avanzado, podrías analizar el contenido PDF
                # para verificar que los colores estén presentes

    def test_pdf_font_rendering(self):
        """Test renderizado de diferentes fuentes"""
        fonts = ['roboto', 'open-sans', 'lato', 'montserrat']
        documento = self._create_test_document()

        for font in fonts:
            with self.subTest(font=font):
                self.company_settings.font_family = font
                self.company_settings.save()

                generator = DocumentoPDFGenerator(documento)
                pdf_content = generator.generate()

                self.assertIsNotNone(pdf_content)
                self.assertGreater(len(pdf_content), 1000)

    def test_pdf_responsive_layout(self):
        """Test que layout se adapte a diferentes tamaños"""
        page_sizes = [
            ('letter', 'Carta US'),
            ('a4', 'A4 Internacional'),
            ('legal', 'Legal US'),
        ]

        documento = self._create_test_document()

        for size_code, size_name in page_sizes:
            with self.subTest(size=size_name):
                generator = DocumentoPDFGenerator(
                    documento,
                    page_size=size_code
                )
                pdf_content = generator.generate()

                self.assertIsNotNone(pdf_content)
                # Verificar que el tamaño afecte el contenido
                self.assertGreater(len(pdf_content), 1000)

    def _create_test_document(self):
        """Crea documento de prueba"""
        # Aquí crearías un documento con datos de prueba
        # Simulando la estructura de tus documentos reales
        pass

    def _resize_logo(self, width, height):
        """Redimensiona logo para testing"""
        # Decodificar logo actual
        logo_data = base64.b64decode(self.company_settings.logo)
        img = Image.open(BytesIO(logo_data))

        # Redimensionar
        img_resized = img.resize((width, height), Image.Resampling.LANCZOS)

        # Convertir de vuelta a base64
        buffer = BytesIO()
        img_resized.save(buffer, format='PNG')
        return base64.b64encode(buffer.getvalue()).decode()


class PDFBrowserCompatibilityTest(TestCase):
    """Tests para compatibilidad entre navegadores"""

    def test_pdf_download_headers(self):
        """Test headers correctos para descarga en navegadores"""
        client = Client()
        user = User.objects.create_user('test', 'test@test.com', 'test123')
        client.force_login(user)

        # Crear documento de prueba
        documento = self._create_test_document()

        # Test descarga PDF
        response = client.get(f'/documentos/{documento.id}/pdf/')

        # Verificar headers
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn('attachment', response['Content-Disposition'])
        self.assertIn('filename=', response['Content-Disposition'])

        # Verificar contenido
        self.assertGreater(len(response.content), 1000)
        self.assertTrue(response.content.startswith(b'%PDF'))

    def test_pdf_inline_display(self):
        """Test visualización inline en navegadores"""
        client = Client()
        user = User.objects.create_user('test2', 'test2@test.com', 'test123')
        client.force_login(user)

        documento = self._create_test_document()

        # Test visualización inline
        response = client.get(f'/documentos/{documento.id}/preview/')

        # Headers para visualización
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn('inline', response['Content-Disposition'])
```

## 4. 📤 SISTEMA IMPORT/EXPORT DE CONFIGURACIÓN

### API Endpoints para Import/Export

```python
# taller/views/branding_api_views.py
import json
import uuid
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.core.serializers import serialize
from django.core.files.base import ContentFile
from taller.models import CompanySettings

@login_required
def export_branding_config(request):
    """Exporta configuración de branding del usuario"""
    try:
        settings = CompanySettings.objects.get(user=request.user)

        # Preparar datos para exportación
        export_data = {
            'version': '1.0',
            'export_date': timezone.now().isoformat(),
            'company_info': {
                'company_name': settings.company_name,
                'tagline': settings.tagline,
                'address': settings.address,
                'phone': settings.phone,
                'email': settings.email,
                'website': settings.website,
            },
            'branding': {
                'primary_color': settings.primary_color,
                'secondary_color': settings.secondary_color,
                'accent_color': settings.accent_color,
                'background_color': settings.background_color,
                'text_color': settings.text_color,
                'font_family': settings.font_family,
                'font_size_base': settings.font_size_base,
                'border_radius': settings.border_radius,
                'shadow_style': settings.shadow_style,
            },
            'localization': {
                'address_cl': settings.address_cl,
                'address_us': settings.address_us,
                'phone_cl': settings.phone_cl,
                'phone_us': settings.phone_us,
                'currency': settings.currency,
                'timezone': settings.timezone,
            },
            'document_settings': {
                'invoice_prefix': settings.invoice_prefix,
                'quote_prefix': settings.quote_prefix,
                'work_order_prefix': settings.work_order_prefix,
                'terms_conditions': settings.terms_conditions,
            }
        }

        # Incluir logo si existe
        if settings.logo:
            # Convertir logo a base64 para portabilidad
            with settings.logo.open('rb') as logo_file:
                logo_data = base64.b64encode(logo_file.read()).decode()
                export_data['logo_data'] = logo_data
                export_data['logo_filename'] = settings.logo.name

        # Generar respuesta JSON
        filename = f"egarage_branding_{request.user.username}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.json"
        response = HttpResponse(
            json.dumps(export_data, indent=2, ensure_ascii=False),
            content_type='application/json'
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        return response

    except CompanySettings.DoesNotExist:
        return JsonResponse({
            'error': 'No se encontró configuración de branding'
        }, status=404)

@login_required
@csrf_exempt
def import_branding_config(request):
    """Importa configuración de branding"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)

    try:
        # Verificar si se subió archivo
        if 'config_file' not in request.FILES:
            return JsonResponse({
                'error': 'No se proporcionó archivo de configuración'
            }, status=400)

        config_file = request.FILES['config_file']

        # Verificar formato JSON
        if not config_file.name.endswith('.json'):
            return JsonResponse({
                'error': 'El archivo debe ser formato JSON'
            }, status=400)

        # Leer y parsear archivo
        try:
            config_data = json.loads(config_file.read().decode('utf-8'))
        except json.JSONDecodeError:
            return JsonResponse({
                'error': 'Archivo JSON inválido'
            }, status=400)

        # Validar estructura
        required_sections = ['company_info', 'branding', 'localization', 'document_settings']
        if not all(section in config_data for section in required_sections):
            return JsonResponse({
                'error': 'Estructura de configuración inválida'
            }, status=400)

        # Obtener o crear configuración
        settings, created = CompanySettings.objects.get_or_create(
            user=request.user
        )

        # Aplicar configuración de empresa
        company_info = config_data['company_info']
        settings.company_name = company_info.get('company_name', settings.company_name)
        settings.tagline = company_info.get('tagline', settings.tagline)
        settings.address = company_info.get('address', settings.address)
        settings.phone = company_info.get('phone', settings.phone)
        settings.email = company_info.get('email', settings.email)
        settings.website = company_info.get('website', settings.website)

        # Aplicar branding
        branding = config_data['branding']
        settings.primary_color = branding.get('primary_color', settings.primary_color)
        settings.secondary_color = branding.get('secondary_color', settings.secondary_color)
        settings.accent_color = branding.get('accent_color', settings.accent_color)
        settings.background_color = branding.get('background_color', settings.background_color)
        settings.text_color = branding.get('text_color', settings.text_color)
        settings.font_family = branding.get('font_family', settings.font_family)
        settings.font_size_base = branding.get('font_size_base', settings.font_size_base)
        settings.border_radius = branding.get('border_radius', settings.border_radius)
        settings.shadow_style = branding.get('shadow_style', settings.shadow_style)

        # Aplicar localización
        localization = config_data['localization']
        settings.address_cl = localization.get('address_cl', settings.address_cl)
        settings.address_us = localization.get('address_us', settings.address_us)
        settings.phone_cl = localization.get('phone_cl', settings.phone_cl)
        settings.phone_us = localization.get('phone_us', settings.phone_us)
        settings.currency = localization.get('currency', settings.currency)
        settings.timezone = localization.get('timezone', settings.timezone)

        # Aplicar configuración de documentos
        doc_settings = config_data['document_settings']
        settings.invoice_prefix = doc_settings.get('invoice_prefix', settings.invoice_prefix)
        settings.quote_prefix = doc_settings.get('quote_prefix', settings.quote_prefix)
        settings.work_order_prefix = doc_settings.get('work_order_prefix', settings.work_order_prefix)
        settings.terms_conditions = doc_settings.get('terms_conditions', settings.terms_conditions)

        # Procesar logo si existe
        if 'logo_data' in config_data and config_data['logo_data']:
            try:
                logo_data = base64.b64decode(config_data['logo_data'])
                logo_filename = config_data.get('logo_filename', f'imported_logo_{uuid.uuid4().hex}.png')

                # Guardar logo
                settings.logo.save(
                    logo_filename,
                    ContentFile(logo_data),
                    save=False
                )
            except Exception as e:
                # Si falla el logo, continuar con el resto de la configuración
                pass

        # Guardar configuración
        settings.save()

        # Limpiar cache
        cache_key_pattern = f'company_settings_{request.user.id}_*'
        cache.delete_pattern(cache_key_pattern)

        return JsonResponse({
            'success': True,
            'message': 'Configuración importada exitosamente',
            'imported_sections': list(config_data.keys())
        })

    except Exception as e:
        return JsonResponse({
            'error': f'Error al importar configuración: {str(e)}'
        }, status=500)

@login_required
def validate_config_file(request):
    """Valida archivo de configuración antes de importar"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)

    try:
        if 'config_file' not in request.FILES:
            return JsonResponse({
                'error': 'No se proporcionó archivo'
            }, status=400)

        config_file = request.FILES['config_file']
        config_data = json.loads(config_file.read().decode('utf-8'))

        # Validaciones
        validation_results = {
            'valid': True,
            'version': config_data.get('version', 'Desconocida'),
            'export_date': config_data.get('export_date'),
            'sections_found': [],
            'warnings': [],
            'errors': []
        }

        # Verificar secciones requeridas
        required_sections = ['company_info', 'branding', 'localization', 'document_settings']
        for section in required_sections:
            if section in config_data:
                validation_results['sections_found'].append(section)
            else:
                validation_results['errors'].append(f'Sección faltante: {section}')
                validation_results['valid'] = False

        # Verificar logo
        if 'logo_data' in config_data:
            try:
                base64.b64decode(config_data['logo_data'])
                validation_results['logo_status'] = 'Válido'
            except:
                validation_results['warnings'].append('Logo inválido, será omitido')
                validation_results['logo_status'] = 'Inválido'
        else:
            validation_results['logo_status'] = 'No incluido'

        # Verificar colores
        branding = config_data.get('branding', {})
        color_fields = ['primary_color', 'secondary_color', 'accent_color']
        for field in color_fields:
            color = branding.get(field)
            if color and not re.match(r'^#[0-9A-Fa-f]{6}$', color):
                validation_results['warnings'].append(f'Color inválido en {field}: {color}')

        return JsonResponse(validation_results)

    except json.JSONDecodeError:
        return JsonResponse({
            'valid': False,
            'errors': ['Archivo JSON inválido']
        })
    except Exception as e:
        return JsonResponse({
            'valid': False,
            'errors': [f'Error al validar archivo: {str(e)}']
        })
```

### Templates para Import/Export

```html
<!-- templates/settings/import_export.html -->
<div class="import-export-section">
    <div class="row">
        <!-- Export -->
        <div class="col-md-6">
            <div class="card">
                <div class="card-header">
                    <h5>📤 Exportar Configuración</h5>
                </div>
                <div class="card-body">
                    <p class="text-muted">
                        Descarga tu configuración de branding completa para respaldo o transferencia.
                    </p>

                    <div class="export-options">
                        <div class="form-check">
                            <input class="form-check-input" type="checkbox" id="export_logo" checked>
                            <label class="form-check-label" for="export_logo">
                                Incluir logo
                            </label>
                        </div>
                        <div class="form-check">
                            <input class="form-check-input" type="checkbox" id="export_colors" checked>
                            <label class="form-check-label" for="export_colors">
                                Incluir paleta de colores
                            </label>
                        </div>
                        <div class="form-check">
                            <input class="form-check-input" type="checkbox" id="export_typography" checked>
                            <label class="form-check-label" for="export_typography">
                                Incluir configuración tipográfica
                            </label>
                        </div>
                    </div>

                    <button class="btn btn-primary mt-3" id="export_config_btn">
                        <i class="fas fa-download"></i> Exportar Configuración
                    </button>
                </div>
            </div>
        </div>

        <!-- Import -->
        <div class="col-md-6">
            <div class="card">
                <div class="card-header">
                    <h5>📥 Importar Configuración</h5>
                </div>
                <div class="card-body">
                    <p class="text-muted">
                        Importa una configuración de branding desde un archivo exportado.
                    </p>

                    <div class="import-zone" id="import_dropzone">
                        <div class="dropzone-content">
                            <i class="fas fa-cloud-upload-alt fa-3x text-muted"></i>
                            <p class="mt-2">Arrastra tu archivo aquí o haz clic para seleccionar</p>
                            <small class="text-muted">Formatos soportados: .json</small>
                        </div>
                        <input type="file" id="config_file_input" accept=".json" style="display: none;">
                    </div>

                    <div class="validation-results mt-3" id="validation_results" style="display: none;">
                        <!-- Resultados de validación aparecerán aquí -->
                    </div>

                    <div class="import-actions mt-3" style="display: none;" id="import_actions">
                        <button class="btn btn-success" id="confirm_import_btn">
                            <i class="fas fa-check"></i> Confirmar Importación
                        </button>
                        <button class="btn btn-secondary" id="cancel_import_btn">
                            Cancelar
                        </button>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>

<script>
// JavaScript para funcionalidad import/export
document.addEventListener('DOMContentLoaded', function() {
    // Export functionality
    document.getElementById('export_config_btn').addEventListener('click', function() {
        const options = {
            include_logo: document.getElementById('export_logo').checked,
            include_colors: document.getElementById('export_colors').checked,
            include_typography: document.getElementById('export_typography').checked,
        };

        // Crear URL con parámetros
        const params = new URLSearchParams(options);
        window.location.href = `/api/branding/export/?${params}`;
    });

    // Import functionality
    const dropzone = document.getElementById('import_dropzone');
    const fileInput = document.getElementById('config_file_input');

    dropzone.addEventListener('click', () => fileInput.click());

    dropzone.addEventListener('dragover', function(e) {
        e.preventDefault();
        this.classList.add('dragover');
    });

    dropzone.addEventListener('dragleave', function(e) {
        this.classList.remove('dragover');
    });

    dropzone.addEventListener('drop', function(e) {
        e.preventDefault();
        this.classList.remove('dragover');

        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFileSelection(files[0]);
        }
    });

    fileInput.addEventListener('change', function(e) {
        if (e.target.files.length > 0) {
            handleFileSelection(e.target.files[0]);
        }
    });

    function handleFileSelection(file) {
        // Validar archivo
        validateConfigFile(file);
    }

    function validateConfigFile(file) {
        const formData = new FormData();
        formData.append('config_file', file);

        fetch('/api/branding/validate/', {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            }
        })
        .then(response => response.json())
        .then(data => {
            displayValidationResults(data);
            if (data.valid) {
                document.getElementById('import_actions').style.display = 'block';
            }
        })
        .catch(error => {
            console.error('Error validating file:', error);
            showError('Error al validar archivo');
        });
    }

    function displayValidationResults(results) {
        const container = document.getElementById('validation_results');
        container.innerHTML = '';
        container.style.display = 'block';

        if (results.valid) {
            container.innerHTML = `
                <div class="alert alert-success">
                    <h6>✅ Archivo válido</h6>
                    <ul class="mb-0">
                        <li>Versión: ${results.version}</li>
                        <li>Fecha exportación: ${results.export_date || 'No especificada'}</li>
                        <li>Secciones encontradas: ${results.sections_found.join(', ')}</li>
                        <li>Logo: ${results.logo_status}</li>
                    </ul>
                </div>
            `;

            if (results.warnings.length > 0) {
                container.innerHTML += `
                    <div class="alert alert-warning">
                        <h6>⚠️ Advertencias</h6>
                        <ul class="mb-0">
                            ${results.warnings.map(w => `<li>${w}</li>`).join('')}
                        </ul>
                    </div>
                `;
            }
        } else {
            container.innerHTML = `
                <div class="alert alert-danger">
                    <h6>❌ Archivo inválido</h6>
                    <ul class="mb-0">
                        ${results.errors.map(e => `<li>${e}</li>`).join('')}
                    </ul>
                </div>
            `;
        }
    }
});
</script>
```

## 🎯 PLAN DE IMPLEMENTACIÓN EMPRESARIAL

### Fase 1: Integración Multilenguaje (2-3 horas)
1. ✅ Crear context processor unificado
2. ✅ Extender modelo CompanySettings con campos avanzados
3. ✅ Actualizar templates base con variables CSS dinámicas
4. ✅ Tests de integración multilenguaje + branding

### Fase 2: Personalización Avanzada (3-4 horas)
1. ✅ Interfaz de personalización completa
2. ✅ Paletas predefinidas y custom
3. ✅ Preview en tiempo real avanzado
4. ✅ Validaciones de contraste y accesibilidad

### Fase 3: Testing Cross-Platform (2-3 horas)
1. ✅ Suite de tests PDF cross-browser
2. ✅ Tests de scaling y responsive
3. ✅ Validación colores y tipografías
4. ✅ Performance testing

### Fase 4: Import/Export (2-3 horas)
1. ✅ API endpoints para import/export
2. ✅ Validación de archivos de configuración
3. ✅ Interfaz drag & drop
4. ✅ Backup automático antes de import

**¿Quieres que implemente alguna de estas mejoras enterprise ahora? Con esto quedas con un sistema de branding verdaderamente profesional y escalable.** 🚀
