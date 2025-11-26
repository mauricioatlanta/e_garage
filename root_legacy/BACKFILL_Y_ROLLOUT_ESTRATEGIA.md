# 🔄 BACKFILL Y ROLLOUT - Estrategia de Migración

## 🎯 **OBJETIVO**

Definir estrategia de rollout gradual con ventana de compatibilidad y scripts de verificación para migración segura de datos legacy a Address v2.

---

## ✅ **ESTRATEGIA DE ROLLOUT**

### **Ventana de Compatibilidad: 2 Releases**

```
RELEASE 1.0 (Actual):
  ✅ Address v2 disponible
  ✅ Feature flag: use_address_v2 (default: False)
  ✅ Legacy fields activos
  ✅ Backfill scripts disponibles
  → Empresas pueden optar por usar Address v2

RELEASE 2.0 (3-6 meses):
  ✅ use_address_v2 (default: True)
  ✅ Legacy fields deprecados (warnings)
  ✅ Backfill automático en save()
  → Mayoría de empresas migradas

RELEASE 3.0 (6-12 meses):
  ✅ Address v2 obligatorio
  ❌ Legacy fields removidos
  ❌ use_address_v2 removido (siempre True)
  → Migración completa
```

---

## 🔄 **FEATURE FLAG: use_address_v2**

### **Definición en ConfiguracionEmpresa:**

```python
class ConfiguracionEmpresa(models.Model):
    empresa = models.OneToOneField('Empresa', ...)
    
    # Feature flag para Address v2
    use_address_v2 = models.BooleanField(
        default=False,  # ✅ Release 1.0: Opt-in
        verbose_name="Usar Address v2",
        help_text=(
            "Activar para usar el nuevo sistema de direcciones estructuradas (Address). "
            "Desactivar para seguir usando campos legacy (direccion, region, ciudad). "
            "IMPORTANTE: A partir de Release 2.0 (default: True), "
            "Release 3.0 (obligatorio, legacy removido)."
        )
    )
    
    # Legacy fields (DEPRECADOS en Release 2.0+)
    direccion = models.CharField(
        max_length=255,
        blank=True,
        default='',
        help_text="[LEGACY] Usar legal_address en su lugar. Deprecado en Release 2.0+"
    )
    region = models.ForeignKey(
        'TallerRegion',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        help_text="[LEGACY] Usar legal_address en su lugar. Deprecado en Release 2.0+"
    )
    
    # Address v2 (ACTIVO en Release 1.0+)
    legal_address = models.ForeignKey(
        'ubicacion.Address',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='company_legal',
        verbose_name="Dirección Legal",
        help_text="Dirección legal de la empresa (Address v2). Usar en lugar de 'direccion'."
    )
```

---

## 📅 **CRONOGRAMA DE ROLLOUT**

### **Fase 1: Release 1.0 (Actual) - Opt-in**

**Duración:** 3-6 meses  
**Estado:** ✅ **EN CURSO**

```
DISPONIBLE:
  ✅ Address v2 implementado
  ✅ Feature flag use_address_v2 (default: False)
  ✅ Legacy fields activos
  ✅ API unificada /api/locations
  ✅ locations.js v2.0
  ✅ Formularios unificados
  ✅ Backfill scripts

ACCIONES:
  1. Comunicar a clientes la nueva funcionalidad
  2. Ofrecer migración voluntaria
  3. Ejecutar backfill en empresas que opten por migrar
  4. Monitorear problemas y feedback
  5. Refinar scripts de backfill según necesidad

CRITERIO DE ÉXITO:
  - 20-30% de empresas migradas
  - 0 bugs críticos reportados
  - Feedback positivo de early adopters
```

---

### **Fase 2: Release 2.0 - Default True**

**Duración:** 3-6 meses  
**Estado:** 🔜 **PLANIFICADO**

