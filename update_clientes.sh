#!/bin/bash
# Script para actualizar lista_clientes.html en PythonAnywhere
# Ejecutar en SSH: bash update_clientes.sh

echo "🚀 Actualizando archivo de clientes..."

cd /home/atlantareciclajes/e_garage

# Backup
echo "📦 Creando backup..."
cp templates/taller/common/clientes/lista_clientes.html templates/taller/common/clientes/lista_clientes.html.backup_$(date +%Y%m%d_%H%M%S)

# Crear el nuevo archivo
echo "📝 Creando archivo nuevo..."
cat > templates/taller/common/clientes/lista_clientes.html << 'ENDOFFILE'
{% extends 'layouts/base_egarage_panel.html' %}
{% load i18n %}
{% load country_url %}
{% load static %}

<!-- 🟢 CRUZ VERDE DE VERIFICACIÓN - SI VES ESTO, EL ARCHIVO SE ACTUALIZÓ -->
<div style="position: fixed; top: 10px; right: 10px; width: 60px; height: 60px; background-color: #00ff00; z-index: 99999; border: 4px solid #000; display: flex; align-items: center; justify-content: center; font-size: 40px; border-radius: 8px; box-shadow: 0 0 20px rgba(0, 255, 0, 0.8);">✅</div>

{% block page_title %}{% trans "CLIENTS" %}{% endblock %}
{% block page_subtitle %}{% trans "Client management system" %}{% endblock %}
{% block page_icon %}👥{% endblock %}

{% block main_actions %}
<a href="{% country_url 'clientes:crear_cliente' %}"
   class="inline-flex items-center gap-2 px-5 py-3 rounded-lg bg-gradient-to-r from-emerald-600 via-lime-600 to-green-600 hover:from-emerald-500 hover:to-green-500 text-white text-base font-bold border border-emerald-400/40 shadow-lg shadow-emerald-900/40 transition-all whitespace-nowrap">
  <span class="text-xl">➕</span>
  <span class="font-extrabold tracking-wide">{% trans "NEW ENTRY" %}</span>
</a>
{% endblock %}

{% block search_bar %}
<div class="space-y-3">
  <div class="relative group">
    <div class="absolute -inset-0.5 rounded-lg bg-gradient-to-r from-cyan-600 via-fuchsia-600 to-lime-600 opacity-40 blur group-hover:opacity-60 transition-opacity"></div>
    <div class="relative flex items-center gap-3 rounded-lg border border-cyan-500/30 bg-black/40 backdrop-blur-sm px-3 py-2">
      <div class="relative flex-1">
        <form method="get" id="search-form" data-search-url="{% country_url 'ajax:buscar_clientes' %}">
          <input type="search" name="q" id="search-input" value="{{ request.GET.q }}" 
                 placeholder="{% trans 'Search clients...' %}"
                 class="w-full pl-10 pr-4 py-3 bg-black/30 text-gray-200 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-cyan-400/50 text-sm rounded-lg border border-cyan-400/20" autocomplete="off" />
          <div class="absolute left-3 top-1/2 transform -translate-y-1/2 text-cyan-400">🔍</div>
        </form>
        <div id="search-results" class="hidden absolute top-full left-0 right-0 mt-2 bg-black/95 border border-cyan-400/30 rounded-lg max-h-96 overflow-y-auto z-50 shadow-xl"></div>
      </div>
    </div>
  </div>
</div>
{% endblock %}

{% block page_extra_css %}
<style>
/* 🎨 DISEÑO FUTURISTA Y TECNOLÓGICO - OPTIMIZADO PARA MÓVIL */
:root {
    --cyber-blue: #00ffff;
    --cyber-green: #00ff88;
    --cyber-purple: #bc13fe;
    --cyber-red: #ff2a6d;
    --cyber-gold: #ffd700;
    --dark-bg: #0a0a0a;
    --card-bg: rgba(16, 20, 24, 0.95);
    --glass-bg: rgba(255, 255, 255, 0.05);
}

