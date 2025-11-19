#!/usr/bin/env python3
"""
Script para importar metodologías desde un archivo Excel
Uso: python importar_metodologias_excel.py "RESUMEN CLIENTES-LAB.xlsx"
"""

import sys
import os
import sqlite3
from datetime import datetime

# Intentar importar pandas u openpyxl
try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    try:
        import openpyxl
        HAS_OPENPYXL = True
        HAS_PANDAS = False
    except ImportError:
        print("❌ Error: Necesitas instalar pandas o openpyxl")
        print("   Instala con: pip install pandas openpyxl")
        sys.exit(1)

def get_db_path():
    """Obtiene la ruta de la base de datos"""
    # Buscar en varios lugares posibles
    possible_paths = [
        'farmavet_web.db',
        'instance/database.db',
        'database.db'
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    # Si no se encuentra, preguntar
    print("⚠️  No se encontró la base de datos automáticamente.")
    db_path = input("Ingresa la ruta a la base de datos: ").strip()
    if os.path.exists(db_path):
        return db_path
    else:
        print(f"❌ Error: No se encontró el archivo: {db_path}")
        sys.exit(1)

def normalize_text(text):
    """Normaliza texto para búsqueda"""
    if not text or pd.isna(text):
        return None
    return str(text).strip()

def import_from_excel(excel_path, db_path, dry_run=False):
    """Importa metodologías desde Excel a la base de datos"""
    
    if not os.path.exists(excel_path):
        print(f"❌ Error: No se encontró el archivo: {excel_path}")
        sys.exit(1)
    
    print(f"📖 Leyendo archivo Excel: {excel_path}")
    
    # Leer Excel
    try:
        if HAS_PANDAS:
            df = pd.read_excel(excel_path, engine='openpyxl')
        else:
            # Usar openpyxl directamente
            from openpyxl import load_workbook
            wb = load_workbook(excel_path)
            ws = wb.active
            
            # Convertir a DataFrame manualmente
            data = []
            headers = [cell.value for cell in ws[1]]
            for row in ws.iter_rows(min_row=2, values_only=True):
                if any(cell for cell in row):  # Saltar filas vacías
                    data.append(dict(zip(headers, row)))
            df = pd.DataFrame(data)
        
        print(f"✅ Archivo leído: {len(df)} filas encontradas")
        print(f"📋 Columnas: {', '.join(df.columns.tolist())}")
        
    except Exception as e:
        print(f"❌ Error leyendo Excel: {str(e)}")
        sys.exit(1)
    
    # Conectar a la base de datos
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Verificar que la tabla existe
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='metodologias'")
    if not cursor.fetchone():
        print("❌ Error: La tabla 'metodologias' no existe en la base de datos")
        conn.close()
        sys.exit(1)
    
    # Mapeo de columnas del Excel a campos de la BD
    # Ajusta estos nombres según las columnas de tu Excel
    column_mapping = {
        'codigo': ['codigo', 'código', 'cod', 'id'],
        'nombre': ['nombre', 'metodologia', 'metodología', 'nombre metodologia'],
        'nombre_en': ['nombre_en', 'nombre en', 'name', 'name_en'],
        'categoria': ['categoria', 'categoría', 'categoria', 'tipo'],
        'analito': ['analito', 'analito', 'sustancia', 'compuesto'],
        'analito_en': ['analito_en', 'analito en', 'analyte', 'analyte_en'],
        'matriz': ['matriz', 'matriz', 'muestra', 'tipo muestra'],
        'matriz_en': ['matriz_en', 'matriz en', 'matrix', 'matrix_en'],
        'tecnica': ['tecnica', 'técnica', 'tecnica analitica', 'método analítico'],
        'tecnica_en': ['tecnica_en', 'tecnica en', 'technique', 'technique_en'],
        'limite_deteccion': ['lod', 'limite deteccion', 'límite detección', 'limite_deteccion'],
        'limite_cuantificacion': ['loq', 'limite cuantificacion', 'límite cuantificación', 'limite_cuantificacion'],
        'norma_referencia': ['norma', 'norma referencia', 'referencia', 'estándar'],
        'vigencia': ['vigencia', 'fecha vigencia', 'validez'],
        'acreditada': ['acreditada', 'acreditado', 'acreditacion', 'acreditación'],
        'orden': ['orden', 'order', 'prioridad']
    }
    
    # Encontrar las columnas del Excel que coinciden
    excel_columns = {col.lower().strip(): col for col in df.columns}
    field_mapping = {}
    
    for db_field, possible_names in column_mapping.items():
        for name in possible_names:
            name_lower = name.lower().strip()
            if name_lower in excel_columns:
                field_mapping[db_field] = excel_columns[name_lower]
                break
    
    print(f"\n📊 Mapeo de columnas detectado:")
    for db_field, excel_col in field_mapping.items():
        print(f"   {db_field} ← {excel_col}")
    
    # Campos requeridos
    required_fields = ['nombre', 'categoria', 'analito', 'matriz']
    missing_fields = [f for f in required_fields if f not in field_mapping]
    
    if missing_fields:
        print(f"\n⚠️  Advertencia: Faltan campos requeridos: {', '.join(missing_fields)}")
        print("   El script intentará continuar, pero algunos campos pueden quedar vacíos")
    
    # Procesar cada fila
    imported = 0
    skipped = 0
    errors = []
    
    print(f"\n🔄 Procesando {len(df)} filas...")
    
    for idx, row in df.iterrows():
        try:
            # Extraer valores
            codigo = normalize_text(row.get(field_mapping.get('codigo', ''))) if field_mapping.get('codigo') else None
            nombre = normalize_text(row.get(field_mapping.get('nombre', ''))) if field_mapping.get('nombre') else None
            nombre_en = normalize_text(row.get(field_mapping.get('nombre_en', ''))) if field_mapping.get('nombre_en') else None
            categoria = normalize_text(row.get(field_mapping.get('categoria', ''))) if field_mapping.get('categoria') else None
            analito = normalize_text(row.get(field_mapping.get('analito', ''))) if field_mapping.get('analito') else None
            analito_en = normalize_text(row.get(field_mapping.get('analito_en', ''))) if field_mapping.get('analito_en') else None
            matriz = normalize_text(row.get(field_mapping.get('matriz', ''))) if field_mapping.get('matriz') else None
            matriz_en = normalize_text(row.get(field_mapping.get('matriz_en', ''))) if field_mapping.get('matriz_en') else None
            tecnica = normalize_text(row.get(field_mapping.get('tecnica', ''))) if field_mapping.get('tecnica') else None
            tecnica_en = normalize_text(row.get(field_mapping.get('tecnica_en', ''))) if field_mapping.get('tecnica_en') else None
            limite_deteccion = normalize_text(row.get(field_mapping.get('limite_deteccion', ''))) if field_mapping.get('limite_deteccion') else None
            limite_cuantificacion = normalize_text(row.get(field_mapping.get('limite_cuantificacion', ''))) if field_mapping.get('limite_cuantificacion') else None
            norma_referencia = normalize_text(row.get(field_mapping.get('norma_referencia', ''))) if field_mapping.get('norma_referencia') else None
            vigencia = normalize_text(row.get(field_mapping.get('vigencia', ''))) if field_mapping.get('vigencia') else None
            
            # Acreditada (puede ser texto como "Sí", "S", "1", True, etc.)
            acreditada_val = row.get(field_mapping.get('acreditada', '')) if field_mapping.get('acreditada') else None
            if acreditada_val is not None:
                acreditada_str = str(acreditada_val).lower().strip()
                acreditada = acreditada_str in ['si', 'sí', 's', 'yes', 'true', '1', 'acreditada', 'acreditado']
            else:
                acreditada = False
            
            # Orden
            orden_val = row.get(field_mapping.get('orden', '')) if field_mapping.get('orden') else None
            if orden_val is not None:
                try:
                    orden = int(float(orden_val))
                except (ValueError, TypeError):
                    orden = None
            else:
                orden = None
            
            # Validar campos requeridos
            if not nombre or not categoria or not analito or not matriz:
                skipped += 1
                errors.append(f"Fila {idx+2}: Faltan campos requeridos (nombre, categoria, analito, matriz)")
                continue
            
            # Verificar si ya existe (por código o por nombre+analito+matriz)
            if codigo:
                cursor.execute("SELECT id FROM metodologias WHERE codigo = ?", (codigo,))
            else:
                cursor.execute("SELECT id FROM metodologias WHERE nombre = ? AND analito = ? AND matriz = ?", 
                             (nombre, analito, matriz))
            
            existing = cursor.fetchone()
            
            if existing:
                if not dry_run:
                    # Actualizar existente
                    cursor.execute('''
                        UPDATE metodologias 
                        SET codigo=?, nombre=?, nombre_en=?, categoria=?, analito=?, analito_en=?,
                            matriz=?, matriz_en=?, tecnica=?, tecnica_en=?, limite_deteccion=?,
                            limite_cuantificacion=?, norma_referencia=?, vigencia=?, acreditada=?, orden=?
                        WHERE id=?
                    ''', (codigo, nombre, nombre_en, categoria, analito, analito_en, matriz, matriz_en,
                          tecnica, tecnica_en, limite_deteccion, limite_cuantificacion, norma_referencia,
                          vigencia, acreditada, orden, existing['id']))
                    print(f"   ✓ Actualizado: {nombre} - {analito} en {matriz}")
                else:
                    print(f"   [DRY RUN] Actualizaría: {nombre} - {analito} en {matriz}")
            else:
                if not dry_run:
                    # Insertar nuevo
                    cursor.execute('''
                        INSERT INTO metodologias 
                        (codigo, nombre, nombre_en, categoria, analito, analito_en, matriz, matriz_en,
                         tecnica, tecnica_en, limite_deteccion, limite_cuantificacion, norma_referencia,
                         vigencia, acreditada, orden, activo)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                    ''', (codigo, nombre, nombre_en, categoria, analito, analito_en, matriz, matriz_en,
                          tecnica, tecnica_en, limite_deteccion, limite_cuantificacion, norma_referencia,
                          vigencia, acreditada, orden))
                    print(f"   + Insertado: {nombre} - {analito} en {matriz}")
                else:
                    print(f"   [DRY RUN] Insertaría: {nombre} - {analito} en {matriz}")
            
            imported += 1
            
        except Exception as e:
            skipped += 1
            errors.append(f"Fila {idx+2}: {str(e)}")
            print(f"   ❌ Error en fila {idx+2}: {str(e)}")
    
    if not dry_run:
        conn.commit()
        print(f"\n✅ Importación completada!")
    else:
        print(f"\n🔍 [DRY RUN] Simulación completada (no se modificó la base de datos)")
    
    print(f"   ✓ Importadas/Actualizadas: {imported}")
    print(f"   ⚠️  Omitidas: {skipped}")
    
    if errors:
        print(f"\n⚠️  Errores encontrados ({len(errors)}):")
        for error in errors[:10]:  # Mostrar solo los primeros 10
            print(f"   - {error}")
        if len(errors) > 10:
            print(f"   ... y {len(errors) - 10} errores más")
    
    conn.close()
    return imported, skipped, len(errors)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Uso: python importar_metodologias_excel.py <archivo_excel> [--dry-run]")
        print("\nEjemplo:")
        print("  python importar_metodologias_excel.py 'RESUMEN CLIENTES-LAB.xlsx'")
        print("  python importar_metodologias_excel.py 'RESUMEN CLIENTES-LAB.xlsx' --dry-run")
        sys.exit(1)
    
    excel_path = sys.argv[1]
    dry_run = '--dry-run' in sys.argv or '-n' in sys.argv
    
    if dry_run:
        print("🔍 MODO DRY RUN: No se modificará la base de datos\n")
    
    db_path = get_db_path()
    
    print(f"📁 Base de datos: {db_path}")
    print(f"📊 Archivo Excel: {excel_path}\n")
    
    confirm = input("¿Continuar con la importación? (s/n): ").strip().lower()
    if confirm not in ['s', 'si', 'sí', 'y', 'yes']:
        print("❌ Importación cancelada")
        sys.exit(0)
    
    import_from_excel(excel_path, db_path, dry_run=dry_run)