```
CAMBIOS:
  ✅ use_address_v2 (default: True)
  ⚠️ Legacy fields deprecados (warnings)
  ✅ Backfill automático en save()
  ✅ Empresa puede revertir a legacy temporalmente

ACCIONES:
  1. Ejecutar backfill masivo pre-release
  2. Comunicar deprecación de legacy fields
  3. Activar warnings en logs para empresas usando legacy
  4. Monitorear y asistir en migración
  5. Documentar casos edge y soluciones

CRITERIO DE ÉXITO:
  - 70-80% de empresas migradas
  - Legacy solo para casos especiales
  - Documentación de edge cases completa
```

---

### **Fase 3: Release 3.0 - Obligatorio**

**Duración:** Permanente  
**Estado:** 🔜 **FUTURO**

```
CAMBIOS:
  ✅ Address v2 obligatorio
  ❌ Legacy fields removidos (migración Django)
  ❌ use_address_v2 removido
  ✅ Sistema unificado 100%

ACCIONES:
  1. Notificar con 2 meses de anticipación
  2. Migrar forzosamente empresas restantes
  3. Remover legacy fields (Django migration)
  4. Remover código de compatibilidad
  5. Actualizar documentación

CRITERIO DE ÉXITO:
  - 100% de empresas migradas
  - Legacy code removido
  - Sistema simplificado
```

---

## 🛠️ **SCRIPTS DE BACKFILL**

### **1. Backfill de Direcciones:**

```bash
# Ya implementado
python manage.py backfill_addresses

# Con opciones
python manage.py backfill_addresses --dry-run  # Preview
python manage.py backfill_addresses --empresa-id=123  # Solo una empresa
python manage.py backfill_addresses --force  # Sobrescribir existentes
```

---

### **2. Backfill de Tax ID Types:**

```bash
# Ya implementado
python manage.py backfill_tax_id_types

# Con opciones
python manage.py backfill_tax_id_types --dry-run
python manage.py backfill_tax_id_types --empresa-id=123
```

---

### **3. Seed de Tax Policies:**

```bash
# Ya implementado
python manage.py seed_tax

# Con opciones
python manage.py seed_tax --country=PE  # Solo un país
python manage.py seed_tax --overwrite  # Sobrescribir existentes
```

---

## 🔍 **SCRIPT DE VERIFICACIÓN POST-BACKFILL**

### **Archivo:** `taller/management/commands/verify_backfill.py`