/* --- TYPOGRAPHY & HEADERS --- */
.font-hud { font-family: 'Orbitron', sans-serif; }
.font-tech { font-family: 'Rajdhani', sans-serif; }
.font-code { font-family: 'Share Tech Mono', monospace; }

/* --- TABLE DESKTOP --- */
.cyber-table-container {
    background: var(--card-bg);
    backdrop-filter: blur(16px);
    border: 1px solid rgba(0, 243, 255, 0.3);
    border-top: 3px solid var(--cyber-blue);
    border-radius: 12px;
    box-shadow: 0 8px 32px rgba(0, 255, 255, 0.15);
    overflow: hidden;
}

table { 
    width: 100%; 
    border-collapse: separate; 
    border-spacing: 0; 
}

thead th {
    background: rgba(0, 10, 20, 0.95);
    color: var(--cyber-blue);
    font-family: 'Orbitron', sans-serif;
    font-size: 0.75rem;
    letter-spacing: 2.5px;
    text-transform: uppercase;
    padding: 20px 24px;
    text-align: left;
    border-bottom: 2px solid rgba(0, 243, 255, 0.4);
    text-shadow: 0 0 10px rgba(0, 243, 255, 0.6);
}

tbody td {
    padding: 18px 24px;
    vertical-align: middle;
    color: #e8f0f7;
    font-family: 'Rajdhani', sans-serif;
    font-weight: 500;
    font-size: 1.05rem;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    transition: all 0.3s ease;
}

tbody tr {
    transition: all 0.3s ease;
    position: relative;
}

tbody tr:hover {
    background: rgba(0, 243, 255, 0.08);
    box-shadow: inset 0 0 20px rgba(0, 243, 255, 0.1);
}

tbody tr::before {
    content: '';
    position: absolute;
    left: 0;
    top: 0;
    bottom: 0;
    width: 3px;
    background: var(--cyber-blue);
    opacity: 0;
    transition: opacity 0.3s ease;
}

tbody tr:hover::before {
    opacity: 1;
}

.data-id { 
    color: var(--cyber-purple); 
    font-family: 'Share Tech Mono', monospace; 
    font-weight: 700;
    text-shadow: 0 0 8px rgba(188, 19, 254, 0.5);
}

.data-primary { 
    color: #fff; 
    font-weight: 700; 
    font-size: 1.15rem;
    text-shadow: 0 0 5px rgba(255, 255, 255, 0.3);
}

.data-sub { 
    color: #94a3b8; 
    font-size: 0.9rem; 
}

/* --- MOBILE CARDS - DISEÑO FUTURISTA --- */
.client-card-futuristic {
    background: linear-gradient(145deg, var(--card-bg), rgba(0, 50, 80, 0.3));
    border: 1px solid rgba(0, 243, 255, 0.3);
    border-radius: 16px;
    padding: 1.5rem;
    position: relative;
    overflow: hidden;
    transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
    box-shadow: 
        0 4px 16px rgba(0, 0, 0, 0.4),
        0 0 40px rgba(0, 243, 255, 0.05);
}

.client-card-futuristic::before {
    content: '';
    position: absolute;
    top: -2px;
    left: -2px;
    right: -2px;
    bottom: -2px;
    background: linear-gradient(45deg, 
        transparent 30%, 
        rgba(0, 212, 255, 0.4) 50%, 
        transparent 70%);
    border-radius: 16px;
    z-index: -1;
    opacity: 0;
    animation: border-glow 3s linear infinite;
    background-size: 200% 200%;
}

.client-card-futuristic:hover::before {
    opacity: 1;
}

.client-card-futuristic:hover {
    transform: translateY(-4px);
    border-color: rgba(0, 243, 255, 0.6);
    box-shadow: 
        0 8px 32px rgba(0, 0, 0, 0.5),
        0 0 60px rgba(0, 243, 255, 0.15),
        inset 0 1px 0 rgba(0, 255, 255, 0.2);
}

