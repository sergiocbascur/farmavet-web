# 📋 Archivos Importantes para el Funcionamiento de la Página

## ✅ Archivos Críticos que DEBEN estar en GitHub

### Backend (Python)
- ✅ `app.py` - Aplicación principal Flask
- ✅ `requirements.txt` - Dependencias Python
- ✅ `runtime.txt` - Versión de Python
- ✅ `gunicorn_config.py` - Configuración de Gunicorn
- ✅ `farmavet-web.service` - Servicio systemd
- ✅ `nginx_subdomain.conf` - Configuración Nginx
- ✅ `babel.cfg` - Configuración de traducciones
- ✅ `compile_translations.py` - Script de compilación
- ✅ `create_admin.py` - Script de creación de admin

### Templates (HTML)
- ✅ `templates/index.html` - Página de inicio
- ✅ `templates/faq.html` - Página de FAQ
- ✅ `templates/quienes-somos.html` - Quiénes Somos
- ✅ `templates/servicios.html` - Servicios
- ✅ `templates/equipo.html` - Equipo
- ✅ `templates/docencia.html` - Docencia
- ✅ `templates/investigacion.html` - Investigación
- ✅ `templates/noticias.html` - Noticias
- ✅ `templates/contacto.html` - Contacto
- ✅ `templates/casa-omsa.html` - CASA-OMSA
- ✅ `templates/admin/*.html` - Todos los templates del admin

### Assets (CSS/JS)
- ✅ `assets/css/style.css` - Estilos principales
- ✅ `assets/js/main.js` - JavaScript principal
- ✅ `assets/images/*` - Imágenes estáticas

### Traducciones
- ✅ `translations/es/LC_MESSAGES/messages.po` - Español
- ✅ `translations/en/LC_MESSAGES/messages.po` - Inglés
- ✅ `messages.pot` - Archivo de traducciones base

### Logos
- ✅ `logos/LOGO_FARMAVET_sf.png` - Logo sin fondo (SIN ESPACIOS)
- ✅ `logos/LOGO FARMAVET.png` - Logo con fondo
- ✅ Otros logos de aliados

## ❌ Archivos que NO deben estar en GitHub

### Base de Datos
- ❌ `*.db` - Bases de datos SQLite (se crean automáticamente)
- ❌ `instance/` - Carpeta de instancia Flask

### Archivos de Desarrollo
- ❌ `__pycache__/` - Cache de Python
- ❌ `venv/` - Entorno virtual
- ❌ `.env` - Variables de entorno
- ❌ `*.log` - Archivos de log

### Uploads (estructura sí, archivos no)
- ❌ `static/uploads/*` - Archivos subidos por usuarios
- ✅ `static/uploads/.gitkeep` - Mantener estructura

### Archivos HTML duplicados en raíz
- ❌ `index.html`, `servicios.html`, etc. en la raíz (duplicados)
- ✅ Solo los de `templates/` deben estar en git

## 🔍 Verificación

Para verificar que todos los archivos importantes están en git:

```bash
# Ver archivos no rastreados
git status --short | grep "^??"

# Ver archivos importantes que faltan
git ls-files | grep -E "(app\.py|requirements\.txt|templates/|assets/)"
```

## 📝 Notas

- El logo debe usar `LOGO_FARMAVET_sf.png` (con guion bajo, sin espacios)
- Todos los templates deben estar en `templates/`
- Los archivos HTML en la raíz son duplicados y no deben estar en git
