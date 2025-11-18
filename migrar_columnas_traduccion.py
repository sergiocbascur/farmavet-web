#!/usr/bin/env python3
"""
Script para agregar columnas de traducción faltantes a las tablas existentes
Ejecutar: python migrar_columnas_traduccion.py
"""

import sqlite3
import os

def migrate_database():
    """Agrega columnas de traducción faltantes a las tablas"""
    db_path = os.path.join('instance', 'database.db')
    
    if not os.path.exists(db_path):
        print(f"❌ No se encontró la base de datos en: {db_path}")
        print("   La base de datos se creará automáticamente al iniciar la aplicación.")
        return
    
    print(f"📦 Conectando a la base de datos: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Lista de migraciones a ejecutar
    migrations = [
        # Tabla eventos
        {
            'table': 'eventos',
            'columns': [
                ('titulo_en', 'TEXT'),
                ('descripcion_en', 'TEXT'),
                ('meta_en', 'TEXT'),
                ('texto_boton_en', 'TEXT')
            ]
        },
        # Tabla organigrama
        {
            'table': 'organigrama',
            'columns': [
                ('subseccion_en', 'TEXT'),
                ('cargo_en', 'TEXT'),
                ('descripcion_en', 'TEXT')
            ]
        }
    ]
    
    print("\n🔍 Verificando columnas existentes...\n")
    
    for migration in migrations:
        table = migration['table']
        columns = migration['columns']
        
        # Verificar si la tabla existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
        if not cursor.fetchone():
            print(f"⚠️  Tabla '{table}' no existe. Se creará automáticamente al iniciar la aplicación.")
            continue
        
        print(f"📋 Tabla: {table}")
        
        # Obtener columnas existentes
        cursor.execute(f"PRAGMA table_info({table})")
        existing_columns = [col[1] for col in cursor.fetchall()]
        
        for col_name, col_type in columns:
            if col_name in existing_columns:
                print(f"   ✅ {col_name} ya existe")
            else:
                try:
                    cursor.execute(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_type}")
                    print(f"   ➕ Agregada columna: {col_name}")
                except sqlite3.OperationalError as e:
                    if "duplicate column name" in str(e).lower():
                        print(f"   ✅ {col_name} ya existe (verificado)")
                    else:
                        print(f"   ❌ Error al agregar {col_name}: {e}")
    
    conn.commit()
    conn.close()
    
    print("\n✅ Migración completada")
    print("\n💡 Reinicia el servicio para aplicar los cambios:")
    print("   sudo systemctl restart farmavet-web")

if __name__ == '__main__':
    migrate_database()

