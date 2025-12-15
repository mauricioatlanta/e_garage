# FASE 4 – QA Checklist de Verificación Manual

**Fecha:** 2025-01-XX  
**Estado:** ✅ Listo para verificación manual

---

## 📋 Checklist de Verificación

### 1️⃣ Labels por País/Idioma (FASE 1)

#### ✅ Configuración Base
- [x] `taller/config/ui_labels.py` existe con todos los países
- [x] `taller/context_processors/ui_labels.py` existe
- [x] Context processor registrado en `gestion_taller/settings/base.py`
- [x] `URL_PREFIX_TO_COUNTRY` mapea correctamente todos los países

#### 🔍 Verificación Manual por País

**Chile (`/cl/...`):**
- [ ] Menú principal muestra: **"Documentos"**
- [ ] Botón "Nuevo" muestra: **"Nuevo Documento"**
- [ ] Título de página: **"Documentos"**
- [ ] Tipos muestran: **"Factura"**, **"Presupuesto"**, **"Orden de Trabajo"**
- [ ] Número de documento: **"N° Documento"**
- [ ] Botones: **"Crear Documento"**, **"Editar Documento"**

**USA (`/us/...`):**
- [ ] Menú principal muestra: **"Invoices"**
- [ ] Botón "Nuevo" muestra: **"New Invoice"**
- [ ] Título de página: **"Invoices"**
- [ ] Tipos muestran: **"Invoice"**, **"Estimate"**, **"Work Order"**
- [ ] Número de documento: **"Invoice Number"**
- [ ] Botones: **"Create Invoice"**, **"Edit Invoice"**

**México (`/mx/...`):**
- [ ] Menú principal muestra: **"Documentos"**
- [ ] Número de documento: **"Folio"** (específico de México)
- [ ] Tipo estimate: **"Cotización"** (no "Presupuesto")
- [ ] Tipo work order: **"Orden de Servicio"** (no "Orden de Trabajo")

**Perú (`/pe/...`):**
- [ ] Menú principal muestra: **"Comprobantes"**
- [ ] Tipo estimate: **"Proforma"**
- [ ] Número: **"N° Comprobante"**

**Argentina (`/ar/...`):**
- [ ] Menú principal muestra: **"Comprobantes"**
- [ ] Tipo estimate: **"Presupuesto"**
- [ ] Número: **"N° Comprobante"**

**Brasil (`/br/...`):**
- [ ] Menú principal muestra: **"Documentos"** (portugués)
- [ ] Tipo invoice: **"Nota Fiscal"**
- [ ] Tipo estimate: **"Orçamento"**
- [ ] Tipo work order: **"Ordem de Serviço"**

---

### 2️⃣ Botones "PLANES" y "PROBAR GRATIS" (FASE 2)

#### ✅ Botón "PLANES"
**Landing Chile:**
- [ ] Navegación muestra: **"PLANES"** (no "SUSCRIBIRSE")
- [ ] Click en "PLANES" → navega a `/cl/es/precios/` o `{% url 'precios' %}`
- [ ] Muestra página de pricing correctamente

**Landing USA:**
- [ ] Navegación muestra: **"PLANES"** o **"PLANS"**
- [ ] Click en "PLANES" → navega a `/us/pricing/` o `{% url 'precios' %}`
- [ ] Muestra página de pricing correctamente

#### ✅ Botón "PROBAR GRATIS"
**Landing Chile:**
- [ ] Botón muestra: **"Probar Gratis 30 días"** o **"PROBAR GRATIS"**
- [ ] Click en botón → navega a `/cl/es/accounts/signup/` o `{% url 'account_signup' %}?plan=free`
- [ ] Inicia flujo de registro para Chile
- [ ] No solo se "ilumina", realmente navega

**Landing USA:**
- [ ] Botón muestra: **"Start Free"** o **"Sign In"**
- [ ] Click en botón → navega a `/accounts/login/?country=US` o `{% url 'account_signup' %}?plan=free`
- [ ] Inicia flujo de registro para USA
- [ ] No solo se "ilumina", realmente navega

**Onboarding:**
- [ ] Botón "Probar Gratis" en onboarding Chile → `{% url 'account_signup' %}?plan=free`
- [ ] Botón "Start Free" en onboarding USA → `{% url 'account_signup' %}?plan=free`
- [ ] Botón "Planes" / "Plans" → `{% url 'precios' %}`

---

### 3️⃣ Diseño Visual Público (FASE 3)

#### ✅ Fondos y Animaciones
**Landing Chile (`templates/public/landing_chile_completa.html`):**
- [ ] Fondo es estático (gradiente suave, sin animación)
- [ ] NO hay partículas flotantes visibles
- [ ] NO hay líneas animadas
- [ ] NO hay efectos de rotación o spin
- [ ] Paleta reducida: azul industrial oscuro + verde emerald (CTAs)