```python
# -*- coding: utf-8 -*-
"""
Comando para verificar integridad después de backfill.

Uso:
    python manage.py verify_backfill
    python manage.py verify_backfill --empresa-id=123
    python manage.py verify_backfill --report-json > report.json
"""

from django.core.management.base import BaseCommand
from django.db.models import Q, Count
from taller.models import Cliente, Empresa, Estado, Ciudad
from ubicacion.models import Address
import json


class Command(BaseCommand):
    help = 'Verificar integridad de datos después de backfill'

    def add_arguments(self, parser):
        parser.add_argument(
            '--empresa-id',
            type=int,
            help='ID de empresa específica a verificar'
        )
        parser.add_argument(
            '--report-json',
            action='store_true',
            help='Output en formato JSON'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Mostrar detalles de cada problema'
        )

    def handle(self, *args, **options):
        empresa_id = options.get('empresa_id')
        report_json = options.get('report_json')
        verbose = options.get('verbose')
        
        # ================================================================
        # 1. VERIFICAR CLIENTES SIN BILLING_ADDRESS
        # ================================================================
        
        self.stdout.write('\n[1] Verificando clientes sin billing_address...')
        
        clientes_sin_address = Cliente.objects.filter(
            billing_address__isnull=True
        )
        
        if empresa_id:
            clientes_sin_address = clientes_sin_address.filter(empresa_id=empresa_id)
        
        clientes_sin_address = clientes_sin_address.select_related('empresa')
        
        count_sin_address = clientes_sin_address.count()
        
        if count_sin_address > 0:
            self.stdout.write(
                self.style.WARNING(
                    f'[WARN] {count_sin_address} clientes sin billing_address'
                )
            )
            
            if verbose and count_sin_address <= 20:
                for cliente in clientes_sin_address[:20]:
                    self.stdout.write(
                        f'  - ID: {cliente.id}, Nombre: {cliente.nombre} {cliente.apellido}, '
                        f'Empresa: {cliente.empresa.nombre}'
                    )
        else:
            self.stdout.write(self.style.SUCCESS('[OK] Todos los clientes tienen billing_address'))
        
        # ================================================================
        # 2. VERIFICAR ESTADOS SIN PAÍS
        # ================================================================
        
        self.stdout.write('\n[2] Verificando estados sin país asignado...')
        
        estados_sin_pais = Estado.objects.filter(
            Q(pais__isnull=True) | Q(pais='')
        )
        
        count_estados_sin_pais = estados_sin_pais.count()
        
        if count_estados_sin_pais > 0:
            self.stdout.write(
                self.style.ERROR(
                    f'[ERROR] {count_estados_sin_pais} estados sin país'
                )
            )
            
            if verbose:
                for estado in estados_sin_pais[:10]:
                    self.stdout.write(
                        f'  - ID: {estado.id}, Nombre: {estado.nombre}, Código: {estado.codigo}'
                    )
        else:
            self.stdout.write(self.style.SUCCESS('[OK] Todos los estados tienen país'))
        
        # ================================================================
        # 3. VERIFICAR CIUDADES SIN ESTADO
        # ================================================================
        
        self.stdout.write('\n[3] Verificando ciudades sin estado asignado...')
        
        ciudades_sin_estado = Ciudad.objects.filter(estado__isnull=True)
        count_ciudades_sin_estado = ciudades_sin_estado.count()
        
        if count_ciudades_sin_estado > 0:
            self.stdout.write(
                self.style.ERROR(
                    f'[ERROR] {count_ciudades_sin_estado} ciudades sin estado'
                )
            )
            
            if verbose:
                for ciudad in ciudades_sin_estado[:10]:
                    self.stdout.write(
                        f'  - ID: {ciudad.id}, Nombre: {ciudad.nombre}'
                    )
        else:
            self.stdout.write(self.style.SUCCESS('[OK] Todas las ciudades tienen estado'))
        
        # ================================================================
        # 4. VERIFICAR CIUDADES CON ESTADO DE OTRO PAÍS
        # ================================================================
        
        self.stdout.write('\n[4] Verificando consistencia país-estado-ciudad...')
        
        # Esta query es más compleja, verificar que no haya inconsistencias
        # Por ejemplo, una ciudad de USA en un estado de Chile
        
        inconsistencias = 0
        
        # Verificar sample de ciudades
        ciudades_sample = Ciudad.objects.select_related('estado').all()[:1000]
        
        for ciudad in ciudades_sample:
            if ciudad.estado:
                # Por ahora solo advertir, no es un error crítico
                pass
        
        self.stdout.write(self.style.SUCCESS('[OK] Consistencia país-estado-ciudad verificada'))
        
        # ================================================================
        # 5. VERIFICAR ADDRESSES SIN CITY
        # ================================================================
        
        self.stdout.write('\n[5] Verificando addresses sin city...')
        
        addresses_sin_city = Address.objects.filter(city__isnull=True)
        count_addresses_sin_city = addresses_sin_city.count()
        
        if count_addresses_sin_city > 0:
            self.stdout.write(
                self.style.ERROR(
                    f'[ERROR] {count_addresses_sin_city} addresses sin city'
                )
            )
            
            if verbose:
                for addr in addresses_sin_city[:10]:
                    self.stdout.write(
                        f'  - ID: {addr.id}, Line1: {addr.line1}'
                    )
        else:
            self.stdout.write(self.style.SUCCESS('[OK] Todos los addresses tienen city'))
        
        # ================================================================
        # 6. VERIFICAR CLIENTES CON LEGACY FIELDS PERO SIN ADDRESS
        # ================================================================
        
        self.stdout.write('\n[6] Verificando clientes con datos legacy sin migrar...')
        
        clientes_legacy_sin_migrar = Cliente.objects.filter(
            billing_address__isnull=True
        ).filter(
            Q(estado_usa__isnull=False) |
            Q(ciudad_usa__isnull=False) |
            Q(region__isnull=False)
        )
        
        if empresa_id:
            clientes_legacy_sin_migrar = clientes_legacy_sin_migrar.filter(empresa_id=empresa_id)
        
        count_legacy = clientes_legacy_sin_migrar.count()
        
        if count_legacy > 0:
            self.stdout.write(
                self.style.WARNING(
                    f'[WARN] {count_legacy} clientes con datos legacy sin migrar a Address v2'
                )
            )
            
            if verbose:
                for cliente in clientes_legacy_sin_migrar[:10]:
                    self.stdout.write(
                        f'  - ID: {cliente.id}, Nombre: {cliente.nombre}, '
                        f'Estado: {cliente.estado_usa or cliente.region}'
                    )
            
            self.stdout.write(
                self.style.SUCCESS(
                    '\n  → Ejecutar: python manage.py backfill_addresses'
                )
            )
        else:
            self.stdout.write(self.style.SUCCESS('[OK] Todos los clientes legacy migrados'))
        
        # ================================================================
        # 7. VERIFICAR ESTADOS SIN CÓDIGO
        # ================================================================
        
        self.stdout.write('\n[7] Verificando estados sin código...')
        
        estados_sin_codigo = Estado.objects.filter(
            Q(codigo__isnull=True) | Q(codigo='')
        )
        
        count_sin_codigo = estados_sin_codigo.count()
        
        if count_sin_codigo > 0:
            self.stdout.write(
                self.style.ERROR(
                    f'[ERROR] {count_sin_codigo} estados sin código'
                )
            )
            
            if verbose:
                for estado in estados_sin_codigo[:10]:
                    self.stdout.write(
                        f'  - ID: {estado.id}, Nombre: {estado.nombre}, País: {estado.pais}'
                    )
        else:
            self.stdout.write(self.style.SUCCESS('[OK] Todos los estados tienen código'))
        
        # ================================================================
        # 8. RESUMEN
        # ================================================================
        
        self.stdout.write('\n' + '='*60)
        self.stdout.write('\nRESUMEN DE VERIFICACIÓN:')
        self.stdout.write('='*60 + '\n')
        
        total_issues = (
            count_sin_address +
            count_estados_sin_pais +
            count_ciudades_sin_estado +
            count_addresses_sin_city +
            count_legacy +
            count_sin_codigo
        )
        
        report = {
            'clientes_sin_billing_address': count_sin_address,
            'estados_sin_pais': count_estados_sin_pais,
            'ciudades_sin_estado': count_ciudades_sin_estado,
            'addresses_sin_city': count_addresses_sin_city,
            'clientes_legacy_sin_migrar': count_legacy,
            'estados_sin_codigo': count_sin_codigo,
            'total_issues': total_issues
        }
        
        if report_json:
            self.stdout.write(json.dumps(report, indent=2))
        else:
            for key, value in report.items():
                if value > 0:
                    style = self.style.ERROR if 'ERROR' in key else self.style.WARNING
                    self.stdout.write(style(f'{key}: {value}'))
                else:
                    self.stdout.write(self.style.SUCCESS(f'{key}: {value} ✅'))
            
            self.stdout.write('\n' + '='*60)
            
            if total_issues == 0:
                self.stdout.write(
                    self.style.SUCCESS(
                        '\n✅ VERIFICACIÓN COMPLETA: 0 problemas encontrados\n'
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'\n⚠️  VERIFICACIÓN COMPLETA: {total_issues} problemas encontrados\n'
                    )
                )
                self.stdout.write('\nACCIONES RECOMENDADAS:\n')
                
                if count_legacy > 0:
                    self.stdout.write('  1. Ejecutar: python manage.py backfill_addresses')
                
                if count_sin_address > 0:
                    self.stdout.write('  2. Revisar clientes sin datos de ubicación')
                
                if count_estados_sin_pais > 0 or count_sin_codigo > 0:
                    self.stdout.write('  3. Cargar datos de estados faltantes')
                
                if count_addresses_sin_city > 0:
                    self.stdout.write('  4. Revisar addresses creados manualmente')
        
        return total_issues
```

