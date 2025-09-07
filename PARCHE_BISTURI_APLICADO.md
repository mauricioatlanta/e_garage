🔧 **PARCHE BISTURÍ APLICADO - DIAGNÓSTICO INTENSIVO**

## ✅ **CAMBIOS IMPLEMENTADOS:**

### 1️⃣ **DEBUG Fuerte en Vista** 
```python
# En company_settings_view POST:
print("🧪 DEBUG: request.FILES keys ->", list(request.FILES.keys()))
if 'logo' in request.FILES:
    f = request.FILES['logo']
    print(f"🧪 DEBUG: logo name={getattr(f, 'name', None)} size={getattr(f, 'size', None)} content_type={getattr(f, 'content_type', None)}")
else:
    print("🧪 DEBUG: NO llegó 'logo' en request.FILES")
```

### 2️⃣ **Asignación Forzada de Archivo**
```python
# 🌟 Fuerza de asignación por si el ModelForm lo ignora
if 'logo' in request.FILES:
    obj.logo = request.FILES['logo']
```

### 3️⃣ **Logs de Guardado**
```python
print("🧪 DEBUG: guardado OK. logo en BD:", bool(obj.logo), "->", getattr(obj.logo, 'name', None))
print("🧪 DEBUG: logo URL:", getattr(obj.logo, 'url', None) if obj.logo else None)
```

### 4️⃣ **Cache-Busting en Template**
```html
<img src="{{ company_settings.logo.url }}?v={{ company_settings.updated_at|date:'U' }}" 
     alt="Current Logo" id="logoPreview">
```

### 5️⃣ **Consultas Corregidas**
```python
# Antes: ConfiguracionEmpresa.objects.get(user=request.user) ❌
# Ahora: ConfiguracionEmpresa.objects.get(empresa=request.user.empresa) ✅
```

## 📊 **ESTADO VERIFICADO:**

- ✅ **Usuario:** testuser_usa  
- ✅ **Empresa:** GEORGE AUTO REPAIR
- ✅ **Configuración:** Existe con logo actual: `logos/barco.png`
- ✅ **Formulario:** CompanyInfoForm con campo logo (FileInput)
- ✅ **Media:** `/media/` configurado, directorio `logos/` con 15 archivos
- ✅ **Template:** Cache-busting aplicado

## 🎯 **QUÉ REVELARÁ EL PARCHE:**

### **Si `request.FILES['logo']` aparece:**
✅ **Archivo viaja correctamente** → Se guardará forzadamente  
📋 **Problema era:** ModelForm ignorando archivo o cache viejo

### **Si NO aparece:**
❌ **Archivo no viaja** → Problema en cliente  
📋 **Revisar:** Input disabled, JS bloqueando, form corruption

### **Si se guarda pero no se ve:**
📋 **Problema:** Media serving o cache del navegador  
✅ **Solucionado con:** Cache-busting querystring

## 🔍 **INSTRUCCIONES DE PRUEBA:**

1. **Ir a:** `http://127.0.0.1:8000/cl/taller/settings/`
2. **Abrir:** DevTools → Network tab
3. **Subir:** Imagen PNG/JPG ≤ 2MB  
4. **Presionar:** 💾 UPDATE PROFILE
5. **Verificar:**
   - Request debe ser `multipart/form-data`
   - Logo debe aparecer en form data
   - Console debe mostrar logs `🧪 DEBUG:`

## 📨 **SALIDA ESPERADA:**
```
🧪 DEBUG: request.FILES keys -> ['logo']
🧪 DEBUG: logo name=mi_logo.png size=45832 content_type=image/png
🧪 DEBUG: guardado OK. logo en BD: True -> logos/mi_logo.png
🧪 DEBUG: logo URL: /media/logos/mi_logo.png
```

**Con este parche, si el archivo llega, se guardará SÍ O SÍ.** 🎯
