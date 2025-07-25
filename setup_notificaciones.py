# setup_notificaciones.py - Configuración Inicial de Notificaciones
"""
Script para configurar el sistema de notificaciones con templates predeterminados
"""
import os
import django

# Configurar Django
# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings_sqlite')
django.setup()

from taller.models.notificacion import TipoNotificacion, ConfiguracionNotificacion
from taller.models.empresa import Empresa

def crear_tipos_notificacion():
    """Crear tipos de notificación predeterminados"""
    
    tipos_notificacion = [
        {
            'nombre': 'Email - Documento Creado',
            'evento': 'DOCUMENTO_CREADO',
            'tipo': 'EMAIL',
            'template_asunto': '🚗 Nuevo documento #{{documento.id}} - {{empresa.nombre_taller}}',
            'template_mensaje': '''Estimado/a {{cliente.nombre}},

Le informamos que se ha generado un nuevo documento en nuestro taller:

📄 **Documento #{{documento.id}}**
📅 **Fecha:** {{documento.fecha_documento|date:"d/m/Y"}}
🏢 **Taller:** {{empresa.nombre_taller}}

{% if documento.descripcion %}
**Descripción:**
{{documento.descripcion}}
{% endif %}

{% if datos.total %}
**Total:** ${{datos.total|floatformat:0}}
{% endif %}

Puede contactarnos para cualquier consulta sobre este documento.

**Datos de contacto:**
📧 {{empresa.email}}
📞 {{empresa.telefono}}
📍 {{empresa.direccion}}

¡Gracias por confiar en nosotros!

Saludos cordiales,
Equipo {{empresa.nombre_taller}}''',
            'dias_anticipacion': 0
        },
        {
            'nombre': 'WhatsApp - Documento Creado',
            'evento': 'DOCUMENTO_CREADO',
            'tipo': 'WHATSAPP',
            'template_asunto': 'Documento Creado',
            'template_mensaje': '''¡Hola {{cliente.nombre}}! 👋

Se ha generado el documento #{{documento.id}} en {{empresa.nombre_taller}}.

📅 Fecha: {{documento.fecha_documento|date:"d/m/Y"}}
{% if datos.total %}💰 Total: ${{datos.total|floatformat:0}}{% endif %}

¡Gracias por elegirnos! 🚗✨''',
            'dias_anticipacion': 0
        },
        {
            'nombre': 'Email - Suscripción por Vencer',
            'evento': 'SUSCRIPCION_VENCE',
            'tipo': 'EMAIL',
            'template_asunto': '⚠️ Su suscripción vence en {{datos.dias_restantes}} días - {{empresa.nombre_taller}}',
            'template_mensaje': '''Estimado usuario,

Su suscripción al sistema E-Garage está próxima a vencer:

⏰ **Días restantes:** {{datos.dias_restantes}}
📅 **Fecha de vencimiento:** {{datos.fecha_vencimiento|date:"d/m/Y"}}
🏢 **Empresa:** {{empresa.nombre_taller}}

**Para renovar su suscripción:**
1. Acceda a su panel de administración
2. Vaya a la sección "Suscripción"
3. Seleccione su plan de renovación
4. Complete el proceso de pago

**¿Necesita ayuda?**
Contáctenos en soporte@egarage.com o al teléfono de soporte.

No permita que su servicio se interrumpa. ¡Renueve hoy mismo!

Equipo E-Garage''',
            'dias_anticipacion': 0
        },
        {
            'nombre': 'Email - Recordatorio Mantenimiento',
            'evento': 'MANTENIMIENTO_RECORDATORIO',
            'tipo': 'EMAIL',
            'template_asunto': '🔧 Recordatorio: {{datos.tipo_mantenimiento}} - {{empresa.nombre_taller}}',
            'template_mensaje': '''Estimado/a {{cliente.nombre}},

Le recordamos que tiene programado un mantenimiento para su vehículo:

🚗 **Vehículo:** {{datos.vehiculo}}
🔧 **Tipo de mantenimiento:** {{datos.tipo_mantenimiento}}
📅 **Fecha programada:** {{datos.fecha_programada|date:"d/m/Y"}}
{% if datos.dias_restantes > 0 %}⏰ **Días restantes:** {{datos.dias_restantes}}{% endif %}

{% if datos.descripcion %}
**Descripción:**
{{datos.descripcion}}
{% endif %}

**¿Por qué es importante no olvidarlo?**
- Mantiene su vehículo en óptimas condiciones
- Previene averías costosas
- Garantiza su seguridad y la de su familia
- Conserva el valor de su vehículo

**Para agendar su cita:**
📞 Llámenos al {{empresa.telefono}}
📧 Escríbanos a {{empresa.email}}
📍 Visítenos en {{empresa.direccion}}

**Horarios de atención:**
Lunes a Viernes: 8:00 AM - 6:00 PM
Sábados: 8:00 AM - 2:00 PM

¡No espere hasta último momento! Reserve su cita con anticipación.

Atentamente,
{{empresa.nombre_taller}}''',
            'dias_anticipacion': 0
        },
        {
            'nombre': 'WhatsApp - Recordatorio Mantenimiento',
            'evento': 'MANTENIMIENTO_RECORDATORIO',
            'tipo': 'WHATSAPP',
            'template_asunto': 'Recordatorio Mantenimiento',
            'template_mensaje': '''¡Hola {{cliente.nombre}}! 👋

🔧 Recordatorio de mantenimiento:

🚗 **{{datos.vehiculo}}**
📅 {{datos.fecha_programada|date:"d/m/Y"}}
⚙️ {{datos.tipo_mantenimiento}}

{% if datos.dias_restantes > 0 %}⏰ Faltan {{datos.dias_restantes}} días{% endif %}

Para agendar tu cita:
📞 {{empresa.telefono}}

¡Tu vehículo te lo agradecerá! 🚗✨''',
            'dias_anticipacion': 0
        },
        {
            'nombre': 'Email - Suscripción Vencida',
            'evento': 'SUSCRIPCION_VENCIDA',
            'tipo': 'EMAIL',
            'template_asunto': '🚨 URGENTE: Su suscripción ha vencido - {{empresa.nombre_taller}}',
            'template_mensaje': '''ATENCIÓN: Su suscripción ha vencido

Su acceso al sistema E-Garage se ha suspendido temporalmente debido al vencimiento de su suscripción.

🏢 **Empresa:** {{empresa.nombre_taller}}
📅 **Fecha de vencimiento:** {{datos.fecha_vencimiento|date:"d/m/Y"}}

**Para reactivar su servicio:**
1. Renueve su suscripción inmediatamente
2. Su acceso se restaurará en minutos
3. Todos sus datos están seguros

**Contáctenos urgentemente:**
📧 soporte@egarage.com
📞 Línea de soporte 24/7

¡No pierda más tiempo! Reactive su servicio ahora.''',
            'dias_anticipacion': 0
        },
        {
            'nombre': 'Email - Cliente Inactivo',
            'evento': 'CLIENTE_INACTIVO',
            'tipo': 'EMAIL',
            'template_asunto': '👋 ¡Te extrañamos! - {{empresa.nombre_taller}}',
            'template_mensaje': '''¡Hola {{cliente.nombre}}!

Hemos notado que no nos has visitado en un tiempo y queremos saber de ti.

En {{empresa.nombre_taller}} siempre estamos aquí para cuidar tu vehículo con:
✅ Mantenimiento preventivo
✅ Reparaciones especializadas  
✅ Repuestos originales
✅ Garantía en todos nuestros trabajos

**Oferta especial para ti:**
🎯 20% de descuento en tu próximo servicio
📅 Válido hasta fin de mes

¡Agenda tu cita y aprovecha esta oportunidad!

📞 {{empresa.telefono}}
📧 {{empresa.email}}
📍 {{empresa.direccion}}

¡Te esperamos!
{{empresa.nombre_taller}}''',
            'dias_anticipacion': 0
        }
    ]
    
    created_count = 0
    for tipo_data in tipos_notificacion:
        tipo, created = TipoNotificacion.objects.get_or_create(
            nombre=tipo_data['nombre'],
            defaults=tipo_data
        )
        if created:
            created_count += 1
            print(f"✅ Creado: {tipo.nombre}")
        else:
            print(f"⚠️  Ya existe: {tipo.nombre}")
    
    print(f"\n📊 Tipos de notificación creados: {created_count}")
    return created_count