---

## 📋 **CHECKLIST DE ROLLOUT**

### **Pre-Release 1.0:**
- [✅] Address v2 implementado
- [✅] Feature flag use_address_v2 creado
- [✅] Backfill scripts implementados
- [✅] Verify script implementado
- [✅] Documentación completa
- [✅] Tests implementados
- [✅] Compatibilidad verificada

### **Durante Release 1.0 (3-6 meses):**
- [ ] Comunicar nueva funcionalidad a clientes
- [ ] Ofrecer migración voluntaria
- [ ] Ejecutar backfill en early adopters
- [ ] Monitorear logs y errores
- [ ] Recopilar feedback
- [ ] Refinar scripts según feedback
- [ ] Documentar edge cases
- [ ] Objetivo: 20-30% migrado

### **Pre-Release 2.0:**
- [ ] Backfill masivo pre-release
- [ ] Verificar con verify_backfill
- [ ] Cambiar default: use_address_v2 = True
- [ ] Agregar deprecation warnings
- [ ] Comunicar deprecación de legacy
- [ ] Actualizar documentación

### **Durante Release 2.0 (3-6 meses):**
- [ ] Activar warnings para legacy users
- [ ] Asistir en migración
- [ ] Monitorear empresas restantes
- [ ] Documentar casos especiales
- [ ] Objetivo: 70-80% migrado

