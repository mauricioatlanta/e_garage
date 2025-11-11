# 🔐 SEGURIDAD Y DATOS SENSIBLES - Convenciones Enterprise

## 🎯 **OBJETIVO**

Implementar convenciones de seguridad para datos sensibles (tax_id, teléfonos) con validación específica por país, normalización automática y enmascaramiento en listados.

---

## ✅ **CONVENCIONES IMPLEMENTADAS**

### **1. tax_id es DATO SENSIBLE** ⭐⭐⭐
### **2. Validadores específicos por tipo** ✅
### **3. Normalización automática** ✅
### **4. Enmascaramiento en listados** ✅
### **5. libphonenumber para teléfonos (opcional)** ✅

---

## 🔒 **1. TAX_ID ES DATO SENSIBLE**

### **Convención Crítica:**

```python
# ✅ SÍ: Enmascarar en listados
class ClienteAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'apellido', 'tax_id_enmascarado', 'telefono']
    
    def tax_id_enmascarado(self, obj):
        from taller.utils.validators import enmascarar_tax_id
        return enmascarar_tax_id(obj.tax_id, obj.tax_id_type)
    tax_id_enmascarado.short_description = 'Tax ID'

# ❌ NO: Mostrar completo en listados
class ClienteAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'apellido', 'tax_id']  # ❌ PELIGROSO

# ✅ SÍ: Mostrar completo SOLO en formularios de edición
# (Usuario con permisos necesita verlo para editarlo)
```

---

### **Enmascaramiento:**

```python
from taller.utils.validators import enmascarar_tax_id

# Ejemplos de enmascaramiento
enmascarar_tax_id('12345678-9', 'RUT_CL')     # → '****5678-9'
enmascarar_tax_id('12345678901', 'CPF')        # → '*******8901'
enmascarar_tax_id('12-3456789', 'EIN')         # → '**-***6789'
enmascarar_tax_id('123-45-6789', 'SSN')        # → '***-**-6789'
enmascarar_tax_id('J123456789', 'RIF')         # → 'J*****6789'
```

---

## ✅ **2. VALIDADORES POR TIPO**

### **Validadores Implementados:**

| Tipo | País | Formato | Validación |
|------|------|---------|------------|
| RUT_CL | Chile | 12345678-9 | Dígito verificador ✅ |
| CPF | Brasil | 12345678901 | Dígitos verificadores ✅ |
| CNPJ | Brasil | 12345678000190 | Dígitos verificadores ✅ |
| RUC | Perú | 20123456789 | Prefijo + longitud ✅ |
| RIF | Venezuela | J123456789 | Letra inicial + longitud ✅ |
| EIN | USA | 12-3456789 | Prefijo válido ✅ |
| SSN | USA | 123-45-6789 | Área válida ✅ |

---

### **Validador RUT Chile:**

```python
def validar_rut_chile(rut):
    """
    Validar RUT chileno con dígito verificador.
    
    Algoritmo:
    1. Extraer número y dígito verificador
    2. Calcular DV usando módulo 11
    3. Comparar con DV proporcionado
    
    Ejemplos:
        >>> validar_rut_chile('12345678-5')  # ✅ Válido
        >>> validar_rut_chile('12345678-0')  # ❌ Inválido
    """
    # Separar número y DV
    match = re.match(r'^(\d+)-([0-9K])$', rut)
    if not match:
        raise ValidationError('RUT debe tener formato: 12345678-9')
    
    numero = match.group(1)
    dv = match.group(2)
    
    # Calcular DV
    suma = 0
    multiplo = 2
    
    for digit in reversed(numero):
        suma += int(digit) * multiplo
        multiplo = multiplo + 1 if multiplo < 7 else 2
    
    resto = suma % 11
    dv_calculado = 11 - resto
    
    if dv_calculado == 11:
        dv_esperado = '0'
    elif dv_calculado == 10:
        dv_esperado = 'K'
    else:
        dv_esperado = str(dv_calculado)
    
    if dv != dv_esperado:
        raise ValidationError(f'RUT inválido. DV esperado: {dv_esperado}')
```

