# Implementación: Normalización de Números de Teléfono

## Resumen

Se ha implementado una solución integral para normalizar números de teléfono y asegurar que siempre tengan el prefijo "+" antes de ser guardados o enviados por WhatsApp. El sistema ahora "auto-repara" los números de teléfono basándose en el país seleccionado.

## Cambios Implementados

### 1. Función Utilitaria de Normalización

**Archivo**: `taller/utils/validators.py`

Se creó la función `normalizar_telefono_con_prefijo()` que:
- Normaliza números de teléfono asegurando que tengan el prefijo "+"
- Si el número NO empieza con "+", antepone el prefijo del país según `CountrySettings`
- Limpia el número de caracteres no numéricos (espacios, guiones, paréntesis, etc.)
- Asegura que el número siempre tenga el formato internacional correcto

**Ejemplos de uso**:
```python
from taller.utils.validators import normalizar_telefono_con_prefijo

# Normalizar número sin prefijo
normalizar_telefono_con_prefijo('912345678', 'CL')  # → '+56912345678'
normalizar_telefono_con_prefijo('6789259579', 'US')  # → '+16789259579'

# Número que ya tiene prefijo completo (se limpia pero mantiene el formato)
normalizar_telefono_con_prefijo('+56 9 1234 5678', 'CL')  # → '+56912345678'

# Número con "+" pero sin prefijo del país (Caso común que se repara automáticamente)
normalizar_telefono_con_prefijo('+912345678', 'CL')  # → '+56912345678'  (agrega el 56)
normalizar_telefono_con_prefijo('+6789259579', 'US')  # → '+16789259579'  (agrega el 1)
```

### 2. Validación en el Formulario de Registro

**Archivo**: `taller/forms/suscripcion.py`

Se agregó el método `clean_telefono()` al formulario `FormularioRegistro` que:
- Se ejecuta automáticamente antes de guardar el usuario
- Normaliza el número de teléfono usando el país seleccionado
- Antepone el prefijo correspondiente si el usuario lo olvidó
- Evita que entren datos incompletos en el futuro

**Código implementado**:
```python
def clean_telefono(self):
    from taller.utils.validators import normalizar_telefono_con_prefijo
    
    telefono = self.cleaned_data.get("telefono", "").strip()
    pais = self.cleaned_data.get("pais")
    
    if not telefono:
        return telefono
    
    # Normalizar el número con el prefijo del país
    if pais:
        telefono_normalizado = normalizar_telefono_con_prefijo(telefono, pais)
        return telefono_normalizado
    
    return telefono
```

### 3. Ajuste en el Servicio de Notificación WhatsApp

**Archivo**: `taller/utils/notificaciones_suscripcion.py`

Se actualizaron las funciones de envío de WhatsApp para asegurar que siempre tengan el prefijo "+":

#### Función `enviar_whatsapp()`
- Ahora normaliza el número de teléfono antes de enviarlo
- Verifica que el número tenga el prefijo "+" usando `normalizar_telefono_con_prefijo()`
- Registra en logs el número normalizado para facilitar el debugging

#### Función `enviar_whatsapp_a_numero()`
- Normaliza el número de teléfono antes de enviarlo
- Si se proporciona una empresa, usa su país para normalizar el número
- Asegura que el número esté en el formato correcto antes de la llamada a la API

### 4. Script de Migración para Base de Datos

**Archivo**: `scripts/normalizar_telefonos_empresas.py`

Script para normalizar todos los números de teléfono existentes en la base de datos.

**Uso**:
```bash
python manage.py shell
>>> exec(open('scripts/normalizar_telefonos_empresas.py').read())
```

**O directamente**:
```bash
python manage.py shell < scripts/normalizar_telefonos_empresas.py
```

**Funcionalidad**:
- Recorre todas las empresas registradas
- Para cada empresa que tenga un número de teléfono:
  - Si NO tiene prefijo "+", se le antepone el prefijo según su país
  - Si ya tiene prefijo "+", se normaliza (limpia espacios, guiones, etc.)
- Muestra un resumen de empresas actualizadas y errores encontrados

**Ejemplo de salida**:
```
============================================================
NORMALIZACIÓN DE NÚMEROS DE TELÉFONO
============================================================

Total de empresas a revisar: 150

Reparando: Taller Ejemplo (CL)
  Original: 6789259579
  Prefijo del país: +56
  Normalizado: +566789259579

============================================================
RESUMEN DE NORMALIZACIÓN
============================================================
Total de empresas revisadas: 150
Empresas actualizadas: 25
Empresas con errores: 0

✅ Proceso completado
============================================================
```

## Beneficios

1. **Normalización Automática**: Los nuevos registros se normalizan automáticamente antes de guardar
2. **Reparación de Datos Existentes**: El script de migración permite corregir números existentes en la base de datos
3. **WhatsApp Funcional**: Las notificaciones de extensión de plan se enviarán correctamente porque las APIs internacionales ya no rechazarán el número
4. **Auditoría Mejorada**: En el LogAuditoria se verá el número corregido, facilitando el soporte técnico
5. **Panel Administrativo**: Todos los teléfonos se mostrarán con el formato correcto (ej: +16789259579)

## Próximos Pasos

1. **Ejecutar el script de migración** para normalizar los números existentes:
   ```bash
   python manage.py shell < scripts/normalizar_telefonos_empresas.py
   ```

2. **Probar el registro** con un número sin prefijo para verificar que se normalice correctamente

3. **Verificar el envío de WhatsApp** asegurándote de que las notificaciones lleguen correctamente

## Notas Técnicas

- La función `normalizar_telefono_con_prefijo()` utiliza `CountrySettings.get_country_config()` para obtener el prefijo del país
- Los prefijos están definidos en `taller/config/country_settings.py` (ej: "+56" para CL, "+1" para US)
- La función limpia el número de caracteres no numéricos antes de agregar el prefijo
- **Caso especial**: Si el número empieza con "+" pero le falta el prefijo del país (ej: "+912345678"), la función lo detecta y agrega el prefijo correcto (resultado: "+56912345678")
- Si el número ya tiene el prefijo del país incluido en los dígitos, solo se agrega el "+"

## Archivos Modificados

1. `taller/utils/validators.py` - Nueva función `normalizar_telefono_con_prefijo()`
2. `taller/forms/suscripcion.py` - Método `clean_telefono()` agregado
3. `taller/utils/notificaciones_suscripcion.py` - Funciones de WhatsApp actualizadas
4. `scripts/normalizar_telefonos_empresas.py` - Nuevo script de migración

## Verificación

Para verificar que todo funciona correctamente:

1. **Registro de nuevo usuario**: Intentar registrar un usuario con un número sin prefijo (ej: "912345678" para Chile)
   - El sistema debería normalizarlo a "+56912345678"

2. **Envío de WhatsApp**: Verificar que las notificaciones se envíen correctamente a números normalizados

3. **Panel administrativo**: Verificar que los números se muestren con el formato correcto (con prefijo "+")