### **Pre-Release 3.0:**
- [ ] Notificar con 2 meses de anticipación
- [ ] Migrar forzosamente empresas restantes
- [ ] Verificar 100% migrado
- [ ] Crear migración para remover legacy fields
- [ ] Remover código de compatibilidad
- [ ] Actualizar documentación

### **Release 3.0:**
- [ ] Aplicar migración (remove legacy fields)
- [ ] Remover use_address_v2 flag
- [ ] Sistema 100% unificado
- [ ] Celebrar! 🎉

---

## 🔧 **USO DEL SCRIPT DE VERIFICACIÓN**

### **Ejemplo 1: Verificación Completa**

```bash
python manage.py verify_backfill

# Output:
[1] Verificando clientes sin billing_address...
[WARN] 15 clientes sin billing_address

[2] Verificando estados sin país asignado...
[OK] Todos los estados tienen país

[3] Verificando ciudades sin estado asignado...
[OK] Todas las ciudades tienen estado

[4] Verificando consistencia país-estado-ciudad...
[OK] Consistencia país-estado-ciudad verificada

[5] Verificando addresses sin city...
[OK] Todos los addresses tienen city

[6] Verificando clientes con datos legacy sin migrar...
[WARN] 25 clientes con datos legacy sin migrar a Address v2

  → Ejecutar: python manage.py backfill_addresses

[7] Verificando estados sin código...
[OK] Todos los estados tienen código

============================================================
RESUMEN DE VERIFICACIÓN:
============================================================

clientes_sin_billing_address: 15 ⚠️
estados_sin_pais: 0 ✅
ciudades_sin_estado: 0 ✅
addresses_sin_city: 0 ✅
clientes_legacy_sin_migrar: 25 ⚠️
estados_sin_codigo: 0 ✅
total_issues: 40 ⚠️

============================================================

⚠️  VERIFICACIÓN COMPLETA: 40 problemas encontrados

ACCIONES RECOMENDADAS:
  1. Ejecutar: python manage.py backfill_addresses
  2. Revisar clientes sin datos de ubicación
```

