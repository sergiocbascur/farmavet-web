#!/usr/bin/env python3
"""
Script para configurar SMTP sin necesidad de sudo
Crea un archivo de configuración que la aplicación puede leer
"""

import os
import json
from pathlib import Path

def configurar_smtp():
    """Configura SMTP mediante archivo de configuración"""
    
    print("\n" + "="*60)
    print("  CONFIGURACIÓN SMTP - FARMAVET")
    print("="*60 + "\n")
    
    # Ruta del archivo de configuración (en el directorio del proyecto)
    config_dir = Path(__file__).parent
    config_file = config_dir / 'smtp_config.json'
    
    print("Ingresa la configuración SMTP:\n")
    
    smtp_host = input("SMTP Host (ej: smtp.gmail.com): ").strip()
    smtp_port = input("SMTP Port (ej: 587): ").strip()
    smtp_user = input("SMTP User (email): ").strip()
    smtp_password = input("SMTP Password: ").strip()
    smtp_from = input("SMTP From (email remitente, opcional): ").strip()
    
    if not smtp_from:
        smtp_from = smtp_user
    
    # Validar campos requeridos
    if not all([smtp_host, smtp_port, smtp_user, smtp_password]):
        print("\n❌ Error: Todos los campos son requeridos")
        return False
    
    # Guardar configuración
    config = {
        'SMTP_HOST': smtp_host,
        'SMTP_PORT': int(smtp_port),
        'SMTP_USER': smtp_user,
        'SMTP_PASSWORD': smtp_password,
        'SMTP_FROM': smtp_from
    }
    
    try:
        # Guardar en archivo JSON
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        # Establecer permisos restrictivos (solo lectura para otros)
        os.chmod(config_file, 0o600)
        
        print(f"\n✅ Configuración guardada en: {config_file}")
        print("\n⚠️  IMPORTANTE: Necesitas modificar app.py para leer este archivo")
        print("   O usar EnvironmentFile en systemd (requiere sudo una vez)")
        print("\nPara usar EnvironmentFile:")
        print("1. Convierte el JSON a formato de variables de entorno:")
        print(f"   cat {config_file} | jq -r 'to_entries | .[] | \"\(.key)=\(.value)\"' > smtp.env")
        print("2. Edita /etc/systemd/system/farmavet-web.service y agrega:")
        print(f"   EnvironmentFile=/home/web/farmavet-web/smtp.env")
        print("3. Recarga: sudo systemctl daemon-reload")
        print("4. Reinicia: sudo systemctl restart farmavet-web")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error al guardar configuración: {e}")
        return False

def crear_env_file():
    """Crea un archivo .env con las variables SMTP"""
    
    config_file = Path(__file__).parent / 'smtp_config.json'
    
    if not config_file.exists():
        print("❌ Primero ejecuta la configuración: python3 config_smtp.py")
        return False
    
    # Leer configuración JSON
    with open(config_file, 'r') as f:
        config = json.load(f)
    
    # Crear archivo .env
    env_file = Path(__file__).parent / 'smtp.env'
    
    with open(env_file, 'w') as f:
        for key, value in config.items():
            f.write(f'{key}={value}\n')
    
    os.chmod(env_file, 0o600)
    
    print(f"\n✅ Archivo smtp.env creado: {env_file}")
    print("\nEste archivo puede ser usado con EnvironmentFile en systemd")
    print("(Requiere que alguien con sudo edite el servicio una vez)")
    
    return True

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--create-env':
        crear_env_file()
    else:
        configurar_smtp()
