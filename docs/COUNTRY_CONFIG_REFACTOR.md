# 🌍 Refactorización: Sistema de Configuración Centralizada de Países

**Fecha:** Diciembre 2024  
**Versión:** 1.0  
**Estado:** ✅ Implementado

---

## 📋 Resumen

Se ha implementado un sistema de **"Configuration over Code"** para soportar 8 países (CL, US, MX, PE, CO, EC, BR, VE) sin necesidad de usar `if/elif` en todo el código.

---

## 🎯 Objetivo

Eliminar la lógica hardcodeada de países y centralizar toda la configuración en un solo lugar, facilitando:
- Agregar nuevos países sin tocar múltiples archivos
- Mantener consistencia en formateo de monedas, impuestos y decimales
- Facilitar testing y debugging
- Reducir errores por inconsistencias

---

## 📁 Archivos Creados/Modificados

### Nuevo Archivo Principal

**`taller/utils/country_config.py`**
- Configuración centralizada de los 8 países
- Funciones helper para obtener configuración
- Formateo de monedas unificado

### Archivos Refactorizados

1. **`taller/models/documento.py`**
   - `vat_percent()`: Ahora usa `get_config_from_documento()`
   - `_decimals()`: Ahora usa `get_config_from_documento()`

2. **`taller/models/utils_monedas.py`**
   - `money_quantize()`: Ahora usa `get_currency_decimals()`

3. **`taller/templatetags/money.py`**
   - `money_by_country()`: Ahora usa `format_currency()`

4. **`taller/templatetags/custom_filters.py`**
   - `currency_format()`: Ahora usa `format_currency()`

5. **`taller/utils/pais_utils.py`**
   - `get_configuracion_pais()`: Ahora usa `get_config_from_empresa()`

6. **`taller/config/country_settings.py`**
   - Agregados los 5 países faltantes (PE, CO, EC, BR, VE)

---

## 🔧 Uso del Sistema

### Obtener Configuración de un País

```python
from taller.utils.country_config import get_country_config

# Obtener configuración completa
config = get_country_config('PE')
print(config['currency'])  # 'PEN'
print(config['decimals'])  # 2
print(config['tax_rate'])  # 18.0
print(config['tax_name'])  # 'IGV'
```

### Obtener Configuración desde Empresa

```python
from taller.utils.country_config import get_config_from_empresa

config = get_config_from_empresa(empresa)
# Retorna configuración del país de la empresa
```

### Obtener Configuración desde Documento

```python
from taller.utils.country_config import get_config_from_documento

config = get_config_from_documento(documento)
# Retorna configuración del país del documento
```

### Formatear Moneda

```python
from taller.utils.country_config import format_currency

# Formatear según país
format_currency(1234.56, 'CL')  # '$1.235'
format_currency(1234.56, 'US')  # '$1,234.56'
format_currency(1234.56, 'PE')  # 'S/ 1,234.56'
format_currency(1234.56, 'BR')  # 'R$ 1,234.56'
```

### Obtener Propiedades Específicas

```python
from taller.utils.country_config import (
    get_currency_decimals,
    get_tax_rate,
    get_tax_name,
    get_currency_symbol,
    get_locale
)

decimals = get_currency_decimals('PE')  # 2
tax_rate = get_tax_rate('CO')  # 19.0
tax_name = get_tax_name('BR')  # 'ICMS'
symbol = get_currency_symbol('EC')  # '$'
locale = get_locale('BR')  # 'pt-BR'
```

---

## 📊 Configuración por País

| País | Moneda | Decimales | Impuesto | Nombre Impuesto | Idioma | Locale |
|------|--------|-----------|----------|----------------|--------|--------|
| CL | CLP | 0 | 19.0% | IVA | es | es-CL |
| US | USD | 2 | 0.0%* | Sales Tax | en | en-US |
| MX | MXN | 2 | 16.0% | IVA | es | es-MX |
| PE | PEN | 2 | 18.0% | IGV | es | es-PE |
| CO | COP | 0 | 19.0% | IVA | es | es-CO |
| EC | USD | 2 | 12.0% | IVA | es | es-EC |
| BR | BRL | 2 | 0.0%* | ICMS | pt-br | pt-BR |
| VE | USD | 2 | 16.0% | IVA | es | es-VE |

