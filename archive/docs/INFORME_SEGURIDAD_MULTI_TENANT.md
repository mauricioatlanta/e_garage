# 🔒 INFORME DE SEGURIDAD: AISLAMIENTO MULTI-TENANT

**Fecha**: Diciembre 2025  
**Objetivo**: Verificar y corregir todas las consultas que no filtran por `empresa_id` en modelos sensibles

---

## 📊 RESUMEN EJECUTIVO

Se han identificado **9 vulnerabilidades críticas** donde las consultas a modelos sensibles (Cliente, Vehiculo, Documento) no filtran explícitamente por `empresa_id`, lo que podría permitir acceso cruzado entre suscriptores.

**Estado**: ⚠️ **VULNERABILIDADES ENCONTRADAS** - Requiere corrección inmediata

---

## 🎯 MODELOS SENSIBLES VERIFICADOS

Los siguientes modelos manejan información personal y DEBEN filtrar siempre por `empresa_id`:

1. ✅ **Cliente** - Hereda de `TenantScoped` (tiene campo `empresa`)
2. ✅ **Vehiculo** - Hereda de `TenantScoped` (tiene campo `empresa`)
3. ✅ **Documento** - Tiene campo `empresa` (no hereda de TenantScoped pero debe filtrar)

---

## 🚨 VULNERABILIDADES ENCONTRADAS

### 1. **taller/portal/views.py:100** - CRÍTICO
```python
# ❌ VULNERABLE
return Cliente.objects.get(pk=cliente_id)

# ✅ CORRECTO
return Cliente.objects.get(pk=cliente_id, empresa=cliente.empresa)
```
**Riesgo**: Un cliente podría acceder a datos de otro suscriptor si conoce el ID.

---

### 2. **taller/vehiculos/api.py:244** - CRÍTICO
```python
# ❌ VULNERABLE
cli = Cliente.objects.get(id=payload["cliente_id"])

# ✅ CORRECTO
cli = Cliente.objects.get(id=payload["cliente_id"], empresa=emp)
```
**Riesgo**: API podría devolver clientes de otras empresas si se manipula el payload.

---

### 3. **taller/documentos/api_backup.py:136-140** - CRÍTICO
```python
# ❌ VULNERABLE
cli = Cliente.objects.get(id=payload["cliente_id"])
veh = Vehiculo.objects.get(id=payload["vehiculo_id"])

# ✅ CORRECTO
cli = Cliente.objects.get(id=payload["cliente_id"], empresa=emp)
veh = Vehiculo.objects.get(id=payload["vehiculo_id"], empresa=emp)
```
**Riesgo**: API backup podría crear documentos con datos de otras empresas.

---

### 4. **taller/documentos/views_moderno.py:648** - MEDIO
```python
# ❌ VULNERABLE (aunque cliente ya está filtrado)
vehiculos = Vehiculo.objects.filter(cliente=cliente)

# ✅ CORRECTO (filtro explícito por empresa)
vehiculos = Vehiculo.objects.filter(cliente=cliente, empresa=empresa)
```
**Riesgo**: Bajo, pero mejor práctica es filtrar explícitamente.

---

### 5. **taller/views_extra/portal_views.py** - CRÍTICO (Múltiples)
```python
# ❌ VULNERABLE - Líneas 39, 90, 138, 158, 211, 245, 304
cliente = Cliente.objects.filter(email_cliente=email).first()
vehiculos = Vehiculo.objects.filter(id_cliente=cliente)
documentos = Documento.objects.filter(id_cliente=cliente)

# ✅ CORRECTO
# Nota: Este archivo usa campos legacy (id_cliente). Debe migrar a campos correctos.
```
**Riesgo**: Portal de clientes podría mostrar datos de otras empresas.

---

### 6. **taller/documentos/views.py:578** - MEDIO
```python
# ❌ VULNERABLE (verifica después, pero debería filtrar desde el inicio)
if not Documento.objects.filter(id=documento_id).exists():

# ✅ CORRECTO
if not Documento.objects.filter(id=documento_id, empresa=empresa).exists():
```
**Riesgo**: Podría revelar existencia de documentos de otras empresas.

---

### 7. **taller/documentos/views.py:1106** - MEDIO
```python
# ❌ VULNERABLE (filtra después, pero debería empezar con filtro)
queryset = Documento.objects.all()
if empresa is not None:
    queryset = queryset.filter(empresa=empresa)

# ✅ CORRECTO
queryset = Documento.objects.filter(empresa=empresa) if empresa else Documento.objects.none()
```
**Riesgo**: Bajo, pero mejor práctica.

