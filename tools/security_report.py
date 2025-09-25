#!/usr/bin/env python3
"""
Script para generar un reporte de seguridad legible a partir de pip-audit.
"""

import json
import pathlib
from datetime import datetime


def main():
    report_file = pathlib.Path("reports/pip_audit_env.json")

    if not report_file.exists():
        print("❌ No se encontró el archivo de reporte de pip-audit")
        print("Ejecuta: pip-audit -f json -o reports/pip_audit_env.json")
        return

    with open(report_file, encoding="utf-8") as f:
        data = json.load(f)

    print("🔒 REPORTE DE SEGURIDAD - VULNERABILIDADES EN DEPENDENCIAS")
    print("=" * 60)
    print(f"📅 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    vulnerable_packages = []
    total_vulns = 0

    for dep in data.get("dependencies", []):
        if dep.get("vulns"):
            vulnerable_packages.append(dep)
            total_vulns += len(dep["vulns"])

    print("📊 RESUMEN:")
    print(f"   • Paquetes vulnerables: {len(vulnerable_packages)}")
    print(f"   • Total de vulnerabilidades: {total_vulns}")
    print()

    if not vulnerable_packages:
        print("✅ ¡Excelente! No se encontraron vulnerabilidades.")
        return

    print("🚨 VULNERABILIDADES ENCONTRADAS:")
    print("-" * 60)

    for pkg in vulnerable_packages:
        name = pkg["name"]
        version = pkg["version"]
        vulns = pkg["vulns"]

        print(f"\n📦 {name} v{version}")
        print(f"   Vulnerabilidades: {len(vulns)}")

        for vuln in vulns:
            vuln_id = vuln.get("id", "N/A")
            aliases = vuln.get("aliases", [])
            description = vuln.get("description", "Sin descripción")
            fix_versions = vuln.get("fix_versions", [])

            print(f"   🔴 {vuln_id}")
            if aliases:
                print(f"      CVE: {', '.join(aliases)}")
            if fix_versions:
                print(f"      Versión segura: {', '.join(fix_versions)}")
            print(f"      Descripción: {description[:100]}...")

    print("\n" + "=" * 60)
    print("💡 RECOMENDACIONES:")
    print("1. Actualizar paquetes a las versiones seguras indicadas")
    print("2. Revisar dependencias transitivas")
    print("3. Considerar usar dependabot para actualizaciones automáticas")
    print("4. Ejecutar pip-audit regularmente en CI/CD")

    # Generar archivo de resumen
    summary_file = pathlib.Path("reports/security_summary.md")
    with open(summary_file, "w", encoding="utf-8") as f:
        f.write("# Reporte de Seguridad\n\n")
        f.write(f"**Fecha:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**Paquetes vulnerables:** {len(vulnerable_packages)}\n")
        f.write(f"**Total vulnerabilidades:** {total_vulns}\n\n")

        if vulnerable_packages:
            f.write("## Vulnerabilidades\n\n")
            for pkg in vulnerable_packages:
                f.write(f"### {pkg['name']} v{pkg['version']}\n\n")
                for vuln in pkg["vulns"]:
                    f.write(f"- **{vuln.get('id', 'N/A')}**\n")
                    if vuln.get("aliases"):
                        f.write(f"  - CVE: {', '.join(vuln['aliases'])}\n")
                    if vuln.get("fix_versions"):
                        f.write(
                            f"  - Versión segura: {', '.join(vuln['fix_versions'])}\n"
                        )
                    f.write(f"  - {vuln.get('description', 'Sin descripción')}\n\n")

    print(f"\n📄 Resumen guardado en: {summary_file}")


if __name__ == "__main__":
    main()
