# 🔄 CONVERSIÓN A SIGNUP TEMPLATES UNIFICADOS

## 🎯 **OBJETIVO**

Unificar todos los templates de signup para que usen la misma lógica del template genérico de allauth (`/accounts/signup/`) pero personalizados para cada país con:

1. ✅ Misma lógica de formulario (variables Django `{{ form.campo }}`)
2. ✅ Colores y banderas del país
3. ✅ Moneda nacional equivalente a dólares
4. ✅ Modismos locales

**Fecha:** 2025-11-11  
**Estado:** 🔄 **EN IMPLEMENTACIÓN**

---

## 💱 **EQUIVALENTES EN MONEDA LOCAL**

Basado en tasas de cambio aproximadas (Nov 2025):

| País | Código | Mensual ($20 USD) | Semestral ($100 USD) | Anual ($200 USD) |
|------|--------|-------------------|----------------------|------------------|
| 🇨🇱 Chile | CL | $19,000 | $95,000 | $190,000 |
| 🇧🇷 Brasil | BR | R$ 100 | R$ 500 | R$ 1,000 |
| 🇻🇪 Venezuela | VE | Bs. 730 | Bs. 3,650 | Bs. 7,300 |
| 🇵🇪 Perú | PE | S/ 75 | S/ 375 | S/ 750 |
| 🇺🇸 USA | US | $20 | $100 | $200 |

---

## 🎨 **PERSONALIZACIÓN POR PAÍS**

### **Chile (🇨🇱)**
```yaml
Idioma: Español
Colores: Azul Cian (#22d3ee)
Moneda: Pesos chilenos ($)
Precios:
  - Gratis: $0
  - Mensual: $19,000 / mes
  - Semestral: $95,000 / 6 meses (Ahorra 17%)
  - Anual: $190,000 / año (Ahorra 33%)
Modismos:
  - "Taller" (taller mecánico)
  - "Crear Cuenta"
  - "Información Personal"
```

### **Brasil (🇧🇷)**
```yaml
Idioma: Português
Colores: Verde (#00FF7F), Amarillo (#FFDF00)
Moneda: Reales (R$)
Precios:
  - Grátis: R$ 0
  - Mensal: R$ 100 / mês
  - Semestral: R$ 500 / 6 meses (Economize 17%)
  - Anual: R$ 1,000 / ano (Economize 33%)
Modismos:
  - "Oficina" (taller mecánico)
  - "Criar Conta"
  - "Informações Pessoais"
```

### **Venezuela (🇻🇪)**
```yaml
Idioma: Español
Colores: Amarillo (#FFCC00), Azul (#00247D), Rojo (#CF142B)
Moneda: Bolívares (Bs.)
Precios:
  - Gratis: Bs. 0
  - Mensual: Bs. 730 / mes
  - Semestral: Bs. 3,650 / 6 meses (Ahorra 17%)
  - Anual: Bs. 7,300 / año (Ahorra 33%)
Modismos:
  - "Taller" (taller mecánico)
  - "Crear Cuenta"
  - "Información Personal"
```

### **Perú (🇵🇪)**
```yaml
Idioma: Español
Colores: Rojo (#D91023), Blanco (#FFFFFF)
Moneda: Soles (S/)
Precios:
  - Gratis: S/ 0
  - Mensual: S/ 75 / mes
  - Semestral: S/ 375 / 6 meses (Ahorra 17%)
  - Anual: S/ 750 / año (Ahorra 33%)
Modismos:
  - "Taller" (taller mecánico)
  - "Crear Cuenta"
  - "Información Personal"
```

### **USA (🇺🇸)**
```yaml
Idioma: English
Colores: Azul Cian (#22d3ee)
Moneda: Dólares ($)
Precios:
  - Free: $0
  - Monthly: $20 / month
  - Semi-Annual: $100 / 6 months (Save 17%)
  - Annual: $200 / year (Save 33%)
Modismos:
  - "Shop" / "Workshop" (taller mecánico)
  - "Create Account"
  - "Personal Information"
```

