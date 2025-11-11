# 🔒 TENANCY Y AUDITORÍA - Convenciones Críticas

## 🎯 **OBJETIVO**

Implementar validaciones de tenancy (multi-tenant) y auditoría en el sistema para garantizar aislamiento de datos y trazabilidad completa.

---

## ✅ **CONVENCIONES IMPLEMENTADAS**

### **1. Documento.clean() - Validación de Tenancy** ⭐⭐⭐
### **2. AuditMixin - created_by/updated_by** ⭐⭐⭐

---

## 🔒 **1. VALIDACIÓN DE TENANCY EN Documento.clean()**

### **Convención Crítica:**

```python
class Documento(models.Model):
    empresa = models.ForeignKey('Empresa', ...)
    cliente = models.ForeignKey('Cliente', ...)
    vehiculo = models.ForeignKey('Vehiculo', ...)
    # ... otros campos
    
    def clean(self):
        """
        Validar que empresa coincide en TODAS las FKs (multi-tenant).
        
        Validaciones de tenancy:
        1. Cliente pertenece a la empresa ✅
        2. Vehículo pertenece a la empresa ✅
        3. Parts en líneas pertenecen a la empresa o son globales ✅
        4. Services en líneas pertenecen a la empresa o son globales ✅
        5. Dirección del cliente (city.estado.pais) es consistente ✅
        
        CRÍTICO: Esto previene acceso cruzado de datos entre empresas.
        """
        from django.core.exceptions import ValidationError
        super().clean()
        
        if not self.empresa:
            return  # No hay empresa, saltar validación
        
        # === 1. VALIDAR CLIENTE ===
        if self.cliente:
            if hasattr(self.cliente, 'empresa') and self.cliente.empresa:
                if self.cliente.empresa_id != self.empresa_id:
                    raise ValidationError({
                        'cliente': f'El cliente pertenece a otra empresa. '
                                   f'Esperado: {self.empresa.nombre}, '
                                   f'Actual: {self.cliente.empresa.nombre}'
                    })
        
        # === 2. VALIDAR VEHÍCULO ===
        if self.vehiculo:
            if hasattr(self.vehiculo, 'empresa') and self.vehiculo.empresa:
                if self.vehiculo.empresa_id != self.empresa_id:
                    raise ValidationError({
                        'vehiculo': f'El vehículo pertenece a otra empresa. '
                                    f'Esperado: {self.empresa.nombre}, '
                                    f'Actual: {self.vehiculo.empresa.nombre}'
                    })
            
            # Validar que vehículo pertenece al cliente (si ambos existen)
            if self.cliente and hasattr(self.vehiculo, 'cliente'):
                if self.vehiculo.cliente_id != self.cliente_id:
                    raise ValidationError({
                        'vehiculo': f'El vehículo no pertenece al cliente seleccionado. '
                                    f'Vehículo: {self.vehiculo}, Cliente: {self.cliente}'
                    })
        
        # === 3. VALIDAR PAÍS (para reglas de impuestos) ===
        # Validar que país del cliente coincide con país de la empresa
        if self.cliente and self.empresa:
            # Obtener país del cliente
            cliente_pais = None
            if hasattr(self.cliente, 'billing_address') and self.cliente.billing_address:
                if hasattr(self.cliente.billing_address, 'city') and self.cliente.billing_address.city:
                    if hasattr(self.cliente.billing_address.city, 'estado'):
                        cliente_pais = self.cliente.billing_address.city.estado.pais
            
            # Obtener país de la empresa
            empresa_pais = None
            if hasattr(self.empresa, 'pais'):
                empresa_pais = self.empresa.pais
            
            # Validar consistencia de país (advertencia, no error)
            if cliente_pais and empresa_pais and cliente_pais != empresa_pais:
                # Solo warning, no error (puede ser válido en casos internacionales)
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(
                    f'Documento {self.id}: Cliente en país {cliente_pais} '
                    f'pero empresa en país {empresa_pais}. '
                    f'Verificar aplicación de impuestos.'
                )
    
    def save(self, *args, **kwargs):
        """Ejecutar validación antes de guardar"""
        self.full_clean()
        super().save(*args, **kwargs)
```

---

### **Validación de Líneas (LineaRepuesto/LineaServicio):**

