from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from taller.models.empresa import Empresa
from taller.models.usuario import PerfilUsuario
import json

def registro_gratuito(request):
    """Vista para registro gratuito y automático"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            nombre_taller = data.get('nombre_taller')
            email = data.get('email')
            password = data.get('password')
            nombre_usuario = data.get('nombre_usuario', email.split('@')[0])
            
            # Validaciones básicas
            if not all([nombre_taller, email, password]):
                return JsonResponse({
                    'success': False,
                    'error': 'Todos los campos son obligatorios'
                })
            
            # Verificar si el email ya existe
            if User.objects.filter(email=email).exists():
                return JsonResponse({
                    'success': False,
                    'error': 'Ya existe una cuenta con este email'
                })
            
            # Crear usuario
            user = User.objects.create_user(
                username=email,  # Usamos email como username
                email=email,
                password=password,
                first_name=nombre_usuario
            )
            
            # Crear empresa automáticamente
            empresa = Empresa.objects.create(
                user=user,
                nombre_taller=nombre_taller,
                email=email,
                plan='gratuito',  # Plan gratuito ilimitado
                suscripcion_activa=True
            )
            
            # Crear perfil de usuario
            try:
                perfil = PerfilUsuario.objects.create(
                    usuario=user,
                    empresa=empresa,
                    tipo_usuario='admin'
                )
            except Exception:
                # Si no existe el modelo PerfilUsuario, continuamos
                pass
            
            # Login automático
            user = authenticate(username=email, password=password)
            login(request, user)
            
            return JsonResponse({
                'success': True,
                'message': 'Cuenta creada exitosamente',
                'redirect_url': '/bienvenida/'
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Datos inválidos'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Error interno: {str(e)}'
            })
    
    return render(request, 'onboarding/registro_gratuito.html')

def bienvenida_onboarding(request):
    """Pantalla de bienvenida con primeros pasos"""
    if not request.user.is_authenticated:
        return redirect('registro_gratuito')
    
    # Obtener empresa del usuario
    try:
        empresa = request.user.empresa
    except:
        empresa = None
    
    context = {
        'empresa': empresa,
        'usuario': request.user,
        'primer_ingreso': True
    }
    
    return render(request, 'onboarding/bienvenida.html', context)

def onboarding_paso(request):
    """Pasos del onboarding interactivo"""
    if not request.user.is_authenticated:
        return redirect('onboarding:registro_gratuito')
    
    # Obtener paso del GET parameter, default 1
    paso = int(request.GET.get('paso', 1))
    
    pasos = {
        1: {
            'titulo': '👥 Agregar tu primer cliente',
            'descripcion': 'Comienza agregando información de un cliente',
            'accion_url': '/clientes/nuevo/',
            'template': 'onboarding/paso_cliente.html'
        },
        2: {
            'titulo': '🚗 Registrar un vehículo',
            'descripcion': 'Asocia un vehículo al cliente que acabas de crear',
            'accion_url': '/vehiculos/nuevo/',
            'template': 'onboarding/paso_vehiculo.html'
        },
        3: {
            'titulo': '📋 Crear tu primer documento',
            'descripcion': 'Genera una cotización o factura',
            'accion_url': '/documentos/nuevo/',
            'template': 'onboarding/paso_documento.html'
        },
        4: {
            'titulo': '📊 Ver reportes en acción',
            'descripcion': 'Explora el poder de los reportes con IA',
            'accion_url': '/reportes/demo/',
            'template': 'onboarding/paso_reportes.html'
        },
        5: {
            'titulo': '🧠 Descubre la IA integrada',
            'descripcion': 'Sugerencias automáticas para tu taller',
            'accion_url': '/ia/sugerencias/',
            'template': 'onboarding/paso_ia.html'
        },
        6: {
            'titulo': '🚀 SEO + Analytics configurado',
            'descripcion': 'Tu taller visible en Google con métricas',
            'accion_url': '/seo/configuracion/',
            'template': 'onboarding/paso_seo.html'
        },
        7: {
            'titulo': '💬 WhatsApp Business integrado',
            'descripcion': 'Contacto directo con clientes - ¡Completado!',
            'accion_url': '/whatsapp/configuracion/',
            'template': 'onboarding/paso_whatsapp.html'
        }
    }
    
    if paso not in pasos:
        return redirect('taller:dashboard_suscripciones')
    
    context = {
        'paso_actual': paso,
        'paso_info': pasos[paso],
        'total_pasos': len(pasos),
        'progreso': (paso / len(pasos)) * 100
    }
    
    return render(request, pasos[paso]['template'], context)