def configurar_empresas():
    """Configurar notificaciones para todas las empresas"""
    empresas = Empresa.objects.all()
    configuradas = 0
    
    for empresa in empresas:
        config, created = ConfiguracionNotificacion.objects.get_or_create(
            empresa=empresa,
            defaults={
                'email_activo': True,
                'email_remitente': empresa.email or 'noreply@egarage.local',
                'notificar_documentos': True,
                'notificar_suscripcion': True,
                'notificar_mantenimiento': True,
                'dias_recordatorio_suscripcion': 7,
                'dias_recordatorio_mantenimiento': 7
            }
        )
        
        if created:
            configuradas += 1
            print(f"✅ Configuración creada para: {empresa.nombre_taller}")
        else:
            print(f"⚠️  Ya configurada: {empresa.nombre_taller}")
    
    print(f"\n📊 Empresas configuradas: {configuradas}")
    return configuradas

def crear_recordatorios_ejemplo():
    """Crear algunos recordatorios de mantenimiento de ejemplo"""
    from taller.models.notificacion import RecordatorioMantenimiento
    from taller.models.clientes import Cliente
    from taller.models.vehiculos import Vehiculo
    from datetime import date, timedelta
    
    try:
        # Buscar algunos vehículos para crear recordatorios
        vehiculos = Vehiculo.objects.all()[:3]
        recordatorios_creados = 0
        
        for i, vehiculo in enumerate(vehiculos):
            fecha_programada = date.today() + timedelta(days=5 + i*3)  # 5, 8, 11 días
            
            recordatorio, created = RecordatorioMantenimiento.objects.get_or_create(
                empresa=vehiculo.empresa,
                cliente=vehiculo.cliente,
                vehiculo=vehiculo,
                tipo_mantenimiento=['ACEITE', 'FRENOS', 'REVISION_GENERAL'][i],
                defaults={
                    'descripcion': f'Mantenimiento programado para {vehiculo}',
                    'fecha_programada': fecha_programada,
                    'dias_recordatorio': 7
                }
            )
            
            if created:
                recordatorios_creados += 1
                print(f"✅ Recordatorio creado: {recordatorio}")
        
        print(f"\n📊 Recordatorios de ejemplo creados: {recordatorios_creados}")
        return recordatorios_creados
        
    except Exception as e:
        print(f"❌ Error creando recordatorios: {e}")
        return 0

