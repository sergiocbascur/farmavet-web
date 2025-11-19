# Instrucciones para Importar Metodologías en el VPS

## Paso 1: Subir el archivo Excel al VPS

Puedes usar `scp` o `sftp` para subir el archivo:

```bash
# Desde tu máquina local
scp "RESUMEN CLIENTES-LAB.xlsx" usuario@tu-vps:/ruta/al/proyecto/farmavet-web/
```

O si prefieres, puedes copiar el archivo directamente en el servidor usando un cliente FTP o el editor de archivos del VPS.

## Paso 2: Conectarte al VPS

```bash
ssh usuario@tu-vps
cd /ruta/al/proyecto/farmavet-web
```

## Paso 3: Instalar dependencias (si no están instaladas)

```bash
# Activar el entorno virtual
source venv/bin/activate  # O el nombre de tu venv

# Instalar pandas y openpyxl si no están instalados
pip install pandas openpyxl

# O actualizar requirements.txt e instalar todo
pip install -r requirements.txt
```

## Paso 4: Verificar la ubicación de la base de datos

El script busca automáticamente la base de datos en:
- `farmavet_web.db`
- `instance/database.db`
- `database.db`

Si tu base de datos está en otra ubicación, puedes modificar el script o mover/crear un enlace simbólico.

## Paso 5: Probar primero (modo dry-run)

```bash
python importar_metodologias_excel.py "RESUMEN CLIENTES-LAB.xlsx" --dry-run
```

Esto te mostrará qué se importaría sin modificar la base de datos.

## Paso 6: Importar realmente

```bash
# Sin confirmación (recomendado para scripts automatizados)
python importar_metodologias_excel.py "RESUMEN CLIENTES-LAB.xlsx" --yes

# O con confirmación interactiva
python importar_metodologias_excel.py "RESUMEN CLIENTES-LAB.xlsx"
```

## Paso 7: Reiniciar el servicio (si es necesario)

Después de importar, puede que necesites reiniciar el servicio de Flask:

```bash
sudo systemctl restart farmavet-web
# O el comando que uses para reiniciar tu servicio
```

## Verificación

Puedes verificar que las metodologías se importaron correctamente:

```bash
# Conectarte a la base de datos SQLite
sqlite3 instance/database.db "SELECT COUNT(*) FROM metodologias WHERE activo = 1;"
```

O simplemente revisar en la interfaz web del admin o probar el chatbot.

## Notas

- Asegúrate de tener permisos de escritura en la base de datos
- Si tienes múltiples instancias, verifica que estés importando en la base de datos correcta
- Es recomendable hacer un backup de la base de datos antes de importar:
  ```bash
  cp instance/database.db instance/database.db.backup-$(date +%Y%m%d-%H%M%S)
  ```

