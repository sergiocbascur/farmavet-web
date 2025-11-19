# Instrucciones para Importar Metodologías desde Excel

## Requisitos Previos

1. Instalar las dependencias necesarias:
```bash
pip install pandas openpyxl
```

O si usas `requirements.txt`:
```bash
pip install -r requirements.txt
```

## Uso del Script

### Modo Normal (Importación Real)

```bash
python importar_metodologias_excel.py "RESUMEN CLIENTES-LAB.xlsx"
```

### Modo Dry Run (Simulación - No modifica la BD)

Para ver qué se importaría sin hacer cambios:

```bash
python importar_metodologias_excel.py "RESUMEN CLIENTES-LAB.xlsx" --dry-run
```

## Mapeo de Columnas

El script intenta detectar automáticamente las columnas del Excel y mapearlas a los campos de la base de datos. Busca estas variantes de nombres:

- **codigo**: codigo, código, cod, id
- **nombre**: nombre, metodologia, metodología, nombre metodologia
- **nombre_en**: nombre_en, nombre en, name, name_en
- **categoria**: categoria, categoría, tipo
- **analito**: analito, sustancia, compuesto
- **analito_en**: analito_en, analito en, analyte, analyte_en
- **matriz**: matriz, muestra, tipo muestra
- **matriz_en**: matriz_en, matriz en, matrix, matrix_en
- **tecnica**: tecnica, técnica, tecnica analitica, método analítico
- **tecnica_en**: tecnica_en, tecnica en, technique, technique_en
- **limite_deteccion**: lod, limite deteccion, límite detección
- **limite_cuantificacion**: loq, limite cuantificacion, límite cuantificación
- **norma_referencia**: norma, norma referencia, referencia, estándar
- **vigencia**: vigencia, fecha vigencia, validez
- **acreditada**: acreditada, acreditado, acreditacion, acreditación
- **orden**: orden, order, prioridad

## Campos Requeridos

Los siguientes campos son obligatorios:
- `nombre`
- `categoria`
- `analito`
- `matriz`

Si faltan, la fila se omitirá.

## Comportamiento

- **Si existe una metodología con el mismo código**: Se actualiza
- **Si existe una metodología con el mismo nombre+analito+matriz**: Se actualiza
- **Si no existe**: Se inserta como nueva
- **Todas las metodologías importadas se marcan como activas** (`activo = 1`)

## Ejemplo de Salida

```
📖 Leyendo archivo Excel: RESUMEN CLIENTES-LAB.xlsx
✅ Archivo leído: 50 filas encontradas
📋 Columnas: nombre, analito, matriz, tecnica, lod, loq, acreditada

📊 Mapeo de columnas detectado:
   nombre ← nombre
   analito ← analito
   matriz ← matriz
   tecnica ← tecnica
   limite_deteccion ← lod
   limite_cuantificacion ← loq
   acreditada ← acreditada

🔄 Procesando 50 filas...
   + Insertado: Metodología Diquat - Diquat en musculo de sálmon
   + Insertado: Metodología Amprolio - Amprolio en productos pecuarios
   ...

✅ Importación completada!
   ✓ Importadas/Actualizadas: 48
   ⚠️  Omitidas: 2
```

## Solución de Problemas

### Error: "No se encontró la base de datos"

El script busca automáticamente en:
- `farmavet_web.db`
- `instance/database.db`
- `database.db`

Si no encuentra ninguna, te pedirá que ingreses la ruta manualmente.

### Error: "Faltan campos requeridos"

Asegúrate de que tu Excel tenga columnas con nombres similares a los campos requeridos. Puedes renombrar las columnas en el Excel para que coincidan mejor.

### Error: "Necesitas instalar pandas o openpyxl"

Ejecuta:
```bash
pip install pandas openpyxl
```

## Notas

- El script es **seguro**: no elimina metodologías existentes, solo las actualiza o inserta nuevas
- Puedes ejecutar el script múltiples veces sin problemas
- Usa `--dry-run` primero para verificar que el mapeo de columnas sea correcto

