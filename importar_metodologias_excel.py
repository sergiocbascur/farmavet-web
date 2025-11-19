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
    
    # Leer Excel - El archivo tiene encabezados en la fila 2 (índice 2)
    try:
        if HAS_PANDAS:
            # Leer sin header primero para inspeccionar
            df_raw = pd.read_excel(excel_path, engine='openpyxl', header=None)
            
            # Buscar la fila de encabezados (debería estar en la fila 2)
            header_row = 2
            headers = []
            for j in range(len(df_raw.columns)):
                val = df_raw.iloc[header_row, j]
                if pd.notna(val):
                    headers.append(str(val).strip())
                else:
                    headers.append(f"Col_{j}")
            
            # Leer de nuevo con los encabezados correctos, saltando las primeras filas
            df = pd.read_excel(excel_path, engine='openpyxl', header=header_row, names=headers)
            
            # Los datos empiezan en la fila 4 (después del header en fila 2 y una fila vacía)
            # Eliminar la primera fila si está vacía o es otra fila de encabezados
            if len(df) > 0:
                first_row = df.iloc[0]
                # Si la primera fila parece ser otra fila de encabezados o está vacía, eliminarla
                first_row_str = ' '.join([str(v).lower() for v in first_row.values if pd.notna(v)])
                if 'metodo' in first_row_str.lower() or 'equipo' in first_row_str.lower() or first_row_str.strip() == '':
                    df = df.drop(df.index[0]).reset_index(drop=True)
            
            # Eliminar filas completamente vacías
            df = df.dropna(how='all').reset_index(drop=True)
            
        else:
            # Usar openpyxl directamente
            from openpyxl import load_workbook
            wb = load_workbook(excel_path)
            ws = wb.active
            
            # Convertir a DataFrame manualmente
            # Encabezados en fila 3 (índice 2 en 0-based)
            headers = [str(cell.value).strip() if cell.value else f"Col_{i}" 
                      for i, cell in enumerate(ws[3], 1)]
            
            data = []
            for row in ws.iter_rows(min_row=4, values_only=True):
                if any(cell for cell in row if cell):  # Saltar filas vacías
                    data.append(dict(zip(headers, row)))
            df = pd.DataFrame(data)
        
        print(f"✅ Archivo leído: {len(df)} filas encontradas")
        print(f"📋 Columnas detectadas: {', '.join(df.columns.tolist())}")
        
    except Exception as e:
        print(f"❌ Error leyendo Excel: {str(e)}")
        import traceback
        traceback.print_exc()
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
    # Basado en la estructura real del archivo "RESUMEN CLIENTES-LAB.xlsx"
    column_mapping = {
        'codigo': ['it lf n', 'it lf', 'codigo', 'código', 'cod', 'id', 'unnamed: 1', 'col_1'],
        'analito': ['método', 'metodo', 'mtodo', 'analito', 'analito', 'sustancia', 'compuesto', 'unnamed: 2', 'col_2'],
        'tecnica': ['equipo', 'tecnica', 'técnica', 'tecnica analitica', 'método analítico', 'unnamed: 3', 'col_3'],
        'limite_deteccion': ['ld', 'lod', 'limite deteccion', 'límite detección', 'limite_deteccion', 'unnamed: 4', 'col_4'],
        'limite_cuantificacion': ['lc', 'loq', 'limite cuantificacion', 'límite cuantificación', 'limite_cuantificacion', 'unnamed: 5', 'col_5'],
        'matriz': ['matriz', 'muestra', 'tipo muestra', 'unnamed: 6', 'col_6'],
        'acreditada': ['acreditado\ninn', 'acreditado inn', 'acreditada', 'acreditado', 'acreditacion', 'acreditación', 'unnamed: 7', 'col_7']
    }
    
    # Encontrar las columnas del Excel que coinciden
    excel_columns = {col.lower().strip(): col for col in df.columns}
    field_mapping = {}
    
    for db_field, possible_names in column_mapping.items():
        for name in possible_names:
            name_lower = name.lower().strip()
            # Buscar coincidencia exacta o parcial
            for excel_col in excel_columns.keys():
                if name_lower == excel_col or excel_col.startswith(name_lower) or name_lower in excel_col:
                    field_mapping[db_field] = df.columns[list(excel_columns.keys()).index(excel_col)]
                    break
            if db_field in field_mapping:
                break
    
    print(f"\n📊 Mapeo de columnas detectado:")
    for db_field, excel_col in field_mapping.items():
        print(f"   {db_field} ← {excel_col}")
    
    # Campos requeridos (analito es obligatorio, los demás pueden tener valores por defecto)
    required_fields = ['analito']
    missing_fields = [f for f in required_fields if f not in field_mapping]
    
    if missing_fields:
        print(f"\n❌ Error: Faltan campos requeridos: {', '.join(missing_fields)}")
        print("   No se puede continuar sin estos campos")
        conn.close()
        sys.exit(1)
    
    # Si falta matriz, usar un valor por defecto o intentar inferir
    if 'matriz' not in field_mapping:
        print(f"\n⚠️  Advertencia: No se encontró columna 'matriz', se intentará usar un valor por defecto")
    
    # Categoría por defecto si no existe
    categoria_default = 'residuos'  # Se puede ajustar según necesites
    
    # Procesar cada fila
    imported = 0
    skipped = 0
    errors = []
    
    print(f"\n🔄 Procesando {len(df)} filas...")
    
    for idx, row in df.iterrows():
        try:
            # Extraer valores con manejo mejorado
            codigo = None
            if field_mapping.get('codigo'):
                codigo_val = row.get(field_mapping['codigo'])
                if pd.notna(codigo_val):
                    codigo = str(codigo_val).strip()
            
            # Analito es el campo principal (columna "MÉTODO")
            analito = None
            if field_mapping.get('analito'):
                analito_val = row.get(field_mapping['analito'])
                if pd.notna(analito_val):
                    analito = str(analito_val).strip()
            
            # Si no hay analito, saltar esta fila
            if not analito:
                skipped += 1
                continue
            
            # Usar analito como nombre también (si no hay nombre separado)
            nombre = analito
            
            # Matriz
            matriz = None
            if field_mapping.get('matriz'):
                matriz_val = row.get(field_mapping['matriz'])
                if pd.notna(matriz_val):
                    matriz = str(matriz_val).strip()
            if not matriz:
                matriz = 'No especificada'  # Valor por defecto
            
            # Categoría (por defecto)
            categoria = categoria_default
            
            # Técnica (EQUIPO)
            tecnica = None
            if field_mapping.get('tecnica'):
                tecnica_val = row.get(field_mapping['tecnica'])
                if pd.notna(tecnica_val):
                    tecnica = str(tecnica_val).strip()
            
            # Límites
            limite_deteccion = None
            if field_mapping.get('limite_deteccion'):
                lod_val = row.get(field_mapping['limite_deteccion'])
                if pd.notna(lod_val):
                    limite_deteccion = str(lod_val).strip()
            
            limite_cuantificacion = None
            if field_mapping.get('limite_cuantificacion'):
                loq_val = row.get(field_mapping['limite_cuantificacion'])
                if pd.notna(loq_val):
                    limite_cuantificacion = str(loq_val).strip()
            
            # Otros campos opcionales
            nombre_en = None
            analito_en = None
            matriz_en = None
            tecnica_en = None
            norma_referencia = None
            vigencia = None
            
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
            if not analito:
                skipped += 1
                errors.append(f"Fila {idx+2}: Falta campo requerido (analito/método)")
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