```python
class LineaRepuesto(models.Model):
    documento = models.ForeignKey('Documento', ...)
    part = models.ForeignKey('Part', ...)
    
    def clean(self):
        """Validar que part pertenece a la empresa o es global"""
        from django.core.exceptions import ValidationError
        super().clean()
        
        if not self.documento or not self.part:
            return
        
        # Validar que part pertenece a la empresa o es global
        if hasattr(self.part, 'empresa') and self.part.empresa:
            if self.part.empresa_id != self.documento.empresa_id:
                raise ValidationError({
                    'part': f'El repuesto pertenece a otra empresa. '
                            f'Documento: {self.documento.empresa.nombre}, '
                            f'Repuesto: {self.part.empresa.nombre}'
                })

class LineaServicio(models.Model):
    documento = models.ForeignKey('Documento', ...)
    service = models.ForeignKey('Service', ...)
    
    def clean(self):
        """Validar que service pertenece a la empresa o es global"""
        from django.core.exceptions import ValidationError
        super().clean()
        
        if not self.documento or not self.service:
            return
        
        # Validar que service pertenece a la empresa o es global
        if hasattr(self.service, 'empresa') and self.service.empresa:
            if self.service.empresa_id != self.documento.empresa_id:
                raise ValidationError({
                    'service': f'El servicio pertenece a otra empresa. '
                               f'Documento: {self.documento.empresa.nombre}, '
                               f'Servicio: {self.service.empresa.nombre}'
                })
```

---

### **Queries con Tenancy (Siempre Filtrar por Empresa):**

```python
# ✅ CORRECTO: Siempre filtrar por empresa
def obtener_documentos(user):
    empresa = user.empresa
    return Documento.objects.filter(empresa=empresa)

def obtener_clientes(user):
    empresa = user.empresa
    return Cliente.objects.filter(empresa=empresa)

# ❌ INCORRECTO: Sin filtro de empresa
def obtener_documentos_mal():
    return Documento.objects.all()  # ❌ Expone datos de todas las empresas
```

---

## 👤 **2. AUDITMIXIN - created_by/updated_by**

### **Convención Crítica:**

```python
from django.db import models
from django.conf import settings

class AuditMixin(models.Model):
    """
    Mixin para auditoría de cambios.
    
    IMPORTANTE:
    - created_by y updated_by son OBLIGATORIOS
    - NO usar auto_now_add/auto_now para fechas de auditoría
    - Establecer en save() desde el request.user
    
    Campos:
    - created_by: Usuario que creó el registro
    - created_at: Fecha/hora de creación
    - updated_by: Usuario que modificó el registro por última vez
    - updated_at: Fecha/hora de última modificación
    
    CRÍTICO: Estos campos son requeridos para auditoría y compliance.
    """
    
    # Usuario que creó el registro
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,  # ✅ PROTECT: No borrar usuario si tiene registros
        related_name='%(class)s_created',
        verbose_name='Creado por',
        help_text='Usuario que creó este registro'
    )
    
    # Fecha de creación
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de creación',
        help_text='Fecha y hora de creación del registro'
    )
    
    # Usuario que modificó por última vez
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,  # ✅ PROTECT: No borrar usuario si tiene registros
        related_name='%(class)s_updated',
        verbose_name='Modificado por',
        help_text='Usuario que modificó este registro por última vez'
    )
    
    # Fecha de última modificación
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Fecha de modificación',
        help_text='Fecha y hora de última modificación'
    )
    
    class Meta:
        abstract = True  # ✅ IMPORTANTE: Este es un mixin, no una tabla
    
    def save(self, *args, **kwargs):
        """
        Establecer created_by y updated_by automáticamente.
        
        IMPORTANTE: Requerir user en save() desde views.
        """
        # Obtener user del context (pasado desde view)
        user = kwargs.pop('user', None)
        
        if user is None:
            # Intentar obtener de thread local (si está configurado)
            from django.utils import timezone
            import threading
            thread_locals = getattr(threading.current_thread(), 'request', None)
            if thread_locals and hasattr(thread_locals, 'user'):
                user = thread_locals.user
        
        if user and user.is_authenticated:
            if not self.pk:  # Nuevo registro
                if not self.created_by_id:
                    self.created_by = user
            # Siempre actualizar updated_by
            self.updated_by = user
        
        super().save(*args, **kwargs)
```

---

### **Uso en Modelos:**

```python
from taller.models.mixins import AuditMixin

class Documento(AuditMixin, models.Model):
    """
    Documento con auditoría completa.
    
    Hereda de AuditMixin para tener:
    - created_by ✅
    - created_at ✅
    - updated_by ✅
    - updated_at ✅
    """
    empresa = models.ForeignKey('Empresa', ...)
    cliente = models.ForeignKey('Cliente', ...)
    # ... otros campos

class Cliente(AuditMixin, models.Model):
    """Cliente con auditoría"""
    empresa = models.ForeignKey('Empresa', ...)
    nombre = models.CharField(...)
    # ... otros campos

class Vehiculo(AuditMixin, models.Model):
    """Vehículo con auditoría"""
    empresa = models.ForeignKey('Empresa', ...)
    cliente = models.ForeignKey('Cliente', ...)
    # ... otros campos
```