---

## 📋 **ESTRUCTURA DEL TEMPLATE UNIFICADO**

```html
{% extends 'base.html' %}
{% load static %}

{% block title %}[Título en idioma local] - eGarage [País]{% endblock %}

{% block extra_head %}
<style>
/* Colores personalizados por país */
:root {
    --primary-color: [Color país];
    --secondary-color: [Color secundario];
}

.glass-card {
    background: linear-gradient(...);  /* Gradiente país */
    border: 2px solid var(--primary-color);
}

.brand-name {
    color: var(--primary-color);
}

/* ... más estilos personalizados */
</style>
{% endblock %}

{% block content %}
<div class="signup-container">
    <div class="glass-card">
        <!-- Logo y Marca -->
        <div class="logo-section">
            <img src="{% static 'img/egarage_logo.png' %}" alt="eGarage Logo">
            <div class="brand-name">eGarage [País] [Bandera]</div>
            <div class="subtitle">[Subtítulo en idioma local]</div>
        </div>

        <h2 class="signup-title">[Título en idioma local]</h2>

        <form method="POST" id="signup-form">
            {% csrf_token %}

            <!-- SECCIÓN 1: Datos Personales -->
            <div class="form-section">
                <h3 class="section-title">[En idioma local]</h3>
                
                <div class="form-group">
                    <label>[Nombre]</label>
                    {{ form.nombre }}
                </div>

                <div class="form-group">
                    <label>[Apellido]</label>
                    {{ form.apellido }}
                </div>

                <div class="form-group">
                    <label>[Email]</label>
                    {{ form.email }}
                </div>
            </div>

            <!-- SECCIÓN 2: Datos de la Empresa -->
            <div class="form-section">
                <h3 class="section-title">[En idioma local]</h3>
                
                <div class="form-group">
                    <label>[Nombre del Taller/Oficina]</label>
                    {{ form.nombre_taller }}
                </div>

                <div class="form-group">
                    <label>[Teléfono]</label>
                    {{ form.telefono }}
                </div>

                <div class="form-group">
                    <label>[País]</label>
                    {{ form.pais }}
                </div>
            </div>

            <!-- SECCIÓN 3: Selección de Plan -->
            <div class="form-section">
                <h3 class="section-title">[En idioma local]</h3>
                
                {{ form.plan }}

                <div class="pricing-grid">
                    <!-- Plan Gratis -->
                    <div class="plan-card" data-plan="trial" onclick="selectPlan('trial')">
                        <div class="plan-badge">[GRATIS]</div>
                        <div class="plan-name">[Trial/Prueba]</div>
                        <div class="plan-price">[Moneda] 0</div>
                        <div class="plan-period">30 [días/days]</div>
                        <ul class="plan-features">
                            <li>[Acceso completo]</li>
                            <li>[Sin tarjeta]</li>
                            <li>[Cancela cuando quieras]</li>
                        </ul>
                    </div>

                    <!-- Plan Mensual -->
                    <div class="plan-card" data-plan="mensual" onclick="selectPlan('mensual')">
                        <div class="plan-name">[Mensual/Monthly]</div>
                        <div class="plan-price">[Precio en moneda local]</div>
                        <div class="plan-period">/ [mes/month]</div>
                        <ul class="plan-features">
                            <li>[Usuarios ilimitados]</li>
                            <li>[Todas las funciones]</li>
                        </ul>
                    </div>

                    <!-- Plan Semestral -->
                    <div class="plan-card recommended" data-plan="semestral" onclick="selectPlan('semestral')">
                        <div class="plan-badge gold">⭐ [MEJOR VALOR]</div>
                        <div class="plan-name">[Semestral/Semi-Annual]</div>
                        <div class="plan-price">[Precio en moneda local]</div>
                        <div class="plan-period">/ 6 [meses/months]</div>
                        <div class="plan-savings">[Ahorra/Save] 17%</div>
                        <ul class="plan-features">
                            <li>[Todo del Mensual]</li>
                            <li>[Soporte prioritario]</li>
                        </ul>
                    </div>

                    <!-- Plan Anual (oculto inicialmente) -->
                    <div class="plan-card" data-plan="anual" onclick="selectPlan('anual')">
                        <div class="plan-badge gold">💎 [MEJOR PRECIO]</div>
                        <div class="plan-name">[Anual/Annual]</div>
                        <div class="plan-price">[Precio en moneda local]</div>
                        <div class="plan-period">/ [año/year]</div>
                        <div class="plan-savings">[Ahorra/Save] 33%</div>
                        <ul class="plan-features">
                            <li>[Todo del Semestral]</li>
                            <li>[Mejor valor]</li>
                        </ul>
                    </div>
                </div>
            </div>

            <!-- SECCIÓN 4: Seguridad (Contraseña) -->
            <div class="form-section">
                <h3 class="section-title">[Seguridad/Security]</h3>
                
                <div class="form-group">
                    <label>[Contraseña/Password]</label>
                    {{ form.password1 }}
                </div>

                <div class="form-group">
                    <label>[Confirmar Contraseña]</label>
                    {{ form.password2 }}
                </div>
            </div>

            <!-- Términos -->
            <div class="checkbox-container">
                {{ form.acepta_terminos }}
                <label>[Acepto los términos y condiciones]</label>
            </div>

            <!-- Submit Button -->
            <button type="submit" class="signup-button">[CREAR CUENTA]</button>
        </form>

        <!-- Login Link -->
        <div class="login-link">
            <span>[¿Ya tienes cuenta?] <a href="...">[:Iniciar sesión]</a></span>
        </div>
    </div>
</div>

<script>
function selectPlan(planName) {
    // Actualizar select
    const planSelect = document.getElementById('id_plan');
    if (planSelect) {
        planSelect.value = planName;
    }

    // Visual feedback
    document.querySelectorAll('.plan-card').forEach(card => {
        card.classList.remove('selected');
    });

    const selected = document.querySelector(`[data-plan="${planName}"]`);
    if (selected) {
        selected.classList.add('selected');
    }
}

// Pre-seleccionar plan trial
window.addEventListener('load', function() {
    selectPlan('trial');
});
</script>
{% endblock %}
```