**Landing USA (`templates/us/en/landing/landing_usa.html`):**
- [ ] Fondo es estático (gradiente suave, sin animación)
- [ ] NO hay partículas flotantes visibles
- [ ] NO hay líneas animadas
- [ ] NO hay efectos de rotación o spin
- [ ] Paleta reducida: azul industrial oscuro + verde emerald (CTAs)

**Onboarding (`templates/*/onboarding/bienvenida.html`):**
- [ ] Vanta.js desactivado (no hay globo animado)
- [ ] Grid background desactivado
- [ ] Scan line desactivado
- [ ] Fondo estático profesional

**Pricing (`templates/suspension/precios.html`):**
- [ ] Grid animada desactivada
- [ ] Partículas flotantes desactivadas
- [ ] Líneas de energía desactivadas
- [ ] Fondo estático profesional
- [ ] Tarjetas con glass morphism simplificado

#### ✅ Paleta de Colores
- [ ] Color primario: Azul industrial oscuro (`#1e293b`, `#0f172a`)
- [ ] Color secundario: Gris slate (`#475569`, `#64748b`)
- [ ] Color acento: Verde emerald (`#10b981`) solo para CTAs principales
- [ ] NO hay gradientes multicolor excesivos
- [ ] Botones usan colores sólidos (no neon/gradientes)

#### ✅ Parte Interna (NO TOCADA)
- [ ] Dashboard interno mantiene look futurista
- [ ] Centro de documentos mantiene efectos visuales
- [ ] Solo la parte pública fue simplificada

---

## 🧪 Pruebas de Navegación

### Flujo Completo Chile
1. [ ] Entrar a `/cl/es/` → Landing se ve seria, sin animaciones excesivas
2. [ ] Click en "PLANES" → Lleva a pricing
3. [ ] Click en "PROBAR GRATIS" → Lleva a registro
4. [ ] Completar registro → Login
5. [ ] Entrar a `/cl/es/documentos/lista/` → Menú muestra "Documentos"
6. [ ] Verificar textos: "Factura", "Presupuesto", "Orden de Trabajo"
7. [ ] Click en "Nuevo Documento" → Formulario muestra labels correctos

### Flujo Completo USA
1. [ ] Entrar a `/us/en/` → Landing se ve seria, sin animaciones excesivas
2. [ ] Click en "PLANES" → Lleva a pricing
3. [ ] Click en "Sign In" o "Start Free" → Lleva a registro/login
4. [ ] Completar registro → Login
5. [ ] Entrar a `/us/en/documentos/lista/` → Menú muestra "Invoices"
6. [ ] Verificar textos: "Invoice", "Estimate", "Work Order"
7. [ ] Click en "New Invoice" → Formulario muestra labels correctos

### Flujo México
1. [ ] Entrar a `/mx/es/` → Landing se ve seria
2. [ ] Login → Entrar a documentos
3. [ ] Verificar: "Folio" (no "N° Documento")
4. [ ] Verificar: "Cotización" (no "Presupuesto")
5. [ ] Verificar: "Orden de Servicio" (no "Orden de Trabajo")

---

## 📸 Pantallazos Sugeridos

Para documentación visual, capturar:

1. **Landing Chile** - Vista completa sin animaciones
2. **Landing USA** - Vista completa sin animaciones
3. **Menú interno Chile** - Mostrando "Documentos"
4. **Menú interno USA** - Mostrando "Invoices"
5. **Lista documentos Chile** - Con labels en español
6. **Lista documentos USA** - Con labels en inglés
7. **Lista documentos México** - Con "Folio" y "Cotización"
8. **Pricing page** - Sin animaciones, diseño serio

---

## ✅ Criterios de Aprobación

### FASE 1 - Labels
- ✅ Labels cambian correctamente según país/idioma
- ✅ No se rompieron las vistas
- ✅ Menú, botones y títulos usan `{{ ui_labels.* }}`

### FASE 2 - Botones
- ✅ "PLANES" siempre lleva a pricing
- ✅ "PROBAR GRATIS" siempre lleva a registro
- ✅ Todos los botones navegan (no solo se iluminan)

### FASE 3 - Diseño
- ✅ Parte pública se ve seria y profesional
- ✅ Sin animaciones excesivas en público
- ✅ Paleta de colores reducida
- ✅ Parte interna mantiene look futurista

---

## 🐛 Issues Conocidos

Ninguno reportado hasta ahora.

---

## 📝 Notas

- Los cambios están aplicados y listos para prueba
- El sistema de labels usa fallback a Chile/español si no encuentra combinación
- Las animaciones están comentadas (no eliminadas) para fácil reversión si es necesario
- El diseño futurista interno NO fue tocado

---

**Próximos Pasos:**
1. Ejecutar pruebas manuales según este checklist
2. Capturar pantallazos de cada país
3. Verificar flujos de click end-to-end
4. Ajustar microcopys si es necesario

