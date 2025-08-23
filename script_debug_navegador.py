#!/usr/bin/env python
"""
Script de debug para verificar el problema de modelos en el formulario
"""
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_taller.settings')
django.setup()

from taller.models import MarcaVehiculo, ModeloVehiculo

print("=== SCRIPT DE DEBUG PARA FORMULARIO ===")
print("Copiar y pegar esto en la consola del navegador:\n")

print("""
console.log("🔍 DEBUGGING MODELOS EN FORMULARIO");

// 1. Verificar que los elementos existen
const selectMarca = document.getElementById('id_marca');
const selectModelo = document.getElementById('id_modelo');
console.log("📋 Select Marca:", selectMarca);
console.log("📋 Select Modelo:", selectModelo);

// 2. Mostrar todas las opciones de marca disponibles
console.log("📋 Opciones de Marca:");
Array.from(selectMarca.options).forEach((option, index) => {
    if (option.value) {
        console.log(`  ${index}: ID=${option.value} -> ${option.text}`);
    }
});

// 3. Función para probar manualmente una marca específica
function probarMarca(marcaId) {
    console.log(`🧪 PROBANDO MARCA ID: ${marcaId}`);
    
    const apiUrl = `/api/modelos/${marcaId}/`;
    console.log(`📡 URL: ${apiUrl}`);
    
    fetch(apiUrl)
        .then(res => {
            console.log(`📊 Status: ${res.status}`);
            return res.json();
        })
        .then(data => {
            console.log(`📋 Respuesta:`, data);
            console.log(`📋 Modelos encontrados: ${data.modelos ? data.modelos.length : 0}`);
            if (data.modelos) {
                data.modelos.forEach(modelo => {
                    console.log(`  - ${modelo.nombre} (ID: ${modelo.id})`);
                });
            }
        })
        .catch(error => {
            console.error(`❌ Error:`, error);
        });
}

// 4. Probar marcas específicas""")

# Generar los comandos de prueba para las marcas principales
marcas_principales = ['Ford', 'Chevrolet', 'Toyota', 'Honda']
for nombre_marca in marcas_principales:
    try:
        marca = MarcaVehiculo.objects.get(nombre=nombre_marca)
        print(f'console.log("\\n🧪 Probando {nombre_marca}:");')
        print(f'probarMarca({marca.pk});')
    except MarcaVehiculo.DoesNotExist:
        print(f'console.log("❌ {nombre_marca} no encontrada");')

print("""
// 5. Simular cambio de marca para activar el evento
console.log("\\n🎯 Simulando selección de Ford:");
selectMarca.value = '117';  // ID de Ford
selectMarca.dispatchEvent(new Event('change'));

console.log("\\n✅ Debug completo. Revisa los logs arriba.");
""")

print("\n" + "="*60)
print("INSTRUCCIONES:")
print("1. Abre http://127.0.0.1:8000/en/vehiculos/crear/ en tu navegador")
print("2. Abre las Herramientas de Desarrollador (F12)")
print("3. Ve a la pestaña 'Console'")
print("4. Copia y pega todo el código de arriba")
print("5. Presiona Enter")
print("6. Revisa los logs para ver qué está fallando")
print("="*60)
