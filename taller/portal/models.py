"""
Modelos para el Portal del Cliente
"""

import secrets
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone

from taller.models.clientes import Cliente


class ClienteToken(models.Model):
    """
    Token único y temporal para acceso seguro al portal del cliente.
    Permite que el taller envíe un enlace único al cliente sin necesidad
    de que el cliente tenga una contraseña.
    """

    cliente = models.ForeignKey(
        Cliente, on_delete=models.CASCADE, related_name="tokens_portal", verbose_name="Cliente"
    )
    token = models.CharField(
        max_length=64, unique=True, db_index=True, verbose_name="Token de acceso"
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    fecha_expiracion = models.DateTimeField(verbose_name="Fecha de expiración")
    usado = models.BooleanField(default=False, verbose_name="¿Ya fue usado?")
    fecha_uso = models.DateTimeField(null=True, blank=True, verbose_name="Fecha de uso")
    ip_uso = models.GenericIPAddressField(null=True, blank=True, verbose_name="IP de uso")

    class Meta:
        verbose_name = "Token de Cliente"
        verbose_name_plural = "Tokens de Clientes"
        ordering = ["-fecha_creacion"]
        indexes = [
            models.Index(fields=["token", "usado", "fecha_expiracion"]),
        ]

    def __str__(self):
        return f"Token {self.token[:8]}... para {self.cliente.nombre}"

    @classmethod
    def generar_token(cls, cliente, dias_validez=30):
        """
        Genera un nuevo token para un cliente.

        Args:
            cliente: Instancia de Cliente
            dias_validez: Días de validez del token (default: 30)

        Returns:
            ClienteToken: Instancia creada
        """
        token = secrets.token_urlsafe(48)  # Token seguro de 64 caracteres
        fecha_expiracion = timezone.now() + timedelta(days=dias_validez)

        return cls.objects.create(cliente=cliente, token=token, fecha_expiracion=fecha_expiracion)

    def es_valido(self):
        """Verifica si el token es válido (no usado y no expirado)"""
        if self.usado:
            return False
        if timezone.now() > self.fecha_expiracion:
            return False
        return True

    def usar(self, ip=None):
        """
        Marca el token como usado.

        Args:
            ip: IP desde donde se usó el token
        """
        self.usado = True
        self.fecha_uso = timezone.now()
        if ip:
            self.ip_uso = ip
        self.save()

    def invalidar(self):
        """Invalida el token manualmente"""
        self.usado = True
        self.save()


class ClienteCredencial(models.Model):
    """
    Credenciales de autenticación para clientes finales.
    Permite que los clientes se autentiquen con email/teléfono + contraseña.
    """

    cliente = models.OneToOneField(
        Cliente,
        on_delete=models.CASCADE,
        related_name="credenciales_portal",
        verbose_name="Cliente",
    )
    email = models.EmailField(unique=True, db_index=True, verbose_name="Email de acceso")
    telefono = models.CharField(
        max_length=15, blank=True, null=True, db_index=True, verbose_name="Teléfono de acceso"
    )
    password_hash = models.CharField(max_length=128, verbose_name="Hash de contraseña")
    activo = models.BooleanField(default=True, verbose_name="¿Activo?")
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    ultimo_acceso = models.DateTimeField(null=True, blank=True, verbose_name="Último acceso")

    class Meta:
        verbose_name = "Credencial de Cliente"
        verbose_name_plural = "Credenciales de Clientes"
        indexes = [
            models.Index(fields=["email", "activo"]),
            models.Index(fields=["telefono", "activo"]),
        ]

    def __str__(self):
        return f"Credenciales de {self.cliente.nombre} ({self.email})"

    def set_password(self, raw_password):
        """
        Establece la contraseña del cliente.

        Args:
            raw_password: Contraseña en texto plano
        """
        from django.contrib.auth.hashers import make_password

        self.password_hash = make_password(raw_password)
        self.save()

    def check_password(self, raw_password):
        """
        Verifica si la contraseña es correcta.

        Args:
            raw_password: Contraseña en texto plano

        Returns:
            bool: True si la contraseña es correcta
        """
        from django.contrib.auth.hashers import check_password

        return check_password(raw_password, self.password_hash)

    def actualizar_ultimo_acceso(self):
        """Actualiza la fecha del último acceso"""
        self.ultimo_acceso = timezone.now()
        self.save(update_fields=["ultimo_acceso"])
