# FARMAVET Web - Laboratorio de Farmacología Veterinaria

Sitio web oficial del Laboratorio de Farmacología Veterinaria (FARMAVET) de la Universidad de Chile.

## Descripción

Aplicación web desarrollada con Flask que presenta los servicios, investigación, docencia y noticias del laboratorio FARMAVET. Incluye un panel de administración completo para gestionar contenido dinámico y un sistema de internacionalización (español/inglés).

## Características

- 🌐 **Sistema de internacionalización**: Soporte completo para español e inglés
- 📱 **Diseño responsive**: Optimizado para dispositivos móviles, tablets y desktop
- 🔐 **Panel de administración**: Gestión completa de contenido dinámico
- 🎨 **Interfaz moderna**: Diseño UX/UI profesional con Bootstrap 5
- 📊 **Gestión de contenido**: Noticias, eventos, programas, proyectos, equipo, etc.
- 🖼️ **Carruseles dinámicos**: Sistema de tarjetas destacadas con rotación automática

## Tecnologías

- **Backend**: Flask (Python)
- **Base de datos**: SQLite3
- **Frontend**: HTML5, CSS3, JavaScript (ES6+)
- **Framework CSS**: Bootstrap 5.3.3
- **Iconos**: Bootstrap Icons
- **Internacionalización**: Flask-Babel
- **Seguridad**: Werkzeug (hashing de contraseñas, rate limiting)

## Estructura del Proyecto

```
farmavet-web/
├── app.py                 # Aplicación Flask principal
├── templates/             # Templates Jinja2
│   ├── admin/            # Panel de administración
│   └── *.html            # Páginas públicas
├── static/               # Archivos estáticos (uploads)
├── assets/               # CSS, JS, imágenes
├── translations/        # Archivos de traducción (i18n)
├── logos/               # Logotipos
├── instance/            # Base de datos (ignorado en git)
└── requirements.txt     # Dependencias Python
```

## Instalación

1. Clonar el repositorio:
```bash
git clone https://github.com/tu-usuario/farmavet-web.git
cd farmavet-web
```

2. Crear entorno virtual:
```bash
python -m venv venv
venv\Scripts\activate  # Windows
# o
source venv/bin/activate  # Linux/Mac
```

3. Instalar dependencias:
```bash
pip install -r requirements.txt
```

4. Configurar variables de entorno (opcional):
```bash
# Crear archivo .env
SECRET_KEY=tu-clave-secreta-aqui
```

5. Inicializar base de datos:
```bash
# La base de datos se crea automáticamente al ejecutar la aplicación
python app.py
```

## Uso

### Desarrollo local

```bash
python app.py
```

La aplicación estará disponible en `http://localhost:5000`

### Panel de administración

Acceder a `/login` y usar las credenciales de administrador.

### Compilar traducciones

```bash
# Extraer strings para traducir
pybabel extract -F babel.cfg -k _l -o messages.pot .

# Inicializar traducción (solo primera vez)
pybabel init -i messages.pot -d translations -l en

# Actualizar traducciones
pybabel update -i messages.pot -d translations

# Compilar traducciones
pybabel compile -d translations
```

## Documentación Adicional

- [README_I18N.md](README_I18N.md) - Sistema de internacionalización
- [README_ADMIN.md](README_ADMIN.md) - Panel de administración
- [DEPLOY.md](DEPLOY.md) - Guía de despliegue

## Seguridad

- Rate limiting en intentos de login
- Validación de fortaleza de contraseñas
- Sesiones seguras con cookies HTTPOnly
- Protección CSRF
- Sanitización de inputs

## Licencia

Este proyecto es propiedad de FARMAVET - Universidad de Chile.

## Contacto

Para más información sobre FARMAVET, visita [www.laboratoriofarmavet.cl](https://www.laboratoriofarmavet.cl)