---

## ✅ **VENTAJAS DEL ENFOQUE UNIFICADO**

1. ✅ **Consistencia:** Todos los países usan la misma lógica de formulario
2. ✅ **Mantenibilidad:** Cambios en la lógica se reflejan en todos los países
3. ✅ **Validación:** Django maneja la validación de formularios automáticamente
4. ✅ **Seguridad:** CSRF y validación integrados
5. ✅ **Localización:** Cada país con su idioma, moneda y colores propios
6. ✅ **Escalabilidad:** Fácil agregar nuevos países

---

## 🔄 **PLAN DE IMPLEMENTACIÓN**

### **Paso 1: Actualizar templates existentes**
- [ ] Brasil: Convertir de inputs HTML a variables Django
- [ ] Venezuela: Convertir de inputs HTML a variables Django
- [ ] Perú: Convertir de inputs HTML a variables Django
- [ ] Chile: Usar template genérico o crear específico
- [ ] USA: Usar template genérico o crear específico

### **Paso 2: Actualizar colores y monedas**
- [ ] Aplicar equivalentes en moneda local
- [ ] Mantener colores y banderas del país
- [ ] Traducir todos los textos al idioma local

### **Paso 3: Testing**
- [ ] Probar cada signup en su URL
- [ ] Verificar que los formularios se envíen correctamente
- [ ] Confirmar que los precios sean correctos

---

**Estado:** 🔄 **PREPARANDO IMPLEMENTACIÓN**

**Próximo paso:** Crear los 5 templates unificados basados en esta estructura.

