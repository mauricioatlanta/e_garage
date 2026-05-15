# 📦 Archivos Modificados - Actualización de Signup y Botones USA

## Fecha: $(date +%Y-%m-%d)

## 📝 Archivos Modificados

### 1. Templates de Signup
- ✅ `templates/account/signup.html` - Template principal mejorado con:
  - Campos: Nombre, Apellido, Teléfono, Email, País, Contraseñas
  - Sección de planes (Trial, Mensual, Semestral, Anual)
  - Estilos mejorados con fondos oscuros y contraste
  - Bordes neon y efectos visuales

- ✅ `templates/us/en/account/signup.html` - Copiado template mejorado para USA
  - Misma mecánica que Chile
  - Mismos campos y funcionalidad

### 2. Templates de Bienvenida USA
- ✅ `templates/us/en/onboarding/bienvenida.html` - Botones actualizados:
  - Botón "Subscribe" ahora redirige a `/accounts/signup/?from=us`
  - Botones con estilo futurista unificado
  - Bordes neon brillantes
  - Fondos elegantes con gradientes
  - Espaciado aumentado (gap-5)

- ✅ `templates/us/es/onboarding/bienvenida.html` - Mismos cambios en español

### 3. Formulario de Signup
- ✅ `taller/forms/custom_signup.py` - Agregado campo `country`:
  - Campo país agregado al formulario
  - Detección automática desde URL
  - Validación mejorada

### 4. URLs
- ✅ `gestion_taller/urls.py` - Ruta de signup personalizada:
  - Agregada ruta específica para CustomSignupView
  - Prioridad sobre allauth.urls

## 🚀 Instrucciones para Subir al Servidor

### Opción A: Usando el Script de Deployment Seguro

```bash
# En el servidor (SSH)
cd /ruta/a/egarage
./scripts/deploy_seguro_suscriptores.sh
```

### Opción B: Subir Archivos Manualmente

**Archivos a subir:**
1. `templates/account/signup.html`
2. `templates/us/en/account/signup.html`
3. `templates/us/en/onboarding/bienvenida.html`
4. `templates/us/es/onboarding/bienvenida.html`
5. `taller/forms/custom_signup.py`
6. `gestion_taller/urls.py`

**Método SCP (desde tu PC):**
```bash
scp templates/account/signup.html usuario@servidor:/ruta/a/egarage/templates/account/
scp templates/us/en/account/signup.html usuario@servidor:/ruta/a/egarage/templates/us/en/account/
scp templates/us/en/onboarding/bienvenida.html usuario@servidor:/ruta/a/egarage/templates/us/en/onboarding/
scp templates/us/es/onboarding/bienvenida.html usuario@servidor:/ruta/a/egarage/templates/us/es/onboarding/
scp taller/forms/custom_signup.py usuario@servidor:/ruta/a/egarage/taller/forms/
scp gestion_taller/urls.py usuario@servidor:/ruta/a/egarage/gestion_taller/
```

**Método FileZilla/WinSCP:**
- Conectar al servidor
- Navegar a la carpeta del proyecto
- Subir los archivos manteniendo la estructura de carpetas

### Opción C: Git (si usas repositorio)

```bash
# En tu PC local
git add templates/ taller/forms/custom_signup.py gestion_taller/urls.py
git commit -m "Actualización: Signup mejorado y botones USA con estilo futurista"
git push origin main

# En el servidor
cd /ruta/a/egarage
git pull origin main
./scripts/deploy_seguro_suscriptores.sh
```

## ⚠️ Importante

- **NO se perderán datos**: El script de deployment preserva todos los datos de suscriptores
- **Backup automático**: Se crea backup antes de cualquier cambio
- **Verificación**: El script verifica que los datos se preservaron

## ✅ Verificación Post-Deployment

1. Probar signup en: `http://servidor/accounts/signup/`
2. Verificar que aparecen todos los campos (Nombre, Apellido, Teléfono, Email, País)
3. Verificar que los planes se muestran correctamente
4. Probar botón "Subscribe" en: `http://servidor/us/en/bienvenida/`
5. Verificar que redirige a signup con `?from=us`
6. Verificar que los botones tienen bordes neon brillantes