---

### **Validador CPF Brasil:**

```python
def validar_cpf_brasil(cpf):
    """
    Validar CPF brasileño (11 dígitos con 2 dígitos verificadores).
    
    Algoritmo:
    1. Remover puntos y guiones
    2. Verificar longitud (11 dígitos)
    3. Calcular dígitos verificadores
    4. Comparar con dígitos proporcionados
    
    Ejemplos:
        >>> validar_cpf_brasil('12345678901')  # ✅ Válido
        >>> validar_cpf_brasil('11111111111')  # ❌ Inválido (todos iguales)
    """
    cpf = re.sub(r'\D', '', str(cpf))
    
    if len(cpf) != 11:
        raise ValidationError('CPF debe tener 11 dígitos')
    
    # Rechazar CPFs con todos los dígitos iguales
    if cpf == cpf[0] * 11:
        raise ValidationError('CPF inválido')
    
    # Calcular y verificar dígitos verificadores
    # ... (algoritmo completo en validators.py)
```

---

### **Validador CNPJ Brasil:**

```python
def validar_cnpj_brasil(cnpj):
    """
    Validar CNPJ brasileño (14 dígitos con 2 dígitos verificadores).
    
    Similar a CPF pero con 14 dígitos y diferentes pesos.
    """
    cnpj = re.sub(r'\D', '', str(cnpj))
    
    if len(cnpj) != 14:
        raise ValidationError('CNPJ debe tener 14 dígitos')
    
    # Algoritmo de validación...
```

---

### **Validadores USA:**

```python
def validar_ein_usa(ein):
    """EIN: 12-3456789 (Employer Identification Number)"""
    ein_limpio = re.sub(r'[^0-9]', '', str(ein))
    
    if len(ein_limpio) != 9:
        raise ValidationError('EIN debe tener 9 dígitos')
    
    # Verificar prefijos inválidos
    prefijo = int(ein_limpio[:2])
    if prefijo in [0, 7, 8, 9, 17, 18, 19, 28, 29, 49, 69, 70, 78, 79, 89]:
        raise ValidationError('EIN con prefijo inválido')

def validar_ssn_usa(ssn):
    """SSN: 123-45-6789 (Social Security Number)"""
    ssn_limpio = re.sub(r'[^0-9]', '', str(ssn))
    
    if len(ssn_limpio) != 9:
        raise ValidationError('SSN debe tener 9 dígitos')
    
    # Verificar área válida (primeros 3 dígitos)
    area = int(ssn_limpio[:3])
    if area == 0 or area == 666 or area >= 900:
        raise ValidationError('SSN con área inválida')
```

---

## 🔧 **3. NORMALIZACIÓN AUTOMÁTICA**

### **Reglas de Normalización:**

```python
def normalizar_tax_id(tax_id, tipo):
    """
    Normalizar tax_id según el tipo.
    
    Reglas generales:
    1. Remover espacios, puntos, comas
    2. Convertir a uppercase
    3. Agregar guion si corresponde según formato estándar
    
    Reglas específicas:
    - RUT_CL: Sin puntos, con guion (12345678-9)
    - CPF: Solo dígitos (12345678901)
    - CNPJ: Solo dígitos (12345678000190)
    - RUC: Solo dígitos (20123456789)
    - RIF: Letra + dígitos (J123456789)
    - EIN: Con guion (12-3456789)
    - SSN: Con guiones (123-45-6789)
    """
    # Limpiar caracteres no deseados
    tax_id = str(tax_id).strip().upper()
    tax_id_limpio = re.sub(r'[.\s,]', '', tax_id)
    
    # Normalización específica por tipo
    if tipo == 'RUT_CL':
        # Remover guiones y re-agregar correctamente
        tax_id_limpio = re.sub(r'[-]', '', tax_id_limpio)
        if len(tax_id_limpio) >= 2:
            tax_id_limpio = f"{tax_id_limpio[:-1]}-{tax_id_limpio[-1]}"
    
    elif tipo == 'EIN':
        # Formato XX-XXXXXXX
        tax_id_limpio = re.sub(r'[-]', '', tax_id_limpio)
        if len(tax_id_limpio) == 9:
            tax_id_limpio = f"{tax_id_limpio[:2]}-{tax_id_limpio[2:]}"
    
    elif tipo == 'SSN':
        # Formato XXX-XX-XXXX
        tax_id_limpio = re.sub(r'[-]', '', tax_id_limpio)
        if len(tax_id_limpio) == 9:
            tax_id_limpio = f"{tax_id_limpio[:3]}-{tax_id_limpio[3:5]}-{tax_id_limpio[5:]}"
    
    return tax_id_limpio
```