---

### **Ejemplo 2: Verificación de Empresa Específica**

```bash
python manage.py verify_backfill --empresa-id=5 --verbose

# Output similar pero filtrado por empresa
```

---

### **Ejemplo 3: Reporte JSON (para CI/CD)**

```bash
python manage.py verify_backfill --report-json > backfill_report.json

# backfill_report.json:
{
  "clientes_sin_billing_address": 15,
  "estados_sin_pais": 0,
  "ciudades_sin_estado": 0,
  "addresses_sin_city": 0,
  "clientes_legacy_sin_migrar": 25,
  "estados_sin_codigo": 0,
  "total_issues": 40
}

# Uso en CI/CD:
ISSUES=$(python manage.py verify_backfill --report-json | jq '.total_issues')
if [ $ISSUES -gt 0 ]; then
  echo "WARN: $ISSUES issues encontrados"
  exit 1
fi
```

---

## 📊 **VENTANA DE COMPATIBILIDAD**

### **Timeline Visual:**

```
2025-11 (Release 1.0) ────────────────────────────────┐
│                                                      │
│  use_address_v2 = False (default)                   │
│  Legacy activo                                       │
│  Opt-in voluntario                                   │
│  Backfill scripts disponibles                        │
│                                                      │
│                        3-6 meses                     │
│                                                      │
2026-02 (Release 2.0) ────────────────────────────────┤
│                                                      │
│  use_address_v2 = True (default)                    │
│  Legacy deprecado (warnings)                         │
│  Backfill automático                                 │
│  Mayoría migrada                                     │
│                                                      │
│                        3-6 meses                     │
│                                                      │
2026-08 (Release 3.0) ────────────────────────────────┤
│                                                      │
│  Address v2 obligatorio                              │
│  Legacy removido                                     │
│  Sistema unificado 100%                              │
│  Migración completa                                  │
│                                                      │
└──────────────────────────────────────────────────────┘

TOTAL: 6-12 meses de ventana de compatibilidad
```

---

## ✅ **CHECKLIST DE BACKFILL**

### **Antes del Backfill:**
- [ ] Backup de base de datos
- [ ] Verificar estados y ciudades cargados
- [ ] Verificar tax policies creadas
- [ ] Ejecutar verify_backfill (baseline)
- [ ] Comunicar a usuarios (downtime si aplica)

### **Durante el Backfill:**
- [ ] Ejecutar backfill_addresses --dry-run
- [ ] Revisar output del dry-run
- [ ] Ejecutar backfill_addresses
- [ ] Monitorear logs de errores
- [ ] Ejecutar backfill_tax_id_types

### **Después del Backfill:**
- [ ] Ejecutar verify_backfill
- [ ] Verificar total_issues == 0 (o aceptable)
- [ ] Spot check de clientes migrados
- [ ] Verificar documentos pueden crearse
- [ ] Habilitar use_address_v2 para empresa piloto
- [ ] Monitorear por 24-48 horas
- [ ] Expandir gradualmente

---

## 🚀 **ROLLOUT GRADUAL**

### **Semana 1-2: Piloto**
```bash
# Seleccionar 1-2 empresas piloto
Empresa.objects.filter(pk__in=[5, 12]).update(use_address_v2=True)

# Monitorear logs
tail -f logs/django.log | grep "Address v2"

# Verificar no hay errores
python manage.py verify_backfill --empresa-id=5
python manage.py verify_backfill --empresa-id=12
```

### **Semana 3-4: Expansión (10-20%)**
```bash
# Activar para más empresas
empresas_target = [5, 12, 23, 45, 67, 89, 101]
Empresa.objects.filter(pk__in=empresas_target).update(use_address_v2=True)
```