*Nota: US y BR tienen impuestos que varían por estado, se calculan dinámicamente.

---

## 🔄 Migración de Código Existente

### Antes (Hardcoded)

```python
# ❌ MAL: Lógica hardcodeada
if pais == "CL":
    decimals = 0
    tax_rate = 19.0
elif pais == "US":
    decimals = 2
    tax_rate = 0.0
elif pais == "MX":
    decimals = 2
    tax_rate = 16.0
# ... más países ...
```

### Después (Configuration over Code)

```python
# ✅ BIEN: Usar configuración centralizada
from taller.utils.country_config import get_country_config

config = get_country_config(pais)
decimals = config['decimals']
tax_rate = config['tax_rate']
```

---

## 🎨 Uso en Templates

### Antes

```django
{% if empresa.pais == "CL" %}
    {{ value|floatformat:0 }}
{% elif empresa.pais == "US" %}
    {{ value|floatformat:2 }}
{% endif %}
```

### Después

```django
{{ value|money_by_country:empresa.pais }}
```

O usando el filter mejorado:

```django
{{ value|currency_format:empresa.pais }}
```

---

## 🧪 Testing

### Ejemplo de Test

```python
from taller.utils.country_config import get_country_config, format_currency

def test_peru_config():
    config = get_country_config('PE')
    assert config['currency'] == 'PEN'
    assert config['decimals'] == 2
    assert config['tax_rate'] == 18.0
    assert config['tax_name'] == 'IGV'

def test_currency_formatting():
    assert format_currency(1234.56, 'CL') == '$1.235'
    assert format_currency(1234.56, 'US') == '$1,234.56'
    assert format_currency(1234.56, 'PE') == 'S/ 1,234.56'
```

---

## 🚀 Próximos Pasos

### 1. Refactorizar Código Restante

Buscar y reemplazar todos los `if pais == "CL"` o similares en:
- Vistas
- Formularios
- APIs
- Scripts de migración

### 2. Agregar Tests

Crear tests unitarios para:
- Configuración de cada país
- Formateo de monedas
- Cálculo de impuestos

### 3. Documentar Casos Especiales

- **Brasil (BR)**: ICMS varía por estado, requiere lógica adicional
- **Venezuela (VE)**: Soporte para moneda dual (USD/VES)
- **Ecuador (EC)**: Usa USD pero con textos en español

### 4. Internacionalización (i18n)

Para Brasil, necesitarás:
- Instalar `django-rosetta` o compilar archivos `.po`
- Traducir templates y mensajes al portugués
- Configurar `LANGUAGE_CODE` y `LANGUAGES` en settings

---

## 📝 Notas Importantes

### Casos Especiales

1. **Brasil (BR)**
   - Idioma: Portugués (pt-br)
   - Impuesto: ICMS varía por estado (0% por defecto, calcular dinámicamente)
   - Formato de fecha: DD/MM/YYYY (igual que otros países LATAM)

2. **Ecuador (EC)**
   - Moneda: USD (dólares americanos)
   - Idioma: Español
   - Puede reutilizar lógica financiera de USA pero con textos en español

3. **Venezuela (VE)**
   - Moneda: USD (dolarizado de facto)
   - Considerar agregar soporte para moneda secundaria (VES) en el futuro
   - Campo `supports_dual_currency: True` en configuración

### Compatibilidad

El sistema es **backward compatible**. El código existente seguirá funcionando, pero se recomienda migrar gradualmente a usar `country_config.py`.

---

## ✅ Checklist de Migración

- [x] Crear `country_config.py` con configuración de 8 países
- [x] Refactorizar `Documento.vat_percent()`
- [x] Refactorizar `Documento._decimals()`
- [x] Actualizar `money_quantize()`
- [x] Actualizar template filters
- [x] Actualizar `get_configuracion_pais()`
- [x] Agregar países a `country_settings.py`
- [ ] Buscar y refactorizar otros lugares con lógica hardcodeada
- [ ] Agregar tests unitarios
- [ ] Documentar casos especiales (BR, EC, VE)
- [ ] Configurar i18n para portugués (Brasil)

---

**Última actualización:** Diciembre 2024  
**Autor:** Sistema de Refactorización eGarage



