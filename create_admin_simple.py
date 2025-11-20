"""
Script simplificado para crear usuarios administradores
Uso: python create_admin_simple.py <username> <password>
"""

import sqlite3
import os
import sys
from werkzeug.security import generate_password_hash

def create_admin(username, password):
    # Conectar a la base de datos
    db_path = os.path.join('instance', 'database.db')
    
    # Si no existe, crear la carpeta instance
    os.makedirs('instance', exist_ok=True)
    
    if not os.path.exists(db_path):
        print("ERROR: La base de datos no existe.")
        print("   Asegurate de que la aplicacion se haya ejecutado al menos una vez")
        print("   para crear las tablas de la base de datos.")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Verificar si el usuario ya existe
    cursor.execute("SELECT id FROM admins WHERE username = ?", (username,))
    if cursor.fetchone():
        print(f"ERROR: El usuario '{username}' ya existe.")
        conn.close()
        return False
    
    # Validar contraseña
    if len(password) < 8:
        print("ERROR: La contraseña debe tener al menos 8 caracteres.")
        conn.close()
        return False
    
    # Crear el usuario
    password_hash = generate_password_hash(password)
    
    try:
        cursor.execute('''
            INSERT INTO admins (username, password_hash)
            VALUES (?, ?)
        ''', (username, password_hash))
        
        conn.commit()
        print(f"\nOK: Usuario administrador '{username}' creado exitosamente!")
        print(f"\nAhora puedes iniciar sesion con:")
        print(f"   Usuario: {username}")
        print(f"   Contrasena: [la que proporcionaste]")
        return True
        
    except sqlite3.OperationalError as e:
        if "no such table: admins" in str(e):
            print("\nERROR: La tabla 'admins' no existe.")
            print("   Asegurate de que la aplicacion se haya ejecutado al menos una vez")
            print("   para crear las tablas de la base de datos.")
        else:
            print(f"\nERROR al crear usuario: {e}")
        return False
    except Exception as e:
        print(f"\nERROR inesperado: {e}")
        return False
    finally:
        conn.close()

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Uso: python create_admin_simple.py <username> <password>")
        print("\nEjemplo:")
        print("  python create_admin_simple.py crojas mi_password_seguro")
        sys.exit(1)
    
    username = sys.argv[1].strip()
    password = sys.argv[2]
    
    if not username:
        print("ERROR: El nombre de usuario no puede estar vacio.")
        sys.exit(1)
    
    create_admin(username, password)