@keyframes border-glow {
    0% { background-position: 0% 0%; }
    50% { background-position: 100% 100%; }
    100% { background-position: 0% 0%; }
}

.client-card-header {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    margin-bottom: 1rem;
}

.client-card-title {
    font-family: 'Orbitron', sans-serif;
    font-size: 1.1rem;
    font-weight: 700;
    color: #ffffff;
    text-shadow: 0 0 10px rgba(255, 255, 255, 0.3);
    margin-bottom: 0.25rem;
}

.client-card-id {
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.75rem;
    color: var(--cyber-purple);
    text-shadow: 0 0 8px rgba(188, 19, 254, 0.6);
}

.client-card-info {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
    margin-bottom: 1rem;
    padding: 1rem;
    background: rgba(0, 0, 0, 0.3);
    border-radius: 8px;
    border: 1px solid rgba(0, 243, 255, 0.1);
}

.client-card-info-item {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    font-size: 0.9rem;
    color: #c5d4e3;
}

.client-card-info-icon {
    color: var(--cyber-blue);
    font-size: 0.9rem;
    filter: drop-shadow(0 0 4px rgba(0, 243, 255, 0.6));
    min-width: 16px;
}

/* --- BOTONES MÓVILES FUTURISTAS --- */
.client-actions {
    display: flex !important;
    gap: 0.5rem !important;
    padding-top: 1rem !important;
    border-top: 1px solid rgba(0, 243, 255, 0.2) !important;
}

.btn-futuristic {
    flex: 1 !important;
    display: flex !important;
    flex-direction: column !important;
    align-items: center !important;
    justify-content: center !important;
    gap: 0.4rem !important;
    padding: 0.85rem 0.5rem !important;
    background: linear-gradient(135deg, rgba(5, 15, 30, 0.95) 0%, rgba(10, 25, 45, 0.95) 100%) !important;
    border: 1px solid rgba(0, 212, 255, 0.4) !important;
    border-radius: 10px !important;
    text-decoration: none !important;
    color: #b0e0ff !important;
    font-family: 'Orbitron', sans-serif !important;
    font-weight: 700 !important;
    font-size: 0.75rem !important;
    letter-spacing: 0.5px !important;
    text-transform: uppercase !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    position: relative !important;
    overflow: hidden !important;
    box-shadow: 0 2px 8px rgba(0, 212, 255, 0.2) !important;
    min-height: 70px !important;
}

.btn-futuristic::before {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, 
        transparent 0%, 
        rgba(0, 212, 255, 0.2) 50%,
        transparent 100%);
    transition: left 0.5s ease;
}

.btn-futuristic:hover::before {
    left: 100%;
}

.btn-futuristic:hover {
    transform: translateY(-2px);
    border-color: rgba(0, 212, 255, 0.8);
    color: #ffffff;
    background: linear-gradient(135deg, rgba(10, 25, 45, 0.98) 0%, rgba(15, 35, 55, 0.98) 100%);
    box-shadow:
        0 0 20px rgba(0, 212, 255, 0.4),
        0 0 40px rgba(0, 212, 255, 0.2),
        inset 0 1px 0 rgba(0, 255, 255, 0.3);
}

.btn-futuristic:active {
    transform: translateY(0);
}

.btn-futuristic-icon {
    font-size: 1.6rem !important;
    filter: drop-shadow(0 0 6px rgba(0, 212, 255, 0.7)) !important;
    transition: filter 0.3s ease !important;
    display: block !important;
    visibility: visible !important;
    opacity: 1 !important;
}

.btn-futuristic:hover .btn-futuristic-icon {
    filter: drop-shadow(0 0 10px rgba(0, 255, 255, 1)) !important;
}

.btn-futuristic-text {
    font-size: 0.8rem !important;
    text-shadow: 0 0 8px rgba(0, 212, 255, 0.5) !important;
    letter-spacing: 1px !important;
    display: block !important;
    visibility: visible !important;
    opacity: 1 !important;
    color: #00ffff !important;
}