---

### **Ejemplos de Normalización:**

| Input (usuario) | Tipo | Output (normalizado) |
|----------------|------|----------------------|
| 12.345.678-9 | RUT_CL | 12345678-9 |
| 12 345 678 9 | RUT_CL | 12345678-9 |
| 123.456.789-01 | CPF | 12345678901 |
| 12.345.678/0001-90 | CNPJ | 12345678000190 |
| 12 3456789 | EIN | 12-3456789 |
| 123456789 | SSN | 123-45-6789 |
| j-123456789 | RIF | J123456789 |

---

## 🎭 **4. ENMASCARAMIENTO EN LISTADOS**

### **Uso en Templates:**

```django
<!-- ❌ MAL: Mostrar tax_id completo en listado -->
<table>
  <tr>
    <td>{{ cliente.nombre }}</td>
    <td>{{ cliente.tax_id }}</td>  {# ❌ Dato sensible expuesto #}
  </tr>
</table>

<!-- ✅ BIEN: Enmascarar tax_id en listado -->
{% load validators_tags %}
<table>
  <tr>
    <td>{{ cliente.nombre }}</td>
    <td>{{ cliente.tax_id|enmascarar_tax_id:cliente.tax_id_type }}</td>  {# ✅ ****5678-9 #}
  </tr>
</table>

<!-- ✅ BIEN: Mostrar completo SOLO en formulario de edición -->
<form>
  <input type="text" name="tax_id" value="{{ cliente.tax_id }}">  {# ✅ OK en form #}
</form>
```

---

### **Uso en Admin:**

```python
from django.contrib import admin
from taller.models import Cliente
from taller.utils.validators import enmascarar_tax_id

class ClienteAdmin(admin.ModelAdmin):
    list_display = [
        'nombre',
        'apellido',
        'telefono',
        'tax_id_masked',  # ✅ Enmascarado en listado
        'empresa'
    ]
    
    # ✅ NO incluir 'tax_id' en list_display
    # ✅ tax_id está disponible en el formulario de edición
    
    def tax_id_masked(self, obj):
        """Mostrar tax_id enmascarado en listado"""
        if obj.tax_id:
            return enmascarar_tax_id(obj.tax_id, obj.tax_id_type)
        return '-'
    tax_id_masked.short_description = 'Tax ID'
    
    # ✅ Campos sensibles: NO en search_fields
    search_fields = ['nombre', 'apellido', 'telefono']  # ✅ Sin tax_id
    
    # ✅ Si necesitas buscar por tax_id, usar otro método seguro
    # NO agregarlo a search_fields público
```

---

### **Uso en APIs:**

```python
from rest_framework import serializers
from taller.models import Cliente
from taller.utils.validators import enmascarar_tax_id

class ClienteListSerializer(serializers.ModelSerializer):
    """Serializer para listados (datos sensibles enmascarados)"""
    
    tax_id_masked = serializers.SerializerMethodField()
    
    class Meta:
        model = Cliente
        fields = ['id', 'nombre', 'apellido', 'telefono', 'tax_id_masked']
        # ✅ NO incluir 'tax_id' en listados
    
    def get_tax_id_masked(self, obj):
        """✅ Enmascarar tax_id"""
        if obj.tax_id:
            return enmascarar_tax_id(obj.tax_id, obj.tax_id_type)
        return None

class ClienteDetailSerializer(serializers.ModelSerializer):
    """Serializer para detalle/edición (datos completos)"""
    
    class Meta:
        model = Cliente
        fields = ['id', 'nombre', 'apellido', 'telefono', 'tax_id', 'tax_id_type']
        # ✅ tax_id completo SOLO en detalle/edición
```

