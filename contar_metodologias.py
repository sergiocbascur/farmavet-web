#!/usr/bin/env python3
"""
Script para contar metodologías únicas en la base de datos
Agrupa por nombre + matriz + técnica + categoría (igual que en admin)
"""

import sqlite3
import os

# Ruta a la base de datos
db_path = os.path.join(os.path.dirname(__file__), 'instance', 'farmavet.db')

if not os.path.exists(db_path):
    print(f"❌ No se encontró la base de datos en: {db_path}")
    print("   Buscando en ubicaciones alternativas...")
    # Intentar otras ubicaciones comunes
    alt_paths = [
        'farmavet.db',
        '../instance/farmavet.db',
        '/home/farmavet-web/app/instance/farmavet.db',
        '/home/web/farmavet-web/instance/farmavet.db'
    ]
    for alt_path in alt_paths:
        if os.path.exists(alt_path):
            db_path = alt_path
            print(f"✅ Encontrada en: {db_path}")
            break
    else:
        print("❌ No se encontró la base de datos")
        exit(1)

try:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    
    # Obtener todas las metodologías activas
    metodologias_raw = conn.execute('''
        SELECT nombre, matriz, tecnica, categoria, acreditada
        FROM metodologias 
        WHERE activo = 1
        ORDER BY nombre, matriz, tecnica
    ''').fetchall()
    
    # Agrupar por nombre + matriz + técnica + categoría (igual que en admin)
    metodologias_agrupadas = {}
    for m in metodologias_raw:
        nombre = m['nombre'] or ''
        matriz = m['matriz'] or ''
        tecnica = m['tecnica'] or ''
        categoria = m['categoria'] or 'otros'
        group_key = (nombre, matriz, tecnica, categoria)
        
        if group_key not in metodologias_agrupadas:
            metodologias_agrupadas[group_key] = {
                'acreditada': bool(m['acreditada']),
                'count': 0
            }
        metodologias_agrupadas[group_key]['count'] += 1
    
    # Contar totales
    total_count = len(metodologias_agrupadas)
    total_acreditadas = sum(1 for g in metodologias_agrupadas.values() if g['acreditada'])
    total_registros = len(metodologias_raw)
    
    print("\n" + "="*60)
    print("CONTEO DE METODOLOGÍAS")
    print("="*60)
    print(f"\n📊 Total de registros en BD: {total_registros}")
    print(f"📋 Total de metodologías ÚNICAS: {total_count}")
    print(f"✅ Metodologías acreditadas ISO 17025: {total_acreditadas}")
    print(f"📝 Metodologías no acreditadas: {total_count - total_acreditadas}")
    print("\n" + "-"*60)
    print("NOTA: Una metodología única se define por:")
    print("  - Nombre + Matriz + Técnica + Categoría")
    print("  - Si una metodología tiene múltiples analitos,")
    print("    sigue siendo UNA metodología")
    print("="*60 + "\n")
    
    conn.close()
    
except Exception as e:
    print(f"❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()
    exit(1)