.btn-futuristic:hover .btn-futuristic-text {
    text-shadow: 0 0 12px rgba(0, 255, 255, 0.8) !important;
}

/* Botón DELETE con tema rojo */
.btn-futuristic-delete {
    border-color: rgba(239, 68, 68, 0.4);
    color: #ffb3b3;
}

.btn-futuristic-delete::before {
    background: linear-gradient(90deg, 
        transparent 0%, 
        rgba(239, 68, 68, 0.2) 50%,
        transparent 100%);
}

.btn-futuristic-delete:hover {
    border-color: rgba(239, 68, 68, 0.8);
    background: linear-gradient(135deg, rgba(30, 10, 15, 0.98) 0%, rgba(45, 15, 20, 0.98) 100%);
    box-shadow:
        0 0 20px rgba(239, 68, 68, 0.4),
        0 0 40px rgba(239, 68, 68, 0.2),
        inset 0 1px 0 rgba(255, 150, 150, 0.3);
}

.btn-futuristic-delete .btn-futuristic-icon {
    filter: drop-shadow(0 0 6px rgba(239, 68, 68, 0.7));
}

.btn-futuristic-delete:hover .btn-futuristic-icon {
    filter: drop-shadow(0 0 10px rgba(255, 100, 100, 1));
}

/* --- SEARCH RESULTS --- */
.search-result-item {
    padding: 14px 20px;
    border-bottom: 1px solid rgba(255,255,255,0.05);
    cursor: pointer;
    transition: all 0.3s ease;
    position: relative;
}

.search-result-item::before {
    content: '';
    position: absolute;
    left: 0;
    top: 0;
    bottom: 0;
    width: 0;
    background: var(--cyber-blue);
    transition: width 0.3s ease;
}

.search-result-item:hover {
    background: rgba(0, 243, 255, 0.1);
    padding-left: 28px;
}

.search-result-item:hover::before {
    width: 4px;
}

/* --- BUTTONS DESKTOP --- */
.btn-icon-only {
    width: 36px;
    height: 36px;
    display: flex;
    align-items: center;
    justify-content: center;
    border: 1px solid rgba(0, 243, 255, 0.3);
    color: #94a3b8;
    border-radius: 6px;
    transition: all 0.3s ease;
    background: rgba(0, 10, 20, 0.6);
    position: relative;
    overflow: hidden;
}

.btn-icon-only::before {
    content: '';
    position: absolute;
    inset: 0;
    background: linear-gradient(45deg, transparent, rgba(0, 243, 255, 0.2), transparent);
    opacity: 0;
    transition: opacity 0.3s ease;
}

.btn-icon-only:hover::before {
    opacity: 1;
}

.btn-icon-only:hover {
    color: #fff;
    border-color: var(--cyber-blue);
    box-shadow: 0 0 15px rgba(0, 243, 255, 0.4);
    transform: translateY(-2px);
}

.btn-delete:hover {
    color: var(--cyber-red);
    border-color: var(--cyber-red);
    box-shadow: 0 0 15px rgba(255, 42, 109, 0.4);
}

/* --- PAGINATION --- */
.pagination-wrapper {
    padding: 20px;
    border-top: 1px solid rgba(0, 243, 255, 0.2);
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: rgba(0, 5, 10, 0.5);
}

.page-btn {
    width: 36px; 
    height: 36px;
    display: flex; 
    align-items: center; 
    justify-content: center;
    border: 1px solid rgba(0, 243, 255, 0.3);
    color: #94a3b8;
    font-family: 'Share Tech Mono';
    font-size: 13px;
    transition: all 0.3s ease;
    border-radius: 6px;
    background: rgba(0, 10, 20, 0.6);
}

.page-btn:hover:not(.disabled) {
    border-color: var(--cyber-blue);
    color: var(--cyber-blue);
    box-shadow: 0 0 15px rgba(0, 243, 255, 0.3);
    transform: translateY(-2px);
}