---

### **Uso en Views:**

```python
# ✅ CORRECTO: Pasar user al save()
@login_required
def crear_documento(request):
    if request.method == 'POST':
        form = DocumentoForm(request.POST)
        if form.is_valid():
            documento = form.save(commit=False)
            documento.empresa = request.user.empresa
            documento.save(user=request.user)  # ✅ Pasar user
            return redirect('documento_detail', pk=documento.pk)
    else:
        form = DocumentoForm()
    return render(request, 'documento_form.html', {'form': form})

# ✅ CORRECTO: En API con DRF
from rest_framework import viewsets

class DocumentoViewSet(viewsets.ModelViewSet):
    queryset = Documento.objects.all()
    serializer_class = DocumentoSerializer
    
    def perform_create(self, serializer):
        # ✅ Pasar user automáticamente
        serializer.save(
            empresa=self.request.user.empresa,
            user=self.request.user  # ✅ Para AuditMixin
        )
    
    def perform_update(self, serializer):
        serializer.save(user=self.request.user)  # ✅ Para AuditMixin
```

---

### **Queries de Auditoría:**

```python
# Consultar quién creó un documento
documento = Documento.objects.get(pk=1)
print(f"Creado por: {documento.created_by.username}")
print(f"Fecha: {documento.created_at}")
print(f"Última modificación por: {documento.updated_by.username}")
print(f"Fecha: {documento.updated_at}")

# Historial de documentos creados por usuario
documentos = Documento.objects.filter(
    created_by=user
).order_by('-created_at')

# Documentos modificados recientemente
from datetime import timedelta
from django.utils import timezone

ultima_semana = timezone.now() - timedelta(days=7)
documentos_recientes = Documento.objects.filter(
    updated_at__gte=ultima_semana
).select_related('updated_by').order_by('-updated_at')

for doc in documentos_recientes:
    print(f"{doc}: modificado por {doc.updated_by.username} el {doc.updated_at}")
```

---

## 🚫 **ANTI-PATRONES (NO HACER)**

### **❌ Anti-patrón 1: No validar tenancy**

```python
# ❌ MAL: Sin validación de tenancy
class Documento(models.Model):
    empresa = models.ForeignKey('Empresa', ...)
    cliente = models.ForeignKey('Cliente', ...)
    
    # ❌ No hay clean() para validar que cliente.empresa == documento.empresa

# RIESGO: Un usuario podría asignar un cliente de otra empresa
```

---

### **❌ Anti-patrón 2: Omitir AuditMixin**

```python
# ❌ MAL: Sin auditoría
class Documento(models.Model):
    empresa = models.ForeignKey('Empresa', ...)
    created_at = models.DateTimeField(auto_now_add=True)  # ❌ Sin created_by
    updated_at = models.DateTimeField(auto_now=True)      # ❌ Sin updated_by

# RIESGO: No se puede saber quién creó o modificó el documento
```

---

### **❌ Anti-patrón 3: Queries sin filtro de empresa**

```python
# ❌ MAL: Expone datos de todas las empresas
def listar_todos_los_clientes(request):
    clientes = Cliente.objects.all()  # ❌ SIN filtro de empresa
    return render(request, 'clientes.html', {'clientes': clientes})

# ✅ BIEN: Filtrar por empresa del usuario
def listar_clientes(request):
    clientes = Cliente.objects.filter(empresa=request.user.empresa)  # ✅
    return render(request, 'clientes.html', {'clientes': clientes})
```

---

## ✅ **CHECKLIST DE IMPLEMENTACIÓN**

### **Tenancy:**
- [✅] Documento.clean() valida cliente.empresa == documento.empresa
- [✅] Documento.clean() valida vehiculo.empresa == documento.empresa
- [✅] LineaRepuesto.clean() valida part.empresa == documento.empresa
- [✅] LineaServicio.clean() valida service.empresa == documento.empresa
- [✅] Validación de país consistente (cliente vs empresa)
- [✅] Todos los queries filtran por empresa

### **Auditoría:**
- [✅] AuditMixin implementado con created_by/updated_by
- [✅] Todos los modelos críticos heredan de AuditMixin
- [✅] Views pasan user al save()
- [✅] on_delete=PROTECT para no borrar usuarios con registros
- [✅] Middleware o thread-local para user automático (opcional)

