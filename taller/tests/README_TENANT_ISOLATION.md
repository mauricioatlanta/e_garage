# 🔒 Tests de Aislamiento Multi-Tenant

## 📋 Descripción

Este archivo contiene tests automatizados para validar que el aislamiento de datos entre suscriptores (multi-tenant isolation) funciona correctamente. Estos tests aseguran que:

1. ✅ Un usuario de empresa A **NO puede acceder** a datos de empresa B
2. ✅ Todas las consultas filtran por `empresa_id`
3. ✅ Las APIs rechazan acceso cruzado
4. ✅ Los formularios validan empresa
5. ✅ Las vistas protegen datos multi-tenant

## ⚠️ IMPORTANTE

**Estos tests deben pasar SIEMPRE.** Si fallan, hay una **vulnerabilidad crítica** de seguridad que debe corregirse inmediatamente.

---

## 🚀 Ejecutar Tests

### Opción 1: Ejecutar todos los tests de aislamiento

```bash
# Usando pytest
pytest taller/tests/test_tenant_isolation.py -v

# Usando Django test runner
python manage.py test taller.tests.test_tenant_isolation -v 2
```

### Opción 2: Ejecutar una clase específica

```bash
# Solo tests de Cliente
pytest taller/tests/test_tenant_isolation.py::TestClienteTenantIsolation -v

# Solo tests de Vehiculo
pytest taller/tests/test_tenant_isolation.py::TestVehiculoTenantIsolation -v

# Solo tests de Documento
pytest taller/tests/test_tenant_isolation.py::TestDocumentoTenantIsolation -v
```

### Opción 3: Ejecutar un test específico

```bash
# Test específico
pytest taller/tests/test_tenant_isolation.py::TestClienteTenantIsolation::test_cliente_queryset_filtra_por_empresa -v
```

---

## 📊 Estructura de Tests

### 1. **TestClienteTenantIsolation**
Tests de aislamiento para el modelo `Cliente`:
- ✅ QuerySet filtra por empresa
- ✅ Get sin filtro empresa falla
- ✅ TenantManager funciona correctamente
- ✅ Creación asigna empresa automáticamente

### 2. **TestVehiculoTenantIsolation**
Tests de aislamiento para el modelo `Vehiculo`:
- ✅ QuerySet filtra por empresa
- ✅ Get sin filtro empresa falla
- ✅ Vehículos por cliente filtran empresa
- ✅ Creación asigna empresa

### 3. **TestDocumentoTenantIsolation**
Tests de aislamiento para el modelo `Documento`:
- ✅ QuerySet filtra por empresa
- ✅ Get sin filtro empresa falla
- ✅ Creación asigna empresa

### 4. **TestAPITenantIsolation**
Tests de aislamiento para APIs:
- ✅ API de vehículos por cliente filtra empresa
- ✅ API de crear vehículo valida empresa

### 5. **TestViewsTenantIsolation**
Tests de aislamiento para vistas:
- ✅ Lista de clientes solo muestra empresa del usuario
- ✅ Detalle de cliente de otra empresa devuelve 404
- ✅ Detalle de documento de otra empresa devuelve 404

### 6. **TestFormTenantIsolation**
Tests de aislamiento para formularios:
- ✅ Formulario de documento filtra clientes por empresa
- ✅ Formulario de documento filtra vehículos por empresa

### 7. **TestPortalTenantIsolation**
Tests de aislamiento para portal de clientes:
- ✅ Cliente en portal solo ve sus propios datos

### 8. **TestTenantManagerIsolation**
Tests para validar TenantManager:
- ✅ `for_request()` filtra correctamente
- ✅ `for_tenant()` filtra correctamente

### 9. **TestCrossTenantAccessPrevention**
Tests para prevenir acceso cruzado:
- ✅ No se puede crear documento con cliente de otra empresa
- ✅ No se puede crear vehículo con cliente de otra empresa

### 10. **TestRegresionVulnerabilidadesCorregidas**
Tests de regresión para asegurar que las vulnerabilidades corregidas no reaparezcan:
- ✅ Regresión: `taller/portal/views.py`
- ✅ Regresión: `taller/vehiculos/api.py`
- ✅ Regresión: `taller/documentos/views_moderno.py`

---

## ✅ Resultado Esperado

Todos los tests deben pasar. Si algún test falla:

1. **NO IGNORAR EL ERROR** - Es una vulnerabilidad crítica
2. Revisar el código relacionado
3. Corregir la vulnerabilidad
4. Verificar que todos los tests pasen
5. Documentar la corrección

---

## 🔍 Debugging

Si un test falla, puedes ejecutarlo con más verbosidad:

```bash
# Con output detallado
pytest taller/tests/test_tenant_isolation.py -v -s

# Con pdb (debugger)
pytest taller/tests/test_tenant_isolation.py --pdb

# Solo mostrar errores
pytest taller/tests/test_tenant_isolation.py -v --tb=short
```

---

## 📝 Agregar Nuevos Tests

Al agregar nuevas funcionalidades que involucren modelos multi-tenant:

1. **SIEMPRE** agregar tests de aislamiento
2. Verificar que un usuario no puede acceder a datos de otra empresa
3. Verificar que las consultas filtran por empresa
4. Ejecutar todos los tests antes de hacer commit

### Ejemplo de test nuevo:

```python
def test_nueva_funcionalidad_filtra_empresa(self):
    """Test: Nueva funcionalidad filtra por empresa"""
    # Setup
    resultado_a = MiNuevaFuncionalidad.objects.filter(empresa=self.empresa_a)
    
    # Verificar
    self.assertEqual(resultado_a.count(), 1)
    self.assertNotIn(self.objeto_b, resultado_a)
```

---

## 🎯 Integración Continua

Estos tests deben ejecutarse en:
- ✅ Pre-commit hooks
- ✅ CI/CD pipeline
- ✅ Antes de cada deploy
- ✅ En cada pull request

---

## 📚 Referencias

- Ver `INFORME_SEGURIDAD_MULTI_TENANT.md` para detalles de las vulnerabilidades corregidas
- Ver `core/models.py` para implementación de `TenantScoped` y `TenantManager`
- Ver `core/views.py` para implementación de `TenantViewMixin`

---

**Última actualización**: Diciembre 2025  
**Mantenido por**: Equipo de Desarrollo



