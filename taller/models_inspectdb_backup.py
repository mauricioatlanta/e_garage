
from django.db import models

# Proxy para compatibilidad con código que usa 'Cliente'
class Cliente(models.Model):
    class Meta:
        proxy = True
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'

    def __new__(cls, *args, **kwargs):
        from .models import TallerCliente
        return TallerCliente(*args, **kwargs)


class AccountEmailaddress(models.Model):
    verified = models.BooleanField()
    primary = models.BooleanField()
    user = models.ForeignKey('AuthUser', models.DO_NOTHING)
    email = models.CharField(unique=True, max_length=254)

    cliente = models.ForeignKey('TallerCliente', models.DO_NOTHING)

class Meta:
    managed = False
    db_table = 'account_emailaddress'
    unique_together = (('user', 'primary'), ('user', 'email'),)


class AccountEmailconfirmation(models.Model):
    created = models.DateTimeField()
    sent = models.DateTimeField(blank=True, null=True)
    key = models.CharField(unique=True, max_length=64)
    email_address = models.ForeignKey(AccountEmailaddress, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'account_emailconfirmation'


class AuthGroup(models.Model):
    name = models.CharField(unique=True, max_length=150)

    class Meta:
        managed = False
        db_table = 'auth_group'


class AuthGroupPermissions(models.Model):
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)
    permission = models.ForeignKey('AuthPermission', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_group_permissions'
        unique_together = (('group', 'permission'),)


class AuthPermission(models.Model):
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING)
    codename = models.CharField(max_length=100)
    name = models.CharField(max_length=255)

    class Meta:
        managed = False
        db_table = 'auth_permission'
        unique_together = (('content_type', 'codename'),)


