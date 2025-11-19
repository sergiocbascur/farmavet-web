# Estructura de Datos y Archivos - FARMAVET Web

## 📍 Ubicación de los Datos

### Base de Datos
- **Ubicación**: `instance/database.db`
- **Tipo**: SQLite3
- **Contenido**: Todo el contenido del panel de administración:
  - FAQs
  - Certificados
  - Metodologías analíticas
  - Proyectos
  - Publicaciones científicas
  - Imágenes de galería
  - Noticias
  - Eventos
  - Equipo
  - Estadísticas
  - Y más...

**⚠️ IMPORTANTE**: Esta base de datos contiene TODO el contenido gestionado desde el panel de admin. Si se elimina o modifica el código, la BD permanece intacta.

### Archivos Subidos (Imágenes, Videos, PDFs)

#### Estructura de Carpetas:
```
static/uploads/
├── galeria/          # Imágenes y videos del hero slider y galería general
├── infografias/      # Infografías
├── certificados/     # Certificados en PDF o imagen
├── noticias/         # Imágenes de noticias
├── equipo/           # Fotos del equipo
├── programas/        # Imágenes de programas de docencia
├── testimonios/      # Imágenes de testimonios
└── clientes/         # Logos de clientes
```

**⚠️ IMPORTANTE**: Todos los archivos subidos se guardan en `static/uploads/`. Estos archivos NO se pierden al modificar el código.

## 🔒 Protección de Datos

### ¿Qué se preserva al modificar código?
✅ **Base de datos** (`instance/database.db`) - Se mantiene intacta
✅ **Archivos subidos** (`static/uploads/`) - Se mantienen intactos
✅ **Traducciones** (`translations/`) - Se mantienen intactas
✅ **Logos** (`logos/`) - Se mantienen intactos

### ¿Qué se puede perder?
❌ Cambios en código fuente (`.py`, `.html`, `.css`, `.js`) - Se sobrescriben
❌ Configuraciones temporales en memoria

## 📦 Backup Recomendado

### Antes de hacer cambios importantes:

1. **Backup de Base de Datos**:
   ```bash
   cp instance/database.db instance/database_backup_$(date +%Y%m%d_%H%M%S).db
   ```

2. **Backup de Archivos**:
   ```bash
   cp -r static/uploads static/uploads_backup_$(date +%Y%m%d_%H%M%S)
   ```

3. **Backup Completo del Proyecto**:
   ```bash
   tar -czf farmavet_backup_$(date +%Y%m%d_%H%M%S).tar.gz \
     instance/database.db \
     static/uploads/ \
     translations/ \
     logos/
   ```

## 🎥 Soporte para Videos

### Formatos Soportados:
- MP4 (recomendado)
- WebM
- MOV

### Ubicación:
Los videos se guardan en la misma estructura que las imágenes:
- `static/uploads/galeria/` - Para videos del hero slider
- `static/uploads/infografias/` - Para videos informativos

### Límites:
- Tamaño máximo por archivo: 16MB (configurable en `app.py`)
- Formatos permitidos: mp4, webm, mov

## 📝 Notas Importantes

1. **La base de datos SQLite** es un archivo único que contiene todas las tablas. No se divide en múltiples archivos.

2. **Los archivos subidos** se organizan por tipo en subcarpetas dentro de `static/uploads/`.

3. **Las rutas en la BD** solo guardan el nombre del archivo, no la ruta completa. La ruta se construye dinámicamente según el tipo.

4. **En producción (VPS)**, los datos se guardan en el servidor:
   - **Base de datos**: `/var/www/farmavet-web/instance/database.db` (o la ruta donde despliegues)
   - **Archivos subidos**: `/var/www/farmavet-web/static/uploads/`
   - **Todo está en el VPS**: No se usa almacenamiento externo por defecto
   - ⚠️ **CRÍTICO**: Configurar backups automáticos diarios
   - Ver `GUIA_DESPLIEGUE_VPS.md` para detalles completos de despliegue

## 🔄 Migración de Datos

Si necesitas mover el proyecto:

1. Copia `instance/database.db`
2. Copia toda la carpeta `static/uploads/`
3. Copia `translations/` y `logos/`
4. El resto del código se puede regenerar desde el repositorio

