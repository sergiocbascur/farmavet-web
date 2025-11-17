"""
Script para crear el primer usuario administrador
Ejecutar después del primer despliegue en producción
"""

import sqlite3
import os
from werkzeug.security import generate_password_hash
import getpass

def create_admin():
    # Conectar a la base de datos
    db_path = os.path.join('instance', 'database.db')
    
    # Si no existe, crear la carpeta instance
    os.makedirs('instance', exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Verificar si ya existe un admin
    cursor.execute("SELECT COUNT(*) FROM usuarios WHERE es_admin = 1")
    admin_count = cursor.fetchone()[0]
    
    if admin_count > 0:
        print("⚠️  Ya existe al menos un usuario administrador.")
        response = input("¿Deseas crear otro? (s/n): ")
        if response.lower() != 's':
            print("Operación cancelada.")
            conn.close()
            return
    
    # Solicitar datos
    print("\n=== Crear Usuario Administrador ===")
    username = input("Nombre de usuario: ").strip()
    
    if not username:
        print("❌ El nombre de usuario no puede estar vacío.")
        conn.close()
        return
    
    # Verificar si el usuario ya existe
    cursor.execute("SELECT id FROM usuarios WHERE username = ?", (username,))
    if cursor.fetchone():
        print(f"❌ El usuario '{username}' ya existe.")
        conn.close()
        return
    
    password = getpass.getpass("Contraseña (mínimo 8 caracteres): ")
    
    if len(password) < 8:
        print("❌ La contraseña debe tener al menos 8 caracteres.")
        conn.close()
        return
    
    password_confirm = getpass.getpass("Confirmar contraseña: ")
    
    if password != password_confirm:
        print("❌ Las contraseñas no coinciden.")
        conn.close()
        return
    
    # Crear el usuario
    password_hash = generate_password_hash(password)
    
    try:
        cursor.execute('''
            INSERT INTO usuarios (username, password_hash, es_admin, activo)
            VALUES (?, ?, 1, 1)
        ''', (username, password_hash))
        
        conn.commit()
        print(f"\n✅ Usuario administrador '{username}' creado exitosamente!")
        print("\nAhora puedes iniciar sesión en: https://tu-dominio.com/login")
        
    except sqlite3.OperationalError as e:
        if "no such table: usuarios" in str(e):
            print("\n❌ Error: La tabla 'usuarios' no existe.")
            print("   Asegúrate de que la aplicación se haya ejecutado al menos una vez")
            print("   para crear las tablas de la base de datos.")
        else:
            print(f"\n❌ Error al crear usuario: {e}")
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    create_admin()

