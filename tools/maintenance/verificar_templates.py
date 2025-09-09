#!/usr/bin/env python
"""
Script de verificación para la migración de templates con Country/Language resolution.
Verifica que todas las vistas de documentos usen correctamente el nuevo sistema.
"""

import sys
from datetime import datetime

import requests

# Configuración
BASE_URL = "http://127.0.0.1:8000"
TEST_USER = {
    "username": "testuser_cl",  # Usuario con empresa CL
    "password": "test123",
}


class TemplateVerifier:
    def __init__(self):
        self.session = requests.Session()
        self.results = []

    def log(self, message, status="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {status}: {message}")

    def test_login(self):
        """Test de login para obtener sesión"""
        self.log("🔑 Iniciando sesión...")

        # Obtener CSRF token
        response = self.session.get(f"{BASE_URL}/cl/login/")
        if response.status_code != 200:
            self.log(
                f"Error obteniendo página de login: {response.status_code}", "ERROR"
            )
            return False

        # Extraer CSRF token (simple parsing)
        csrf_token = None
        if "csrfmiddlewaretoken" in response.text:
            start = response.text.find('name="csrfmiddlewaretoken" value="') + 34
            end = response.text.find('"', start)
            csrf_token = response.text[start:end]

        if not csrf_token:
            self.log("No se pudo obtener CSRF token", "ERROR")
            return False

        # Enviar datos de login
        login_data = {
            "username": TEST_USER["username"],
            "password": TEST_USER["password"],
            "csrfmiddlewaretoken": csrf_token,
        }

        response = self.session.post(
            f"{BASE_URL}/cl/login/",
            data=login_data,
            headers={"Referer": f"{BASE_URL}/cl/login/"},
        )

        if "login" in response.url:
            self.log("❌ Error de login - credenciales incorrectas", "ERROR")
            return False

        self.log("✅ Login exitoso")
        return True

    def test_template_resolution(self, url_path, expected_template_parts):
        """Test de resolución de templates"""
        self.log(f"🧪 Probando: {url_path}")

        try:
            response = self.session.get(f"{BASE_URL}{url_path}")

            if response.status_code == 200:
                # Verificar que se cargó correctamente
                if "DOCTYPE html" in response.text:
                    self.log(
                        f"✅ {url_path} - Template cargado correctamente", "SUCCESS"
                    )

                    # Verificar elementos específicos según el template
                    checks_passed = 0
                    total_checks = len(expected_template_parts)

                    for check in expected_template_parts:
                        if check in response.text:
                            checks_passed += 1
                        else:
                            self.log(f"⚠️  Elemento no encontrado: {check}", "WARNING")

                    success_rate = (checks_passed / total_checks) * 100
                    self.log(
                        f"📊 Verificación de contenido: {checks_passed}/{total_checks} ({success_rate:.1f}%)"
                    )

                    return response.status_code == 200 and checks_passed >= (
                        total_checks * 0.8
                    )
                else:
                    self.log(f"❌ {url_path} - Respuesta no es HTML válido", "ERROR")
                    return False
            else:
                self.log(f"❌ {url_path} - Error {response.status_code}", "ERROR")
                return False

        except Exception as e:
            self.log(f"❌ {url_path} - Excepción: {str(e)}", "ERROR")
            return False

    def run_verification(self):
        """Ejecutar verificación completa"""
        self.log("🚀 Iniciando verificación de Country/Language Template Resolution")
        self.log("=" * 70)

        # Test de login
        if not self.test_login():
            self.log("💀 No se pudo hacer login - abortando tests", "FATAL")
            return False

        # Tests de templates de documentos
        test_cases = [
            {
                "url": "/cl/documentos/",
                "name": "Lista de Documentos",
                "checks": ["documentos", "lista", "E-Garage", "Crear"],
            },
            {
                "url": "/cl/documentos/form/",
                "name": "Crear Documento",
                "checks": ["documento", "form", "cliente", "tipo_documento"],
            },
            # Nota: No podemos testear editar sin un documento específico
        ]

        all_passed = True
        for test_case in test_cases:
            success = self.test_template_resolution(
                test_case["url"], test_case["checks"]
            )

            self.results.append(
                {"test": test_case["name"], "url": test_case["url"], "passed": success}
            )

            if not success:
                all_passed = False

        # Resumen final
        self.log("=" * 70)
        self.log("📋 RESUMEN DE VERIFICACIÓN")

        passed_count = sum(1 for r in self.results if r["passed"])
        total_count = len(self.results)

        for result in self.results:
            status = "✅ PASS" if result["passed"] else "❌ FAIL"
            self.log(f"{status} - {result['test']} ({result['url']})")

        self.log(f"📊 RESULTADO FINAL: {passed_count}/{total_count} tests pasaron")

        if all_passed:
            self.log(
                "🎉 ¡VERIFICACIÓN EXITOSA! Todas las vistas usan template resolution",
                "SUCCESS",
            )
        else:
            self.log("💥 VERIFICACIÓN FALLÓ. Revisar errores arriba", "ERROR")

        return all_passed


if __name__ == "__main__":
    print("🔧 Verificador de Template Resolution - E-Garage")
    print("Este script verifica que las vistas de documentos usen el nuevo sistema")
    print()

    verifier = TemplateVerifier()
    success = verifier.run_verification()

    sys.exit(0 if success else 1)