.page-current { 
    background: var(--cyber-blue); 
    color: #000; 
    font-weight: bold; 
    border-color: var(--cyber-blue);
    box-shadow: 0 0 20px rgba(0, 243, 255, 0.5);
}

/* --- RESPONSIVE OPTIMIZATIONS --- */
@media screen and (max-width: 768px) {
    .client-card-futuristic {
        padding: 1.25rem !important;
    }
    
    .client-card-title {
        font-size: 1rem !important;
    }
    
    .btn-futuristic {
        min-height: 75px !important;
        padding: 0.9rem 0.6rem !important;
        flex-direction: column !important;
        align-items: center !important;
        justify-content: center !important;
    }
    
    .btn-futuristic-icon {
        font-size: 1.8rem !important;
        display: block !important;
        visibility: visible !important;
        opacity: 1 !important;
    }
    
    .btn-futuristic-text {
        font-size: 0.85rem !important;
        letter-spacing: 1.2px !important;
        display: block !important;
        visibility: visible !important;
        opacity: 1 !important;
        color: #00ffff !important;
        text-shadow: 0 0 10px rgba(0, 255, 255, 0.8) !important;
    }
    
    /* FORZAR VISIBILIDAD EN TODOS LOS BOTONES DE ACCIÓN */
    .client-actions {
        display: flex !important;
        visibility: visible !important;
        opacity: 1 !important;
    }
    
    .client-actions .btn-futuristic {
        display: flex !important;
        visibility: visible !important;
        opacity: 1 !important;
    }
    
    .client-actions .btn-futuristic-icon,
    .client-actions .btn-futuristic-text {
        display: block !important;
        visibility: visible !important;
        opacity: 1 !important;
    }
}

@media screen and (max-width: 480px) {
    .client-card-futuristic {
        padding: 1rem !important;
    }
    
    .btn-futuristic {
        min-height: 70px !important;
        font-size: 0.7rem !important;
        flex-direction: column !important;
    }
    
    .btn-futuristic-icon {
        font-size: 1.6rem !important;
        display: block !important;
        visibility: visible !important;
        opacity: 1 !important;
    }
    
    .btn-futuristic-text {
        font-size: 0.75rem !important;
        display: block !important;
        visibility: visible !important;
        opacity: 1 !important;
        color: #00ffff !important;
        text-shadow: 0 0 10px rgba(0, 255, 255, 1) !important;
    }
}

/* Empty State */
.empty-state {
    text-align: center;
    padding: 4rem 2rem;
}

.empty-state-icon {
    font-size: 5rem;
    opacity: 0.4;
    filter: drop-shadow(0 0 20px rgba(0, 243, 255, 0.3));
    margin-bottom: 1.5rem;
}

.empty-state-title {
    font-family: 'Orbitron', sans-serif;
    font-size: 1.75rem;
    font-weight: 700;
    color: #e8f0f7;
    margin-bottom: 1rem;
    text-shadow: 0 0 10px rgba(255, 255, 255, 0.2);
}

.empty-state-text {
    color: #94a3b8;
    margin-bottom: 2rem;
    max-width: 500px;
    margin-left: auto;
    margin-right: auto;
}
</style>
{% endblock %}