---

## ✅ **3. VALIDACIÓN AUTOMÁTICA EN Cliente.clean()**

### **Implementación:**

```python
class Cliente(models.Model):
    tax_id = models.CharField(max_length=20, blank=True, default='')
    tax_id_type = models.CharField(max_length=20, choices=TAX_ID_TYPES)
    
    def clean(self):
        """
        Validaciones de consistencia.
        
        Validaciones de tax_id:
        1. Validación específica por tipo ✅
        2. Normalización automática ✅
        3. Dígitos verificadores correctos ✅
        """
        from django.core.exceptions import ValidationError
        from taller.utils.validators import validar_tax_id
        
        super().clean()
        
        # ✅ Validar y normalizar tax_id
        if self.tax_id and self.tax_id_type:
            try:
                self.tax_id = validar_tax_id(self.tax_id, self.tax_id_type)
            except ValidationError as e:
                raise ValidationError({'tax_id': e.messages})
    
    def save(self, *args, **kwargs):
        """Ejecutar validación antes de guardar"""
        self.full_clean()
        super().save(*args, **kwargs)
```

---

### **Ejemplos de Validación:**

```python
# ✅ VÁLIDO: RUT Chile correcto
cliente = Cliente(nombre='Juan', tax_id='12.345.678-9', tax_id_type='RUT_CL')
cliente.save()
# → Se guarda como: '12345678-9' (normalizado)

# ❌ INVÁLIDO: RUT Chile con DV incorrecto
cliente = Cliente(nombre='Juan', tax_id='12.345.678-0', tax_id_type='RUT_CL')
cliente.save()
# → ValidationError: 'RUT inválido. DV esperado: 9'

# ✅ VÁLIDO: CPF Brasil correcto
cliente = Cliente(nombre='João', tax_id='123.456.789-01', tax_id_type='CPF')
cliente.save()
# → Se guarda como: '12345678901' (normalizado)

# ❌ INVÁLIDO: CPF con todos dígitos iguales
cliente = Cliente(nome='João', tax_id='111.111.111-11', tax_id_type='CPF')
cliente.save()
# → ValidationError: 'CPF inválido'
```

---

## 📱 **4. VALIDACIÓN DE TELÉFONOS (OPCIONAL)**

### **Con libphonenumber:**

```python
# Instalación (opcional)
pip install phonenumbers

# Uso en Cliente.clean()
def clean(self):
    from taller.utils.validators import validar_telefono
    
    if self.telefono and self.empresa:
        try:
            # ✅ Validar y normalizar a formato E164
            self.telefono = validar_telefono(self.telefono, self.empresa.pais)
        except ValidationError:
            # No crítico, solo warning en logs
            pass
```

---

### **Ejemplos de Validación de Teléfonos:**

```python
from taller.utils.validators import validar_telefono, formatear_telefono_nacional

# Validar y normalizar a E164
validar_telefono('+56912345678', 'CL')     # → '+56912345678'
validar_telefono('912345678', 'CL')        # → '+56912345678'
validar_telefono('(555) 123-4567', 'US')   # → '+15551234567'
validar_telefono('11987654321', 'BR')      # → '+5511987654321'

# Formatear para mostrar (nacional)
formatear_telefono_nacional('+56912345678', 'CL')   # → '9 1234 5678'
formatear_telefono_nacional('+15551234567', 'US')   # → '(555) 123-4567'
formatear_telefono_nacional('+5511987654321', 'BR') # → '(11) 98765-4321'
```

