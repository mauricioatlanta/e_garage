#!/usr/bin/env python
"""
Script para crear el template futuristic_company_settings.html en el servidor
"""
import os

# Ruta donde debe ir el archivo
template_dir = "/home/atlantareciclajes/apps/egarage/releases/2025-11-17_1615_eg/templates/taller/us/en/settings"
template_path = os.path.join(template_dir, "futuristic_company_settings.html")

# Contenido completo del template
template_content = """{% extends "base.html" %}
{% load static %}
{% load country_url %}

{% block title %}⚡ FUTURISTIC COMPANY CONTROL CENTER ⚡{% endblock %}

{% block extra_css %}
<style>
    /* ===== FUTURISTIC ANIMATED BACKGROUND ===== */
    body {
        background: linear-gradient(45deg, #0a0a0a, #1a1a2e, #16213e, #0f3460);
        background-size: 400% 400%;
        animation: gradientShift 15s ease infinite;
        min-height: 100vh;
        overflow-x: hidden;
    }

    @keyframes gradientShift {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    /* ===== FLOATING PARTICLES BACKGROUND ===== */
    .particles {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        pointer-events: none;
        z-index: 1;
    }

    .particle {
        position: absolute;
        width: 2px;
        height: 2px;
        background: #00ffff;
        border-radius: 50%;
        animation: float 6s infinite linear;
        opacity: 0.7;
    }

    @keyframes float {
        0% {
            transform: translateY(100vh) rotate(0deg);
            opacity: 0;
        }
        10% {
            opacity: 0.7;
        }
        90% {
            opacity: 0.7;
        }
        100% {
            transform: translateY(-100px) rotate(360deg);
            opacity: 0;
        }
    }

    /* ===== NEON GLOW EFFECTS ===== */
    .neon-glow {
        box-shadow:
            0 0 5px #00ffff,
            0 0 10px #00ffff,
            0 0 15px #00ffff,
            0 0 20px #00ffff;
        animation: neonPulse 2s ease-in-out infinite alternate;
    }

    @keyframes neonPulse {
        from {
            box-shadow:
                0 0 5px #00ffff,
                0 0 10px #00ffff,
                0 0 15px #00ffff,
                0 0 20px #00ffff;
        }
        to {
            box-shadow:
                0 0 10px #00ffff,
                0 0 20px #00ffff,
                0 0 30px #00ffff,
                0 0 40px #00ffff;
        }
    }

    /* ===== MAIN CONTAINER ===== */
    .futuristic-container {
        position: relative;
        z-index: 10;
        padding: 2rem;
        max-width: 1400px;
        margin: 0 auto;
    }

    /* ===== HEADER SECTION ===== */
    .control-header {
        text-align: center;
        margin-bottom: 3rem;
        padding: 2rem;
        background: rgba(0, 0, 0, 0.8);
        border: 2px solid #00ffff;
        border-radius: 20px;
        backdrop-filter: blur(10px);
        position: relative;
        overflow: hidden;
    }

    .control-header::before {
        content: '';
        position: absolute;
        top: -2px;
        left: -2px;
        right: -2px;
        bottom: -2px;
        background: linear-gradient(45deg, #00ffff, #ff00ff, #ffff00, #00ffff);
        border-radius: 20px;
        z-index: -1;
        animation: borderRotate 3s linear infinite;
    }

    @keyframes borderRotate {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }

    .control-title {
        font-size: 3rem;
        font-weight: 900;
        background: linear-gradient(45deg, #00ffff, #ff00ff, #ffff00);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        text-shadow: 0 0 30px rgba(0, 255, 255, 0.5);
        margin-bottom: 1rem;
        animation: titleGlow 2s ease-in-out infinite alternate;
    }

    @keyframes titleGlow {
        from { text-shadow: 0 0 30px rgba(0, 255, 255, 0.5); }
        to { text-shadow: 0 0 50px rgba(0, 255, 255, 0.8), 0 0 70px rgba(255, 0, 255, 0.3); }
    }

    .control-subtitle {
        color: #00ffff;
        font-size: 1.2rem;
        font-weight: 300;
        letter-spacing: 2px;
        text-transform: uppercase;
    }

    /* ===== CONTROL PANELS ===== */
    .control-panel {
        background: rgba(0, 0, 0, 0.9);
        border: 2px solid #00ffff;
        border-radius: 15px;
        padding: 2rem;
        margin-bottom: 2rem;
        backdrop-filter: blur(15px);
        position: relative;
        transition: all 0.3s ease;
    }

    .control-panel:hover {
        transform: translateY(-5px);
        box-shadow:
            0 10px 30px rgba(0, 255, 255, 0.3),
            0 0 20px rgba(0, 255, 255, 0.2);
    }

    .panel-header {
        display: flex;
        align-items: center;
        margin-bottom: 2rem;
        padding-bottom: 1rem;
        border-bottom: 1px solid #00ffff;
    }

    .panel-icon {
        font-size: 2rem;
        color: #00ffff;
        margin-right: 1rem;
        animation: iconPulse 2s ease-in-out infinite;
    }

    @keyframes iconPulse {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.1); }
    }

    .panel-title {
        color: #00ffff;
        font-size: 1.5rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    /* ===== FORM ELEMENTS ===== */
    .futuristic-input {
        background: rgba(0, 0, 0, 0.8);
        border: 2px solid #333;
        border-radius: 10px;
        padding: 1rem;
        color: #00ffff;
        font-size: 1rem;
        width: 100%;
        transition: all 0.3s ease;
        backdrop-filter: blur(5px);
    }

    .futuristic-input:focus {
        outline: none;
        border-color: #00ffff;
        box-shadow:
            0 0 10px rgba(0, 255, 255, 0.5),
            inset 0 0 10px rgba(0, 255, 255, 0.1);
        background: rgba(0, 0, 0, 0.9);
    }

    .futuristic-input::placeholder {
        color: #666;
        font-style: italic;
    }

    .futuristic-label {
        color: #00ffff;
        font-weight: 600;
        margin-bottom: 0.5rem;
        display: block;
        text-transform: uppercase;
        letter-spacing: 1px;
        font-size: 0.9rem;
    }

    /* ===== BUTTONS ===== */
    .cyber-button {
        background: linear-gradient(45deg, #00ffff, #0080ff);
        border: none;
        border-radius: 10px;
        padding: 1rem 2rem;
        color: #000;
        font-weight: 700;
        font-size: 1rem;
        text-transform: uppercase;
        letter-spacing: 1px;
        cursor: pointer;
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
        box-shadow: 0 5px 15px rgba(0, 255, 255, 0.3);
    }

    .cyber-button::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
        transition: left 0.5s;
    }

    .cyber-button:hover::before {
        left: 100%;
    }

    .cyber-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(0, 255, 255, 0.5);
    }

    .cyber-button:active {
        transform: translateY(0);
    }

    .cyber-button.danger {
        background: linear-gradient(45deg, #ff0080, #ff4040);
        box-shadow: 0 5px 15px rgba(255, 0, 128, 0.3);
    }

    .cyber-button.danger:hover {
        box-shadow: 0 8px 25px rgba(255, 0, 128, 0.5);
    }

    /* ===== LOGO PREVIEW ===== */
    .logo-preview {
        border: 2px dashed #00ffff;
        border-radius: 10px;
        padding: 2rem;
        text-align: center;
        background: rgba(0, 0, 0, 0.5);
        margin: 1rem 0;
        transition: all 0.3s ease;
    }

    .logo-preview:hover {
        border-color: #ff00ff;
        background: rgba(0, 0, 0, 0.7);
    }

    .logo-preview img {
        max-width: 200px;
        max-height: 200px;
        border-radius: 10px;
        box-shadow: 0 0 20px rgba(0, 255, 255, 0.3);
    }

    /* ===== TECHNICIAN GRID ===== */
    .technician-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
        gap: 1.5rem;
        margin-top: 2rem;
    }

    .technician-card {
        background: rgba(0, 0, 0, 0.8);
        border: 2px solid #333;
        border-radius: 15px;
        padding: 1.5rem;
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }

    .technician-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, #00ffff, #ff00ff, #ffff00);
        transform: scaleX(0);
        transition: transform 0.3s ease;
    }

    .technician-card:hover::before {
        transform: scaleX(1);
    }

    .technician-card:hover {
        border-color: #00ffff;
        transform: translateY(-5px);
        box-shadow: 0 10px 30px rgba(0, 255, 255, 0.2);
    }

    .technician-card.active {
        border-color: #00ff00;
    }

    .technician-card.inactive {
        border-color: #ff4040;
        opacity: 0.7;
    }

    .technician-name {
        color: #00ffff;
        font-size: 1.2rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }

    .technician-info {
        color: #ccc;
        font-size: 0.9rem;
        margin-bottom: 1rem;
    }

    .technician-status {
        display: inline-block;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        text-transform: uppercase;
    }

    .status-active {
        background: rgba(0, 255, 0, 0.2);
        color: #00ff00;
        border: 1px solid #00ff00;
    }

    .status-inactive {
        background: rgba(255, 64, 64, 0.2);
        color: #ff4040;
        border: 1px solid #ff4040;
    }

    /* ===== RESPONSIVE DESIGN ===== */
    @media (max-width: 768px) {
        .control-title {
            font-size: 2rem;
        }

        .futuristic-container {
            padding: 1rem;
        }

        .control-panel {
            padding: 1.5rem;
        }

        .technician-grid {
            grid-template-columns: 1fr;
        }
    }

    /* ===== LOADING ANIMATION ===== */
    .loading-spinner {
        display: inline-block;
        width: 20px;
        height: 20px;
        border: 3px solid rgba(0, 255, 255, 0.3);
        border-radius: 50%;
        border-top-color: #00ffff;
        animation: spin 1s ease-in-out infinite;
    }

    @keyframes spin {
        to { transform: rotate(360deg); }
    }

    /* ===== SUCCESS/ERROR MESSAGES ===== */
    .cyber-message {
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        font-weight: 600;
        text-align: center;
        animation: messageSlide 0.5s ease-out;
    }

    @keyframes messageSlide {
        from {
            opacity: 0;
            transform: translateY(-20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    .message-success {
        background: rgba(0, 255, 0, 0.2);
        border: 2px solid #00ff00;
        color: #00ff00;
    }

    .message-error {
        background: rgba(255, 0, 0, 0.2);
        border: 2px solid #ff4040;
        color: #ff4040;
    }
</style>
{% endblock %}

{% block content %}
<!-- ===== FLOATING PARTICLES ===== -->
<div class="particles" id="particles"></div>

<div class="futuristic-container">
    <!-- ===== HEADER ===== -->
    <div class="control-header">
        <h1 class="control-title">⚡ CONTROL CENTER ⚡</h1>
        <p class="control-subtitle">Advanced Company Configuration & Management System</p>
    </div>

    <!-- ===== MESSAGES ===== -->
    {% if messages %}
        {% for message in messages %}
            <div class="cyber-message message-{{ message.tags|default:'success' }}">
                {{ message }}
            </div>
        {% endfor %}
    {% endif %}

    <!-- ===== COMPANY PROFILE PANEL ===== -->
    <div class="control-panel neon-glow">
        <div class="panel-header">
            <div class="panel-icon">🏢</div>
            <h2 class="panel-title">Company Profile</h2>
        </div>

        <form method="post" enctype="multipart/form-data" id="companyForm">
            {% csrf_token %}
            <input type="hidden" name="section" value="company">

            <div class="row">
                <div class="col-md-6">
                    <label class="futuristic-label">Company Name</label>
                    <input type="text" name="company_name" class="futuristic-input"
                           value="{{ company_settings.company_name|default:'' }}"
                           placeholder="Enter your company name">
                </div>
                <div class="col-md-6">
                    <label class="futuristic-label">Tagline / Motto</label>
                    <input type="text" name="tagline" class="futuristic-input"
                           value="{{ company_settings.tagline|default:'' }}"
                           placeholder="Your company motto">
                </div>
            </div>

            <div class="row mt-3">
                <div class="col-md-6">
                    <label class="futuristic-label">Address</label>
                    <textarea name="address" class="futuristic-input" rows="3"
                              placeholder="Company address">{{ company_settings.address|default:'' }}</textarea>
                </div>
                <div class="col-md-6">
                    <label class="futuristic-label">Contact Information</label>
                    <input type="text" name="phone" class="futuristic-input mb-2"
                           value="{{ company_settings.phone|default:'' }}"
                           placeholder="Phone number">
                    <input type="email" name="email" class="futuristic-input mb-2"
                           value="{{ company_settings.email|default:'' }}"
                           placeholder="Email address">
                    <input type="url" name="website" class="futuristic-input"
                           value="{{ company_settings.website|default:'' }}"
                           placeholder="Website URL">
                </div>
            </div>

            <div class="row mt-3">
                <div class="col-md-12">
                    <label class="futuristic-label">Company Logo</label>
                    <div class="logo-preview">
                        {% if company_settings.logo %}
                            <img src="{{ company_settings.logo.url }}" alt="Current Logo" id="logoPreview">
                        {% else %}
                            <div style="color: #666; font-style: italic;">No logo uploaded</div>
                        {% endif %}
                    </div>
                    <input type="file" name="logo" class="futuristic-input" accept="image/*"
                           onchange="previewLogo(this)">
                </div>
            </div>

            <div class="row mt-3">
                <div class="col-md-6">
                    <label class="futuristic-label">Primary Color</label>
                    <input type="color" name="primary_color" class="futuristic-input"
                           value="{{ company_settings.primary_color|default:'#00ffff' }}">
                </div>
                <div class="col-md-6">
                    <label class="futuristic-label">Currency</label>
                    <select name="currency" class="futuristic-input">
                        <option value="USD" {% if company_settings.currency == 'USD' %}selected{% endif %}>USD - US Dollar</option>
                        <option value="CLP" {% if company_settings.currency == 'CLP' %}selected{% endif %}>CLP - Chilean Peso</option>
                        <option value="EUR" {% if company_settings.currency == 'EUR' %}selected{% endif %}>EUR - Euro</option>
                        <option value="MXN" {% if company_settings.currency == 'MXN' %}selected{% endif %}>MXN - Mexican Peso</option>
                    </select>
                </div>
            </div>

            <div class="text-center mt-4">
                <button type="submit" class="cyber-button">
                    <span class="loading-spinner" style="display: none;"></span>
                    💾 SAVE COMPANY PROFILE
                </button>
            </div>
        </form>
    </div>

    <!-- ===== TECHNICIAN MANAGEMENT PANEL ===== -->
    <div class="control-panel neon-glow">
        <div class="panel-header">
            <div class="panel-icon">👨‍🔧</div>
            <h2 class="panel-title">Technician Management</h2>
        </div>

        <!-- Add New Technician Form -->
        <form method="post" id="technicianForm">
            {% csrf_token %}
            <input type="hidden" name="section" value="technician">
            <input type="hidden" name="action" value="add">

            <div class="row">
                <div class="col-md-4">
                    <label class="futuristic-label">Full Name</label>
                    <input type="text" name="nombre" class="futuristic-input"
                           placeholder="Technician name" required>
                </div>
                <div class="col-md-4">
                    <label class="futuristic-label">Phone</label>
                    <input type="tel" name="telefono" class="futuristic-input"
                           placeholder="Phone number">
                </div>
                <div class="col-md-4">
                    <label class="futuristic-label">Address</label>
                    <input type="text" name="direccion" class="futuristic-input"
                           placeholder="Address">
                </div>
            </div>

            <div class="text-center mt-3">
                <button type="submit" class="cyber-button">
                    <span class="loading-spinner" style="display: none;"></span>
                    ➕ ADD TECHNICIAN
                </button>
            </div>
        </form>

        <!-- Technicians Grid -->
        <div class="technician-grid" id="techniciansGrid">
            {% for tecnico in tecnicos %}
                <div class="technician-card {% if tecnico.activo %}active{% else %}inactive{% endif %}">
                    <div class="technician-name">{{ tecnico.nombre }}</div>
                    <div class="technician-info">
                        {% if tecnico.telefono %}
                            <div>📞 {{ tecnico.telefono }}</div>
                        {% endif %}
                        {% if tecnico.direccion %}
                            <div>📍 {{ tecnico.direccion }}</div>
                        {% endif %}
                    </div>
                    <div class="d-flex justify-content-between align-items-center">
                        <span class="technician-status {% if tecnico.activo %}status-active{% else %}status-inactive{% endif %}">
                            {% if tecnico.activo %}ACTIVE{% else %}INACTIVE{% endif %}
                        </span>
                        <div>
                            <button class="cyber-button" style="padding: 0.5rem 1rem; font-size: 0.8rem; margin-right: 0.5rem;"
                                    onclick="toggleTechnician({{ tecnico.id }}, {% if tecnico.activo %}false{% else %}true{% endif %})">
                                {% if tecnico.activo %}⏸️ DEACTIVATE{% else %}▶️ ACTIVATE{% endif %}
                            </button>
                            <button class="cyber-button danger" style="padding: 0.5rem 1rem; font-size: 0.8rem;"
                                    onclick="deleteTechnician({{ tecnico.id }})">
                                🗑️ DELETE
                            </button>
                        </div>
                    </div>
                </div>
            {% empty %}
                <div class="col-12 text-center" style="color: #666; font-style: italic; padding: 2rem;">
                    No technicians registered yet. Add your first technician above.
                </div>
            {% endfor %}
        </div>
    </div>

    <!-- ===== SYSTEM STATUS PANEL ===== -->
    <div class="control-panel">
        <div class="panel-header">
            <div class="panel-icon">📊</div>
            <h2 class="panel-title">System Status</h2>
        </div>

        <div class="row">
            <div class="col-md-3 text-center">
                <div style="color: #00ffff; font-size: 2rem; font-weight: 700;">{{ tecnicos|length }}</div>
                <div style="color: #ccc;">Technicians</div>
            </div>
            <div class="col-md-3 text-center">
                <div style="color: #00ff00; font-size: 2rem; font-weight: 700;">{{ tecnicos|length|add:"-1"|add:"1" }}</div>
                <div style="color: #ccc;">Active</div>
            </div>
            <div class="col-md-3 text-center">
                <div style="color: #ff00ff; font-size: 2rem; font-weight: 700;">{{ company_settings.company_name|length|default:0 }}</div>
                <div style="color: #ccc;">Company Name Length</div>
            </div>
            <div class="col-md-3 text-center">
                <div style="color: #ffff00; font-size: 2rem; font-weight: 700;">ONLINE</div>
                <div style="color: #ccc;">System Status</div>
            </div>
        </div>
    </div>
</div>

<script>
// ===== FLOATING PARTICLES =====
function createParticles() {
    const particlesContainer = document.getElementById('particles');
    const particleCount = 50;

    for (let i = 0; i < particleCount; i++) {
        const particle = document.createElement('div');
        particle.className = 'particle';
        particle.style.left = Math.random() * 100 + '%';
        particle.style.animationDelay = Math.random() * 6 + 's';
        particle.style.animationDuration = (Math.random() * 3 + 3) + 's';
        particlesContainer.appendChild(particle);
    }
}

// ===== LOGO PREVIEW =====
function previewLogo(input) {
    if (input.files && input.files[0]) {
        const reader = new FileReader();
        reader.onload = function(e) {
            const preview = document.getElementById('logoPreview');
            if (preview) {
                preview.src = e.target.result;
            } else {
                const logoPreview = document.querySelector('.logo-preview');
                logoPreview.innerHTML = `<img src="${e.target.result}" alt="Logo Preview" id="logoPreview" style="max-width: 200px; max-height: 200px; border-radius: 10px; box-shadow: 0 0 20px rgba(0, 255, 255, 0.3);">`;
            }
        };
        reader.readAsDataURL(input.files[0]);
    }
}

// ===== TECHNICIAN MANAGEMENT =====
function toggleTechnician(technicianId, activate) {
    const formData = new FormData();
    formData.append('csrfmiddlewaretoken', document.querySelector('[name=csrfmiddlewaretoken]').value);
    formData.append('section', 'technician');
    formData.append('action', 'toggle');
    formData.append('technician_id', technicianId);
    formData.append('activate', activate);

    fetch(window.location.href, {
        method: 'POST',
        body: formData
    })
    .then(response => response.text())
    .then(() => {
        location.reload();
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error updating technician status');
    });
}

function deleteTechnician(technicianId) {
    if (confirm('Are you sure you want to delete this technician?')) {
        const formData = new FormData();
        formData.append('csrfmiddlewaretoken', document.querySelector('[name=csrfmiddlewaretoken]').value);
        formData.append('section', 'technician');
        formData.append('action', 'delete');
        formData.append('technician_id', technicianId);

        fetch(window.location.href, {
            method: 'POST',
            body: formData
        })
        .then(response => response.text())
        .then(() => {
            location.reload();
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error deleting technician');
        });
    }
}

// ===== FORM SUBMISSION WITH LOADING =====
document.getElementById('companyForm').addEventListener('submit', function(e) {
    const button = this.querySelector('.cyber-button');
    const spinner = button.querySelector('.loading-spinner');
    button.disabled = true;
    spinner.style.display = 'inline-block';
});

document.getElementById('technicianForm').addEventListener('submit', function(e) {
    const button = this.querySelector('.cyber-button');
    const spinner = button.querySelector('.loading-spinner');
    button.disabled = true;
    spinner.style.display = 'inline-block';
});

// ===== INITIALIZE =====
document.addEventListener('DOMContentLoaded', function() {
    createParticles();

    // Add some interactive effects
    const panels = document.querySelectorAll('.control-panel');
    panels.forEach(panel => {
        panel.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-5px) scale(1.02)';
        });

        panel.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0) scale(1)';
        });
    });
});
</script>
{% endblock %}
"""

print("=" * 70)
print("CREANDO TEMPLATE EN EL SERVIDOR")
print("=" * 70)

# Crear el directorio si no existe
try:
    os.makedirs(template_dir, exist_ok=True)
    print(f"✅ Directorio creado/verificado: {template_dir}")
except Exception as e:
    print(f"❌ Error al crear directorio: {e}")
    exit(1)

# Escribir el archivo
try:
    with open(template_path, "w", encoding="utf-8") as f:
        f.write(template_content)
    print(f"✅ Archivo creado exitosamente: {template_path}")

    # Verificar el tamaño del archivo
    file_size = os.path.getsize(template_path)
    print(f"✅ Tamaño del archivo: {file_size} bytes")

    # Contar líneas
    with open(template_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        print(f"✅ Líneas en el archivo: {len(lines)}")

    print("\n" + "=" * 70)
    print("✅ TEMPLATE CREADO EXITOSAMENTE")
    print("=" * 70)

except Exception as e:
    print(f"❌ Error al escribir el archivo: {e}")
    import traceback

    traceback.print_exc()
    exit(1)
