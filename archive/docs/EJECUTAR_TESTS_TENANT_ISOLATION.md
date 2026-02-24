# 🧪 Guía Rápida: Ejecutar Tests de Aislamiento Multi-Tenant

## 🚀 Comandos Rápidos

### Windows (PowerShell)

```powershell
# Ejecutar todos los tests
python -m pytest taller/tests/test_tenant_isolation.py -v

# Ejecutar solo tests de Cliente
python -m pytest taller/tests/test_tenant_isolation.py::TestClienteTenantIsolation -v

# Ejecutar solo tests de Vehiculo
python -m pytest taller/tests/test_tenant_isolation.py::TestVehiculoTenantIsolation -v

# Ejecutar solo tests de Documento
python -m pytest taller/tests/test_tenant_isolation.py::TestDocumentoTenantIsolation -v

# Ejecutar con output detallado
python -m pytest taller/tests/test_tenant_isolation.py -v -s

# Ejecutar usando Django test runner
python manage.py test taller.tests.test_tenant_isolation -v 2
```

### Linux/Mac

```bash
# Ejecutar todos los tests
pytest taller/tests/test_tenant_isolation.py -v

# Ejecutar solo tests de Cliente
pytest taller/tests/test_tenant_isolation.py::TestClienteTenantIsolation -v

# Ejecutar solo tests de Vehiculo
pytest taller/tests/test_tenant_isolation.py::TestVehiculoTenantIsolation -v

# Ejecutar solo tests de Documento
pytest taller/tests/test_tenant_isolation.py::TestDocumentoTenantIsolation -v

# Ejecutar con output detallado
pytest taller/tests/test_tenant_isolation.py -v -s

# Ejecutar usando Django test runner
python manage.py test taller.tests.test_tenant_isolation -v 2
```

---

## ✅ Resultado Esperado

Todos los tests deben pasar. Si ves algo como:

```
test_cliente_queryset_filtra_por_empresa ... PASSED
test_vehiculo_queryset_filtra_por_empresa ... PASSED
test_documento_queryset_filtra_por_empresa ... PASSED
...
========================= X passed in Y.YYs =========================
```

¡Perfecto! El aislamiento multi-tenant está funcionando correctamente.

---

## ❌ Si un Test Falla

Si ves algo como:

```
FAILED test_cliente_queryset_filtra_por_empresa
AssertionError: Cliente de otra empresa encontrado
```

**ACCIÓN INMEDIATA:**
1. ⚠️ **NO IGNORAR** - Es una vulnerabilidad crítica
2. Revisar el código relacionado
3. Ver `INFORME_SEGURIDAD_MULTI_TENANT.md` para referencia
4. Corregir la vulnerabilidad
5. Ejecutar tests nuevamente hasta que todos pasen

---

## 📊 Cobertura de Tests

Los tests cubren:

- ✅ **Modelos**: Cliente, Vehiculo, Documento
- ✅ **APIs**: Crear vehículo, vehículos por cliente
- ✅ **Vistas**: Lista, detalle, portal
- ✅ **Formularios**: DocumentoForm
- ✅ **Managers**: TenantManager
- ✅ **Regresiones**: Vulnerabilidades corregidas

---

## 🔄 Integración en CI/CD

Para integrar en tu pipeline:

```yaml
# Ejemplo para GitHub Actions
- name: Run Tenant Isolation Tests
  run: |
    python -m pytest taller/tests/test_tenant_isolation.py -v
```

```bash
# Ejemplo para pre-commit hook
#!/bin/bash
python -m pytest taller/tests/test_tenant_isolation.py -v
if [ $? -ne 0 ]; then
    echo "❌ Tests de aislamiento multi-tenant fallaron"
    exit 1
fi
```

---

**¡Mantén estos tests pasando siempre!** 🔒