{% block panel_content %}
<!-- Desktop: Tabla -->
<div class="hidden md:block cyber-table-container shadow-2xl">
    <div class="overflow-x-auto">
        <table class="w-full">
            <thead>
                <tr>
                    <th width="80">ID</th>
                    <th>{% trans "Entity Profile" %}</th>
                    <th class="hidden md:table-cell">{% trans "Contact Node" %}</th>
                    <th class="hidden md:table-cell">{% trans "Comm. Link" %}</th>
                    <th class="hidden xl:table-cell">{% trans "Location" %}</th>
                    <th class="text-right pr-8">{% trans "Operations" %}</th>
                </tr>
            </thead>
            <tbody>
                {% for cliente in cliente_list %}
                <tr class="group">
                    <td class="font-code data-id pl-6">#{{ cliente.pk }}</td>
                    <td>
                        <div class="flex flex-col">
                            <span class="data-primary">{{ cliente.nombre }} {{ cliente.apellido }}</span>
                            <span class="md:hidden data-sub mt-1 font-code text-cyan-500">{{ cliente.email }}</span>
                        </div>
                    </td>
                    <td class="hidden md:table-cell">
                        <span class="data-sub">{{ cliente.email|default:'<span class="opacity-30">N/A</span>' }}</span>
                    </td>
                    <td class="hidden md:table-cell font-code text-sm text-cyan-100/70">
                        {{ cliente.telefono|default:'<span class="opacity-30">---</span>' }}
                    </td>
                    <td class="hidden xl:table-cell">
                        <div class="flex items-center gap-2 text-gray-300">
                            <i class="fas fa-map-marker-alt text-cyan-500/50 text-xs"></i>
                            {% if cliente.empresa.pais == 'US' %}
                                {% if cliente.ciudad_usa %}{{ cliente.ciudad_usa }}, {{ cliente.estado_usa }}{% else %}<span class="opacity-30">UNKNOWN</span>{% endif %}
                            {% else %}
                                {% if cliente.ciudad %}{{ cliente.ciudad.nombre }}{% else %}<span class="opacity-30">UNKNOWN</span>{% endif %}
                            {% endif %}
                        </div>
                    </td>
                    <td class="text-right pr-4 sm:pr-6">
                        <div class="flex items-center justify-end gap-2 sm:gap-2 action-group">
                            <a href="{% country_url 'clientes:ver_cliente' cliente.pk %}" class="btn-icon-only w-10 h-10 sm:w-8 sm:h-8 flex items-center justify-center" title="{% trans 'Inspect' %}">
                                <i class="fas fa-eye text-sm sm:text-xs"></i>
                            </a>
                            <a href="{% country_url 'clientes:editar_cliente' cliente.pk %}" class="btn-icon-only w-10 h-10 sm:w-8 sm:h-8 flex items-center justify-center" title="{% trans 'Modify' %}">
                                <i class="fas fa-pen text-sm sm:text-xs"></i>
                            </a>
                            <a href="{% country_url 'clientes:eliminar_cliente' cliente_id=cliente.pk %}" 
                               class="btn-icon-only btn-delete w-10 h-10 sm:w-8 sm:h-8 flex items-center justify-center" 
                               title="{% trans 'Purge' %}" 
                               onclick="return confirmarEliminacion('{{ cliente.nombre }} {{ cliente.apellido }}')">
                                <i class="fas fa-trash-alt text-sm sm:text-xs"></i>
                            </a>
                        </div>
                    </td>
                </tr>
                {% empty %}
                <tr>
                    <td colspan="6" class="text-center py-16">
                        <div class="text-center py-12 sm:py-16 px-4">
                            <div class="text-6xl mb-4 opacity-50">👥</div>
                            <h3 class="text-xl sm:text-2xl font-semibold text-gray-300 mb-2">
                                {% trans "No clients found" %}
                            </h3>
                            <p class="text-sm sm:text-base text-gray-500 mb-6 max-w-md mx-auto">
                                {% trans "Create your first client to start managing your customer database." %}
                            </p>
                            <a href="{% country_url 'clientes:crear_cliente' %}" class="inline-flex items-center justify-center gap-2 px-6 py-4 text-base sm:text-lg font-extrabold rounded-xl bg-gradient-to-r from-cyan-500 to-blue-500 hover:from-cyan-400 hover:to-blue-400 text-white shadow-lg hover:shadow-xl transition-all">
                                <span class="text-xl">➕</span>
                                <span>{% trans "Create First Client" %}</span>
                            </a>
                        </div>
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
    
    {% if page_obj.has_other_pages %}
    <div class="pagination-wrapper">
        <div class="text-xs font-code text-cyan-500/60 hidden sm:block">
            {% blocktrans with start=page_obj.start_index end=page_obj.end_index total=page_obj.paginator.count %}DISPLAYING {{ start }}-{{ end }} / {{ total }} UNITS{% endblocktrans %}
        </div>
        <div class="flex gap-1">
            {% if page_obj.has_previous %}
                <a href="?q={{ request.GET.q }}&page={{ page_obj.previous_page_number }}" class="page-btn"><i class="fas fa-angle-left"></i></a>
            {% endif %}
            <span class="page-btn page-current">{{ page_obj.number }}</span>
            {% if page_obj.has_next %}
                <a href="?q={{ request.GET.q }}&page={{ page_obj.next_page_number }}" class="page-btn"><i class="fas fa-angle-right"></i></a>
            {% endif %}
        </div>
    </div>
    {% endif %}
