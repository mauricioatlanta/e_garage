# 📦 ACTUALIZACIÓN: Inclusión de Archivos Estáticos (CSS/JS)

## ✅ Cambios Realizados

### 1. Script de Preparación (`preparar_actualizacion.ps1`)

**Ubicación**: `E:\projecto\e_garage\scripts_deploy\preparar_actualizacion.ps1`

**Cambio**: Se agregó la copia de la carpeta `static/` que incluye:
- CSS personalizados (dashboard.css, etc.)
- JavaScript personalizado
- Archivos estáticos de Tailwind
- Otros recursos estáticos

**Código agregado**:
```powershell
# Static (CSS/JS)
Write-Host ""
Write-Host "Copiando static (CSS/JS)..." -ForegroundColor Cyan
$staticSource = Join-Path $PROJECT_ROOT "static"
if (Test-Path $staticSource) {
    if (Copy-Directory -Source $staticSource -Dest "static" -Description "Static completo (CSS/JS)") {
        $archivosCopiados++
    }
} else {
    Write-Host "   ADVERTENCIA: No se encontro carpeta static/ en $staticSource" -ForegroundColor Yellow
}
```

### 2. Script de Actualización en Servidor (`2_actualizar_ESTRUCTURA_COMPLETA.sh`)

**Ubicación**: `/home/atlantareciclajes/scripts_deploy/2_actualizar_ESTRUCTURA_COMPLETA.sh`

**Cambio**: Se agregó la sección para copiar archivos estáticos al servidor.

**Código agregado**:
```bash
# ============================================
# ARCHIVOS ESTÁTICOS (CSS/JS)
# ============================================

echo ""
echo "🎨 COPIANDO ARCHIVOS ESTÁTICOS (CSS/JS)..."

if [ -d "${DEPLOY_PATH}/static" ]; then
    # Copiar archivos estáticos personalizados
    if [ -d "${PROJECT_PATH}/static" ]; then
        # Hacer backup de static actual
        echo "   💾 Haciendo backup de static actual..."
        cp -r "${PROJECT_PATH}/static" "${PROJECT_PATH}/static_backup_${BACKUP_DATE}" 2>/dev/null || true
    fi
    
    # Copiar static completo
    cp -r "${DEPLOY_PATH}/static" "${PROJECT_PATH}/"
    echo "   ✅ Static copiado (CSS/JS)"
else
    echo "   ⚠️  No se encontró static/ en el paquete"
fi
```

### 3. Script de Actualización Alternativo (`2_actualizar_FIXED.sh`)

**Ubicación**: `/home/atlantareciclajes/scripts_deploy/2_actualizar_FIXED.sh`

**Cambio**: Se agregó el paso 13/13 para copiar archivos estáticos.

---

## 🚀 Cómo Usar

### Próxima Actualización

1. **En tu PC**, ejecuta:
   ```powershell
   cd E:\projecto\e_garage
   powershell -ExecutionPolicy Bypass -File .\scripts_deploy\preparar_actualizacion.ps1
   ```

2. El script ahora incluirá automáticamente:
   - ✅ Templates
   - ✅ Código Python
   - ✅ **Static (CSS/JS)** ← NUEVO
   - ✅ Configuración
   - ✅ Otras apps

3. **Sube el ZIP** al servidor con FileZilla

4. **En el servidor**, ejecuta:
   ```bash
   cd /home/atlantareciclajes/scripts_deploy/
   ./2_actualizar_ESTRUCTURA_COMPLETA.sh
   ```

5. El script copiará automáticamente los archivos estáticos y luego ejecutará `collectstatic`

---

## 📝 Notas Importantes

### Sobre `collectstatic` vs Copiar `static/`

- **`collectstatic`**: Recolecta archivos estáticos de todas las apps Django y los coloca en `STATIC_ROOT` (normalmente `staticfiles/`)
- **Copiar `static/`**: Copia archivos estáticos personalizados que no están en las apps Django

**Ambos son necesarios**:
1. Los archivos personalizados se copian desde `static/`
2. Luego `collectstatic` los recolecta junto con los de las apps Django
3. Finalmente se sirven desde `staticfiles/` en producción

### Estructura Esperada

```
deploy_atlantareciclajes/
├── templates/
├── taller/
├── static/          ← NUEVO
│   ├── css/
│   │   └── dashboard.css
│   ├── js/
│   └── ...
├── gestion_taller/
└── ...
```

---

## ✅ Verificación

Después de actualizar, verifica que los archivos estáticos se copiaron:

```bash
# En el servidor
cd /home/atlantareciclajes/apps/egarage/current/
ls -la static/css/ | head -10
ls -la static/js/ | head -10
```

---

## 🔄 Próximos Pasos

1. ✅ Script actualizado para incluir `static/`
2. ⏭️  Ejecutar `preparar_actualizacion.ps1` en la próxima actualización
3. ⏭️  Los archivos estáticos se incluirán automáticamente en el ZIP
4. ⏭️  El script de actualización los copiará al servidor

---

**¡Listo!** 🎉 Ahora los archivos CSS/JS se incluirán automáticamente en cada actualización.





