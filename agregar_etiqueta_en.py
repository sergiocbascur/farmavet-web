#!/usr/bin/env python3
"""
Script para agregar la columna etiqueta_en a la tabla estadisticas
Ejecutar en el servidor si la migración automática no funcionó
"""

import sqlite3
import os

def agregar_columna():
    db_path = os.path.join('instance', 'database.db')
    
    if not os.path.exists(db_path):
        print(f"❌ Error: No se encuentra la base de datos en {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Verificar si la columna ya existe
    cursor.execute("PRAGMA table_info(estadisticas)")
    columns = [column[1] for column in cursor.fetchall()]
    
    if 'etiqueta_en' in columns:
        print("✅ La columna 'etiqueta_en' ya existe en la tabla estadisticas")
    else:
        print("⚠️  La columna 'etiqueta_en' NO existe. Agregándola...")
        try:
            cursor.execute('ALTER TABLE estadisticas ADD COLUMN etiqueta_en TEXT')
            conn.commit()
            print("✅ Columna 'etiqueta_en' agregada exitosamente")
        except Exception as e:
            print(f"❌ Error al agregar la columna: {e}")
    
    # Verificar nuevamente
    cursor.execute("PRAGMA table_info(estadisticas)")
    columns = [column[1] for column in cursor.fetchall()]
    print(f"\n📋 Columnas actuales en 'estadisticas': {', '.join(columns)}")
    
    conn.close()

if __name__ == '__main__':
    agregar_columna()