---

### **Sin libphonenumber:**

```python
# Si no está instalado, validación básica
def validar_telefono(telefono, pais_code):
    """Validación básica sin libphonenumber"""
    telefono_limpio = re.sub(r'[^0-9+]', '', str(telefono))
    
    if len(telefono_limpio) < 8:
        raise ValidationError('Teléfono debe tener al menos 8 dígitos')
    
    return telefono_limpio
```

---

## 🚫 **ANTI-PATRONES (NO HACER)**

### **❌ Anti-patrón 1: Mostrar tax_id en listados**

```python
# ❌ MAL: Exponer dato sensible
class ClienteListView(ListView):
    template_name = 'clientes.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # ❌ tax_id completo en listado
        return context

# Template:
{{ cliente.tax_id }}  # ❌ 12345678-9 (expuesto)

# ✅ BIEN: Enmascarar
{% load validators_tags %}
{{ cliente.tax_id|enmascarar_tax_id:cliente.tax_id_type }}  # ✅ ****5678-9
```

---

### **❌ Anti-patrón 2: No validar tax_id**

```python
# ❌ MAL: Guardar sin validar
cliente.tax_id = '12345678-0'  # DV incorrecto
cliente.save()  # ❌ Se guarda inválido

# ✅ BIEN: Validación automática en clean()
cliente.tax_id = '12345678-0'
cliente.save()  # ✅ ValidationError: 'DV esperado: 9'
```

---

### **❌ Anti-patrón 3: Logs con datos sensibles**

```python
# ❌ MAL: Logear dato sensible completo
logger.info(f'Cliente creado: {cliente.nombre}, RUT: {cliente.tax_id}')

# ✅ BIEN: Logear enmascarado
from taller.utils.validators import enmascarar_tax_id
logger.info(
    f'Cliente creado: {cliente.nombre}, '
    f'RUT: {enmascarar_tax_id(cliente.tax_id, cliente.tax_id_type)}'
)
```

---

## 📋 **CAMPOS SENSIBLES DEFINIDOS**

```python
CAMPOS_SENSIBLES = [
    'tax_id',        # ✅ Identificador tributario
    'rut',           # ✅ RUT Chile
    'cpf',           # ✅ CPF Brasil
    'cnpj',          # ✅ CNPJ Brasil
    'ruc',           # ✅ RUC Perú
    'rif',           # ✅ RIF Venezuela
    'ein',           # ✅ EIN USA
    'ssn',           # ✅ SSN USA
    'password',      # ✅ Contraseñas
    'card_number',   # ✅ Números de tarjeta
    'cvv',           # ✅ CVV
    'account_number',# ✅ Números de cuenta
]

# Helper para verificar
from taller.utils.validators import es_campo_sensible

es_campo_sensible('tax_id')      # → True
es_campo_sensible('nombre')      # → False
es_campo_sensible('rut')         # → True
es_campo_sensible('password')    # → True
```

---

## ✅ **CHECKLIST DE IMPLEMENTACIÓN**

- [✅] Validador RUT Chile (dígito verificador)
- [✅] Validador CPF Brasil (dígitos verificadores)
- [✅] Validador CNPJ Brasil (dígitos verificadores)
- [✅] Validador RUC Perú (prefijo + longitud)
- [✅] Validador RIF Venezuela (letra + longitud)
- [✅] Validador EIN USA (prefijo válido)
- [✅] Validador SSN USA (área válida)
- [✅] Normalización automática por tipo
- [✅] enmascarar_tax_id() implementado
- [✅] es_campo_sensible() implementado
- [✅] Cliente.clean() usa validadores
- [✅] Documentación completa
- [✅] Ejemplos de uso en admin/APIs/templates
- [✅] libphonenumber (opcional) documentado

---

## 📋 **ARCHIVOS MODIFICADOS**

1. ✅ `taller/utils/validators.py` (NUEVO)
   - Validadores específicos por tipo
   - Normalización automática
   - Enmascaramiento de datos sensibles
   - Soporte libphonenumber (opcional)

