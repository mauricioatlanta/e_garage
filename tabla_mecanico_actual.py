# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class TallerMecanico(models.Model):
    nombre = models.CharField(max_length=100)
    activo = models.BooleanField()
    empresa = models.ForeignKey('TallerEmpresa', models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'taller_mecanico'
        unique_together = (('empresa', 'nombre'),)
