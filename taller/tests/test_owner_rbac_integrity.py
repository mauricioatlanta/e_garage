from django.contrib.auth.models import Group, User
from django.test import TestCase

from taller.models.empresa import Empresa
from taller.models.team_member import TeamMember


class OwnerRBACIntegrityTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        for role in ["Owner", "Admin", "Vendedor", "Tecnico"]:
            Group.objects.get_or_create(name=role)

    def _crear_user(self, username):
        return User.objects.create_user(
            username=username,
            email=f"{username}@example.com",
            password="testpass123",
        )

    def _crear_empresa(self, user, nombre="Empresa Test", pais="CL"):
        return Empresa.objects.create(
            user=user,
            nombre_taller=nombre,
            empresa=nombre,
            pais=pais,
        )

    def test_empresa_create_auto_assigns_owner_group_and_teammember(self):
        user = self._crear_user("owner_create")
        empresa = self._crear_empresa(user, "Empresa Create")

        user.refresh_from_db()

        self.assertTrue(
            user.groups.filter(name="Owner").exists(),
            "El owner lógico debe quedar en grupo Owner al crear Empresa",
        )
        self.assertTrue(
            TeamMember.objects.filter(
                user=user,
                empresa=empresa,
                rol="Owner",
                is_active=True,
            ).exists(),
            "Debe crearse TeamMember Owner activo al crear Empresa",
        )

    def test_empresa_save_repairs_missing_owner_group_and_teammember(self):
        user = self._crear_user("owner_repair")
        empresa = self._crear_empresa(user, "Empresa Repair")

        user.groups.clear()
        TeamMember.objects.filter(user=user, empresa=empresa).delete()

        empresa.nombre_taller = "Empresa Repair 2"
        empresa.save()

        user.refresh_from_db()

        self.assertTrue(
            user.groups.filter(name="Owner").exists(),
            "Si el owner pierde el grupo, save() de Empresa debe repararlo",
        )
        self.assertTrue(
            TeamMember.objects.filter(
                user=user,
                empresa=empresa,
                rol="Owner",
                is_active=True,
            ).exists(),
            "Si falta TeamMember Owner, save() de Empresa debe recrearlo",
        )