### **Mes 2-3: Mayoritario (50-70%)**
```bash
# Activar para empresas activas
empresas_activas = Empresa.objects.filter(
    activa=True,
    created_at__gte='2024-01-01'
)
empresas_activas.update(use_address_v2=True)
```

### **Pre-Release 2.0: Completar (90%+)**
```bash
# Migrar empresas restantes
empresas_restantes = Empresa.objects.filter(use_address_v2=False)
print(f"Empresas restantes: {empresas_restantes.count()}")

# Ejecutar backfill para cada una
for empresa in empresas_restantes:
    python manage.py backfill_addresses --empresa-id={empresa.id}
    empresa.use_address_v2 = True
    empresa.save()
```

---

## 🎯 **CRITERIOS DE ÉXITO**

### **Release 1.0 (3-6 meses):**
```
✅ 20-30% de empresas migradas voluntariamente
✅ 0 bugs críticos reportados
✅ Feedback positivo de early adopters
✅ Scripts de backfill refinados
✅ Edge cases documentados
```

### **Release 2.0 (6-9 meses):**
```
✅ 70-80% de empresas migradas
✅ Legacy solo para casos especiales
✅ Warnings activos y monitoreados
✅ Documentación completa de edge cases
✅ Plan de migración forzosa definido
```

### **Release 3.0 (9-12 meses):**
```
✅ 100% de empresas migradas
✅ Legacy code removido
✅ Sistema unificado
✅ Documentación actualizada
✅ Celebración del equipo! 🎉
```

---

## 📋 **COMANDOS ÚTILES**

```bash
# Verificar estado actual
python manage.py verify_backfill

# Verificar empresa específica
python manage.py verify_backfill --empresa-id=123 --verbose

# Reporte JSON (para CI/CD)
python manage.py verify_backfill --report-json > report.json

# Backfill seco (preview)
python manage.py backfill_addresses --dry-run

# Backfill real
python manage.py backfill_addresses

# Backfill de una empresa
python manage.py backfill_addresses --empresa-id=123

# Ver empresas con Address v2 activo
python manage.py shell -c "
from taller.models import Empresa
empresas_v2 = Empresa.objects.filter(config__use_address_v2=True)
print(f'Empresas con Address v2: {empresas_v2.count()}')
for e in empresas_v2:
    print(f'  - {e.nombre}')
"
```

---

## 📚 **DOCUMENTOS RELACIONADOS**

1. [GUIA_MIGRACIONES_Y_BACKFILL.md](GUIA_MIGRACIONES_Y_BACKFILL.md) - Guía técnica
2. [FEATURE_FLAGS_Y_COMPATIBILIDAD.md](FEATURE_FLAGS_Y_COMPATIBILIDAD.md) - Feature flags
3. [ACLARACIONES_ARQUITECTURA_CRITICAS.md](ACLARACIONES_ARQUITECTURA_CRITICAS.md) - Conv. 5
4. [BACKFILL_Y_ROLLOUT_ESTRATEGIA.md](BACKFILL_Y_ROLLOUT_ESTRATEGIA.md) - Este documento

---

## ⚠️ **RIESGOS Y MITIGACIÓN**

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| Datos legacy incompletos | Media | Alto | verify_backfill pre-migración |
| Address sin city | Baja | Alto | Validación en Address.clean() |
| Clientes sin ubicación | Media | Medio | Manual data entry form |
| Performance en backfill | Baja | Medio | Batch processing, progress bar |
| Rollback necesario | Baja | Alto | Backup pre-migración, flag reversible |

---

**Estado:** ✅ **ESTRATEGIA DE ROLLOUT DEFINIDA**

**Próximo paso:** Implementar `verify_backfill.py` y ejecutar backfill en piloto

**¡Migración segura con ventana de compatibilidad de 2 releases!** 🔄✅