---

### 8. **taller/documentos/views_class_based.py:116** - MEDIO
```python
# ❌ VULNERABLE (solo para debug, pero debería filtrar)
documento_exists = Documento.objects.filter(pk=pk).first()

# ✅ CORRECTO
documento_exists = Documento.objects.filter(pk=pk, empresa=empresa).first()
```
**Riesgo**: Podría revelar existencia de documentos de otras empresas.

---

### 9. **taller/views_extra/views_cliente.py:10** - CRÍTICO
```python
# ❌ VULNERABLE (usa campo 'user' que parece legacy)
clientes = Cliente.objects.filter(user=request.user)

# ✅ CORRECTO
clientes = Cliente.objects.filter(empresa=request.user.empresa)
```
**Riesgo**: Vista legacy podría mostrar clientes incorrectos.

---

## ✅ CORRECCIONES APLICADAS

Todas las vulnerabilidades han sido corregidas en los archivos correspondientes:

### Archivos Corregidos:

1. ✅ **taller/portal/views.py** - Agregada validación de empresa en `_get_cliente_autenticado()`
2. ✅ **taller/vehiculos/api.py** - Filtro por empresa agregado en consulta de Cliente
3. ✅ **taller/documentos/api_backup.py** - Filtros por empresa agregados en Cliente y Vehiculo
4. ✅ **taller/documentos/views_moderno.py** - Filtro por empresa agregado en consulta de Vehiculo
5. ✅ **taller/documentos/views.py** - Filtros por empresa mejorados (2 correcciones)
6. ✅ **taller/documentos/views_class_based.py** - Filtro por empresa agregado en consulta de debug
7. ✅ **taller/views_extra/views_cliente.py** - Migrado de campo legacy 'user' a 'empresa' (2 correcciones)
8. ✅ **taller/views_extra/portal_views.py** - Múltiples correcciones:
   - Migrado de campos legacy (`id_cliente` → `cliente`, `id_vehiculo` → `vehiculo`)
   - Migrado de campos legacy (`fecha_documento` → `fecha_emision`, `tipo_documento` → `tipo`)
   - Filtros por empresa agregados en todas las consultas (8 correcciones)

**Total**: 9 vulnerabilidades críticas corregidas en 8 archivos

---

## 🛡️ RECOMENDACIONES ADICIONALES

### 1. **Usar TenantManager siempre**
```python
# ✅ MEJOR PRÁCTICA
clientes = Cliente.objects.for_tenant(empresa)
# o
clientes = Cliente.objects.for_request(request)
```

### 2. **Validar en formularios**
```python
# ✅ MEJOR PRÁCTICA
def clean(self):
    if self.instance.empresa_id != self.empresa.id:
        raise ValidationError("No pertenece a tu empresa")
```

### 3. **Middleware de validación**
Considerar agregar middleware que valide automáticamente que todas las consultas a modelos TenantScoped incluyan filtro de empresa.

### 4. **Tests automatizados**
Crear tests que verifiquen que:
- Un usuario de empresa A no puede acceder a datos de empresa B
- Todas las APIs filtran por empresa
- Todos los formularios validan empresa

---

## 📝 NOTAS IMPORTANTES

1. **TenantScoped**: Los modelos que heredan de `TenantScoped` tienen un `TenantManager` que puede filtrar automáticamente, pero **NO es suficiente**. Siempre debemos filtrar explícitamente en las vistas.

2. **TenantViewMixin**: El mixin `TenantViewMixin` en `core/views.py` filtra automáticamente en `get_queryset()`, pero solo funciona para vistas basadas en clases que lo usen.

3. **APIs**: Las APIs REST deben validar explícitamente el filtro de empresa en cada endpoint.

4. **Portal de Clientes**: El portal usa campos legacy (`id_cliente`) que deberían migrarse a la estructura correcta.

---

## ✅ CHECKLIST DE VERIFICACIÓN

- [x] Revisar todas las consultas a Cliente
- [x] Revisar todas las consultas a Vehiculo
- [x] Revisar todas las consultas a Documento
- [x] Corregir vulnerabilidades encontradas
- [x] Migrar campos legacy en portal_views.py
- [ ] Crear tests de aislamiento multi-tenant (recomendado)
- [ ] Documentar mejores prácticas para el equipo (recomendado)
- [ ] Revisar otros archivos legacy y migrar campos obsoletos (recomendado)

---

**Estado Final**: ✅ **TODAS LAS VULNERABILIDADES CORREGIDAS**

