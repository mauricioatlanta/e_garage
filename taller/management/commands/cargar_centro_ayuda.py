"""
Comando para cargar el contenido inicial del Centro de Ayuda de eGarage

Ejecutar: python manage.py cargar_centro_ayuda
"""

from django.core.management.base import BaseCommand
from django.utils.text import slugify

from taller.models.help import HelpArticle, HelpCategory


class Command(BaseCommand):
    help = "Carga el contenido inicial del Centro de Ayuda con todas las categorías y artículos"

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("🚀 Iniciando carga del Centro de Ayuda..."))

        # Definir categorías con iconos
        categorias_data = [
            {
                "nombre": "Primeros Pasos",
                "icono": "fas fa-rocket",
                "descripcion": "Guías para comenzar a usar eGarage",
                "orden": 1,
            },
            {
                "nombre": "Clientes y Vehículos",
                "icono": "fas fa-users",
                "descripcion": "Gestión de clientes y vehículos",
                "orden": 2,
            },
            {
                "nombre": "Documentos (OT, Presupuestos, Facturas)",
                "icono": "fas fa-file-invoice",
                "descripcion": "Creación y gestión de documentos",
                "orden": 3,
            },
            {
                "nombre": "Repuestos y Servicios",
                "icono": "fas fa-cogs",
                "descripcion": "Gestión de repuestos y servicios",
                "orden": 4,
            },
            {
                "nombre": "Inventario y Compras",
                "icono": "fas fa-warehouse",
                "descripcion": "Control de inventario y compras",
                "orden": 5,
            },
            {
                "nombre": "Reportes y Finanzas",
                "icono": "fas fa-chart-line",
                "descripcion": "Reportes y análisis financiero",
                "orden": 6,
            },
            {
                "nombre": "Roles y Permisos",
                "icono": "fas fa-user-shield",
                "descripcion": "Gestión de usuarios y permisos",
                "orden": 7,
            },
            {
                "nombre": "Configuración de la Empresa",
                "icono": "fas fa-cog",
                "descripcion": "Configuración general del sistema",
                "orden": 8,
            },
            {
                "nombre": "Problemas Frecuentes (FAQ)",
                "icono": "fas fa-question-circle",
                "descripcion": "Soluciones a problemas comunes",
                "orden": 9,
            },
            {
                "nombre": "Cuenta, Suscripción y Pagos",
                "icono": "fas fa-credit-card",
                "descripcion": "Gestión de cuenta y suscripción",
                "orden": 10,
            },
        ]

        # Crear categorías
        categorias_creadas = {}
        for cat_data in categorias_data:
            categoria, created = HelpCategory.objects.get_or_create(
                slug=slugify(cat_data["nombre"]), defaults=cat_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"✅ Categoría creada: {categoria.nombre}"))
            else:
                # Actualizar si ya existe
                for key, value in cat_data.items():
                    setattr(categoria, key, value)
                categoria.save()
                self.stdout.write(
                    self.style.WARNING(f"⚠️  Categoría actualizada: {categoria.nombre}")
                )
            categorias_creadas[cat_data["nombre"]] = categoria

        # Definir artículos por categoría
        articulos_data = {
            "Primeros Pasos": [
                {
                    "titulo": "¿Qué es eGarage?",
                    "contenido": """
                    <h2>¿Qué es eGarage?</h2>
                    <p>eGarage es un sistema completo de gestión diseñado específicamente para talleres automotrices, casas de repuestos y desarmadurías. Es una plataforma multi-país, multi-idioma y multi-rubro que se adapta a las necesidades de tu negocio.</p>
                    
                    <h3>Características principales:</h3>
                    <ul>
                        <li><strong>Multi-país:</strong> Funciona en Chile, USA, México y otros países con configuraciones específicas</li>
                        <li><strong>Multi-idioma:</strong> Disponible en español e inglés según el país</li>
                        <li><strong>Multi-rubro:</strong> Ideal para talleres mecánicos, vulcanizaciones, repuestos y más</li>
                        <li><strong>Gestión completa:</strong> Clientes, vehículos, documentos, inventario y reportes</li>
                    </ul>
                    
                    <p>eGarage te permite digitalizar todas las operaciones de tu taller, desde la recepción de vehículos hasta la facturación y el control de inventario.</p>
                    """,
                    "orden": 1,
                },
                {
                    "titulo": "Cómo iniciar sesión y seleccionar el país correcto",
                    "contenido": """
                    <h2>Cómo iniciar sesión y seleccionar el país correcto</h2>
                    
                    <h3>Paso 1: Acceder a eGarage</h3>
                    <p>Ingresa a <strong>egarage.cl</strong> o la URL correspondiente a tu país.</p>
                    
                    <h3>Paso 2: Seleccionar país</h3>
                    <p>En la página de inicio, selecciona tu país:</p>
                    <ul>
                        <li>🇨🇱 Chile</li>
                        <li>🇺🇸 Estados Unidos</li>
                        <li>🇲🇽 México</li>
                        <li>Y otros países disponibles</li>
                    </ul>
                    
                    <h3>Paso 3: Seleccionar idioma (solo USA)</h3>
                    <p>Si estás en USA, podrás elegir entre:</p>
                    <ul>
                        <li>English</li>
                        <li>Español</li>
                    </ul>
                    
                    <h3>Paso 4: Iniciar sesión</h3>
                    <p>Puedes iniciar sesión de dos formas:</p>
                    <ol>
                        <li><strong>Con correo y clave:</strong> Ingresa tu correo electrónico y contraseña</li>
                        <li><strong>Prueba gratis:</strong> Haz clic en "Activar prueba gratis" para crear una cuenta nueva</li>
                    </ol>
                    
                    <p><strong>Nota importante:</strong> Asegúrate de seleccionar el país correcto, ya que esto afecta la configuración de moneda, impuestos y otras opciones del sistema.</p>
                    """,
                    "orden": 2,
                },
                {
                    "titulo": "Recorrido general del panel",
                    "contenido": """
                    <h2>Recorrido general del panel</h2>
                    
                    <p>Una vez que inicias sesión, verás el <strong>Dashboard</strong> principal de eGarage. Este es tu centro de operaciones.</p>
                    
                    <h3>Elementos principales del panel:</h3>
                    
                    <h4>1. Dashboard</h4>
                    <p>El dashboard muestra información clave de tu negocio:</p>
                    <ul>
                        <li>Resumen de ventas</li>
                        <li>Documentos recientes</li>
                        <li>Alertas importantes</li>
                        <li>Accesos rápidos</li>
                    </ul>
                    
                    <h4>2. Accesos rápidos</h4>
                    <p>Botones principales para acciones comunes:</p>
                    <ul>
                        <li>Crear nuevo documento</li>
                        <li>Agregar cliente</li>
                        <li>Agregar vehículo</li>
                        <li>Ver reportes</li>
                    </ul>
                    
                    <h4>3. Menú lateral (o menú móvil)</h4>
                    <p>Navegación principal del sistema:</p>
                    <ul>
                        <li><strong>Clientes:</strong> Gestión de clientes</li>
                        <li><strong>Vehículos:</strong> Gestión de vehículos</li>
                        <li><strong>Documentos:</strong> Presupuestos, OTs y Facturas</li>
                        <li><strong>Repuestos:</strong> Inventario de repuestos</li>
                        <li><strong>Servicios:</strong> Catálogo de servicios</li>
                        <li><strong>Reportes:</strong> Análisis y estadísticas</li>
                        <li><strong>Configuración:</strong> Ajustes del sistema</li>
                    </ul>
                    
                    <p><strong>Tip:</strong> En dispositivos móviles, el menú se convierte en un botón hamburguesa (☰) en la esquina superior.</p>
                    """,
                    "orden": 3,
                },
            ],
            "Clientes y Vehículos": [
                {
                    "titulo": "Crear un cliente",
                    "contenido": """
                    <h2>Crear un cliente</h2>
                    
                    <p>Para crear un nuevo cliente en eGarage:</p>
                    
                    <h3>Paso 1: Acceder a Clientes</h3>
                    <p>Desde el menú principal, selecciona <strong>Clientes</strong> y luego <strong>Nuevo Cliente</strong>.</p>
                    
                    <h3>Paso 2: Completar información básica</h3>
                    <ul>
                        <li><strong>Nombre:</strong> Nombre completo del cliente</li>
                        <li><strong>RUT/DNI/Número de identificación:</strong> Según el país</li>
                        <li><strong>Email:</strong> Correo electrónico (opcional pero recomendado)</li>
                        <li><strong>Teléfono:</strong> Número de contacto</li>
                    </ul>
                    
                    <h3>Paso 3: Regiones/Ciudades dinámicas</h3>
                    <p>El sistema carga automáticamente las regiones y ciudades según tu país:</p>
                    <ol>
                        <li>Selecciona la <strong>Región/Estado</strong></li>
                        <li>Selecciona la <strong>Ciudad</strong> (se actualiza según la región elegida)</li>
                    </ol>
                    
                    <h3>Paso 4: Contactos</h3>
                    <p>Puedes agregar múltiples contactos para el mismo cliente:</p>
                    <ul>
                        <li>Nombre del contacto</li>
                        <li>Teléfono</li>
                        <li>Email</li>
                    </ul>
                    
                    <h3>Paso 5: Extras opcionales</h3>
                    <p>Información adicional que puedes incluir:</p>
                    <ul>
                        <li>Dirección completa</li>
                        <li>Notas sobre el cliente</li>
                        <li>Fecha de nacimiento</li>
                    </ul>
                    
                    <p><strong>Tip:</strong> Guarda la información más completa posible para facilitar futuras búsquedas y contactos.</p>
                    """,
                    "orden": 1,
                },
                {
                    "titulo": "Crear un vehículo",
                    "contenido": """
                    <h2>Crear un vehículo</h2>
                    
                    <p>Antes de crear un vehículo, asegúrate de tener un cliente creado.</p>
                    
                    <h3>Paso 1: Seleccionar cliente</h3>
                    <p>Desde el menú, ve a <strong>Vehículos</strong> > <strong>Nuevo Vehículo</strong>. Primero debes seleccionar el <strong>cliente</strong> al que pertenece el vehículo.</p>
                    
                    <h3>Paso 2: Seleccionar año, marca y modelo</h3>
                    <p>El sistema usa un catálogo jerárquico:</p>
                    <ol>
                        <li><strong>Año:</strong> Selecciona el año del vehículo</li>
                        <li><strong>Marca:</strong> La lista de marcas se carga según el año seleccionado</li>
                        <li><strong>Modelo:</strong> Los modelos se cargan según la marca seleccionada</li>
                    </ol>
                    
                    <p><strong>Nota:</strong> Si no aparece una marca o modelo, puede que no esté en el catálogo. Contacta al soporte para agregarlo.</p>
                    
                    <h3>Paso 3: Información adicional</h3>
                    <ul>
                        <li><strong>Motor:</strong> Tipo de motor (opcional)</li>
                        <li><strong>Caja:</strong> Tipo de transmisión (opcional)</li>
                        <li><strong>VIN:</strong> Número de identificación del vehículo (recomendado)</li>
                        <li><strong>Color:</strong> Con autocompletado - empieza a escribir y el sistema sugiere colores</li>
                        <li><strong>Patente/Placa:</strong> Número de placa del vehículo</li>
                    </ul>
                    
                    <h3>Paso 4: Guardar</h3>
                    <p>Una vez completada la información, haz clic en <strong>Guardar</strong>. El vehículo quedará asociado al cliente seleccionado.</p>
                    """,
                    "orden": 2,
                },
                {
                    "titulo": "Editar o consultar vehículos",
                    "contenido": """
                    <h2>Editar o consultar vehículos</h2>
                    
                    <h3>Consultar vehículos</h3>
                    <p>Para ver todos los vehículos:</p>
                    <ol>
                        <li>Ve a <strong>Vehículos</strong> en el menú principal</li>
                        <li>Verás una lista de todos los vehículos registrados</li>
                        <li>Puedes filtrar por cliente, marca, modelo, etc.</li>
                    </ol>
                    
                    <h3>Ver detalles de un vehículo</h3>
                    <p>Haz clic en cualquier vehículo de la lista para ver:</p>
                    <ul>
                        <li>Información completa del vehículo</li>
                        <li>Historial de documentos asociados</li>
                        <li>Servicios realizados</li>
                    </ul>
                    
                    <h3>Editar un vehículo</h3>
                    <p>Para editar la información de un vehículo:</p>
                    <ol>
                        <li>Accede al detalle del vehículo</li>
                        <li>Haz clic en el botón <strong>Editar</strong></li>
                        <li>Modifica los campos necesarios</li>
                        <li>Guarda los cambios</li>
                    </ol>
                    
                    <p><strong>Nota:</strong> Algunos campos como el cliente asociado pueden tener restricciones de edición por seguridad.</p>
                    """,
                    "orden": 3,
                },
                {
                    "titulo": "Errores comunes al crear vehículo",
                    "contenido": """
                    <h2>Errores comunes al crear vehículo</h2>
                    
                    <h3>1. No carga la lista de modelos</h3>
                    <p><strong>Causas posibles:</strong></p>
                    <ul>
                        <li>No has seleccionado una marca primero</li>
                        <li>El año seleccionado no tiene modelos para esa marca</li>
                        <li>Problema de conexión o caché del navegador</li>
                    </ul>
                    <p><strong>Solución:</strong> Asegúrate de seleccionar primero el año, luego la marca, y finalmente el modelo aparecerá.</p>
                    
                    <h3>2. No aparece la marca que busco</h3>
                    <p><strong>Causas posibles:</strong></p>
                    <ul>
                        <li>La marca no está en el catálogo para ese año</li>
                        <li>El nombre de la marca está escrito diferente</li>
                    </ul>
                    <p><strong>Solución:</strong> Intenta buscar con diferentes variaciones del nombre o contacta al soporte para agregar la marca.</p>
                    
                    <h3>3. Cliente no seleccionado</h3>
                    <p><strong>Error:</strong> "Debe seleccionar un cliente"</p>
                    <p><strong>Solución:</strong> Siempre debes seleccionar un cliente antes de crear un vehículo. Si no tienes un cliente, créalo primero desde el menú de Clientes.</p>
                    
                    <h3>4. Caché móvil</h3>
                    <p>Si estás en un dispositivo móvil y los datos no se cargan:</p>
                    <ul>
                        <li>Limpia la caché del navegador</li>
                        <li>Recarga la página</li>
                        <li>Verifica tu conexión a internet</li>
                    </ul>
                    """,
                    "orden": 4,
                },
            ],
            "Documentos (OT, Presupuesto, Factura)": [
                {
                    "titulo": "Crear documento paso a paso",
                    "contenido": """
                    <h2>Crear documento paso a paso</h2>
                    
                    <p>Los documentos en eGarage pueden ser: <strong>Presupuestos</strong>, <strong>Órdenes de Trabajo (OT)</strong> o <strong>Facturas</strong>.</p>
                    
                    <h3>Paso 1: Seleccionar tipo de documento</h3>
                    <p>Desde el menú <strong>Documentos</strong>, selecciona el tipo de documento que deseas crear:</p>
                    <ul>
                        <li><strong>Presupuesto:</strong> Cotización para el cliente</li>
                        <li><strong>Orden de Trabajo:</strong> Trabajo en proceso</li>
                        <li><strong>Factura:</strong> Documento de venta final</li>
                    </ul>
                    
                    <h3>Paso 2: Número asignado automáticamente</h3>
                    <p>El sistema asigna automáticamente un número secuencial al documento. Este número es único y no se puede modificar.</p>
                    
                    <h3>Paso 3: Seleccionar cliente y vehículo</h3>
                    <ol>
                        <li>Selecciona el <strong>cliente</strong> desde el campo de búsqueda (autocompletado)</li>
                        <li>Selecciona el <strong>vehículo</strong> del cliente (se cargan automáticamente según el cliente)</li>
                    </ol>
                    
                    <h3>Paso 4: Seleccionar técnico</h3>
                    <p>Asigna el <strong>técnico</strong> responsable del trabajo. Este campo puede ser obligatorio según tu configuración.</p>
                    
                    <h3>Paso 5: Agregar repuestos</h3>
                    <p>Para agregar repuestos al documento:</p>
                    <ol>
                        <li>Haz clic en <strong>Agregar Repuesto</strong></li>
                        <li>Busca por nombre o código</li>
                        <li>Selecciona la cantidad</li>
                        <li>El precio se carga automáticamente (puedes modificarlo)</li>
                    </ol>
                    
                    <h3>Paso 6: Agregar servicios</h3>
                    <p>Para agregar servicios:</p>
                    <ol>
                        <li>Haz clic en <strong>Agregar Servicio</strong></li>
                        <li>Selecciona la categoría y subcategoría</li>
                        <li>Elige el servicio específico</li>
                        <li>Ingresa el precio (editable)</li>
                    </ol>
                    
                    <h3>Paso 7: Guardar</h3>
                    <p>Una vez completado, haz clic en <strong>Guardar</strong>. El documento quedará registrado en el sistema.</p>
                    """,
                    "orden": 1,
                },
                {
                    "titulo": "Cómo funciona el IVA y sales tax",
                    "contenido": """
                    <h2>Cómo funciona el IVA y sales tax</h2>
                    
                    <p>eGarage calcula automáticamente los impuestos según tu país y configuración.</p>
                    
                    <h3>Chile - IVA 19%</h3>
                    <p>En Chile, el <strong>IVA del 19%</strong> se aplica solo a los <strong>repuestos</strong>:</p>
                    <ul>
                        <li>Los servicios NO tienen IVA</li>
                        <li>Los repuestos SÍ tienen IVA (19%)</li>
                        <li>El cálculo es automático</li>
                    </ul>
                    
                    <h3>USA - Sales Tax</h3>
                    <p>En Estados Unidos, el <strong>sales tax</strong> varía según el estado:</p>
                    <ul>
                        <li>Se configura en la configuración de la empresa</li>
                        <li>Puede aplicarse a repuestos y/o servicios según tu estado</li>
                        <li>El porcentaje se define en la configuración</li>
                    </ul>
                    
                    <h3>Cálculo dinámico del total</h3>
                    <p>El sistema calcula automáticamente:</p>
                    <ol>
                        <li><strong>Subtotal:</strong> Suma de repuestos + servicios (sin impuestos)</li>
                        <li><strong>Impuestos:</strong> IVA o sales tax según corresponda</li>
                        <li><strong>Total:</strong> Subtotal + Impuestos</li>
                    </ol>
                    
                    <p><strong>Nota:</strong> Puedes configurar si los impuestos se aplican por defecto en la configuración de la empresa.</p>
                    """,
                    "orden": 2,
                },
                {
                    "titulo": "Convertir presupuesto en OT o factura",
                    "contenido": """
                    <h2>Convertir presupuesto en OT o factura</h2>
                    
                    <p>eGarage te permite convertir documentos fácilmente:</p>
                    
                    <h3>Convertir Presupuesto en OT</h3>
                    <ol>
                        <li>Abre el presupuesto que deseas convertir</li>
                        <li>Haz clic en el botón <strong>Convertir en OT</strong></li>
                        <li>El sistema creará una nueva Orden de Trabajo con la misma información</li>
                        <li>El presupuesto original se mantiene como referencia</li>
                    </ol>
                    
                    <h3>Convertir OT en Factura</h3>
                    <ol>
                        <li>Abre la Orden de Trabajo completada</li>
                        <li>Haz clic en <strong>Convertir en Factura</strong></li>
                        <li>Se creará una factura con todos los repuestos y servicios de la OT</li>
                        <li>La OT se marca como facturada</li>
                    </ol>
                    
                    <h3>Convertir Presupuesto directamente en Factura</h3>
                    <p>También puedes convertir un presupuesto directamente en factura si el cliente acepta la cotización.</p>
                    
                    <p><strong>Ventaja:</strong> No necesitas reescribir toda la información. El sistema copia automáticamente todos los datos.</p>
                    """,
                    "orden": 3,
                },
                {
                    "titulo": "Imprimir o exportar PDF",
                    "contenido": """
                    <h2>Imprimir o exportar PDF</h2>
                    
                    <h3>Imprimir documento</h3>
                    <ol>
                        <li>Abre el documento que deseas imprimir</li>
                        <li>Haz clic en el botón <strong>Imprimir</strong></li>
                        <li>Se abrirá una vista previa optimizada para impresión</li>
                        <li>Usa la función de impresión de tu navegador (Ctrl+P / Cmd+P)</li>
                    </ol>
                    
                    <h3>Exportar a PDF</h3>
                    <ol>
                        <li>Abre el documento</li>
                        <li>Haz clic en <strong>Exportar PDF</strong></li>
                        <li>El sistema generará un PDF con el formato oficial</li>
                        <li>El PDF se descargará automáticamente</li>
                    </ol>
                    
                    <h3>Características del PDF</h3>
                    <ul>
                        <li>Incluye el logo de tu empresa (si está configurado)</li>
                        <li>Formato profesional con todos los datos</li>
                        <li>Listo para enviar por email o entregar al cliente</li>
                    </ul>
                    
                    <p><strong>Tip:</strong> Los PDFs generados incluyen toda la información del documento: cliente, vehículo, repuestos, servicios, impuestos y totales.</p>
                    """,
                    "orden": 4,
                },
            ],
            "Repuestos y Servicios": [
                {
                    "titulo": "Agregar repuestos a un documento",
                    "contenido": """
                    <h2>Agregar repuestos a un documento</h2>
                    
                    <h3>Método 1: Buscar repuesto existente</h3>
                    <ol>
                        <li>En el formulario del documento, haz clic en <strong>Agregar Repuesto</strong></li>
                        <li>Usa el campo de búsqueda para encontrar el repuesto:</li>
                        <ul>
                            <li>Busca por <strong>nombre</strong> del repuesto</li>
                            <li>O busca por <strong>código</strong> de parte</li>
                        </ul>
                        <li>Selecciona el repuesto de la lista</li>
                        <li>Ingresa la <strong>cantidad</strong></li>
                        <li>El <strong>precio</strong> se carga automáticamente (precio de venta configurado)</li>
                        <li>El <strong>subtotal</strong> se calcula automáticamente (cantidad × precio)</li>
                    </ol>
                    
                    <h3>Método 2: Crear repuesto si no existe</h3>
                    <p>Si el repuesto no está en tu inventario:</p>
                    <ol>
                        <li>Haz clic en <strong>Crear Nuevo Repuesto</strong></li>
                        <li>Completa la información:</li>
                        <ul>
                            <li>Nombre del repuesto</li>
                            <li>Código de parte (opcional)</li>
                            <li>Precio de compra</li>
                            <li>Precio de venta</li>
                            <li>Stock inicial (opcional)</li>
                        </ul>
                        <li>Guarda el repuesto</li>
                        <li>El repuesto se agregará automáticamente al documento</li>
                    </ol>
                    
                    <h3>Modificar precio</h3>
                    <p>Puedes modificar el precio del repuesto directamente en el documento si necesitas hacer un ajuste especial.</p>
                    
                    <p><strong>Nota:</strong> Al guardar el documento, si el repuesto tiene control de inventario, el stock se reducirá automáticamente.</p>
                    """,
                    "orden": 1,
                },
                {
                    "titulo": "Agregar servicios",
                    "contenido": """
                    <h2>Agregar servicios</h2>
                    
                    <h3>Paso 1: Seleccionar categoría</h3>
                    <p>Los servicios están organizados por categorías:</p>
                    <ul>
                        <li>Mecánica General</li>
                        <li>Electricidad</li>
                        <li>Pintura y Hojalatería</li>
                        <li>Vulcanización</li>
                        <li>Y más...</li>
                    </ul>
                    
                    <h3>Paso 2: Seleccionar subcategoría</h3>
                    <p>Dentro de cada categoría hay subcategorías más específicas para facilitar la búsqueda.</p>
                    
                    <h3>Paso 3: Elegir servicio</h3>
                    <p>Selecciona el servicio específico que deseas agregar al documento.</p>
                    
                    <h3>Paso 4: Precio editable</h3>
                    <p>El precio del servicio se carga automáticamente, pero puedes modificarlo:</p>
                    <ul>
                        <li>Haz clic en el campo de precio</li>
                        <li>Ingresa el nuevo precio</li>
                        <li>El subtotal se actualiza automáticamente</li>
                    </ul>
                    
                    <h3>Crear servicio nuevo desde el formulario</h3>
                    <p>Si necesitas agregar un servicio que no existe:</p>
                    <ol>
                        <li>Haz clic en <strong>Crear Nuevo Servicio</strong></li>
                        <li>Completa:</li>
                        <ul>
                            <li>Categoría</li>
                            <li>Subcategoría (o créala si no existe)</li>
                            <li>Nombre del servicio</li>
                            <li>Precio por defecto</li>
                        </ul>
                        <li>Guarda el servicio</li>
                        <li>Se agregará automáticamente al documento</li>
                    </ol>
                    """,
                    "orden": 2,
                },
                {
                    "titulo": "Gestionar inventario",
                    "contenido": """
                    <h2>Gestionar inventario</h2>
                    
                    <p>El módulo de inventario te permite controlar el stock de tus repuestos.</p>
                    
                    <h3>Entradas de stock</h3>
                    <p>Para registrar compras o entradas de repuestos:</p>
                    <ol>
                        <li>Ve a <strong>Repuestos</strong> > <strong>Inventario</strong></li>
                        <li>Selecciona el repuesto</li>
                        <li>Haz clic en <strong>Entrada de Stock</strong></li>
                        <li>Ingresa:</li>
                        <ul>
                            <li>Cantidad a agregar</li>
                            <li>Precio de compra (opcional)</li>
                            <li>Fecha de entrada</li>
                        </ul>
                        <li>El stock se actualiza automáticamente</li>
                    </ol>
                    
                    <h3>Salidas por ventas</h3>
                    <p>Cuando creas una factura o OT con repuestos:</p>
                    <ul>
                        <li>El stock se reduce automáticamente al guardar el documento</li>
                        <li>Si no hay suficiente stock, el sistema te alertará</li>
                        <li>Puedes ver el historial de salidas en el detalle del repuesto</li>
                    </ul>
                    
                    <h3>Ajustes de inventario</h3>
                    <p>Para corregir diferencias de inventario:</p>
                    <ol>
                        <li>Ve al repuesto que deseas ajustar</li>
                        <li>Haz clic en <strong>Ajuste de Inventario</strong></li>
                        <li>Ingresa la cantidad correcta</li>
                        <li>Agrega una nota explicando el ajuste</li>
                        <li>El sistema registrará el ajuste en el historial</li>
                    </ol>
                    
                    <h3>Ver historial</h3>
                    <p>Cada repuesto tiene un historial completo de:</p>
                    <ul>
                        <li>Entradas (compras)</li>
                        <li>Salidas (ventas)</li>
                        <li>Ajustes</li>
                        <li>Fechas y cantidades</li>
                    </ul>
                    """,
                    "orden": 3,
                },
            ],
            "Inventario y Compras": [
                {
                    "titulo": "Registrar compra de repuestos",
                    "contenido": """
                    <h2>Registrar compra de repuestos</h2>
                    
                    <p>Para registrar una compra de repuestos y actualizar el inventario:</p>
                    
                    <h3>Paso 1: Acceder al módulo de compras</h3>
                    <p>Ve a <strong>Repuestos</strong> > <strong>Compras</strong> o <strong>Inventario</strong> > <strong>Nueva Compra</strong>.</p>
                    
                    <h3>Paso 2: Seleccionar o crear repuesto</h3>
                    <ul>
                        <li>Si el repuesto ya existe, búscalo y selecciónalo</li>
                        <li>Si es nuevo, créalo primero desde el catálogo de repuestos</li>
                    </ul>
                    
                    <h3>Paso 3: Ingresar información de compra</h3>
                    <p>Completa los siguientes campos:</p>
                    <ul>
                        <li><strong>Precio de compra:</strong> Precio al que compraste el repuesto</li>
                        <li><strong>Precio de venta:</strong> Precio al que lo venderás (puede ser diferente al precio de compra)</li>
                        <li><strong>Cantidad:</strong> Cantidad de unidades compradas</li>
                        <li><strong>Proveedor:</strong> (Opcional) Nombre del proveedor</li>
                        <li><strong>Fecha:</strong> Fecha de la compra</li>
                    </ul>
                    
                    <h3>Paso 4: Ganancia</h3>
                    <p>El sistema calcula automáticamente:</p>
                    <ul>
                        <li><strong>Ganancia unitaria:</strong> Precio de venta - Precio de compra</li>
                        <li><strong>Ganancia total:</strong> Ganancia unitaria × Cantidad</li>
                        <li><strong>Margen de ganancia:</strong> Porcentaje de ganancia sobre el precio de venta</li>
                    </ul>
                    
                    <h3>Paso 5: Guardar</h3>
                    <p>Al guardar la compra:</p>
                    <ul>
                        <li>El stock del repuesto se incrementa automáticamente</li>
                        <li>Se registra la entrada en el historial de inventario</li>
                        <li>Los precios se actualizan (si los modificaste)</li>
                    </ul>
                    """,
                    "orden": 1,
                },
                {
                    "titulo": "Reintegro de stock al eliminar venta",
                    "contenido": """
                    <h2>Reintegro de stock al eliminar venta</h2>
                    
                    <p>Si eliminas o anulas un documento que contenía repuestos, el sistema reintegra automáticamente el stock.</p>
                    
                    <h3>¿Cuándo se reintegra el stock?</h3>
                    <ul>
                        <li>Al <strong>eliminar</strong> un documento (factura, OT, presupuesto convertido)</li>
                        <li>Al <strong>anular</strong> una factura</li>
                        <li>Al <strong>revertir</strong> una conversión de documento</li>
                    </ul>
                    
                    <h3>Proceso automático</h3>
                    <p>El sistema:</p>
                    <ol>
                        <li>Identifica todos los repuestos del documento eliminado</li>
                        <li>Suma las cantidades vendidas de cada repuesto</li>
                        <li>Reintegra esas cantidades al stock disponible</li>
                        <li>Registra el movimiento en el historial de inventario</li>
                    </ol>
                    
                    <h3>Verificar reintegro</h3>
                    <p>Para verificar que el stock se reintegró correctamente:</p>
                    <ol>
                        <li>Ve al repuesto en cuestión</li>
                        <li>Revisa el <strong>Historial de Inventario</strong></li>
                        <li>Deberías ver una entrada de "Reintegro por eliminación de documento"</li>
                    </ol>
                    
                    <p><strong>Nota:</strong> El reintegro es automático e inmediato. No necesitas hacer nada manualmente.</p>
                    """,
                    "orden": 2,
                },
                {
                    "titulo": "Alertas de stock bajo",
                    "contenido": """
                    <h2>Alertas de stock bajo</h2>
                    
                    <p>eGarage te alerta automáticamente cuando un repuesto tiene stock bajo.</p>
                    
                    <h3>Configurar nivel de alerta</h3>
                    <p>Para cada repuesto puedes configurar:</p>
                    <ul>
                        <li><strong>Stock mínimo:</strong> Cantidad mínima antes de alertar</li>
                        <li><strong>Stock crítico:</strong> Cantidad muy baja (alerta urgente)</li>
                    </ul>
                    
                    <h3>Dónde ver las alertas</h3>
                    <ul>
                        <li><strong>Dashboard:</strong> Panel principal muestra alertas de stock bajo</li>
                        <li><strong>Módulo de Repuestos:</strong> Lista de repuestos con stock bajo destacados</li>
                        <li><strong>Al crear documento:</strong> Si intentas vender un repuesto con stock bajo, verás una advertencia</li>
                    </ul>
                    
                    <h3>Tipos de alertas</h3>
                    <ul>
                        <li><strong>Amarillo:</strong> Stock bajo (cerca del mínimo)</li>
                        <li><strong>Rojo:</strong> Stock crítico (por debajo del mínimo)</li>
                        <li><strong>Sin stock:</strong> No hay unidades disponibles</li>
                    </ul>
                    
                    <h3>Acciones recomendadas</h3>
                    <p>Cuando recibas una alerta:</p>
                    <ol>
                        <li>Revisa el stock actual del repuesto</li>
                        <li>Decide si necesitas hacer una compra</li>
                        <li>Registra la compra para actualizar el stock</li>
                    </ol>
                    
                    <p><strong>Tip:</strong> Configura los niveles de alerta según tu frecuencia de ventas para evitar quedarte sin stock.</p>
                    """,
                    "orden": 3,
                },
            ],
            "Reportes y Finanzas": [
                {
                    "titulo": "Reportes incluidos",
                    "contenido": """
                    <h2>Reportes incluidos</h2>
                    
                    <p>eGarage incluye una variedad de reportes para analizar tu negocio:</p>
                    
                    <h3>1. Ventas por técnico</h3>
                    <p>Analiza el desempeño de cada técnico:</p>
                    <ul>
                        <li>Total de ventas por técnico</li>
                        <li>Número de documentos atendidos</li>
                        <li>Comparación entre técnicos</li>
                        <li>Período de tiempo personalizable</li>
                    </ul>
                    
                    <h3>2. Repuestos más vendidos</h3>
                    <p>Identifica tus productos estrella:</p>
                    <ul>
                        <li>Lista de repuestos ordenados por cantidad vendida</li>
                        <li>Ingresos generados por cada repuesto</li>
                        <li>Análisis de rotación de inventario</li>
                    </ul>
                    
                    <h3>3. Servicios más usados</h3>
                    <p>Descubre qué servicios son más demandados:</p>
                    <ul>
                        <li>Ranking de servicios por frecuencia</li>
                        <li>Ingresos por tipo de servicio</li>
                        <li>Tendencias por período</li>
                    </ul>
                    
                    <h3>4. Rentabilidad mensual</h3>
                    <p>Análisis financiero completo:</p>
                    <ul>
                        <li>Ingresos totales del mes</li>
                        <li>Costos y gastos</li>
                        <li>Ganancia neta</li>
                        <li>Comparación mes a mes</li>
                        <li>Gráficos visuales</li>
                    </ul>
                    
                    <h3>5. Inteligencia Operativa (solo admins)</h3>
                    <p>Dashboard avanzado con:</p>
                    <ul>
                        <li>Análisis predictivo</li>
                        <li>Recomendaciones de negocio</li>
                        <li>Insights automatizados</li>
                        <li>Proyecciones de ventas</li>
                    </ul>
                    <p><strong>Nota:</strong> Este reporte solo está disponible para administradores y dueños.</p>
                    
                    <h3>Exportar reportes</h3>
                    <p>Todos los reportes se pueden exportar a:</p>
                    <ul>
                        <li>PDF para impresión</li>
                        <li>Excel para análisis avanzado</li>
                        <li>CSV para importar en otros sistemas</li>
                    </ul>
                    """,
                    "orden": 1,
                },
                {
                    "titulo": "Exportación para IVA (Chile)",
                    "contenido": """
                    <h2>Exportación para IVA (Chile)</h2>
                    
                    <p>eGarage facilita la exportación de datos para la declaración de IVA en Chile.</p>
                    
                    <h3>Formato CSV</h3>
                    <p>El sistema genera un archivo CSV con:</p>
                    <ul>
                        <li>Todas las ventas del período seleccionado</li>
                        <li>Desglose de IVA por documento</li>
                        <li>Totales de IVA a favor y a pagar</li>
                        <li>Información de clientes y documentos</li>
                    </ul>
                    
                    <h3>Cómo exportar</h3>
                    <ol>
                        <li>Ve a <strong>Reportes</strong> > <strong>Exportación IVA</strong></li>
                        <li>Selecciona el período (mes, trimestre, año)</li>
                        <li>Haz clic en <strong>Exportar CSV</strong></li>
                        <li>El archivo se descargará automáticamente</li>
                    </ol>
                    
                    <h3>No requiere certificado digital</h3>
                    <p>La exportación de eGarage:</p>
                    <ul>
                        <li>No requiere certificado digital</li>
                        <li>Genera un archivo estándar compatible con sistemas contables</li>
                        <li>Puedes importarlo directamente en tu software contable</li>
                        <li>O usarlo como referencia para tu declaración manual</li>
                    </ul>
                    
                    <h3>Información incluida</h3>
                    <p>El CSV incluye columnas para:</p>
                    <ul>
                        <li>Fecha del documento</li>
                        <li>Número de documento</li>
                        <li>RUT del cliente</li>
                        <li>Monto neto</li>
                        <li>IVA (19%)</li>
                        <li>Total</li>
                    </ul>
                    
                    <p><strong>Tip:</strong> Exporta mensualmente para mantener tus registros actualizados y facilitar la declaración anual.</p>
                    """,
                    "orden": 2,
                },
            ],
            "Roles y Permisos": [
                {
                    "titulo": "Tipos de usuarios",
                    "contenido": """
                    <h2>Tipos de usuarios</h2>
                    
                    <p>eGarage tiene diferentes tipos de usuarios con distintos niveles de acceso:</p>
                    
                    <h3>1. Administrador</h3>
                    <p>Acceso completo al sistema:</p>
                    <ul>
                        <li>Gestión de todos los módulos</li>
                        <li>Configuración del sistema</li>
                        <li>Reportes y análisis</li>
                        <li>Gestión de usuarios</li>
                    </ul>
                    
                    <h3>2. Vendedor</h3>
                    <p>Enfocado en ventas y atención al cliente:</p>
                    <ul>
                        <li>Crear presupuestos y facturas</li>
                        <li>Gestionar clientes</li>
                        <li>Consultar inventario</li>
                        <li>Ver reportes de ventas</li>
                    </ul>
                    
                    <h3>3. Mecánico</h3>
                    <p>Acceso a operaciones del taller:</p>
                    <ul>
                        <li>Ver y editar sus órdenes de trabajo asignadas</li>
                        <li>Registrar servicios realizados</li>
                        <li>Consultar información de vehículos</li>
                        <li>No puede ver información financiera sensible</li>
                    </ul>
                    
                    <h3>4. Dueño</h3>
                    <p>Máximo nivel de acceso:</p>
                    <ul>
                        <li>Todos los permisos de administrador</li>
                        <li>Acceso a Business Intelligence</li>
                        <li>Configuración de suscripción</li>
                        <li>Gestión completa de la empresa</li>
                    </ul>
                    
                    <h3>5. Cliente externo (opcional)</h3>
                    <p>Acceso limitado para clientes:</p>
                    <ul>
                        <li>Ver estado de sus vehículos</li>
                        <li>Consultar documentos relacionados</li>
                        <li>Recibir notificaciones</li>
                        <li>Portal del cliente (si está habilitado)</li>
                    </ul>
                    """,
                    "orden": 1,
                },
                {
                    "titulo": "Qué puede y no puede hacer cada rol",
                    "contenido": """
                    <h2>Qué puede y no puede hacer cada rol</h2>
                    
                    <h3>Administrador</h3>
                    <p><strong>Puede:</strong></p>
                    <ul>
                        <li>✅ Crear, editar y eliminar documentos</li>
                        <li>✅ Gestionar clientes y vehículos</li>
                        <li>✅ Configurar el sistema</li>
                        <li>✅ Ver reportes</li>
                        <li>✅ Gestionar inventario</li>
                        <li>✅ Crear y gestionar usuarios</li>
                    </p>
                    <p><strong>No puede:</strong></p>
                    <ul>
                        <li>❌ Acceder a Business Intelligence (solo dueños)</li>
                        <li>❌ Cambiar configuración de suscripción</li>
                    </ul>
                    
                    <h3>Vendedor</h3>
                    <p><strong>Puede:</strong></p>
                    <ul>
                        <li>✅ Crear presupuestos y facturas</li>
                        <li>✅ Gestionar clientes</li>
                        <li>✅ Consultar inventario</li>
                        <li>✅ Ver reportes de ventas</li>
                    </ul>
                    <p><strong>No puede:</strong></p>
                    <ul>
                        <li>❌ Ver reportes financieros detallados</li>
                        <li>❌ Modificar configuración del sistema</li>
                        <li>❌ Gestionar usuarios</li>
                        <li>❌ Ver Business Intelligence</li>
                    </ul>
                    
                    <h3>Mecánico</h3>
                    <p><strong>Puede:</strong></p>
                    <ul>
                        <li>✅ Ver sus órdenes de trabajo asignadas</li>
                        <li>✅ Actualizar estado de trabajos</li>
                        <li>✅ Registrar servicios realizados</li>
                        <li>✅ Consultar información de vehículos</li>
                    </ul>
                    <p><strong>No puede:</strong></p>
                    <ul>
                        <li>❌ Ver información financiera (ganancias, costos)</li>
                        <li>❌ Crear facturas</li>
                        <li>❌ Modificar precios</li>
                        <li>❌ Acceder a configuración</li>
                        <li>❌ Ver reportes financieros</li>
                    </ul>
                    
                    <h3>Dueño</h3>
                    <p><strong>Puede:</strong></p>
                    <ul>
                        <li>✅ Todo lo que puede un administrador</li>
                        <li>✅ Acceder a Business Intelligence</li>
                        <li>✅ Gestionar suscripción y pagos</li>
                        <li>✅ Ver todos los reportes financieros</li>
                        <li>✅ Configuración completa del sistema</li>
                    </ul>
                    <p><strong>No puede:</strong></p>
                    <ul>
                        <li>❌ (Tiene acceso completo)</li>
                    </ul>
                    """,
                    "orden": 2,
                },
            ],
            "Configuración de la Empresa": [
                {
                    "titulo": "Cambiar logo, colores y nombre público",
                    "contenido": """
                    <h2>Cambiar logo, colores y nombre público</h2>
                    
                    <p>Personaliza la apariencia de eGarage para tu empresa usando la configuración de empresa.</p>
                    
                    <h3>Acceder a la configuración</h3>
                    <p>Ve a <strong>Configuración</strong> > <strong>Empresa</strong> (o usa el modelo ConfiguracionEmpresa).</p>
                    
                    <h3>Cambiar logo</h3>
                    <ol>
                        <li>En la sección <strong>Información Básica</strong></li>
                        <li>Haz clic en <strong>Subir Logo</strong></li>
                        <li>Selecciona la imagen de tu logo (formato PNG, JPG recomendado)</li>
                        <li>El logo aparecerá en:</li>
                        <ul>
                            <li>Documentos (presupuestos, facturas)</li>
                            <li>Dashboard</li>
                            <li>Encabezados del sistema</li>
                        </ul>
                    </ol>
                    
                    <h3>Cambiar colores</h3>
                    <p>En la sección <strong>Configuración Visual</strong>:</p>
                    <ul>
                        <li><strong>Brand Color:</strong> Color principal de tu marca</li>
                        <li>Este color se usa en elementos de la interfaz</li>
                        <li>Puedes usar un selector de color o ingresar el código hexadecimal</li>
                    </ul>
                    
                    <h3>Cambiar nombre público</h3>
                    <p>El <strong>nombre público</strong> es el que aparece en:</p>
                    <ul>
                        <li>Documentos emitidos</li>
                        <li>Comunicaciones con clientes</li>
                        <li>Portal del cliente (si está habilitado)</li>
                    </ul>
                    <p>Puede ser diferente al nombre legal de la empresa.</p>
                    
                    <h3>Tagline</h3>
                    <p>Opcionalmente puedes agregar un <strong>tagline</strong> o eslogan que aparecerá junto a tu nombre en algunos documentos.</p>
                    
                    <p><strong>Tip:</strong> Usa un logo de alta calidad (mínimo 200x200px) para que se vea bien en los documentos impresos.</p>
                    """,
                    "orden": 1,
                },
                {
                    "titulo": "Configurar IVA o sales tax según país",
                    "contenido": """
                    <h2>Configurar IVA o sales tax según país</h2>
                    
                    <p>La configuración de impuestos varía según tu país.</p>
                    
                    <h3>Chile - IVA 19%</h3>
                    <p>Para configurar el IVA en Chile:</p>
                    <ol>
                        <li>Ve a <strong>Configuración</strong> > <strong>Empresa</strong></li>
                        <li>En la sección <strong>Configuración Financiera</strong>:</li>
                        <ul>
                            <li><strong>Moneda:</strong> CLP (pesos chilenos)</li>
                            <li><strong>Tasa de impuesto:</strong> 19 (para IVA del 19%)</li>
                            <li><strong>Aplicar impuesto por defecto:</strong> Marca esta opción si quieres que el IVA se aplique automáticamente a los repuestos</li>
                        </ul>
                    </ol>
                    
                    <h3>USA - Sales Tax</h3>
                    <p>Para configurar el sales tax en USA:</p>
                    <ol>
                        <li>Ve a <strong>Configuración</strong> > <strong>Empresa</strong></li>
                        <li>En la sección <strong>Configuración Financiera</strong>:</li>
                        <ul>
                            <li><strong>Moneda:</strong> USD (dólares)</li>
                            <li><strong>Tasa de impuesto:</strong> Ingresa el porcentaje según tu estado (ej: 8.5 para 8.5%)</li>
                            <li><strong>Aplicar impuesto por defecto:</strong> Activa si quieres que se aplique automáticamente</li>
                        </ul>
                    </ol>
                    
                    <h3>Notas importantes</h3>
                    <ul>
                        <li>La tasa de impuesto se ingresa como número (19 para 19%, 8.5 para 8.5%)</li>
                        <li>Puedes desactivar "Aplicar impuesto por defecto" si prefieres aplicarlo manualmente en cada documento</li>
                        <li>Los cambios se aplican a documentos nuevos, no a documentos ya creados</li>
                    </ul>
                    """,
                    "orden": 2,
                },
                {
                    "titulo": "Configuraciones especiales por país",
                    "contenido": """
                    <h2>Configuraciones especiales por país</h2>
                    
                    <h3>Chile: CLP, IVA 19%</h3>
                    <p>Configuración estándar para Chile:</p>
                    <ul>
                        <li><strong>Moneda:</strong> CLP (Pesos Chilenos)</li>
                        <li><strong>IVA:</strong> 19% solo en repuestos</li>
                        <li><strong>Formato de números:</strong> Separador de miles: punto (.), Decimal: coma (,)</li>
                        <li><strong>RUT:</strong> Formato chileno (12.345.678-9)</li>
                    </ul>
                    
                    <h3>USA: USD y sales tax</h3>
                    <p>Configuración estándar para USA:</p>
                    <ul>
                        <li><strong>Moneda:</strong> USD (Dólares)</li>
                        <li><strong>Sales Tax:</strong> Varía por estado (configura según tu ubicación)</li>
                        <li><strong>Formato de números:</strong> Separador de miles: coma (,), Decimal: punto (.)</li>
                        <li><strong>Tax ID:</strong> SSN o EIN según corresponda</li>
                    </ul>
                    
                    <h3>México: MXN, IVA 16%</h3>
                    <p>Configuración estándar para México:</p>
                    <ul>
                        <li><strong>Moneda:</strong> MXN (Pesos Mexicanos)</li>
                        <li><strong>IVA:</strong> 16% (configurable)</li>
                        <li><strong>Formato de números:</strong> Separador de miles: coma (,), Decimal: punto (.)</li>
                        <li><strong>RFC:</strong> Formato mexicano</li>
                    </ul>
                    
                    <h3>Otros países</h3>
                    <p>eGarage se adapta a las configuraciones de cada país. Contacta al soporte si necesitas configuraciones específicas para tu país.</p>
                    """,
                    "orden": 3,
                },
            ],
            "Problemas Frecuentes (FAQ)": [
                {
                    "titulo": "No carga la lista de marcas",
                    "contenido": """
                    <h2>No carga la lista de marcas</h2>
                    
                    <p>Si al intentar crear un vehículo no se carga la lista de marcas, prueba las siguientes soluciones:</p>
                    
                    <h3>Causa 1: Caché móvil</h3>
                    <p><strong>Síntoma:</strong> En dispositivos móviles, la lista no aparece o tarda mucho.</p>
                    <p><strong>Solución:</strong></p>
                    <ol>
                        <li>Limpia la caché del navegador</li>
                        <li>Cierra y vuelve a abrir la aplicación</li>
                        <li>Recarga la página (pull to refresh en móvil)</li>
                    </ol>
                    
                    <h3>Causa 2: Script de carga no ejecutado</h3>
                    <p><strong>Síntoma:</strong> El campo de marca está vacío y no responde.</p>
                    <p><strong>Solución:</strong></p>
                    <ol>
                        <li>Recarga la página completamente (Ctrl+F5 o Cmd+Shift+R)</li>
                        <li>Verifica que JavaScript esté habilitado en tu navegador</li>
                        <li>Revisa la consola del navegador (F12) para ver si hay errores</li>
                    </ol>
                    
                    <h3>Causa 3: Falta de datos iniciales</h3>
                    <p><strong>Síntoma:</strong> El catálogo de marcas está vacío en la base de datos.</p>
                    <p><strong>Solución:</strong></p>
                    <ol>
                        <li>Contacta al administrador del sistema</li>
                        <li>Se debe ejecutar el comando de carga de catálogo: <code>python manage.py cargar_marcas_modelos</code></li>
                        <li>O contacta al soporte de eGarage</li>
                    </ol>
                    
                    <h3>Verificación rápida</h3>
                    <p>Para verificar si el problema es del catálogo:</p>
                    <ol>
                        <li>Intenta seleccionar un año diferente</li>
                        <li>Verifica tu conexión a internet</li>
                        <li>Prueba en otro navegador</li>
                    </ol>
                    """,
                    "orden": 1,
                },
                {
                    "titulo": "No puedo guardar un documento",
                    "contenido": """
                    <h2>No puedo guardar un documento</h2>
                    
                    <p>Si al intentar guardar un documento aparece un error, revisa los siguientes puntos:</p>
                    
                    <h3>Error: Falta cliente</h3>
                    <p><strong>Problema:</strong> No has seleccionado un cliente.</p>
                    <p><strong>Solución:</strong></p>
                    <ol>
                        <li>Selecciona un cliente del campo de búsqueda</li>
                        <li>Si el cliente no existe, créalo primero desde el menú de Clientes</li>
                        <li>El campo de cliente es obligatorio</li>
                    </ol>
                    
                    <h3>Error: Falta vehículo</h3>
                    <p><strong>Problema:</strong> No has seleccionado un vehículo.</p>
                    <p><strong>Solución:</strong></p>
                    <ol>
                        <li>Primero selecciona el cliente</li>
                        <li>Luego selecciona el vehículo del cliente</li>
                        <li>Si el vehículo no existe, créalo desde el menú de Vehículos</li>
                    </ol>
                    
                    <h3>Error: Sin repuestos/servicios</h3>
                    <p><strong>Problema:</strong> El documento no tiene repuestos ni servicios agregados.</p>
                    <p><strong>Solución:</strong></p>
                    <ol>
                        <li>Agrega al menos un repuesto O un servicio</li>
                        <li>Un documento vacío no se puede guardar</li>
                    </ol>
                    
                    <h3>Error: Campo técnico obligatorio</h3>
                    <p><strong>Problema:</strong> El sistema requiere asignar un técnico al documento.</p>
                    <p><strong>Solución:</strong></p>
                    <ol>
                        <li>Selecciona un técnico del campo correspondiente</li>
                        <li>Si no hay técnicos creados, ve a Configuración > Técnicos y crea uno</li>
                        <li>Este campo puede ser obligatorio según la configuración de tu empresa</li>
                    </ol>
                    
                    <h3>Otros errores comunes</h3>
                    <ul>
                        <li><strong>Error de conexión:</strong> Verifica tu internet y recarga la página</li>
                        <li><strong>Error de permisos:</strong> Verifica que tu usuario tenga permisos para crear documentos</li>
                        <li><strong>Error de validación:</strong> Revisa que todos los campos requeridos estén completos</li>
                    </ul>
                    """,
                    "orden": 2,
                },
            ],
            "Cuenta, Suscripción y Pagos": [
                {
                    "titulo": "Activar prueba gratis",
                    "contenido": """
                    <h2>Activar prueba gratis</h2>
                    
                    <p>eGarage ofrece una prueba gratuita de 30 días para que conozcas todas las funcionalidades.</p>
                    
                    <h3>Paso 1: Registrarse</h3>
                    <p>En la página de inicio:</p>
                    <ol>
                        <li>Haz clic en <strong>Probar Gratis</strong> o <strong>Activar Prueba</strong></li>
                        <li>Completa el formulario de registro:</li>
                        <ul>
                            <li>Nombre completo</li>
                            <li>Email</li>
                            <li>Contraseña</li>
                            <li>Nombre de tu empresa/taller</li>
                        </ul>
                    </ol>
                    
                    <h3>Paso 2: Confirmar email</h3>
                    <p>Revisa tu correo y haz clic en el enlace de confirmación.</p>
                    
                    <h3>Paso 3: Acceder al sistema</h3>
                    <p>Una vez confirmado, ya puedes iniciar sesión y comenzar a usar eGarage.</p>
                    
                    <h3>¿Qué incluye la prueba?</h3>
                    <ul>
                        <li>✅ Acceso completo a todas las funcionalidades</li>
                        <li>✅ Hasta 30 días de uso gratuito</li>
                        <li>✅ Sin necesidad de tarjeta de crédito</li>
                        <li>✅ Soporte por email</li>
                    </ul>
                    
                    <h3>Después de la prueba</h3>
                    <p>Al finalizar los 30 días:</p>
                    <ul>
                        <li>Recibirás un recordatorio antes del vencimiento</li>
                        <li>Podrás elegir un plan de suscripción</li>
                        <li>Tus datos se conservan</li>
                    </ul>
                    """,
                    "orden": 1,
                },
                {
                    "titulo": "Planes por país",
                    "contenido": """
                    <h2>Planes por país</h2>
                    
                    <p>eGarage ofrece diferentes planes según tu país y necesidades.</p>
                    
                    <h3>Chile</h3>
                    <ul>
                        <li><strong>Plan Básico:</strong> Ideal para talleres pequeños</li>
                        <li><strong>Plan Premium:</strong> Para talleres medianos con más funcionalidades</li>
                        <li><strong>Plan Empresarial:</strong> Para grandes operaciones con soporte prioritario</li>
                    </ul>
                    
                    <h3>USA</h3>
                    <ul>
                        <li><strong>Basic Plan:</strong> Essential features for small shops</li>
                        <li><strong>Premium Plan:</strong> Advanced features for growing businesses</li>
                        <li><strong>Enterprise Plan:</strong> Full features with priority support</li>
                    </ul>
                    
                    <h3>México</h3>
                    <ul>
                        <li><strong>Plan Básico:</strong> Funcionalidades esenciales</li>
                        <li><strong>Plan Premium:</strong> Funcionalidades avanzadas</li>
                        <li><strong>Plan Empresarial:</strong> Máximo rendimiento</li>
                    </ul>
                    
                    <h3>Comparar planes</h3>
                    <p>Para ver una comparación detallada de planes y precios:</p>
                    <ol>
                        <li>Ve a la sección de <strong>Precios</strong> en el sitio web</li>
                        <li>O contacta al equipo de ventas</li>
                    </ol>
                    
                    <p><strong>Nota:</strong> Los precios pueden variar según el país y la moneda local.</p>
                    """,
                    "orden": 2,
                },
                {
                    "titulo": "Cambiar plan o medio de pago",
                    "contenido": """
                    <h2>Cambiar plan o medio de pago</h2>
                    
                    <h3>Cambiar de plan</h3>
                    <p>Para cambiar a un plan diferente:</p>
                    <ol>
                        <li>Ve a <strong>Configuración</strong> > <strong>Suscripción</strong></li>
                        <li>Haz clic en <strong>Cambiar Plan</strong></li>
                        <li>Selecciona el nuevo plan que deseas</li>
                        <li>Revisa los cambios y confirma</li>
                    </ol>
                    
                    <h3>Actualizar medio de pago</h3>
                    <p>Para cambiar tu tarjeta o método de pago:</p>
                    <ol>
                        <li>Ve a <strong>Configuración</strong> > <strong>Suscripción</strong></li>
                        <li>Haz clic en <strong>Método de Pago</strong></li>
                        <li>Ingresa los nuevos datos de pago</li>
                        <li>Guarda los cambios</li>
                    </ol>
                    
                    <h3>Facturación</h3>
                    <p>Puedes ver y descargar tus facturas:</p>
                    <ul>
                        <li>Historial de pagos</li>
                        <li>Facturas en PDF</li>
                        <li>Exportar para contabilidad</li>
                    </ul>
                    
                    <h3>Cancelar suscripción</h3>
                    <p>Si necesitas cancelar tu suscripción:</p>
                    <ol>
                        <li>Ve a <strong>Configuración</strong> > <strong>Suscripción</strong></li>
                        <li>Haz clic en <strong>Cancelar Suscripción</strong></li>
                        <li>Confirma la cancelación</li>
                    </ol>
                    <p><strong>Nota:</strong> Tu cuenta seguirá activa hasta el final del período pagado. Tus datos se conservan por 30 días después de la cancelación.</p>
                    """,
                    "orden": 3,
                },
            ],
        }

        # Crear artículos
        total_articulos = 0
        for categoria_nombre, articulos in articulos_data.items():
            categoria = categorias_creadas.get(categoria_nombre)
            if not categoria:
                self.stdout.write(
                    self.style.ERROR(f"❌ Categoría no encontrada: {categoria_nombre}")
                )
                continue

            for art_data in articulos:
                slug = slugify(art_data["titulo"])
                articulo, created = HelpArticle.objects.get_or_create(
                    slug=slug,
                    defaults={
                        "categoria": categoria,
                        "titulo": art_data["titulo"],
                        "contenido": art_data["contenido"],
                        "orden": art_data.get("orden", 0),
                    },
                )
                if created:
                    self.stdout.write(
                        self.style.SUCCESS(f"  ✅ Artículo creado: {articulo.titulo}")
                    )
                    total_articulos += 1
                else:
                    # Actualizar si ya existe
                    for key, value in art_data.items():
                        if key != "titulo":  # No actualizar título (es parte del slug)
                            setattr(articulo, key, value)
                    articulo.categoria = categoria
                    articulo.save()
                    self.stdout.write(
                        self.style.WARNING(f"  ⚠️  Artículo actualizado: {articulo.titulo}")
                    )

        self.stdout.write(self.style.SUCCESS(f"\n🎉 ¡Centro de Ayuda cargado exitosamente!"))
        self.stdout.write(self.style.SUCCESS(f"📊 Resumen:"))
        self.stdout.write(self.style.SUCCESS(f"   - Categorías: {len(categorias_creadas)}"))
        self.stdout.write(self.style.SUCCESS(f"   - Artículos: {total_articulos}"))
        self.stdout.write(self.style.SUCCESS(f"\n🌐 Accede al Centro de Ayuda en: /help/"))