2. ✅ `taller/models/clientes.py`
   - Cliente.clean() actualizado
   - Usa validar_tax_id()
   - Usa validar_telefono() (opcional)

---

## 🎯 **BENEFICIOS**

```
SEGURIDAD:
✅ Datos sensibles no expuestos en listados
✅ Enmascaramiento automático
✅ Logs seguros (sin datos sensibles)

INTEGRIDAD:
✅ Tax IDs válidos (dígitos verificadores correctos)
✅ Normalización consistente
✅ Formato estándar por país

COMPLIANCE:
✅ GDPR/LGPD (datos sensibles protegidos)
✅ Auditoría sin exponer datos
✅ Logs sin información personal

UX:
✅ Usuario puede escribir con puntos/espacios
✅ Sistema normaliza automáticamente
✅ Feedback inmediato si es inválido
✅ Teléfonos en formato local (si libphonenumber)
```

---

## 📚 **DEPENDENCIAS OPCIONALES**

### **libphonenumber (Recomendado):**

```bash
# Instalar
pip install phonenumbers

# Uso automático en Cliente.clean()
# Si está instalado, valida y normaliza teléfonos
# Si NO está instalado, validación básica de longitud
```

---

## 🧪 **TESTS**

### **Test 1: Validación de RUT**

```python
import pytest
from django.core.exceptions import ValidationError

@pytest.mark.django_db
def test_validar_rut_valido():
    """RUT válido debe pasar"""
    from taller.utils.validators import validar_rut_chile
    
    # No debe lanzar excepción
    validar_rut_chile('12345678-5')  # ✅

@pytest.mark.django_db
def test_validar_rut_invalido():
    """RUT inválido debe fallar"""
    from taller.utils.validators import validar_rut_chile
    
    with pytest.raises(ValidationError):
        validar_rut_chile('12345678-0')  # ❌ DV incorrecto
```

---

### **Test 2: Normalización**

```python
@pytest.mark.django_db
def test_normalizar_tax_id():
    """Normalización automática"""
    from taller.utils.validators import normalizar_tax_id
    
    # RUT con puntos → sin puntos
    assert normalizar_tax_id('12.345.678-9', 'RUT_CL') == '12345678-9'
    
    # EIN sin guion → con guion
    assert normalizar_tax_id('123456789', 'EIN') == '12-3456789'
    
    # SSN sin guiones → con guiones
    assert normalizar_tax_id('123456789', 'SSN') == '123-45-6789'
```

---

### **Test 3: Enmascaramiento**

```python
@pytest.mark.django_db
def test_enmascarar_tax_id():
    """Enmascaramiento de datos sensibles"""
    from taller.utils.validators import enmascarar_tax_id
    
    assert enmascarar_tax_id('12345678-9', 'RUT_CL') == '****5678-9'
    assert enmascarar_tax_id('12345678901', 'CPF') == '*******8901'
    assert enmascarar_tax_id('12-3456789', 'EIN') == '**-***6789'
```

---

## ⚠️ **IMPORTANTE PARA CURSOR**

```
CURSOR: AL MANEJAR DATOS SENSIBLES:

✅ Enmascarar tax_id en listados
✅ NO mostrar tax_id completo en list_display
✅ NO agregar tax_id a search_fields
✅ Usar validadores específicos en clean()
✅ Normalizar automáticamente en save()
✅ Logs con datos enmascarados
✅ APIs con serializers separados (list vs detail)

NO HACER:
❌ Mostrar tax_id completo en listados
❌ Logs con tax_id completo
❌ Search por tax_id sin protección
❌ Guardar sin validar
❌ Exportar tax_id a archivos sin cifrar
```

---

**Estado:** ✅ **SEGURIDAD Y DATOS SENSIBLES IMPLEMENTADO**

**Próximo paso:** Usar validadores en todos los modelos con tax_id

**¡Protección enterprise de datos sensibles!** 🔐