</div>

<!-- Móvil: Cards Futuristas -->
<div class="md:hidden space-y-4">
    {% for cliente in cliente_list %}
    <div class="client-card-futuristic">
        <div class="client-card-header">
            <div class="flex-1">
                <h3 class="client-card-title">
                    {{ cliente.nombre }} {{ cliente.apellido }}
                </h3>
                <p class="client-card-id">#{{ cliente.pk }}</p>
            </div>
        </div>
        
        <div class="client-card-info">
            <div class="client-card-info-item">
                <i class="fas fa-envelope client-card-info-icon"></i>
                <span>{{ cliente.email|default:"Sin email" }}</span>
            </div>
            {% if cliente.telefono %}
            <div class="client-card-info-item">
                <i class="fas fa-phone client-card-info-icon"></i>
                <span>{{ cliente.telefono }}</span>
            </div>
            {% endif %}
            {% if cliente.ciudad or cliente.ciudad_usa %}
            <div class="client-card-info-item">
                <i class="fas fa-map-marker-alt client-card-info-icon"></i>
                <span>
                    {% if cliente.empresa.pais == 'US' %}
                        {% if cliente.ciudad_usa %}{{ cliente.ciudad_usa }}, {{ cliente.estado_usa }}{% else %}UNKNOWN{% endif %}
                    {% else %}
                        {% if cliente.ciudad %}{{ cliente.ciudad.nombre }}{% else %}UNKNOWN{% endif %}
                    {% endif %}
                </span>
            </div>
            {% endif %}
        </div>
        
        <div class="client-actions">
            <a href="{% country_url 'clientes:ver_cliente' cliente.pk %}" class="btn-futuristic">
                <span class="btn-futuristic-icon">👁️</span>
                <span class="btn-futuristic-text">{% trans "View" %}</span>
            </a>
            <a href="{% country_url 'clientes:editar_cliente' cliente.pk %}" class="btn-futuristic">
                <span class="btn-futuristic-icon">✏️</span>
                <span class="btn-futuristic-text">{% trans "Edit" %}</span>
            </a>
            <a href="{% country_url 'clientes:eliminar_cliente' cliente_id=cliente.pk %}" 
               onclick="return confirmarEliminacion('{{ cliente.nombre }} {{ cliente.apellido }}')"
               class="btn-futuristic btn-futuristic-delete">
                <span class="btn-futuristic-icon">🗑️</span>
                <span class="btn-futuristic-text">{% trans "Delete" %}</span>
            </a>
        </div>
    </div>
    {% empty %}
    <div class="empty-state">
        <div class="empty-state-icon">👥</div>
        <h3 class="empty-state-title">
            {% trans "No clients found" %}
        </h3>
        <p class="empty-state-text">
            {% trans "Create your first client to start managing your customer database." %}
        </p>
        <a href="{% country_url 'clientes:crear_cliente' %}" class="inline-flex items-center justify-center gap-3 px-8 py-4 text-lg font-extrabold rounded-xl bg-gradient-to-r from-cyan-500 via-blue-500 to-purple-500 hover:from-cyan-400 hover:via-blue-400 hover:to-purple-400 text-white shadow-xl hover:shadow-2xl transition-all border border-cyan-400/50" style="font-family: 'Orbitron', sans-serif;">
            <span class="text-2xl">➕</span>
            <span>{% trans "Create First Client" %}</span>
        </a>
    </div>
    {% endfor %}
