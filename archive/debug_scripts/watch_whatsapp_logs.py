#!/usr/bin/env python
"""
Script helper para ver logs de WhatsApp en tiempo real
Filtra y muestra solo los logs relevantes de eGarage Air
"""
import subprocess
import sys
import re

def colorize_log(line):
    """Colorear logs según su nivel"""
    if "ERROR" in line:
        return f"\033[91m{line}\033[0m"  # Rojo
    elif "WARNING" in line:
        return f"\033[93m{line}\033[0m"  # Amarillo
    elif "INFO" in line:
        return f"\033[92m{line}\033[0m"  # Verde
    elif "DEBUG" in line:
        return f"\033[96m{line}\033[0m"  # Cyan
    return line

def filter_whatsapp_logs():
    """Filtrar y mostrar solo logs de WhatsApp"""
    print("="*70)
    print("🔍 FILTRADOR DE LOGS - eGarage Air (WhatsApp)")
    print("="*70)
    print("\n📋 Mostrando solo logs de WhatsApp...")
    print("💡 Presiona Ctrl+C para salir\n")
    print("-"*70)
    
    # Ejecutar runserver y capturar output
    try:
        process = subprocess.Popen(
            ["python", "manage.py", "runserver"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        keywords = [
            "whatsapp",
            "INFO",
            "ERROR",
            "WARNING",
            "DEBUG",
            "Mensaje recibido",
            "Estado actual",
            "Procesando acción",
            "Confianza",
            "Sesión",
        ]
        
        for line in process.stdout:
            line_lower = line.lower()
            
            # Mostrar si contiene palabras clave relevantes
            if any(keyword.lower() in line_lower for keyword in keywords):
                # Colorear y mostrar
                colored = colorize_log(line.rstrip())
                print(colored)
            # También mostrar líneas que parecen ser de Django/requests
            elif "POST /whatsapp/webhook/" in line or "GET /whatsapp/webhook/" in line:
                print(f"\033[94m{line.rstrip()}\033[0m")  # Azul para requests
    
    except KeyboardInterrupt:
        print("\n\n👋 Filtrador detenido")
        process.terminate()
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    filter_whatsapp_logs()