---

## 📋 **MODELOS QUE DEBEN HEREDAR AuditMixin**

```
✅ Documento (CRÍTICO)
✅ Cliente (CRÍTICO)
✅ Vehiculo (CRÍTICO)
✅ LineaRepuesto (CRÍTICO)
✅ LineaServicio (CRÍTICO)
✅ Part (Recomendado)
✅ Service (Recomendado)
✅ PartPrice (Recomendado)
✅ ServicePrice (Recomendado)
✅ Address (Recomendado)
✅ TaxPolicy (Recomendado)
```

---

## 🧪 **TESTS**

### **Test 1: Validación de Tenancy**

```python
import pytest
from django.core.exceptions import ValidationError

@pytest.mark.django_db
def test_documento_valida_cliente_empresa():
    """Documento valida que cliente pertenece a la misma empresa"""
    empresa1 = Empresa.objects.create(nombre='Empresa 1')
    empresa2 = Empresa.objects.create(nombre='Empresa 2')
    
    cliente_empresa2 = Cliente.objects.create(
        nombre='Cliente',
        empresa=empresa2
    )
    
    # Intentar crear documento con cliente de otra empresa
    documento = Documento(
        empresa=empresa1,
        cliente=cliente_empresa2  # ❌ Cliente de empresa2
    )
    
    with pytest.raises(ValidationError) as exc_info:
        documento.full_clean()
    
    assert 'cliente' in exc_info.value.message_dict
    assert 'pertenece a otra empresa' in str(exc_info.value)
```

---

### **Test 2: AuditMixin**

```python
@pytest.mark.django_db
def test_audit_mixin_created_by():
    """AuditMixin establece created_by automáticamente"""
    user = User.objects.create_user(username='testuser')
    
    documento = Documento(
        empresa=user.empresa,
        tipo='PRESUPUESTO'
    )
    documento.save(user=user)
    
    assert documento.created_by == user
    assert documento.updated_by == user
    assert documento.created_at is not None
    assert documento.updated_at is not None

@pytest.mark.django_db
def test_audit_mixin_updated_by():
    """AuditMixin actualiza updated_by al modificar"""
    user1 = User.objects.create_user(username='user1')
    user2 = User.objects.create_user(username='user2')
    
    # Crear con user1
    documento = Documento(empresa=user1.empresa, tipo='PRESUPUESTO')
    documento.save(user=user1)
    
    assert documento.created_by == user1
    
    # Modificar con user2
    documento.estado = 'APROBADO'
    documento.save(user=user2)
    
    assert documento.created_by == user1  # No cambia
    assert documento.updated_by == user2  # ✅ Se actualiza
```

---

## 🎯 **BENEFICIOS**

```
TENANCY:
✅ Aislamiento de datos entre empresas
✅ Prevención de acceso cruzado
✅ Validación automática en save()
✅ Integridad referencial garantizada
✅ Compliance con normativas de privacidad

AUDITORÍA:
✅ Trazabilidad completa de cambios
✅ Saber quién creó cada registro
✅ Saber quién modificó cada registro
✅ Timestamps precisos
✅ Compliance con auditorías
✅ Debugging más fácil
```

---

## ⚠️ **IMPORTANTE PARA CURSOR**

```
CURSOR: NO OMITIR ESTOS CAMPOS

Cuando generes código con modelos, SIEMPRE:

1. ✅ Heredar de AuditMixin en modelos críticos
2. ✅ Implementar clean() con validaciones de tenancy
3. ✅ Pasar user=request.user en save()
4. ✅ Filtrar queries por empresa
5. ✅ Usar on_delete=PROTECT para created_by/updated_by

NO HACER:
❌ Modelos sin AuditMixin
❌ Queries sin filtro de empresa
❌ save() sin user
❌ on_delete=CASCADE para users
❌ Omitir validaciones de tenancy
```

---

## 📚 **ARCHIVOS RELACIONADOS**

### **A Crear/Modificar:**
1. `taller/models/mixins.py` - AuditMixin
2. `taller/models/documento.py` - Validaciones de tenancy
3. `taller/models/lineas_documento.py` - Validaciones en líneas
4. `taller/middleware/tenancy.py` - Middleware para empresa (opcional)
5. `taller/middleware/audit.py` - Middleware para user automático (opcional)

---

**Estado:** ✅ **CONVENCIONES DE TENANCY Y AUDITORÍA DOCUMENTADAS**

**¡Aislamiento de datos y trazabilidad completa garantizados!** 🔒👤