class AuthUser(models.Model):
    password = models.CharField(max_length=128)
    last_login = models.DateTimeField(blank=True, null=True)
    is_superuser = models.BooleanField()
    username = models.CharField(unique=True, max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.CharField(max_length=254)
    is_staff = models.BooleanField()
    is_active = models.BooleanField()
    date_joined = models.DateTimeField()
    first_name = models.CharField(max_length=150)

    class Meta:
        managed = False
        db_table = 'auth_user'


class AuthUserGroups(models.Model):
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_groups'
        unique_together = (('user', 'group'),)


class AuthUserUserPermissions(models.Model):
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    permission = models.ForeignKey(AuthPermission, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_user_permissions'
        unique_together = (('user', 'permission'),)


class DjangoAdminLog(models.Model):
    object_id = models.TextField(blank=True, null=True)
    object_repr = models.CharField(max_length=200)
    action_flag = models.PositiveSmallIntegerField()
    change_message = models.TextField()
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING, blank=True, null=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    action_time = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_admin_log'


class DjangoContentType(models.Model):
    app_label = models.CharField(max_length=100)
    model = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'django_content_type'
        unique_together = (('app_label', 'model'),)


class DjangoMigrations(models.Model):
    app = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    applied = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_migrations'


class DjangoSession(models.Model):
    session_key = models.CharField(primary_key=True, max_length=40)
    session_data = models.TextField()
    expire_date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_session'


class DjangoSite(models.Model):
    name = models.CharField(max_length=50)
    domain = models.CharField(unique=True, max_length=100)

    class Meta:
        managed = False
        db_table = 'django_site'


class SocialaccountSocialaccount(models.Model):
    provider = models.CharField(max_length=200)
    uid = models.CharField(max_length=191)
    last_login = models.DateTimeField()
    date_joined = models.DateTimeField()
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    extra_data = models.JSONField()

    class Meta:
        managed = False
        db_table = 'socialaccount_socialaccount'
        unique_together = (('provider', 'uid'),)


class SocialaccountSocialapp(models.Model):
    provider = models.CharField(max_length=30)
    name = models.CharField(max_length=40)
    client_id = models.CharField(max_length=191)
    secret = models.CharField(max_length=191)
    key = models.CharField(max_length=191)
    provider_id = models.CharField(max_length=200)
    settings = models.JSONField()

    class Meta:
        managed = False
        db_table = 'socialaccount_socialapp'


class SocialaccountSocialappSites(models.Model):
    socialapp = models.ForeignKey(SocialaccountSocialapp, models.DO_NOTHING)
    site = models.ForeignKey(DjangoSite, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'socialaccount_socialapp_sites'
        unique_together = (('socialapp', 'site'),)


class SocialaccountSocialtoken(models.Model):
    token = models.TextField()
    token_secret = models.TextField()
    expires_at = models.DateTimeField(blank=True, null=True)
    account = models.ForeignKey(SocialaccountSocialaccount, models.DO_NOTHING)
    app = models.ForeignKey(SocialaccountSocialapp, models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'socialaccount_socialtoken'
        unique_together = (('app', 'account'),)


class TallerCategoriaservicio(models.Model):
    nombre = models.CharField(max_length=255)
    descripcion = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'taller_categoriaservicio'


class TallerCita(models.Model):
    fecha = models.DateTimeField()
    motivo = models.TextField()
    cliente = models.ForeignKey('TallerCliente', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'taller_cita'


class TallerCitataller(models.Model):
    fecha = models.DateField()
    hora = models.TimeField()
    tipo = models.CharField(max_length=20)
    estado = models.CharField(max_length=20)
    cliente = models.ForeignKey('TallerCliente', models.DO_NOTHING)
    vehiculo = models.ForeignKey('Vehiculo', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'taller_citataller'


class TallerCiudad(models.Model):
    nombre = models.CharField(max_length=100)
    region = models.ForeignKey('Region', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'taller_ciudad'


class TallerCliente(models.Model):
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100, blank=True, null=True)
    telefono = models.CharField(max_length=15, blank=True, null=True)
    correo = models.CharField(max_length=254, blank=True, null=True)
    direccion = models.CharField(max_length=255, blank=True, null=True)
    ciudad = models.ForeignKey('Ciudad', models.DO_NOTHING, blank=True, null=True)
    region = models.ForeignKey('Region', models.DO_NOTHING, blank=True, null=True)
    email = models.CharField(max_length=254, blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'taller_cliente'


class TallerDetalledocumento(models.Model):
    tipo_item = models.CharField(max_length=20)
    nombre_repuesto = models.CharField(max_length=100)
    part_number = models.CharField(max_length=100)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=5)  # max_digits and decimal_places have been guessed, as this database handles decimal fields as float
    precio_compra = models.DecimalField(max_digits=10, decimal_places=5)  # max_digits and decimal_places have been guessed, as this database handles decimal fields as float
    precio_venta = models.DecimalField(max_digits=10, decimal_places=5)  # max_digits and decimal_places have been guessed, as this database handles decimal fields as float
    cantidad = models.PositiveIntegerField()
    subtotal = models.DecimalField(max_digits=10, decimal_places=5)  # max_digits and decimal_places have been guessed, as this database handles decimal fields as float
    comentario_mecanico = models.TextField(blank=True, null=True)
    imagen_evidencia = models.CharField(max_length=100, blank=True, null=True)
    documento = models.ForeignKey('Documento', models.DO_NOTHING)
    repuesto = models.ForeignKey('TallerRepuesto', models.DO_NOTHING, blank=True, null=True)
    servicio = models.ForeignKey('TallerServicio', models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'taller_detalledocumento'


class Documento(models.Model):
    tipo_documento = models.CharField(max_length=50)
    fecha = models.DateField()

    class Meta:
        managed = False
        db_table = 'taller_documentotaller'


class TallerMarca(models.Model):
    nombre = models.CharField(max_length=50)

    class Meta:
        managed = False
        db_table = 'taller_marca'


class TallerModelo(models.Model):
    nombre = models.CharField(max_length=50)
    marca = models.ForeignKey(TallerMarca, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'taller_modelo'


class TallerPlantillaservicio(models.Model):
    nombre = models.CharField(unique=True, max_length=100)
    descripcion = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'taller_plantillaservicio'


class TallerPlantillaservicioServicios(models.Model):
    plantillaservicio = models.ForeignKey(TallerPlantillaservicio, models.DO_NOTHING)
    servicio = models.ForeignKey('TallerServicio', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'taller_plantillaservicio_servicios'
        unique_together = (('plantillaservicio', 'servicio'),)


class Region(models.Model):
    nombre = models.CharField(unique=True, max_length=100)

    class Meta:
        managed = False
        db_table = 'taller_region'


class TallerRepuesto(models.Model):
    nombre_repuesto = models.CharField(max_length=100)
    part_number = models.CharField(max_length=100)
    precio_venta = models.DecimalField(max_digits=10, decimal_places=5)  # max_digits and decimal_places have been guessed, as this database handles decimal fields as float
    precio_compra = models.DecimalField(max_digits=10, decimal_places=5)  # max_digits and decimal_places have been guessed, as this database handles decimal fields as float
    stock = models.IntegerField()
    tienda = models.ForeignKey('Tienda', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'taller_repuesto'
        unique_together = (('tienda', 'part_number'),)


class TallerServicio(models.Model):
    nombre = models.CharField(max_length=255)
    precio = models.DecimalField(max_digits=10, decimal_places=5)  # max_digits and decimal_places have been guessed, as this database handles decimal fields as float
    categoria = models.ForeignKey(TallerCategoriaservicio, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'taller_servicio'


class TallerSuscripcion(models.Model):
    plan = models.CharField(max_length=50)
    fecha_inicio = models.DateField()
    fecha_vencimiento = models.DateField()
    estado = models.CharField(max_length=20)
    cliente = models.ForeignKey('TallerCliente', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'taller_suscripcion'


class Tienda(models.Model):
    nombre = models.CharField(unique=True, max_length=100)
    direccion = models.CharField(max_length=255, blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    activo = models.BooleanField()

    class Meta:
        managed = False
        db_table = 'taller_tienda'


class Vehiculo(models.Model):
    anio = models.PositiveIntegerField()
    patente = models.CharField(unique=True, max_length=10)
    motor = models.CharField(max_length=100, blank=True, null=True)
    caja = models.CharField(max_length=100, blank=True, null=True)
    vin = models.CharField(unique=True, max_length=50, blank=True, null=True)
    color = models.CharField(max_length=50, blank=True, null=True)
    cliente = models.ForeignKey('TallerCliente', models.DO_NOTHING)
    modelo = models.ForeignKey(TallerModelo, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'taller_vehiculo'