def test_notificacion():
    """Probar el sistema de notificaciones con un ejemplo"""
    from taller.utils.notificaciones import NotificacionManager
    from taller.models.documento import Documento
    
    try:
        # Buscar una empresa y documento para probar
        empresa = Empresa.objects.first()
        documento = Documento.objects.first()
        
        if not empresa or not documento:
            print("❌ No hay datos suficientes para probar")
            return False
        
        print(f"\n🧪 PROBANDO NOTIFICACIONES...")
        print(f"   Empresa: {empresa.nombre_taller}")
        print(f"   Documento: #{documento.id}")
        
        manager = NotificacionManager(empresa)
        
        # Crear notificación de prueba
        notificaciones = manager.crear_notificacion(
            evento='DOCUMENTO_CREADO',
            destinatario_email='test@ejemplo.com',
            destinatario_nombre='Cliente de Prueba',
            destinatario_telefono='+56912345678',
            documento=documento,
            cliente=documento.cliente if hasattr(documento, 'cliente') else None,
            datos_extra={
                'numero_documento': documento.id,
                'total': 50000
            }
        )
        
        if notificaciones:
            print(f"✅ Notificaciones creadas: {len(notificaciones)}")
            for notif in notificaciones:
                print(f"   - {notif.tipo_notificacion.nombre}: {notif.estado}")
            return True
        else:
            print("❌ No se crearon notificaciones")
            return False
            
    except Exception as e:
        print(f"❌ Error en prueba: {e}")
        return False

def main():
    """Función principal de configuración"""
    print("🚀 === CONFIGURACIÓN SISTEMA DE NOTIFICACIONES ===\n")
    
    # 1. Crear tipos de notificación
    print("1️⃣ CREANDO TIPOS DE NOTIFICACIÓN...")
    tipos_creados = crear_tipos_notificacion()
    
    # 2. Configurar empresas
    print("\n2️⃣ CONFIGURANDO EMPRESAS...")
    empresas_config = configurar_empresas()
    
    # 3. Crear recordatorios de ejemplo
    print("\n3️⃣ CREANDO RECORDATORIOS DE EJEMPLO...")
    recordatorios_creados = crear_recordatorios_ejemplo()
    
    # 4. Probar el sistema
    print("\n4️⃣ PROBANDO SISTEMA...")
    test_ok = test_notificacion()
    
    # Resumen
    print(f"\n{'='*60}")
    print("📊 RESUMEN DE CONFIGURACIÓN")
    print(f"{'='*60}")
    print(f"✅ Tipos de notificación: {tipos_creados} creados")
    print(f"✅ Empresas configuradas: {empresas_config} configuradas")
    print(f"✅ Recordatorios de ejemplo: {recordatorios_creados} creados")
    print(f"✅ Prueba del sistema: {'EXITOSA' if test_ok else 'FALLÓ'}")
    
    if test_ok:
        print(f"\n🎉 ¡SISTEMA DE NOTIFICACIONES CONFIGURADO EXITOSAMENTE!")
        print(f"\n📋 PRÓXIMOS PASOS:")
        print(f"   1. Configurar credenciales de email en cada empresa")
        print(f"   2. Configurar APIs de WhatsApp/SMS si se requieren")
        print(f"   3. Programar ejecución periódica del procesador")
        print(f"   4. Probar envío real de notificaciones")
    else:
        print(f"\n⚠️  Configuración completada con advertencias")

if __name__ == "__main__":
    main()
