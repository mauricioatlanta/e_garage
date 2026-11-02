# 🔧 Fixes: Branding + Estabilidad

## ✅ Cambios Aplicados

### 1. **Logo Generation Infinito - SOLUCIONADO** ✅

**Problema**: El método `_resize_logo()` se ejecutaba cada vez que se guardaba `CompanySettings`, incluso si el logo no había cambiado, generando logos infinitos y consumiendo disco.

**Solución**:
- ✅ Verificación de cambio de logo antes de procesar
- ✅ Cache: verifica si el archivo ya está optimizado (< 1KB o ya en formato correcto)
- ✅ Solo procesa si el logo es nuevo o cambió
- ✅ Optimización: verifica dimensiones antes de redimensionar

**Archivo modificado**: `taller/models/company_settings.py`

**Cambios clave**:
```python
# Antes: siempre procesaba
if self.logo:
    self._resize_logo()

# Ahora: solo procesa si cambió
logo_changed = False
if self.logo:
    if not self.pk or old_instance.logo != self.logo:
        logo_changed = True

if self.logo and logo_changed:
    self._resize_logo()
```

### 2. **Paginación sin order_by() - VERIFICADO** ✅

**Problema**: ListViews con `paginate_by` sin `order_by()` generan warnings de Django.

**Verificación**:
- ✅ `DocumentoListView` (views_migrated.py): tiene `.order_by("-fecha_emision", "-id")`
- ✅ `DocumentoListView` (views_cbv.py): tiene `ordering = ("-fecha_emision", "-id")`
- ✅ `DocumentoListViewBase` (views_listado.py): tiene `.order_by("-fecha_emision", "-id")`
- ✅ `RepuestoListView`: tiene `ordering = ("nombre", "id")`
- ✅ `ClienteListView`: tiene `ordering = ("apellido", "nombre", "id")`
- ✅ `VehiculoListView`: tiene `ordering = ("-id",)`
- ✅ `ServicioListView`: tiene `ordering = ("nombre", "id")`
- ✅ `TeamListView`: tiene `.order_by("-fecha_creacion")` en queryset

**Resultado**: Todos los ListViews con paginación tienen ordenamiento definido. ✅

### 3. **Datetimes Naive - SCRIPT DE LIMPIEZA CREADO** ✅

**Problema**: Datetimes naive en seeders/fixtures pueden causar warnings y problemas de timezone.

**Solución**: Script de limpieza creado en `taller/management/commands/fix_naive_datetimes.py`

**Uso**:
```bash
# Ver qué se corregiría (sin hacer cambios)
python manage.py fix_naive_datetimes --dry-run

# Aplicar correcciones
python manage.py fix_naive_datetimes

# Corregir un modelo específico
python manage.py fix_naive_datetimes --model Documento
```

**Modelos verificados**:
- `Documento`: `fecha_emision`, `created_at`, `updated_at`
- `Cliente`: `created_at`, `updated_at`
- `Vehiculo`: `created_at`, `updated_at`
- `CompanySettings`: `created_at`, `updated_at`

## 📋 Comandos de Verificación (Servidor)

```bash
# Estado rápido
sudo systemctl status egarage-gunicorn --no-pager -l | head -n 40
sudo journalctl -u egarage-gunicorn -n 120 --no-pager

# App sanity
cd /srv/egarage
sudo -u egarage -H bash -lc 'cd /srv/egarage && /srv/egarage/venv/bin/python manage.py check'
sudo -u egarage -H bash -lc 'cd /srv/egarage && /srv/egarage/venv/bin/python manage.py migrate'

# Static/media sanity
sudo -u egarage -H bash -lc 'cd /srv/egarage && /srv/egarage/venv/bin/python manage.py collectstatic --noinput'
ls -lah /srv/egarage/media/company_logos | tail

# Verificar logos (no deberían generarse infinitos)
ls -lah /srv/egarage/media/company_logos | wc -l
```

## 🎯 Próximos Pasos Recomendados

1. **Ejecutar script de limpieza de datetimes**:
   ```bash
   python manage.py fix_naive_datetimes --dry-run  # Primero verificar
   python manage.py fix_naive_datetimes             # Luego aplicar
   ```

2. **Monitorear logs de logo**:
   - Verificar que no se generen logos duplicados
   - Revisar tamaño de `/media/company_logos/`

3. **Verificar warnings de paginación**:
   - Ejecutar `python manage.py check` y buscar warnings de paginación
   - Todos los ListViews deberían estar limpios ahora

## 📝 Notas Técnicas

- **Logo optimization**: Ahora solo se procesa cuando el logo realmente cambia o es nuevo
- **Cache check**: Verifica tamaño de archivo y formato antes de procesar
- **Timezone**: Script convierte datetimes naive a UTC (timezone-aware)
- **Performance**: Los cambios de logo no afectan el rendimiento en saves normales