</div>
{% endblock %}

{% block page_extra_js %}
<script>
function confirmarEliminacion(nombre) {
    return confirm(`⚠️ {% trans "SYSTEM ALERT: PURGE PROTOCOL" %}\n\n{% trans "Target" %}: ${nombre}\n\n{% trans "Confirm permanent deletion?" %}`);
}

(function() {
    const elements = {
        input: document.getElementById('search-input'),
        results: document.getElementById('search-results'),
        form: document.getElementById('search-form')
    };

    if (!elements.input || !elements.form) return;

    const SEARCH_URL = elements.form.dataset.searchUrl;
    let debounceTimer;

    async function performSearch(query) {
        if (!SEARCH_URL) {
            console.error('❌ Search URL not found');
            return;
        }

        try {
            const response = await fetch(`${SEARCH_URL}?q=${encodeURIComponent(query)}`, {
                headers: { 'X-Requested-With': 'XMLHttpRequest' }
            });
            
            if (!response.ok) throw new Error('Network error');
            
            const data = await response.json();
            const results = Array.isArray(data) ? data : (data.results || data.clientes || []);
            renderResults(results);

        } catch (error) {
            console.error('Search error:', error);
            elements.results.innerHTML = '<div class="p-4 text-red-400 text-center font-code text-sm">CONNECTION ERROR</div>';
        }
    }

    function renderResults(results) {
        if (results.length === 0) {
            elements.results.innerHTML = '<div class="p-4 text-gray-500 text-center italic">{% trans "No records found" %}.</div>';
            elements.results.classList.remove('hidden');
            return;
        }

        const html = results.map(item => `
            <div class="search-result-item" onclick="window.location.href='${location.pathname.replace('clientes/', '')}clientes/ver/${item.pk || item.id}/'">
                <div class="font-bold text-white text-sm">${item.nombre} ${item.apellido || ''}</div>
                <div class="text-xs text-cyan-500/70 font-code mt-1 flex gap-3">
                    ${item.email ? `<span><i class="fas fa-envelope"></i> ${item.email}</span>` : ''}
                    ${item.telefono ? `<span><i class="fas fa-phone"></i> ${item.telefono}</span>` : ''}
                </div>
            </div>
        `).join('');

        elements.results.innerHTML = html;
        elements.results.classList.remove('hidden');
    }

    elements.input.addEventListener('input', (e) => {
        const query = e.target.value.trim();
        clearTimeout(debounceTimer);
        
        if (query.length < 2) {
            elements.results.classList.add('hidden');
            return;
        }

        elements.results.classList.remove('hidden');
        elements.results.innerHTML = '<div class="p-4 text-cyan-400 text-center font-code text-xs animate-pulse">{% trans "SEARCHING DATABASE..." %}</div>';

        debounceTimer = setTimeout(() => performSearch(query), 400);
    });

    document.addEventListener('click', (e) => {
        if (!elements.form.contains(e.target)) {
            elements.results.classList.add('hidden');
        }
    });
})();
</script>
{% endblock %}
ENDOFFILE

echo "✅ Archivo actualizado"

# Recargar aplicación
touch /var/www/atlantareciclajes_pythonanywhere_com_wsgi.py

echo "✅ Aplicación recargada"
echo ""
echo "🎉 ¡Actualización completada!"
echo ""
echo "🟢 VERIFICACIÓN:"
echo "   Abre en tu celular: https://www.egarage.cl/us/clientes/"
echo "   Busca una CRUZ VERDE ✅ en la esquina superior derecha"
echo ""
echo "   SI LA VES → Archivo actualizado correctamente"
echo "   NO LA VES → Hay un problema, ejecuta el script de nuevo"










