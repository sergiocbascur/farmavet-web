#!/usr/bin/env python3
"""
Script para generar una SECRET_KEY segura para Flask
Ejecutar: python generar_secret_key.py
"""

import secrets
import string

def generate_secret_key(length=50):
    """Genera una clave secreta aleatoria y segura"""
    alphabet = string.ascii_letters + string.digits + string.punctuation
    # Remover caracteres problemáticos para variables de entorno
    alphabet = alphabet.replace('"', '').replace("'", '').replace('$', '').replace('`', '')
    return ''.join(secrets.choice(alphabet) for _ in range(length))

if __name__ == '__main__':
    secret_key = generate_secret_key()
    print("=" * 60)
    print("SECRET_KEY generada:")
    print("=" * 60)
    print(secret_key)
    print("=" * 60)
    print("\nPara usar esta clave:")
    print("1. Agregar al archivo de servicio systemd:")
    print(f'   Environment="SECRET_KEY={secret_key}"')
    print("\n2. O exportar como variable de entorno:")
    print(f'   export SECRET_KEY="{secret_key}"')
    print("\n3. O crear archivo .env (no subir a Git):")
    print(f'   SECRET_KEY={secret_key}')
    print("=" * 60)

