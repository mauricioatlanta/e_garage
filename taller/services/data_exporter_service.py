import json
from django.core.serializers.json import DjangoJSONEncoder
from django.conf import settings
from taller.models.clientes import Cliente
from taller.models.vehiculos import Vehiculo
from taller.models.documento import Documento
from taller.utils.email_helper import get_branded_from_email, send_email_with_reply_to

class DataExporterService:
    @classmethod
    def exportar_y_enviar_datos(cls, empresa):
        """
        Compila toda la información histórica del taller y la envía 
        por correo electrónico al dueño antes de iniciar el periodo de gracia.
        """
        if not empresa.email:
            return False

        # 1. Extraer los registros de la base de datos filtrados estrictamente por la empresa
        clientes = list(Cliente.objects.filter(empresa=empresa).values())
        vehiculos = list(Vehiculo.objects.filter(empresa=empresa).values())
        documentos = list(Documento.objects.filter(empresa=empresa).values())

        # 2. Estructurar el diccionario del respaldo maestro
        respaldo_maestro = {
            "taller": {
                "id": empresa.id,
                "nombre_taller": empresa.nombre_taller,
                "pais": empresa.pais,
                "fecha_baja": empresa.fecha_baja
            },
            "clientes": clientes,
            "vehiculos": vehiculos,
            "documentos_y_ots": documentos
        }

        # 3. Convertir a un string JSON formateado y legible (Human-Readable)
        json_data = json.dumps(respaldo_maestro, cls=DjangoJSONEncoder, indent=4, ensure_ascii=False)

        # 4. Redactar y enviar el correo con el adjunto
        subject = f"Respaldo oficial de datos de tu taller: {empresa.nombre_taller}"
        message = (
            f"Hola,\n\n"
            f"Lamentamos que dejes eGarage. Conforme a nuestras políticas de portabilidad, "
            f"adjuntamos en este correo un archivo de respaldo con el 100% de tus datos corporativos "
            f"(Clientes, Vehículos, Historial y Órdenes de Trabajo) en formato estándar JSON.\n\n"
            f"⚠️ ATENCIÓN: Guardaremos tu información de manera segura en nuestros servidores por un lapso "
            f"de 6 meses (180 días) a contar desde hoy. Si deseas reactivar tu cuenta en este intervalo, "
            f"recuperarás tu panel tal cual lo dejaste. Pasado este plazo, tu base de datos se eliminará de forma irreversible.\n\n"
            f"Gracias por haber confiado en nosotros.\n"
            f"El equipo de eGarage."
        )

        try:
            # Reutilizamos la función nativa de tu proyecto para despachar correos con adjuntos
            # Si 'send_email_with_reply_to' no soporta adjuntos de forma nativa, Django permite usar EmailMessage
            from django.core.mail import EmailMessage
            
            email_msg = EmailMessage(
                subject=subject,
                body=message,
                from_email=get_branded_from_email(settings.DEFAULT_FROM_EMAIL),
                to=[empresa.email]
            )
            # Adjuntamos el archivo de texto directamente en memoria sin ocupar espacio en disco duro
            email_msg.attach(f"respaldo_egarage_{empresa.id}.json", json_data, "application/json")
            email_msg.send(fail_silently=False)
            return True
        except Exception as e:
            # Loggear el error si el proveedor de correos falla
            print(f"[ERROR EXPORTER] Falló el despacho del correo: {str(e)}")
            return False
