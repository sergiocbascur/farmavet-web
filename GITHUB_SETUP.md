# Configuración de GitHub para FARMAVET Web

## Pasos para conectar el repositorio local con GitHub

### 1. Crear el repositorio en GitHub

1. Ve a [GitHub](https://github.com) e inicia sesión
2. Haz clic en el botón **"+"** en la esquina superior derecha
3. Selecciona **"New repository"**
4. Completa el formulario:
   - **Repository name**: `farmavet-web`
   - **Description**: `Sitio web del Laboratorio de Farmacología Veterinaria - Universidad de Chile`
   - **Visibility**: Elige **Private** (recomendado) o **Public**
   - **NO marques** "Initialize this repository with a README" (ya tenemos uno)
   - **NO agregues** .gitignore ni licencia (ya están configurados)
5. Haz clic en **"Create repository"**

### 2. Conectar el repositorio local con GitHub

Después de crear el repositorio, GitHub te mostrará instrucciones. Ejecuta estos comandos en la terminal (desde la carpeta `farmavet-web`):

```bash
# Agregar el repositorio remoto (reemplaza TU_USUARIO con tu usuario de GitHub)
git remote add origin https://github.com/TU_USUARIO/farmavet-web.git

# Verificar que se agregó correctamente
git remote -v

# Cambiar el nombre de la rama principal a 'main' (si GitHub usa 'main' por defecto)
git branch -M main

# Subir el código al repositorio
git push -u origin main
```

### 3. Verificar la conexión

1. Ve a tu repositorio en GitHub: `https://github.com/TU_USUARIO/farmavet-web`
2. Deberías ver todos los archivos del proyecto
3. El commit inicial debería aparecer en el historial

## Comandos útiles para el día a día

### Ver el estado del repositorio
```bash
git status
```

### Agregar cambios
```bash
# Agregar todos los archivos modificados
git add .

# O agregar archivos específicos
git add app.py templates/index.html
```

### Hacer commit
```bash
git commit -m "Descripción breve de los cambios"
```

### Subir cambios a GitHub
```bash
git push
```

### Actualizar desde GitHub (si trabajas en múltiples lugares)
```bash
git pull
```

### Ver el historial de commits
```bash
git log --oneline
```

## Buenas prácticas

1. **Commits descriptivos**: Escribe mensajes claros que expliquen qué cambiaste
   - ✅ Bueno: `"Agregar sistema de tarjetas destacadas con carrusel"`
   - ❌ Malo: `"cambios"`

2. **Commits frecuentes**: Haz commits pequeños y frecuentes en lugar de uno grande al final

3. **No subir archivos sensibles**: 
   - Nunca subas archivos `.env` con claves secretas
   - No subas la base de datos `instance/database.db`
   - El `.gitignore` ya está configurado para excluir estos archivos

4. **Ramas para nuevas características**: Si trabajas en una nueva funcionalidad, considera crear una rama:
   ```bash
   git checkout -b nueva-funcionalidad
   # ... hacer cambios ...
   git commit -m "Agregar nueva funcionalidad"
   git push -u origin nueva-funcionalidad
   ```

## Estructura de ramas recomendada

- `main`: Código de producción estable
- `develop`: Desarrollo activo
- `feature/nombre-feature`: Nuevas funcionalidades
- `fix/nombre-fix`: Correcciones de bugs

## Solución de problemas

### Si olvidaste agregar un archivo al .gitignore
```bash
# Remover del índice pero mantener el archivo local
git rm --cached archivo-no-deseado.db
git commit -m "Remover archivo del control de versiones"
```

### Si necesitas revertir cambios locales
```bash
# Descartar cambios en un archivo específico
git checkout -- archivo.py

# Descartar todos los cambios locales
git reset --hard HEAD
```

### Si necesitas actualizar desde GitHub
```bash
git pull origin main
```

## Notas importantes

- El archivo `.gitignore` ya está configurado para excluir:
  - Base de datos (`*.db`, `*.sqlite`)
  - Archivos de entorno (`.env`)
  - Archivos de Python compilados (`__pycache__/`)
  - Carpetas de backups (`backup_*/`)
  - Archivos subidos por usuarios (`static/uploads/*`)

- **Nunca subas**:
  - Credenciales o claves secretas
  - La base de datos de producción
  - Archivos grandes innecesarios

