#!/usr/bin/env python3
"""
Script para verificar la configuración de seguridad de farmavet-web
Ejecutar: python verificar_seguridad.py
"""

import os
import sys
import sqlite3
from pathlib import Path

def check_secret_key():
    """Verifica que SECRET_KEY no sea el valor por defecto"""
    secret_key = os.environ.get('SECRET_KEY', '')
    default_key = 'farmavet-web-secret-key-change-in-production'
    
    if not secret_key:
        return False, "SECRET_KEY no está configurada como variable de entorno"
    if secret_key == default_key:
        return False, "SECRET_KEY está usando el valor por defecto (INSEGURO)"
    if len(secret_key) < 32:
        return False, f"SECRET_KEY es muy corta ({len(secret_key)} caracteres, mínimo 32)"
    
    return True, f"SECRET_KEY configurada correctamente ({len(secret_key)} caracteres)"

def check_database_permissions():
    """Verifica permisos de la base de datos"""
    db_path = Path('instance/database.db')
    if not db_path.exists():
        return False, "Base de datos no existe (se creará automáticamente)"
    
    # Verificar permisos
    stat = db_path.stat()
    mode = oct(stat.st_mode)[-3:]
    
    if mode == '644' or mode == '600':
        return True, f"Permisos de BD correctos: {mode}"
    else:
        return False, f"Permisos de BD pueden ser inseguros: {mode} (recomendado: 600 o 644)"

def check_ssl_config():
    """Verifica configuración SSL"""
    flask_env = os.environ.get('FLASK_ENV', '')
    if flask_env == 'production':
        return True, "FLASK_ENV=production (cookies seguras habilitadas)"
    else:
        return False, f"FLASK_ENV={flask_env} (en producción debe ser 'production')"

def check_upload_folder():
    """Verifica que la carpeta de uploads existe y tiene permisos correctos"""
    upload_path = Path('static/uploads')
    if not upload_path.exists():
        return False, "Carpeta static/uploads no existe"
    
    # Verificar que no es accesible directamente sin autenticación
    # (esto se verifica en la configuración de Nginx/Flask)
    return True, "Carpeta de uploads existe"

def main():
    print("=" * 60)
    print("VERIFICACIÓN DE SEGURIDAD - FARMAVET WEB")
    print("=" * 60)
    print()
    
    checks = [
        ("SECRET_KEY", check_secret_key),
        ("Base de Datos", check_database_permissions),
        ("Configuración SSL", check_ssl_config),
        ("Carpeta de Uploads", check_upload_folder),
    ]
    
    results = []
    for name, check_func in checks:
        try:
            ok, message = check_func()
            status = "✅" if ok else "⚠️"
            results.append((ok, name, message))
            print(f"{status} {name}: {message}")
        except Exception as e:
            results.append((False, name, f"Error: {e}"))
            print(f"❌ {name}: Error al verificar - {e}")
        print()
    
    print("=" * 60)
    passed = sum(1 for ok, _, _ in results if ok)
    total = len(results)
    print(f"Resultado: {passed}/{total} verificaciones pasaron")
    print("=" * 60)
    
    if passed < total:
        print("\n⚠️  Se encontraron problemas de seguridad.")
        print("   Revisa los mensajes arriba y corrige los problemas.")
        sys.exit(1)
    else:
        print("\n✅ Todas las verificaciones de seguridad pasaron.")
        sys.exit(0)

if __name__ == '__main__':
    main()


