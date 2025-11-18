"""
Backend Flask para panel de administración de FARMAVET Web
Permite editar contenido sin tocar código HTML
"""

from flask import Flask, render_template, request, redirect, url_for, flash, session, send_from_directory, jsonify
from flask_babel import Babel, gettext as _, get_locale, lazy_gettext as _l
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import sqlite3
import os
import json
import time
import secrets
from datetime import datetime, timedelta
from functools import wraps

# Configuración
app = Flask(__name__)
# SECRET_KEY: usar variable de entorno o generar una segura
_secret_key = os.environ.get('SECRET_KEY', '').strip()
if not _secret_key or _secret_key == 'farmavet-web-secret-key-change-in-production':
    # Generar una clave segura si no está configurada
    _secret_key = secrets.token_urlsafe(50)
    print("⚠️  ADVERTENCIA: SECRET_KEY no configurada. Se generó una temporal.")
    print("   Para producción, configura SECRET_KEY como variable de entorno.")
app.secret_key = _secret_key
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg'}

# Configuración de seguridad
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=2)  # Sesión expira en 2 horas
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('FLASK_ENV') == 'production'  # Solo HTTPS en producción
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Rate limiting para login (simple en memoria)
login_attempts = {}  # {ip: {'count': int, 'last_attempt': float}}
MAX_LOGIN_ATTEMPTS = 5
LOGIN_LOCKOUT_TIME = 300  # 5 minutos

# Configuración de Flask-Babel
app.config['BABEL_DEFAULT_LOCALE'] = 'es'
app.config['BABEL_DEFAULT_TIMEZONE'] = 'America/Santiago'
app.config['BABEL_TRANSLATION_DIRECTORIES'] = 'translations'
babel = Babel()

# Filtro personalizado para Jinja2: parsear JSON
@app.template_filter('from_json')
def from_json_filter(value):
    """Convierte un string JSON a lista/dict"""
    if not value or value == '[]' or value == '{}':
        return []
    try:
        return json.loads(value)
    except:
        return []

# Función helper para traducir contenido dinámico de BD
def get_translated_field(record, field_name, default=None):
    """
    Obtiene el valor traducido de un campo de la BD.
    Busca campo_field_en si el idioma es 'en', sino devuelve el campo original.
    Funciona con sqlite3.Row, dict y objetos con atributos.
    Ejemplo: get_translated_field(noticia, 'titulo') -> noticia.titulo_en si lang='en', sino noticia.titulo
    """
    lang = get_language()
    if lang == 'en':
        translated_field = f'{field_name}_en'
        # Intentar obtener el campo traducido
        try:
            # Para sqlite3.Row (se puede acceder como dict o con keys())
            if hasattr(record, 'keys'):
                if translated_field in record.keys():
                    value = record[translated_field]
                    if value and str(value).strip():
                        return value
            # Para dict
            elif isinstance(record, dict):
                translated_value = record.get(translated_field)
                if translated_value and str(translated_value).strip():
                    return translated_value
            # Para objetos con atributos
            elif hasattr(record, translated_field):
                value = getattr(record, translated_field, None)
                if value and str(value).strip():
                    return value
        except (KeyError, AttributeError, TypeError):
            pass
    
    # Devolver el campo original
    try:
        # Para sqlite3.Row
        if hasattr(record, 'keys'):
            if field_name in record.keys():
                return record[field_name]
        # Para dict
        elif isinstance(record, dict):
            return record.get(field_name, default)
        # Para objetos con atributos
        elif hasattr(record, field_name):
            return getattr(record, field_name, default)
    except (KeyError, AttributeError, TypeError):
        pass
    
    return default

# Hacer la función disponible en templates
@app.context_processor
def inject_helpers():
    return dict(
        get_translated_field=get_translated_field, 
        _=_, 
        csrf_token=generate_csrf_token()
    )

# Crear directorios necesarios
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('static/uploads/programas', exist_ok=True)
os.makedirs('static/uploads/testimonios', exist_ok=True)
os.makedirs('static/uploads/noticias', exist_ok=True)
os.makedirs('static/uploads/equipo', exist_ok=True)
os.makedirs('static/uploads/clientes', exist_ok=True)
os.makedirs('static/uploads/hero-media', exist_ok=True)

# Base de datos
# En producción, usar instance/ para que Flask lo maneje correctamente
DATABASE = os.path.join('instance', 'database.db')

def get_db():
    """Obtiene conexión a la base de datos"""
    # Asegurar que la carpeta instance existe
    os.makedirs('instance', exist_ok=True)
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Inicializa la base de datos con las tablas necesarias"""
    conn = get_db()
    
    # Tabla de administradores
    conn.execute('''
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabla de programas de educación continua
    conn.execute('''
        CREATE TABLE IF NOT EXISTS programas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo TEXT NOT NULL,  -- 'diplomado', 'curso', 'taller'
            titulo TEXT NOT NULL,
            descripcion TEXT,
            modalidad TEXT,
            horario TEXT,
            patrocinio TEXT,
            auspicio TEXT,
            email_contacto TEXT,
            texto_boton TEXT DEFAULT 'Postular',
            orden INTEGER DEFAULT 0,
            activo INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabla de testimonios
    conn.execute('''
        CREATE TABLE IF NOT EXISTS testimonios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            contenido TEXT NOT NULL,
            autor TEXT,
            categoria TEXT,  -- 'pregrado', 'postgrado', 'industria', etc.
            tags TEXT,  -- JSON array de tags
            imagen TEXT,  -- Ruta a imagen opcional
            orden INTEGER DEFAULT 0,
            activo INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabla de noticias
    conn.execute('''
        CREATE TABLE IF NOT EXISTS noticias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            resumen TEXT,
            contenido TEXT,
            imagen TEXT,
            imagen_zoom REAL DEFAULT 1.0,  -- Zoom de la imagen (0.5 a 5.0)
            imagen_x REAL DEFAULT 0.0,  -- Posición X de la imagen
            imagen_y REAL DEFAULT 0.0,  -- Posición Y de la imagen
            categoria TEXT,  -- 'investigacion', 'servicios', 'docencia', 'eventos'
            fecha TEXT,
            enlace_externo TEXT,
            orden INTEGER DEFAULT 0,
            destacada INTEGER DEFAULT 0,
            activa INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Agregar columnas de imagen si no existen (para bases de datos existentes)
    try:
        conn.execute('ALTER TABLE noticias ADD COLUMN imagen_zoom REAL DEFAULT 1.0')
    except:
        pass  # La columna ya existe
    try:
        conn.execute('ALTER TABLE noticias ADD COLUMN imagen_x REAL DEFAULT 0.0')
    except:
        pass  # La columna ya existe
    try:
        conn.execute('ALTER TABLE noticias ADD COLUMN imagen_y REAL DEFAULT 0.0')
    except:
        pass  # La columna ya existe
    # Campos de traducción para noticias
    try:
        conn.execute('ALTER TABLE noticias ADD COLUMN titulo_en TEXT')
    except:
        pass
    try:
        conn.execute('ALTER TABLE noticias ADD COLUMN resumen_en TEXT')
    except:
        pass
    try:
        conn.execute('ALTER TABLE noticias ADD COLUMN contenido_en TEXT')
    except:
        pass
    try:
        conn.execute('ALTER TABLE noticias ADD COLUMN categoria_en TEXT')
    except:
        pass
    
    # Campos de traducción para testimonios
    try:
        conn.execute('ALTER TABLE testimonios ADD COLUMN titulo_en TEXT')
    except:
        pass
    try:
        conn.execute('ALTER TABLE testimonios ADD COLUMN contenido_en TEXT')
    except:
        pass
    
    # Campos de traducción para programas
    try:
        conn.execute('ALTER TABLE programas ADD COLUMN titulo_en TEXT')
    except:
        pass
    try:
        conn.execute('ALTER TABLE programas ADD COLUMN descripcion_en TEXT')
    except:
        pass
    try:
        conn.execute('ALTER TABLE programas ADD COLUMN tipo_en TEXT')
    except:
        pass
    try:
        conn.execute('ALTER TABLE programas ADD COLUMN modalidad_en TEXT')
    except:
        pass
    try:
        conn.execute('ALTER TABLE programas ADD COLUMN horario_en TEXT')
    except:
        pass
    try:
        conn.execute('ALTER TABLE programas ADD COLUMN texto_boton_en TEXT')
    except:
        pass
    try:
        conn.execute('ALTER TABLE programas ADD COLUMN patrocinio_en TEXT')
    except:
        pass
    try:
        conn.execute('ALTER TABLE programas ADD COLUMN auspicio_en TEXT')
    except:
        pass
    
    # Campos de traducción para proyectos
    try:
        conn.execute('ALTER TABLE proyectos ADD COLUMN titulo_en TEXT')
    except:
        pass
    try:
        conn.execute('ALTER TABLE proyectos ADD COLUMN descripcion_en TEXT')
    except:
        pass
    try:
        conn.execute('ALTER TABLE proyectos ADD COLUMN tipo_en TEXT')
    except:
        pass
    
    # Campos de traducción para publicaciones
    try:
        conn.execute('ALTER TABLE publicaciones ADD COLUMN titulo_en TEXT')
    except:
        pass
    try:
        conn.execute('ALTER TABLE publicaciones ADD COLUMN descripcion_en TEXT')
    except:
        pass
    
    # Campos de traducción para equipo
    try:
        conn.execute('ALTER TABLE equipo ADD COLUMN biografia_en TEXT')
    except:
        pass
    
    # Tabla de organigrama (cargos/posiciones)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS organigrama (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            seccion TEXT NOT NULL,  -- 'direccion', 'tecnico', 'calidad', 'administracion', 'investigacion'
            subseccion TEXT,  -- 'Jefe Técnico', 'Operaciones de Laboratorio', etc.
            subseccion_en TEXT,
            cargo TEXT NOT NULL,  -- Nombre del cargo
            cargo_en TEXT,
            descripcion TEXT,  -- Descripción del cargo
            descripcion_en TEXT,
            orden INTEGER DEFAULT 0,
            activo INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    # Migración: agregar campos de traducción si no existen (para bases de datos existentes)
    try:
        conn.execute('ALTER TABLE organigrama ADD COLUMN subseccion_en TEXT')
    except:
        pass  # La columna ya existe
    try:
        conn.execute('ALTER TABLE organigrama ADD COLUMN cargo_en TEXT')
    except:
        pass  # La columna ya existe
    try:
        conn.execute('ALTER TABLE organigrama ADD COLUMN descripcion_en TEXT')
    except:
        pass  # La columna ya existe
    
    # Tabla de miembros del equipo (ahora referencian cargos del organigrama)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS equipo (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            cargo_id INTEGER,  -- Referencia al organigrama
            cargo TEXT,  -- Mantener por compatibilidad, pero se usará cargo_id
            biografia TEXT,
            email TEXT,
            imagen TEXT,
            imagen_zoom REAL DEFAULT 1.0,  -- Zoom de la imagen (0.5 a 5.0)
            imagen_x REAL DEFAULT 0.0,  -- Posición X de la imagen
            imagen_y REAL DEFAULT 0.0,  -- Posición Y de la imagen
            tags TEXT,  -- JSON array de tags
            orden INTEGER DEFAULT 0,
            activo INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (cargo_id) REFERENCES organigrama(id)
        )
    ''')
    
    # Agregar columnas si no existen (para bases de datos existentes)
    try:
        conn.execute('ALTER TABLE equipo ADD COLUMN cargo_id INTEGER')
    except:
        pass  # La columna ya existe
    try:
        conn.execute('ALTER TABLE equipo ADD COLUMN tags TEXT')
    except:
        pass  # La columna ya existe
    try:
        conn.execute('ALTER TABLE equipo ADD COLUMN redes_sociales TEXT')
    except:
        pass  # La columna ya existe
    try:
        conn.execute('ALTER TABLE equipo ADD COLUMN imagen_zoom REAL DEFAULT 1.0')
    except:
        pass  # La columna ya existe
    try:
        conn.execute('ALTER TABLE equipo ADD COLUMN imagen_x REAL DEFAULT 0.0')
    except:
        pass  # La columna ya existe
    try:
        conn.execute('ALTER TABLE equipo ADD COLUMN imagen_y REAL DEFAULT 0.0')
    except:
        pass  # La columna ya existe
    try:
        conn.execute('ALTER TABLE clientes ADD COLUMN mostrar_en_index INTEGER DEFAULT 0')
    except:
        pass  # La columna ya existe
    try:
        conn.execute('ALTER TABLE clientes ADD COLUMN mostrar_en_casa_omsa INTEGER DEFAULT 0')
    except:
        pass  # La columna ya existe
    
    # Tabla de convenios/alianzas
    conn.execute('''
        CREATE TABLE IF NOT EXISTS convenios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            tipo TEXT,  -- 'publico', 'privado', 'internacional'
            descripcion TEXT,
            logo TEXT,
            enlace TEXT,
            orden INTEGER DEFAULT 0,
            activo INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabla de hero_media (para sección de imágenes/tarjetas en hero de páginas)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS hero_media (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pagina TEXT NOT NULL,  -- 'index', 'quienes-somos', 'servicios', etc.
            tipo TEXT NOT NULL DEFAULT 'imagen',  -- 'imagen' o 'tarjeta'
            titulo TEXT,  -- Para tarjetas
            titulo_en TEXT,
            contenido TEXT,  -- Para tarjetas: lista de textos (JSON array o texto separado por saltos de línea)
            contenido_en TEXT,
            imagenes TEXT,  -- JSON array de URLs de imágenes (para tipo 'imagen')
            imagenes_ajustes TEXT,  -- JSON object con ajustes por imagen: {"url1": {"zoom": 1.0, "x": 0, "y": 0}, ...}
            orden INTEGER DEFAULT 0,
            activo INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Agregar columna de ajustes si no existe
    try:
        conn.execute('ALTER TABLE hero_media ADD COLUMN imagenes_ajustes TEXT')
    except:
        pass
    
    # Tabla de tarjetas destacadas (tarjetas blancas con título, contenido y enlace opcional)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS tarjetas_destacadas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pagina TEXT NOT NULL,  -- 'index', 'quienes-somos', 'servicios', etc.
            titulo TEXT NOT NULL,
            titulo_en TEXT,
            contenido TEXT NOT NULL,  -- Texto del contenido (puede ser lista separada por saltos de línea o texto simple)
            contenido_en TEXT,
            enlace TEXT,  -- URL opcional
            texto_enlace TEXT,  -- Texto del enlace (opcional)
            texto_enlace_en TEXT,
            orden INTEGER DEFAULT 0,
            activo INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabla de clientes/logos
    conn.execute('''
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            logo TEXT,
            enlace TEXT,
            categoria TEXT,  -- 'cliente', 'aliado', 'patrocinador'
            mostrar_en_index INTEGER DEFAULT 0,  -- Mostrar en "Clientes y aliados" (index.html)
            mostrar_en_casa_omsa INTEGER DEFAULT 0,  -- Mostrar en "Aliados estratégicos" (casa-omsa.html)
            orden INTEGER DEFAULT 0,
            activo INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Campos de traducción para clientes/aliados
    try:
        conn.execute('ALTER TABLE clientes ADD COLUMN nombre_en TEXT')
    except:
        pass
    
    # Tabla de estadísticas/números destacados
    conn.execute('''
        CREATE TABLE IF NOT EXISTS estadisticas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero INTEGER NOT NULL,
            sufijo TEXT,  -- '+', 'er', 'º', etc.
            etiqueta TEXT NOT NULL,
            etiqueta_en TEXT,
            orden INTEGER DEFAULT 0,
            activo INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    # Migración: agregar campo etiqueta_en si no existe (para bases de datos existentes)
    try:
        conn.execute('ALTER TABLE estadisticas ADD COLUMN etiqueta_en TEXT')
    except:
        pass  # La columna ya existe
    
    # Tabla de eventos
    conn.execute('''
        CREATE TABLE IF NOT EXISTS eventos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            titulo_en TEXT,
            fecha TEXT NOT NULL,  -- Formato: "Abril 2025", "Mayo 2025", etc.
            meta TEXT,  -- Modalidad, ubicación, etc.
            meta_en TEXT,
            descripcion TEXT,
            descripcion_en TEXT,
            enlace TEXT,
            texto_boton TEXT DEFAULT 'Ver más',
            texto_boton_en TEXT,
            orden INTEGER DEFAULT 0,
            activo INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    # Migración: agregar campos de traducción si no existen (para bases de datos existentes)
    try:
        conn.execute('ALTER TABLE eventos ADD COLUMN titulo_en TEXT')
    except:
        pass  # La columna ya existe
    try:
        conn.execute('ALTER TABLE eventos ADD COLUMN descripcion_en TEXT')
    except:
        pass  # La columna ya existe
    try:
        conn.execute('ALTER TABLE eventos ADD COLUMN meta_en TEXT')
    except:
        pass  # La columna ya existe
    try:
        conn.execute('ALTER TABLE eventos ADD COLUMN texto_boton_en TEXT')
    except:
        pass  # La columna ya existe
    
    # Tabla de contenido editable (textos generales)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS contenido (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            seccion TEXT UNIQUE NOT NULL,  -- 'hero_titulo', 'quienes_somos', etc.
            titulo TEXT,
            texto TEXT,
            imagen TEXT,
            orden INTEGER DEFAULT 0,
            activo INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabla de proyectos destacados
    conn.execute('''
        CREATE TABLE IF NOT EXISTS proyectos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            descripcion TEXT,
            tipo TEXT,  -- 'FONDECYT Regular', 'FONDEF', 'Cooperación internacional', etc.
            enlace TEXT,
            orden INTEGER DEFAULT 0,
            activo INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabla de publicaciones científicas
    conn.execute('''
        CREATE TABLE IF NOT EXISTS publicaciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            descripcion TEXT,
            revista TEXT,  -- 'Journal of Veterinary Pharmacology', etc.
            año TEXT,  -- '2025', '2024', etc.
            enlace TEXT,
            tags TEXT,  -- JSON array de tags
            orden INTEGER DEFAULT 0,
            activo INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Crear usuario admin por defecto si no existe
    cursor = conn.execute('SELECT COUNT(*) as count FROM admins')
    count = cursor.fetchone()['count']
    if count == 0:
        default_password = generate_password_hash('admin123')
        conn.execute('INSERT INTO admins (username, password_hash) VALUES (?, ?)', 
                    ('admin', default_password))
        print("✅ Usuario admin creado: username='admin', password='admin123'")
        print("⚠️  IMPORTANTE: Cambia la contraseña después del primer login")
    
    conn.commit()
    conn.close()

# Funciones de seguridad
def check_rate_limit(ip_address):
    """Verifica si una IP ha excedido el límite de intentos de login"""
    now = time.time()
    if ip_address in login_attempts:
        attempts = login_attempts[ip_address]
        # Si han pasado más de LOGIN_LOCKOUT_TIME segundos, resetear
        if now - attempts['last_attempt'] > LOGIN_LOCKOUT_TIME:
            login_attempts[ip_address] = {'count': 0, 'last_attempt': now}
            return True
        # Si excedió el límite, verificar si aún está bloqueado
        if attempts['count'] >= MAX_LOGIN_ATTEMPTS:
            time_remaining = LOGIN_LOCKOUT_TIME - (now - attempts['last_attempt'])
            if time_remaining > 0:
                return False, time_remaining
            else:
                # Resetear después del bloqueo
                login_attempts[ip_address] = {'count': 0, 'last_attempt': now}
                return True
    return True

def record_failed_login(ip_address):
    """Registra un intento de login fallido"""
    now = time.time()
    if ip_address in login_attempts:
        login_attempts[ip_address]['count'] += 1
        login_attempts[ip_address]['last_attempt'] = now
    else:
        login_attempts[ip_address] = {'count': 1, 'last_attempt': now}

def reset_login_attempts(ip_address):
    """Resetea los intentos de login después de un login exitoso"""
    if ip_address in login_attempts:
        del login_attempts[ip_address]

def validate_password_strength(password):
    """Valida la fortaleza de la contraseña"""
    if len(password) < 8:
        return False, "La contraseña debe tener al menos 8 caracteres"
    if not any(c.isupper() for c in password):
        return False, "La contraseña debe contener al menos una letra mayúscula"
    if not any(c.islower() for c in password):
        return False, "La contraseña debe contener al menos una letra minúscula"
    if not any(c.isdigit() for c in password):
        return False, "La contraseña debe contener al menos un número"
    return True, None

# Protección CSRF básica
def generate_csrf_token():
    """Genera un token CSRF y lo guarda en la sesión"""
    if 'csrf_token' not in session:
        session['csrf_token'] = secrets.token_urlsafe(32)
    return session['csrf_token']

def validate_csrf_token(token):
    """Valida un token CSRF"""
    if 'csrf_token' not in session:
        return False
    return secrets.compare_digest(session['csrf_token'], token)


# Decorador para requerir login
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session:
            return redirect(url_for('public_login'))
        # Renovar sesión si está activa
        session.permanent = True
        return f(*args, **kwargs)
    return decorated_function

# Decorador para validar CSRF en rutas POST
def csrf_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.method == 'POST':
            token = request.form.get('csrf_token', '')
            if not validate_csrf_token(token):
                flash('Token de seguridad inválido', 'error')
                # Intentar redirigir a la página anterior o dashboard
                referrer = request.referrer or url_for('admin_dashboard')
                return redirect(referrer)
        return f(*args, **kwargs)
    return decorated_function

# Rutas para archivos estáticos
@app.route('/assets/<path:filename>')
def assets(filename):
    return send_from_directory('assets', filename)

@app.route('/logos/<path:filename>')
def logos(filename):
    return send_from_directory('logos', filename)

# Sistema de idioma con Flask-Babel
# En Flask-Babel 4.0.0, se registra la función directamente
def get_locale():
    """Obtener idioma actual desde sesión, por defecto español"""
    return session.get('language', 'es')

# Registrar la función con Babel (Flask-Babel 4.0.0)
babel.init_app(app, locale_selector=get_locale)

@app.route('/set_language/<lang>')
def set_language(lang):
    """Cambiar idioma y redirigir a la página actual"""
    if lang in ['es', 'en']:
        session['language'] = lang
        session.permanent = True  # Hacer la sesión permanente
    # Obtener la página de referencia o usar index
    referrer = request.referrer
    if referrer:
        # Extraer la ruta de la URL de referencia
        from urllib.parse import urlparse
        parsed = urlparse(referrer)
        path = parsed.path
        if path and path != '/set_language/es' and path != '/set_language/en':
            return redirect(path)
    return redirect(url_for('index'))

def get_language():
    """Obtener idioma actual desde sesión, por defecto español (compatibilidad)"""
    return session.get('language', 'es')

# Rutas públicas (páginas del sitio)
@app.route('/')
@app.route('/index.html')
def index():
    # SIEMPRE usar template si existe, nunca archivo estático
    if os.path.exists('templates/index.html'):
        conn = get_db()
        estadisticas = conn.execute('''
            SELECT * FROM estadisticas WHERE activo = 1 
            ORDER BY orden, id
        ''').fetchall()
        noticias = conn.execute('''
            SELECT * FROM noticias WHERE activa = 1 
            ORDER BY destacada DESC, fecha DESC, id DESC LIMIT 3
        ''').fetchall()
        clientes = conn.execute('''
            SELECT * FROM clientes WHERE activo = 1 AND mostrar_en_index = 1 
            ORDER BY orden, id
        ''').fetchall()
        tarjetas_destacadas = conn.execute('''
            SELECT * FROM tarjetas_destacadas WHERE pagina = 'index' AND activo = 1 
            ORDER BY orden, id
        ''').fetchall()
        conn.close()
        lang = get_language()
        locale = get_locale()
        return render_template('index.html', estadisticas=estadisticas, noticias=noticias, clientes=clientes, tarjetas_destacadas=tarjetas_destacadas, lang=lang, locale=locale)
    else:
        return "Página no encontrada. El template debe existir en templates/index.html", 404

@app.route('/equipo')
@app.route('/equipo.html')
def equipo_page():
    """Ruta específica para página de equipo"""
    lang = get_language()
    locale = get_locale()
    conn = get_db()
    # Verificar qué columnas de traducción existen
    cursor = conn.execute("PRAGMA table_info(organigrama)")
    columns = [col[1] for col in cursor.fetchall()]
    has_subseccion_en = 'subseccion_en' in columns
    has_cargo_en = 'cargo_en' in columns
    has_descripcion_en = 'descripcion_en' in columns
    
    # Construir SELECT dinámicamente según columnas disponibles
    select_cols = ['o.*']
    if has_subseccion_en:
        select_cols.append('o.subseccion_en')
    if has_cargo_en:
        select_cols.append('o.cargo_en')
    if has_descripcion_en:
        select_cols.append('o.descripcion_en')
    select_cols.extend([
        'e.id as miembro_id',
        'e.nombre as miembro_nombre',
        'e.biografia as miembro_biografia',
        'e.email as miembro_email',
        'e.imagen as miembro_imagen',
        'e.imagen_zoom as miembro_imagen_zoom',
        'e.imagen_x as miembro_imagen_x',
        'e.imagen_y as miembro_imagen_y',
        'e.tags as miembro_tags',
        'e.redes_sociales as miembro_redes',
        'o.cargo as cargo_nombre'
    ])
    
    # Obtener organigrama con sus miembros asignados
    query = f'''
        SELECT {', '.join(select_cols)}
        FROM organigrama o
        LEFT JOIN equipo e ON o.id = e.cargo_id AND e.activo = 1
        WHERE o.activo = 1
        ORDER BY o.seccion, o.orden, o.id, e.orden
    '''
    organigrama_raw = conn.execute(query).fetchall()
    
    # Organizar organigrama por sección y subsección
    organigrama_organizado = {}
    for row in organigrama_raw:
        seccion = row['seccion']
        subseccion = row['subseccion'] or 'Sin subsección'
        
        if seccion not in organigrama_organizado:
            organigrama_organizado[seccion] = {}
        
        if subseccion not in organigrama_organizado[seccion]:
            organigrama_organizado[seccion][subseccion] = []
        
        # Agregar cargo con su miembro (si existe)
        cargo_data = {
            'id': row['id'],
            'cargo': row['cargo'],
            'descripcion': row['descripcion'],
            'subseccion': row['subseccion'],
            'subseccion_en': row['subseccion_en'] if 'subseccion_en' in row.keys() else None,
            'cargo_en': row['cargo_en'] if 'cargo_en' in row.keys() else None,
            'descripcion_en': row['descripcion_en'] if 'descripcion_en' in row.keys() else None,
            'orden': row['orden'],
            'miembro': None
        }
        
        # Si hay miembro asignado
        if row['miembro_id']:
            # Parsear redes sociales si existen
            redes_sociales = {}
            if row['miembro_redes']:
                try:
                    redes_sociales = json.loads(row['miembro_redes'])
                except:
                    redes_sociales = {}
            
            cargo_data['miembro'] = {
                'id': row['miembro_id'],
                'nombre': row['miembro_nombre'],
                'biografia': row['miembro_biografia'],
                'email': row['miembro_email'],
                'imagen': row['miembro_imagen'],
                'imagen_zoom': row['miembro_imagen_zoom'],
                'imagen_x': row['miembro_imagen_x'],
                'imagen_y': row['miembro_imagen_y'],
                'tags': row['miembro_tags'],
                'redes_sociales': redes_sociales,
                'cargo_nombre': row['cargo_nombre']
            }
            cargo_data['cargo_nombre'] = row['cargo_nombre']
        else:
            # Si no hay miembro, al menos mostrar el nombre del cargo
            cargo_data['cargo_nombre'] = row['cargo']
        
        organigrama_organizado[seccion][subseccion].append(cargo_data)
    
    # Obtener también la sección de dirección (miembros destacados)
    select_direccion = ['e.*', 'o.cargo as cargo_nombre', 'o.seccion as cargo_seccion', 
                       'o.descripcion as cargo_descripcion']
    if has_cargo_en:
        select_direccion.append('o.cargo_en as cargo_nombre_en')
    if has_descripcion_en:
        select_direccion.append('o.descripcion_en as cargo_descripcion_en')
    
    query_direccion = f'''
        SELECT {', '.join(select_direccion)}
        FROM equipo e
        INNER JOIN organigrama o ON e.cargo_id = o.id
        WHERE e.activo = 1 AND o.seccion = 'direccion' AND o.activo = 1
        ORDER BY e.orden, e.id
    '''
    direccion_raw = conn.execute(query_direccion).fetchall()
    
    # Convertir Row objects a diccionarios y parsear redes sociales
    direccion = []
    for row in direccion_raw:
        miembro = dict(row)
        # Asegurar que cargo_nombre esté presente (debería venir de la query)
        if not miembro.get('cargo_nombre'):
            if miembro.get('cargo'):
                miembro['cargo_nombre'] = miembro.get('cargo')
            elif miembro.get('cargo_id'):
                # Intentar obtenerlo del organigrama como último recurso
                cargo_obj = conn.execute('SELECT cargo FROM organigrama WHERE id = ?', (miembro.get('cargo_id'),)).fetchone()
                if cargo_obj:
                    miembro['cargo_nombre'] = cargo_obj['cargo']
        
        # Parsear redes sociales
        if miembro.get('redes_sociales'):
            try:
                miembro['redes_sociales'] = json.loads(miembro['redes_sociales'])
            except:
                miembro['redes_sociales'] = {}
        else:
            miembro['redes_sociales'] = {}
        direccion.append(miembro)
    
    tarjetas_destacadas = conn.execute('''
        SELECT * FROM tarjetas_destacadas WHERE pagina = 'equipo' AND activo = 1 
        ORDER BY orden, id
    ''').fetchall()
    conn.close()
    return render_template('equipo.html', organigrama=organigrama_organizado, direccion=direccion, tarjetas_destacadas=tarjetas_destacadas, lang=lang, locale=locale)

@app.route('/<page>.html')
def page(page):
    """Rutas dinámicas para páginas HTML - SIEMPRE prioriza templates"""
    # Obtener idioma actual
    lang = get_language()
    locale = get_locale()
    
    # Verificar primero si existe template (para evitar servir archivos estáticos con Jinja2)
    template_file = f'{page}.html'
    
    if os.path.exists(f'templates/{template_file}'):
        # Páginas que necesitan datos de la BD
        if page == 'docencia':
            conn = get_db()
            programas = conn.execute('''
                SELECT * FROM programas WHERE activo = 1 
                ORDER BY orden, id DESC
            ''').fetchall()
            testimonios = conn.execute('''
                SELECT * FROM testimonios WHERE activo = 1 
                ORDER BY orden, id DESC
            ''').fetchall()
            tarjetas_destacadas = conn.execute('''
                SELECT * FROM tarjetas_destacadas WHERE pagina = 'docencia' AND activo = 1 
                ORDER BY orden, id
            ''').fetchall()
            conn.close()
            return render_template('docencia.html', programas=programas, testimonios=testimonios, tarjetas_destacadas=tarjetas_destacadas, lang=lang, locale=locale)
        
        elif page == 'noticias':
            conn = get_db()
            noticias = conn.execute('''
                SELECT * FROM noticias WHERE activa = 1 
                ORDER BY destacada DESC, fecha DESC, id DESC
            ''').fetchall()
            eventos = conn.execute('''
                SELECT * FROM eventos WHERE activo = 1 
                ORDER BY orden, id
            ''').fetchall()
            tarjetas_destacadas = conn.execute('''
                SELECT * FROM tarjetas_destacadas WHERE pagina = 'noticias' AND activo = 1 
                ORDER BY orden, id
            ''').fetchall()
            conn.close()
            return render_template('noticias.html', noticias=noticias, eventos=eventos, tarjetas_destacadas=tarjetas_destacadas, lang=lang, locale=locale)
        
        elif page == 'equipo':
            # SIEMPRE usar template, nunca archivo estático
            conn = get_db()
            # Obtener organigrama con sus miembros asignados
            organigrama_raw = conn.execute('''
                SELECT o.*, 
                       o.subseccion_en, o.cargo_en, o.descripcion_en,
                       e.id as miembro_id,
                       e.nombre as miembro_nombre,
                       e.biografia as miembro_biografia,
                       e.email as miembro_email,
                       e.imagen as miembro_imagen,
                       e.imagen_zoom as miembro_imagen_zoom,
                       e.imagen_x as miembro_imagen_x,
                       e.imagen_y as miembro_imagen_y,
                       e.tags as miembro_tags,
                       e.redes_sociales as miembro_redes,
                       o.cargo as cargo_nombre
                FROM organigrama o
                LEFT JOIN equipo e ON o.id = e.cargo_id AND e.activo = 1
                WHERE o.activo = 1
                ORDER BY o.seccion, o.orden, o.id, e.orden
            ''').fetchall()
            
            # Organizar organigrama por sección y subsección
            organigrama_organizado = {}
            for row in organigrama_raw:
                seccion = row['seccion']
                subseccion = row['subseccion'] or 'Sin subsección'
                
                if seccion not in organigrama_organizado:
                    organigrama_organizado[seccion] = {}
                
                if subseccion not in organigrama_organizado[seccion]:
                    organigrama_organizado[seccion][subseccion] = []
                
                # Agregar cargo con su miembro (si existe)
                cargo_data = {
                    'id': row['id'],
                    'cargo': row['cargo'],
                    'descripcion': row['descripcion'],
                    'subseccion': row['subseccion'],
                    'subseccion_en': row['subseccion_en'] if 'subseccion_en' in row.keys() else None,
                    'cargo_en': row['cargo_en'] if 'cargo_en' in row.keys() else None,
                    'descripcion_en': row['descripcion_en'] if 'descripcion_en' in row.keys() else None,
                    'orden': row['orden'],
                    'miembro': None
                }
                
                # Si hay miembro asignado
                if row['miembro_id']:
                    # Parsear redes sociales si existen
                    redes_sociales = {}
                    if row['miembro_redes']:
                        try:
                            redes_sociales = json.loads(row['miembro_redes'])
                        except:
                            redes_sociales = {}
                    
                    cargo_data['miembro'] = {
                        'id': row['miembro_id'],
                        'nombre': row['miembro_nombre'],
                        'biografia': row['miembro_biografia'],
                        'email': row['miembro_email'],
                        'imagen': row['miembro_imagen'],
                        'imagen_zoom': row['miembro_imagen_zoom'],
                        'imagen_x': row['miembro_imagen_x'],
                        'imagen_y': row['miembro_imagen_y'],
                        'tags': row['miembro_tags'],
                        'redes_sociales': redes_sociales,
                        'cargo_nombre': row['cargo_nombre']
                    }
                    cargo_data['cargo_nombre'] = row['cargo_nombre']
                else:
                    # Si no hay miembro, al menos mostrar el nombre del cargo
                    cargo_data['cargo_nombre'] = row['cargo']
                
                organigrama_organizado[seccion][subseccion].append(cargo_data)
            
            # Obtener también la sección de dirección (miembros destacados)
            # Obtener miembros que tienen cargo_id en sección dirección
            direccion_raw = conn.execute('''
                SELECT e.*, o.cargo as cargo_nombre, o.cargo_en as cargo_nombre_en, 
                       o.seccion as cargo_seccion, o.descripcion as cargo_descripcion, o.descripcion_en as cargo_descripcion_en
                FROM equipo e
                INNER JOIN organigrama o ON e.cargo_id = o.id
                WHERE e.activo = 1 AND o.seccion = 'direccion' AND o.activo = 1
                ORDER BY e.orden, e.id
            ''').fetchall()
            
            # Convertir Row objects a diccionarios y parsear redes sociales
            direccion = []
            for row in direccion_raw:
                miembro = dict(row)
                # Asegurar que cargo_nombre esté presente (debería venir de la query)
                if not miembro.get('cargo_nombre'):
                    if miembro.get('cargo'):
                        miembro['cargo_nombre'] = miembro.get('cargo')
                    elif miembro.get('cargo_id'):
                        # Intentar obtenerlo del organigrama como último recurso
                        cargo_obj = conn.execute('SELECT cargo FROM organigrama WHERE id = ?', (miembro.get('cargo_id'),)).fetchone()
                        if cargo_obj:
                            miembro['cargo_nombre'] = cargo_obj['cargo']
                
                # Parsear redes sociales
                if miembro.get('redes_sociales'):
                    try:
                        miembro['redes_sociales'] = json.loads(miembro['redes_sociales'])
                    except:
                        miembro['redes_sociales'] = {}
                else:
                    miembro['redes_sociales'] = {}
                direccion.append(miembro)
            
            tarjetas_destacadas = conn.execute('''
                SELECT * FROM tarjetas_destacadas WHERE pagina = 'equipo' AND activo = 1 
                ORDER BY orden, id
            ''').fetchall()
            conn.close()
            return render_template('equipo.html', organigrama=organigrama_organizado, direccion=direccion, tarjetas_destacadas=tarjetas_destacadas, lang=lang, locale=locale)
        
        elif page == 'convenios':
            conn = get_db()
            convenios = conn.execute('''
                SELECT * FROM convenios WHERE activo = 1 
                ORDER BY orden, id
            ''').fetchall()
            conn.close()
            return render_template('convenios.html', convenios=convenios, lang=lang, locale=locale)
        
        elif page == 'casa-omsa':
            conn = get_db()
            aliados_casa_omsa = conn.execute('''
                SELECT * FROM clientes WHERE activo = 1 AND mostrar_en_casa_omsa = 1 
                ORDER BY orden, id
            ''').fetchall()
            tarjetas_destacadas = conn.execute('''
                SELECT * FROM tarjetas_destacadas WHERE pagina = 'casa-omsa' AND activo = 1 
                ORDER BY orden, id
            ''').fetchall()
            conn.close()
            return render_template('casa-omsa.html', aliados_casa_omsa=aliados_casa_omsa, tarjetas_destacadas=tarjetas_destacadas, lang=lang, locale=locale)
        
        elif page == 'investigacion':
            conn = get_db()
            proyectos = conn.execute('''
                SELECT * FROM proyectos WHERE activo = 1 
                ORDER BY orden, id
            ''').fetchall()
            publicaciones = conn.execute('''
                SELECT * FROM publicaciones WHERE activo = 1 
                ORDER BY orden, id
            ''').fetchall()
            tarjetas_destacadas = conn.execute('''
                SELECT * FROM tarjetas_destacadas WHERE pagina = 'investigacion' AND activo = 1 
                ORDER BY orden, id
            ''').fetchall()
            conn.close()
            return render_template('investigacion.html', proyectos=proyectos, publicaciones=publicaciones, tarjetas_destacadas=tarjetas_destacadas, lang=lang, locale=locale)
        
        # Si existe template pero no necesita datos especiales, renderizarlo con lang
        # Incluir tarjetas destacadas para todas las páginas
        conn = get_db()
        tarjetas_destacadas = conn.execute('''
            SELECT * FROM tarjetas_destacadas WHERE pagina = ? AND activo = 1 
            ORDER BY orden, id
        ''', (page,)).fetchall()
        # Debug temporal: verificar qué se está consultando
        # print(f"DEBUG: Página '{page}', Tarjetas encontradas: {len(tarjetas_destacadas)}")
        conn.close()
        return render_template(template_file, tarjetas_destacadas=tarjetas_destacadas, lang=lang, locale=locale)
    
    # Si NO existe template, servir archivo estático (solo si no tiene Jinja2)
    elif os.path.exists(f'{page}.html'):
        return send_from_directory('.', f'{page}.html')
    else:
        return f"Página {page} no encontrada", 404

# Ruta de login pública (solo para panel de admin)
@app.route('/login', methods=['GET', 'POST'])
def public_login():
    """Login público para acceso al panel de administración"""
    if request.method == 'POST':
        # Obtener IP del cliente para rate limiting
        ip_address = request.remote_addr
        
        # Verificar rate limiting
        rate_check = check_rate_limit(ip_address)
        if rate_check is not True:
            time_remaining = rate_check[1]
            minutes = int(time_remaining // 60)
            seconds = int(time_remaining % 60)
            flash(f'Demasiados intentos fallidos. Intenta nuevamente en {minutes}m {seconds}s', 'error')
            return render_template('public_login.html', redirect_to='admin')
        
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        conn = get_db()
        admin = conn.execute(
            'SELECT * FROM admins WHERE username = ?', (username,)
        ).fetchone()
        conn.close()
        
        if admin and check_password_hash(admin['password_hash'], password):
            # Login exitoso
            session['admin_id'] = admin['id']
            session['admin_username'] = admin['username']
            session.permanent = True
            reset_login_attempts(ip_address)
            flash('Sesión iniciada correctamente', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            # Login fallido
            record_failed_login(ip_address)
            flash('Usuario o contraseña incorrectos', 'error')
    
    # Mostrar formulario de login
    return render_template('public_login.html', redirect_to='admin')

# Rutas de administración
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Login alternativo para panel de admin (redirige a /login)"""
    return redirect(url_for('public_login'))

@app.route('/admin/logout')
def admin_logout():
    session.clear()
    flash('Sesión cerrada', 'info')
    return redirect(url_for('public_login'))

@app.route('/admin')
@login_required
def admin_dashboard():
    conn = get_db()
    
    # Estadísticas
    stats = {
        'programas': conn.execute('SELECT COUNT(*) as count FROM programas WHERE activo = 1').fetchone()['count'],
        'testimonios': conn.execute('SELECT COUNT(*) as count FROM testimonios WHERE activo = 1').fetchone()['count'],
        'noticias': conn.execute('SELECT COUNT(*) as count FROM noticias WHERE activa = 1').fetchone()['count'],
        'eventos': conn.execute('SELECT COUNT(*) as count FROM eventos WHERE activo = 1').fetchone()['count'],
        'equipo': conn.execute('SELECT COUNT(*) as count FROM equipo WHERE activo = 1').fetchone()['count'],
        'clientes': conn.execute('SELECT COUNT(*) as count FROM clientes WHERE activo = 1').fetchone()['count'],
        'estadisticas': conn.execute('SELECT COUNT(*) as count FROM estadisticas WHERE activo = 1').fetchone()['count'],
        'proyectos': conn.execute('SELECT COUNT(*) as count FROM proyectos WHERE activo = 1').fetchone()['count'],
        'publicaciones': conn.execute('SELECT COUNT(*) as count FROM publicaciones WHERE activo = 1').fetchone()['count']
    }
    
    conn.close()
    return render_template('admin/dashboard.html', stats=stats)

# Cambio de contraseña
@app.route('/admin/cambiar-contrasena', methods=['GET', 'POST'])
@login_required
@csrf_required
def admin_cambiar_contrasena():
    if request.method == 'POST':
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validar que se proporcionaron todas las contraseñas
        if not current_password or not new_password or not confirm_password:
            flash('Todos los campos son requeridos', 'error')
            return render_template('admin/cambiar_contrasena.html')
        
        # Validar que las nuevas contraseñas coincidan
        if new_password != confirm_password:
            flash('Las nuevas contraseñas no coinciden', 'error')
            return render_template('admin/cambiar_contrasena.html')
        
        # Validar fortaleza de la nueva contraseña
        is_valid, error_msg = validate_password_strength(new_password)
        if not is_valid:
            flash(error_msg, 'error')
            return render_template('admin/cambiar_contrasena.html')
        
        # Verificar contraseña actual
        conn = get_db()
        admin = conn.execute(
            'SELECT * FROM admins WHERE id = ?', (session['admin_id'],)
        ).fetchone()
        
        if not admin or not check_password_hash(admin['password_hash'], current_password):
            flash('La contraseña actual es incorrecta', 'error')
            conn.close()
            return render_template('admin/cambiar_contrasena.html')
        
        # Actualizar contraseña
        new_password_hash = generate_password_hash(new_password)
        conn.execute(
            'UPDATE admins SET password_hash = ? WHERE id = ?',
            (new_password_hash, session['admin_id'])
        )
        conn.commit()
        conn.close()
        
        flash('Contraseña actualizada correctamente', 'success')
        return redirect(url_for('admin_dashboard'))
    
    return render_template('admin/cambiar_contrasena.html')

# Gestión de programas
@app.route('/admin/programas')
@login_required
def admin_programas():
    conn = get_db()
    programas = conn.execute('SELECT * FROM programas ORDER BY orden, id DESC').fetchall()
    conn.close()
    return render_template('admin/programas.html', programas=programas)

@app.route('/admin/programas/nuevo', methods=['GET', 'POST'])
@login_required
def admin_programa_nuevo():
    if request.method == 'POST':
        conn = get_db()
        conn.execute('''
            INSERT INTO programas (tipo, titulo, descripcion, modalidad, horario, 
                                 patrocinio, auspicio, email_contacto, texto_boton, orden, activo, 
                                 titulo_en, descripcion_en, tipo_en, modalidad_en, horario_en, texto_boton_en, patrocinio_en, auspicio_en)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            request.form.get('tipo'),
            request.form.get('titulo'),
            request.form.get('descripcion'),
            request.form.get('modalidad'),
            request.form.get('horario'),
            request.form.get('patrocinio'),
            request.form.get('auspicio'),
            request.form.get('email_contacto'),
            request.form.get('texto_boton', 'Postular'),
            int(request.form.get('orden', 0)),
            1 if request.form.get('activo') == 'on' else 0,
            request.form.get('titulo_en', '').strip() or None,
            request.form.get('descripcion_en', '').strip() or None,
            request.form.get('tipo_en', '').strip() or None,
            request.form.get('modalidad_en', '').strip() or None,
            request.form.get('horario_en', '').strip() or None,
            request.form.get('texto_boton_en', '').strip() or None,
            request.form.get('patrocinio_en', '').strip() or None,
            request.form.get('auspicio_en', '').strip() or None
        ))
        conn.commit()
        conn.close()
        flash('Programa creado correctamente', 'success')
        return redirect(url_for('admin_programas'))
    
    return render_template('admin/programa_form.html')

@app.route('/admin/programas/<int:programa_id>/editar', methods=['GET', 'POST'])
@login_required
def admin_programa_editar(programa_id):
    conn = get_db()
    
    if request.method == 'POST':
        conn.execute('''
            UPDATE programas 
            SET tipo=?, titulo=?, descripcion=?, modalidad=?, horario=?,
                patrocinio=?, auspicio=?, email_contacto=?, texto_boton=?, 
                orden=?, activo=?, titulo_en=?, descripcion_en=?, tipo_en=?, modalidad_en=?, 
                horario_en=?, texto_boton_en=?, patrocinio_en=?, auspicio_en=?, updated_at=CURRENT_TIMESTAMP
            WHERE id=?
        ''', (
            request.form.get('tipo'),
            request.form.get('titulo'),
            request.form.get('descripcion'),
            request.form.get('modalidad'),
            request.form.get('horario'),
            request.form.get('patrocinio'),
            request.form.get('auspicio'),
            request.form.get('email_contacto'),
            request.form.get('texto_boton', 'Postular'),
            int(request.form.get('orden', 0)),
            1 if request.form.get('activo') == 'on' else 0,
            request.form.get('titulo_en', '').strip() or None,
            request.form.get('descripcion_en', '').strip() or None,
            request.form.get('tipo_en', '').strip() or None,
            request.form.get('modalidad_en', '').strip() or None,
            request.form.get('horario_en', '').strip() or None,
            request.form.get('texto_boton_en', '').strip() or None,
            request.form.get('patrocinio_en', '').strip() or None,
            request.form.get('auspicio_en', '').strip() or None,
            programa_id
        ))
        conn.commit()
        conn.close()
        flash('Programa actualizado correctamente', 'success')
        return redirect(url_for('admin_programas'))
    
    programa = conn.execute('SELECT * FROM programas WHERE id = ?', (programa_id,)).fetchone()
    conn.close()
    
    if not programa:
        flash('Programa no encontrado', 'error')
        return redirect(url_for('admin_programas'))
    
    return render_template('admin/programa_form.html', programa=programa)

@app.route('/admin/programas/<int:programa_id>/eliminar', methods=['POST'])
@login_required
@csrf_required
def admin_programa_eliminar(programa_id):
    conn = get_db()
    conn.execute('DELETE FROM programas WHERE id = ?', (programa_id,))
    conn.commit()
    conn.close()
    flash('Programa eliminado', 'success')
    return redirect(url_for('admin_programas'))

# Gestión de testimonios
@app.route('/admin/testimonios')
@login_required
def admin_testimonios():
    conn = get_db()
    testimonios = conn.execute('SELECT * FROM testimonios ORDER BY orden, id DESC').fetchall()
    conn.close()
    return render_template('admin/testimonios.html', testimonios=testimonios)

@app.route('/admin/testimonios/nuevo', methods=['GET', 'POST'])
@login_required
def admin_testimonio_nuevo():
    if request.method == 'POST':
        conn = get_db()
        tags = request.form.get('tags', '')
        tags_json = json.dumps([tag.strip() for tag in tags.split(',') if tag.strip()])
        
        conn.execute('''
            INSERT INTO testimonios (titulo, contenido, autor, categoria, tags, imagen, orden, activo, titulo_en, contenido_en)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            request.form.get('titulo'),
            request.form.get('contenido'),
            request.form.get('autor'),
            request.form.get('categoria'),
            tags_json,
            request.form.get('imagen'),
            int(request.form.get('orden', 0)),
            1 if request.form.get('activo') == 'on' else 0,
            request.form.get('titulo_en', '').strip() or None,
            request.form.get('contenido_en', '').strip() or None
        ))
        conn.commit()
        conn.close()
        flash('Testimonio creado correctamente', 'success')
        return redirect(url_for('admin_testimonios'))
    
    return render_template('admin/testimonio_form.html')

@app.route('/admin/testimonios/<int:testimonio_id>/editar', methods=['GET', 'POST'])
@login_required
def admin_testimonio_editar(testimonio_id):
    conn = get_db()
    
    if request.method == 'POST':
        tags = request.form.get('tags', '')
        tags_json = json.dumps([tag.strip() for tag in tags.split(',') if tag.strip()])
        
        conn.execute('''
            UPDATE testimonios 
            SET titulo=?, contenido=?, autor=?, categoria=?, tags=?, 
                imagen=?, orden=?, activo=?, titulo_en=?, contenido_en=?, updated_at=CURRENT_TIMESTAMP
            WHERE id=?
        ''', (
            request.form.get('titulo'),
            request.form.get('contenido'),
            request.form.get('autor'),
            request.form.get('categoria'),
            tags_json,
            request.form.get('imagen'),
            int(request.form.get('orden', 0)),
            1 if request.form.get('activo') == 'on' else 0,
            request.form.get('titulo_en', '').strip() or None,
            request.form.get('contenido_en', '').strip() or None,
            testimonio_id
        ))
        conn.commit()
        conn.close()
        flash('Testimonio actualizado correctamente', 'success')
        return redirect(url_for('admin_testimonios'))
    
    testimonio = conn.execute('SELECT * FROM testimonios WHERE id = ?', (testimonio_id,)).fetchone()
    conn.close()
    
    if not testimonio:
        flash('Testimonio no encontrado', 'error')
        return redirect(url_for('admin_testimonios'))
    
    # Convertir tags JSON a string
    tags_list = json.loads(testimonio['tags']) if testimonio['tags'] else []
    testimonio_dict = dict(testimonio)
    testimonio_dict['tags'] = ', '.join(tags_list)
    
    return render_template('admin/testimonio_form.html', testimonio=testimonio_dict)

@app.route('/admin/testimonios/<int:testimonio_id>/eliminar', methods=['POST'])
@login_required
@csrf_required
def admin_testimonio_eliminar(testimonio_id):
    conn = get_db()
    conn.execute('DELETE FROM testimonios WHERE id = ?', (testimonio_id,))
    conn.commit()
    conn.close()
    flash('Testimonio eliminado', 'success')
    return redirect(url_for('admin_testimonios'))

# Gestor de imágenes
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/admin/upload', methods=['POST'])
@login_required
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No se envió ningún archivo'}), 400
    
    file = request.files['file']
    folder = request.form.get('folder', 'general')
    
    if file.filename == '':
        return jsonify({'error': 'No se seleccionó ningún archivo'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # Agregar timestamp para evitar conflictos
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
        filename = timestamp + filename
        
        upload_path = os.path.join(app.config['UPLOAD_FOLDER'], folder)
        os.makedirs(upload_path, exist_ok=True)
        
        filepath = os.path.join(upload_path, filename)
        file.save(filepath)
        
        # Retornar URL absoluta para que funcione desde cualquier dominio
        url = f'{request.host_url.rstrip("/")}/static/uploads/{folder}/{filename}'
        return jsonify({'url': url, 'filename': filename})
    
    return jsonify({'error': 'Tipo de archivo no permitido'}), 400

@app.route('/static/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# ============================================
# GESTIÓN DE NOTICIAS
# ============================================

@app.route('/admin/noticias')
@login_required
def admin_noticias():
    conn = get_db()
    noticias = conn.execute('SELECT * FROM noticias ORDER BY destacada DESC, fecha DESC, id DESC').fetchall()
    conn.close()
    return render_template('admin/noticias.html', noticias=noticias)

@app.route('/admin/noticias/nuevo', methods=['GET', 'POST'])
@login_required
def admin_noticia_nuevo():
    if request.method == 'POST':
        try:
            conn = get_db()
            # Asegurar que activa sea True por defecto si no se especifica
            activa = 1 if request.form.get('activa') == 'on' or request.form.get('activa') == '' else 0
            destacada = 1 if request.form.get('destacada') == 'on' else 0
            
            # Obtener valores de posición y zoom de la imagen
            imagen_zoom = float(request.form.get('imagen_zoom', 1.0) or 1.0)
            imagen_x = float(request.form.get('imagen_x', 0.0) or 0.0)
            imagen_y = float(request.form.get('imagen_y', 0.0) or 0.0)
            
            conn.execute('''
                INSERT INTO noticias (titulo, resumen, contenido, imagen, imagen_zoom, imagen_x, imagen_y, categoria, fecha, enlace_externo, orden, destacada, activa, titulo_en, resumen_en, contenido_en, categoria_en)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                request.form.get('titulo', '').strip(),
                request.form.get('resumen', '').strip(),
                request.form.get('contenido', '').strip(),
                request.form.get('imagen', '').strip(),
                imagen_zoom,
                imagen_x,
                imagen_y,
                request.form.get('categoria', '').strip(),
                request.form.get('fecha', '').strip(),
                request.form.get('enlace_externo', '').strip(),
                int(request.form.get('orden', 0) or 0),
                destacada,
                activa,
                request.form.get('titulo_en', '').strip() or None,
                request.form.get('resumen_en', '').strip() or None,
                request.form.get('contenido_en', '').strip() or None,
                request.form.get('categoria_en', '').strip() or None
            ))
            conn.commit()
            conn.close()
            flash('Noticia creada correctamente', 'success')
            return redirect(url_for('admin_noticias'))
        except Exception as e:
            flash(f'Error al crear noticia: {str(e)}', 'error')
            return render_template('admin/noticia_form.html')
    
    return render_template('admin/noticia_form.html')

@app.route('/admin/noticias/<int:noticia_id>/editar', methods=['GET', 'POST'])
@login_required
def admin_noticia_editar(noticia_id):
    conn = get_db()
    
    if request.method == 'POST':
        # Obtener valores de posición y zoom de la imagen
        imagen_zoom = float(request.form.get('imagen_zoom', 1.0) or 1.0)
        imagen_x = float(request.form.get('imagen_x', 0.0) or 0.0)
        imagen_y = float(request.form.get('imagen_y', 0.0) or 0.0)
        
        conn.execute('''
            UPDATE noticias 
            SET titulo=?, resumen=?, contenido=?, imagen=?, imagen_zoom=?, imagen_x=?, imagen_y=?, categoria=?, 
                fecha=?, enlace_externo=?, orden=?, destacada=?, activa=?, 
                titulo_en=?, resumen_en=?, contenido_en=?, categoria_en=?, updated_at=CURRENT_TIMESTAMP
            WHERE id=?
        ''', (
            request.form.get('titulo'),
            request.form.get('resumen'),
            request.form.get('contenido'),
            request.form.get('imagen'),
            imagen_zoom,
            imagen_x,
            imagen_y,
            request.form.get('categoria'),
            request.form.get('fecha'),
            request.form.get('enlace_externo'),
            int(request.form.get('orden', 0)),
            1 if request.form.get('destacada') == 'on' else 0,
            1 if request.form.get('activa') == 'on' else 0,
            request.form.get('titulo_en', '').strip() or None,
            request.form.get('resumen_en', '').strip() or None,
            request.form.get('contenido_en', '').strip() or None,
            request.form.get('categoria_en', '').strip() or None,
            noticia_id
        ))
        conn.commit()
        conn.close()
        flash('Noticia actualizada correctamente', 'success')
        return redirect(url_for('admin_noticias'))
    
    noticia = conn.execute('SELECT * FROM noticias WHERE id = ?', (noticia_id,)).fetchone()
    conn.close()
    
    if not noticia:
        flash('Noticia no encontrada', 'error')
        return redirect(url_for('admin_noticias'))
    
    return render_template('admin/noticia_form.html', noticia=noticia)

@app.route('/admin/noticias/<int:noticia_id>/eliminar', methods=['POST'])
@login_required
@csrf_required
def admin_noticia_eliminar(noticia_id):
    conn = get_db()
    conn.execute('DELETE FROM noticias WHERE id = ?', (noticia_id,))
    conn.commit()
    conn.close()
    flash('Noticia eliminada', 'success')
    return redirect(url_for('admin_noticias'))

# ============================================
# GESTIÓN DE ORGANIGRAMA
# ============================================

@app.route('/admin/organigrama')
@login_required
def admin_organigrama():
    conn = get_db()
    organigrama = conn.execute('''
        SELECT * FROM organigrama 
        ORDER BY seccion, orden, id
    ''').fetchall()
    conn.close()
    return render_template('admin/organigrama.html', organigrama=organigrama)

@app.route('/admin/organigrama/nuevo', methods=['GET', 'POST'])
@login_required
def admin_organigrama_nuevo():
    if request.method == 'POST':
        try:
            conn = get_db()
            activo = 1 if request.form.get('activo') == 'on' or request.form.get('activo') == '' else 0
            
            conn.execute('''
                INSERT INTO organigrama (seccion, subseccion, cargo, descripcion, orden, activo, subseccion_en, cargo_en, descripcion_en)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                request.form.get('seccion', '').strip(),
                request.form.get('subseccion', '').strip(),
                request.form.get('cargo', '').strip(),
                request.form.get('descripcion', '').strip(),
                int(request.form.get('orden', 0) or 0),
                activo,
                request.form.get('subseccion_en', '').strip() or None,
                request.form.get('cargo_en', '').strip() or None,
                request.form.get('descripcion_en', '').strip() or None
            ))
            conn.commit()
            conn.close()
            flash('Cargo creado correctamente', 'success')
            return redirect(url_for('admin_organigrama'))
        except Exception as e:
            flash(f'Error al crear cargo: {str(e)}', 'error')
            return render_template('admin/organigrama_form.html')
    
    return render_template('admin/organigrama_form.html')

@app.route('/admin/organigrama/<int:cargo_id>/editar', methods=['GET', 'POST'])
@login_required
def admin_organigrama_editar(cargo_id):
    conn = get_db()
    
    if request.method == 'POST':
        conn.execute('''
            UPDATE organigrama 
            SET seccion=?, subseccion=?, cargo=?, descripcion=?, orden=?, activo=?, 
                subseccion_en=?, cargo_en=?, descripcion_en=?, updated_at=CURRENT_TIMESTAMP
            WHERE id=?
        ''', (
            request.form.get('seccion'),
            request.form.get('subseccion'),
            request.form.get('cargo'),
            request.form.get('descripcion'),
            int(request.form.get('orden', 0)),
            1 if request.form.get('activo') == 'on' else 0,
            request.form.get('subseccion_en', '').strip() or None,
            request.form.get('cargo_en', '').strip() or None,
            request.form.get('descripcion_en', '').strip() or None,
            cargo_id
        ))
        conn.commit()
        conn.close()
        flash('Cargo actualizado correctamente', 'success')
        return redirect(url_for('admin_organigrama'))
    
    cargo = conn.execute('SELECT * FROM organigrama WHERE id = ?', (cargo_id,)).fetchone()
    conn.close()
    
    if not cargo:
        flash('Cargo no encontrado', 'error')
        return redirect(url_for('admin_organigrama'))
    
    return render_template('admin/organigrama_form.html', cargo=cargo)

@app.route('/admin/organigrama/<int:cargo_id>/eliminar', methods=['POST'])
@login_required
@csrf_required
def admin_organigrama_eliminar(cargo_id):
    conn = get_db()
    # Verificar si hay miembros asignados a este cargo
    miembros = conn.execute('SELECT COUNT(*) as count FROM equipo WHERE cargo_id = ?', (cargo_id,)).fetchone()
    if miembros['count'] > 0:
        flash('No se puede eliminar: hay miembros asignados a este cargo', 'error')
        conn.close()
        return redirect(url_for('admin_organigrama'))
    
    conn.execute('DELETE FROM organigrama WHERE id = ?', (cargo_id,))
    conn.commit()
    conn.close()
    flash('Cargo eliminado', 'success')
    return redirect(url_for('admin_organigrama'))

# ============================================
# GESTIÓN DE EQUIPO
# ============================================

@app.route('/admin/equipo')
@login_required
def admin_equipo():
    conn = get_db()
    equipo = conn.execute('''
        SELECT e.*, o.cargo as cargo_nombre, o.seccion, o.subseccion
        FROM equipo e
        LEFT JOIN organigrama o ON e.cargo_id = o.id
        ORDER BY e.orden, e.id
    ''').fetchall()
    conn.close()
    return render_template('admin/equipo.html', equipo=equipo)

@app.route('/admin/equipo/nuevo', methods=['GET', 'POST'])
@login_required
def admin_equipo_nuevo():
    if request.method == 'POST':
        conn = get_db()
        tags = request.form.get('tags', '')
        tags_json = json.dumps([tag.strip() for tag in tags.split(',') if tag.strip()])
        
        cargo_id = request.form.get('cargo_id')
        if cargo_id:
            cargo_id = int(cargo_id)
        else:
            cargo_id = None
        
        # Obtener el cargo del organigrama para mantener compatibilidad
        cargo_nombre = None
        if cargo_id:
            cargo_obj = conn.execute('SELECT cargo FROM organigrama WHERE id = ?', (cargo_id,)).fetchone()
            if cargo_obj:
                cargo_nombre = cargo_obj['cargo']
        
        # Procesar redes sociales (JSON)
        redes_sociales = {}
        if request.form.get('linkedin'):
            redes_sociales['linkedin'] = request.form.get('linkedin')
        redes_json = json.dumps(redes_sociales) if redes_sociales else None
        
        # Obtener valores de posición y zoom de la imagen
        imagen_zoom = float(request.form.get('imagen_zoom', 1.0) or 1.0)
        imagen_x = float(request.form.get('imagen_x', 0.0) or 0.0)
        imagen_y = float(request.form.get('imagen_y', 0.0) or 0.0)
        
        conn.execute('''
            INSERT INTO equipo (nombre, cargo_id, cargo, biografia, email, imagen, imagen_zoom, imagen_x, imagen_y, tags, redes_sociales, orden, activo, biografia_en)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            request.form.get('nombre'),
            cargo_id,
            cargo_nombre,
            request.form.get('biografia'),
            request.form.get('email'),
            request.form.get('imagen'),
            imagen_zoom,
            imagen_x,
            imagen_y,
            tags_json,
            redes_json,
            int(request.form.get('orden', 0)),
            1 if request.form.get('activo') == 'on' else 0,
            request.form.get('biografia_en', '').strip() or None
        ))
        conn.commit()
        conn.close()
        flash('Miembro del equipo creado correctamente', 'success')
        return redirect(url_for('admin_equipo'))
    
    # Obtener lista de cargos del organigrama
    conn = get_db()
    cargos = conn.execute('''
        SELECT * FROM organigrama 
        WHERE activo = 1 
        ORDER BY seccion, orden, cargo
    ''').fetchall()
    conn.close()
    return render_template('admin/equipo_form.html', cargos=cargos)

@app.route('/admin/equipo/<int:miembro_id>/editar', methods=['GET', 'POST'])
@login_required
def admin_equipo_editar(miembro_id):
    conn = get_db()
    
    if request.method == 'POST':
        tags = request.form.get('tags', '')
        tags_json = json.dumps([tag.strip() for tag in tags.split(',') if tag.strip()])
        
        cargo_id = request.form.get('cargo_id')
        if cargo_id:
            cargo_id = int(cargo_id)
        else:
            cargo_id = None
        
        # Obtener el cargo del organigrama para mantener compatibilidad
        cargo_nombre = None
        if cargo_id:
            cargo_obj = conn.execute('SELECT cargo FROM organigrama WHERE id = ?', (cargo_id,)).fetchone()
            if cargo_obj:
                cargo_nombre = cargo_obj['cargo']
        
        # Procesar redes sociales (JSON)
        redes_sociales = {}
        if request.form.get('linkedin'):
            redes_sociales['linkedin'] = request.form.get('linkedin')
        redes_json = json.dumps(redes_sociales) if redes_sociales else None
        
        # Obtener valores de posición y zoom de la imagen
        imagen_zoom = float(request.form.get('imagen_zoom', 1.0) or 1.0)
        imagen_x = float(request.form.get('imagen_x', 0.0) or 0.0)
        imagen_y = float(request.form.get('imagen_y', 0.0) or 0.0)
        
        conn.execute('''
            UPDATE equipo 
            SET nombre=?, cargo_id=?, cargo=?, biografia=?, email=?, imagen=?, 
                imagen_zoom=?, imagen_x=?, imagen_y=?, tags=?, redes_sociales=?, orden=?, activo=?, 
                biografia_en=?, updated_at=CURRENT_TIMESTAMP
            WHERE id=?
        ''', (
            request.form.get('nombre'),
            cargo_id,
            cargo_nombre,
            request.form.get('biografia'),
            request.form.get('email'),
            request.form.get('imagen'),
            imagen_zoom,
            imagen_x,
            imagen_y,
            tags_json,
            redes_json,
            int(request.form.get('orden', 0)),
            1 if request.form.get('activo') == 'on' else 0,
            request.form.get('biografia_en', '').strip() or None,
            miembro_id
        ))
        conn.commit()
        conn.close()
        flash('Miembro del equipo actualizado correctamente', 'success')
        return redirect(url_for('admin_equipo'))
    
    miembro = conn.execute('SELECT * FROM equipo WHERE id = ?', (miembro_id,)).fetchone()
    cargos = conn.execute('''
        SELECT * FROM organigrama 
        WHERE activo = 1 
        ORDER BY seccion, orden, cargo
    ''').fetchall()
    conn.close()
    
    if not miembro:
        flash('Miembro no encontrado', 'error')
        return redirect(url_for('admin_equipo'))
    
    # Convertir tags JSON a string
    tags_list = json.loads(miembro['tags']) if miembro['tags'] else []
    miembro_dict = dict(miembro)
    miembro_dict['tags'] = ', '.join(tags_list)
    
    return render_template('admin/equipo_form.html', miembro=miembro_dict, cargos=cargos)

@app.route('/admin/equipo/<int:miembro_id>/eliminar', methods=['POST'])
@login_required
@csrf_required
def admin_equipo_eliminar(miembro_id):
    conn = get_db()
    conn.execute('DELETE FROM equipo WHERE id = ?', (miembro_id,))
    conn.commit()
    conn.close()
    flash('Miembro eliminado', 'success')
    return redirect(url_for('admin_equipo'))

# ============================================
# GESTIÓN DE CONVENIOS - ELIMINADA DEL PANEL DE ADMINISTRACIÓN
# La tabla de convenios se mantiene en la BD para uso futuro si es necesario
# ============================================
# GESTIÓN DE CLIENTES/LOGOS
# ============================================

@app.route('/admin/clientes')
@login_required
def admin_clientes():
    """Redirige a la gestión unificada de clientes/aliados"""
    return redirect(url_for('admin_aliados_casa_omsa'))

@app.route('/admin/aliados-casa-omsa')
@login_required
def admin_aliados_casa_omsa():
    conn = get_db()
    aliados = conn.execute('SELECT * FROM clientes ORDER BY orden, id').fetchall()
    conn.close()
    return render_template('admin/aliados_casa_omsa.html', aliados=aliados)

@app.route('/admin/clientes/nuevo', methods=['GET', 'POST'])
@login_required
def admin_cliente_nuevo():
    if request.method == 'POST':
        conn = get_db()
        conn.execute('''
            INSERT INTO clientes (nombre, nombre_en, logo, enlace, categoria, mostrar_en_index, mostrar_en_casa_omsa, orden, activo)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            request.form.get('nombre'),
            request.form.get('nombre_en', '').strip() or None,
            request.form.get('logo'),
            request.form.get('enlace'),
            request.form.get('categoria'),
            1 if request.form.get('mostrar_en_index') == 'on' else 0,
            1 if request.form.get('mostrar_en_casa_omsa') == 'on' else 0,
            int(request.form.get('orden', 0)),
            1 if request.form.get('activo') == 'on' else 0
        ))
        conn.commit()
        conn.close()
        flash('Cliente/Aliado creado correctamente', 'success')
        return redirect(url_for('admin_clientes'))
    
    return render_template('admin/cliente_form.html')

@app.route('/admin/clientes/<int:cliente_id>/editar', methods=['GET', 'POST'])
@login_required
def admin_cliente_editar(cliente_id):
    conn = get_db()
    
    if request.method == 'POST':
        conn.execute('''
            UPDATE clientes 
            SET nombre=?, nombre_en=?, logo=?, enlace=?, categoria=?, mostrar_en_index=?, mostrar_en_casa_omsa=?, orden=?, activo=?, updated_at=CURRENT_TIMESTAMP
            WHERE id=?
        ''', (
            request.form.get('nombre'),
            request.form.get('nombre_en', '').strip() or None,
            request.form.get('logo'),
            request.form.get('enlace'),
            request.form.get('categoria'),
            1 if request.form.get('mostrar_en_index') == 'on' else 0,
            1 if request.form.get('mostrar_en_casa_omsa') == 'on' else 0,
            int(request.form.get('orden', 0)),
            1 if request.form.get('activo') == 'on' else 0,
            cliente_id
        ))
        conn.commit()
        conn.close()
        flash('Cliente/Aliado actualizado correctamente', 'success')
        return redirect(url_for('admin_clientes'))
    
    cliente = conn.execute('SELECT * FROM clientes WHERE id = ?', (cliente_id,)).fetchone()
    conn.close()
    
    if not cliente:
        flash('Cliente no encontrado', 'error')
        return redirect(url_for('admin_clientes'))
    
    return render_template('admin/cliente_form.html', cliente=cliente)

@app.route('/admin/clientes/<int:cliente_id>/eliminar', methods=['POST'])
@login_required
@csrf_required
def admin_cliente_eliminar(cliente_id):
    conn = get_db()
    conn.execute('DELETE FROM clientes WHERE id = ?', (cliente_id,))
    conn.commit()
    conn.close()
    flash('Cliente eliminado', 'success')
    return redirect(url_for('admin_clientes'))

# ============================================
# GESTIÓN DE PROYECTOS DESTACADOS
# ============================================

@app.route('/admin/proyectos')
@login_required
def admin_proyectos():
    conn = get_db()
    proyectos = conn.execute('SELECT * FROM proyectos ORDER BY orden, id').fetchall()
    conn.close()
    return render_template('admin/proyectos.html', proyectos=proyectos)

@app.route('/admin/proyectos/nuevo', methods=['GET', 'POST'])
@login_required
def admin_proyecto_nuevo():
    if request.method == 'POST':
        conn = get_db()
        conn.execute('''
            INSERT INTO proyectos (titulo, descripcion, tipo, enlace, orden, activo, titulo_en, descripcion_en, tipo_en)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            request.form.get('titulo'),
            request.form.get('descripcion'),
            request.form.get('tipo'),
            request.form.get('enlace'),
            int(request.form.get('orden', 0)),
            1 if request.form.get('activo') == 'on' else 0,
            request.form.get('titulo_en', '').strip() or None,
            request.form.get('descripcion_en', '').strip() or None,
            request.form.get('tipo_en', '').strip() or None
        ))
        conn.commit()
        conn.close()
        flash('Proyecto creado correctamente', 'success')
        return redirect(url_for('admin_proyectos'))
    
    return render_template('admin/proyecto_form.html')

@app.route('/admin/proyectos/<int:proyecto_id>/editar', methods=['GET', 'POST'])
@login_required
def admin_proyecto_editar(proyecto_id):
    conn = get_db()
    
    if request.method == 'POST':
        conn.execute('''
            UPDATE proyectos 
            SET titulo=?, descripcion=?, tipo=?, enlace=?, orden=?, activo=?, 
                titulo_en=?, descripcion_en=?, tipo_en=?, updated_at=CURRENT_TIMESTAMP
            WHERE id=?
        ''', (
            request.form.get('titulo'),
            request.form.get('descripcion'),
            request.form.get('tipo'),
            request.form.get('enlace'),
            int(request.form.get('orden', 0)),
            1 if request.form.get('activo') == 'on' else 0,
            request.form.get('titulo_en', '').strip() or None,
            request.form.get('descripcion_en', '').strip() or None,
            request.form.get('tipo_en', '').strip() or None,
            proyecto_id
        ))
        conn.commit()
        conn.close()
        flash('Proyecto actualizado correctamente', 'success')
        return redirect(url_for('admin_proyectos'))
    
    proyecto = conn.execute('SELECT * FROM proyectos WHERE id = ?', (proyecto_id,)).fetchone()
    conn.close()
    
    if not proyecto:
        flash('Proyecto no encontrado', 'error')
        return redirect(url_for('admin_proyectos'))
    
    return render_template('admin/proyecto_form.html', proyecto=proyecto)

@app.route('/admin/proyectos/<int:proyecto_id>/eliminar', methods=['POST'])
@login_required
@csrf_required
def admin_proyecto_eliminar(proyecto_id):
    conn = get_db()
    conn.execute('DELETE FROM proyectos WHERE id = ?', (proyecto_id,))
    conn.commit()
    conn.close()
    flash('Proyecto eliminado', 'success')
    return redirect(url_for('admin_proyectos'))

# ============================================
# GESTIÓN DE PUBLICACIONES CIENTÍFICAS
# ============================================

@app.route('/admin/publicaciones')
@login_required
def admin_publicaciones():
    conn = get_db()
    publicaciones = conn.execute('SELECT * FROM publicaciones ORDER BY orden, id').fetchall()
    conn.close()
    return render_template('admin/publicaciones.html', publicaciones=publicaciones)

@app.route('/admin/publicaciones/nuevo', methods=['GET', 'POST'])
@login_required
def admin_publicacion_nuevo():
    if request.method == 'POST':
        conn = get_db()
        tags = request.form.get('tags', '')
        tags_json = json.dumps([tag.strip() for tag in tags.split(',') if tag.strip()])
        
        conn.execute('''
            INSERT INTO publicaciones (titulo, descripcion, revista, año, enlace, tags, orden, activo, titulo_en, descripcion_en)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            request.form.get('titulo'),
            request.form.get('descripcion'),
            request.form.get('revista'),
            request.form.get('año'),
            request.form.get('enlace'),
            tags_json,
            int(request.form.get('orden', 0)),
            1 if request.form.get('activo') == 'on' else 0,
            request.form.get('titulo_en', '').strip() or None,
            request.form.get('descripcion_en', '').strip() or None
        ))
        conn.commit()
        conn.close()
        flash('Publicación creada correctamente', 'success')
        return redirect(url_for('admin_publicaciones'))
    
    return render_template('admin/publicacion_form.html')

@app.route('/admin/publicaciones/<int:publicacion_id>/editar', methods=['GET', 'POST'])
@login_required
def admin_publicacion_editar(publicacion_id):
    conn = get_db()
    
    if request.method == 'POST':
        tags = request.form.get('tags', '')
        tags_json = json.dumps([tag.strip() for tag in tags.split(',') if tag.strip()])
        
        conn.execute('''
            UPDATE publicaciones 
            SET titulo=?, descripcion=?, revista=?, año=?, enlace=?, tags=?, orden=?, activo=?, 
                titulo_en=?, descripcion_en=?, updated_at=CURRENT_TIMESTAMP
            WHERE id=?
        ''', (
            request.form.get('titulo'),
            request.form.get('descripcion'),
            request.form.get('revista'),
            request.form.get('año'),
            request.form.get('enlace'),
            tags_json,
            int(request.form.get('orden', 0)),
            1 if request.form.get('activo') == 'on' else 0,
            request.form.get('titulo_en', '').strip() or None,
            request.form.get('descripcion_en', '').strip() or None,
            publicacion_id
        ))
        conn.commit()
        conn.close()
        flash('Publicación actualizada correctamente', 'success')
        return redirect(url_for('admin_publicaciones'))
    
    publicacion = conn.execute('SELECT * FROM publicaciones WHERE id = ?', (publicacion_id,)).fetchone()
    conn.close()
    
    if not publicacion:
        flash('Publicación no encontrada', 'error')
        return redirect(url_for('admin_publicaciones'))
    
    return render_template('admin/publicacion_form.html', publicacion=publicacion)

@app.route('/admin/publicaciones/<int:publicacion_id>/eliminar', methods=['POST'])
@login_required
@csrf_required
def admin_publicacion_eliminar(publicacion_id):
    conn = get_db()
    conn.execute('DELETE FROM publicaciones WHERE id = ?', (publicacion_id,))
    conn.commit()
    conn.close()
    flash('Publicación eliminada', 'success')
    return redirect(url_for('admin_publicaciones'))

# ============================================
# GESTIÓN DE ESTADÍSTICAS
# ============================================

@app.route('/admin/estadisticas')
@login_required
def admin_estadisticas():
    conn = get_db()
    estadisticas = conn.execute('SELECT * FROM estadisticas ORDER BY orden, id').fetchall()
    conn.close()
    return render_template('admin/estadisticas.html', estadisticas=estadisticas)

@app.route('/admin/estadisticas/nuevo', methods=['GET', 'POST'])
@login_required
def admin_estadistica_nuevo():
    if request.method == 'POST':
        try:
            conn = get_db()
            # Asegurar que activo sea True por defecto si no se especifica
            activo = 1 if request.form.get('activo') == 'on' or request.form.get('activo') == '' else 0
            
            conn.execute('''
                INSERT INTO estadisticas (numero, sufijo, etiqueta, etiqueta_en, orden, activo)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                int(request.form.get('numero', 0) or 0),
                request.form.get('sufijo', '').strip(),
                request.form.get('etiqueta', '').strip(),
                request.form.get('etiqueta_en', '').strip() or None,
                int(request.form.get('orden', 0) or 0),
                activo
            ))
            conn.commit()
            conn.close()
            flash('Estadística creada correctamente', 'success')
            return redirect(url_for('admin_estadisticas'))
        except Exception as e:
            flash(f'Error al crear estadística: {str(e)}', 'error')
            return render_template('admin/estadistica_form.html')
    
    return render_template('admin/estadistica_form.html')

@app.route('/admin/estadisticas/<int:estadistica_id>/editar', methods=['GET', 'POST'])
@login_required
def admin_estadistica_editar(estadistica_id):
    conn = get_db()
    
    if request.method == 'POST':
        conn.execute('''
            UPDATE estadisticas 
            SET numero=?, sufijo=?, etiqueta=?, etiqueta_en=?, orden=?, activo=?, updated_at=CURRENT_TIMESTAMP
            WHERE id=?
        ''', (
            int(request.form.get('numero', 0)),
            request.form.get('sufijo', ''),
            request.form.get('etiqueta'),
            request.form.get('etiqueta_en', '').strip() or None,
            int(request.form.get('orden', 0)),
            1 if request.form.get('activo') == 'on' else 0,
            estadistica_id
        ))
        conn.commit()
        conn.close()
        flash('Estadística actualizada correctamente', 'success')
        return redirect(url_for('admin_estadisticas'))
    
    estadistica = conn.execute('SELECT * FROM estadisticas WHERE id = ?', (estadistica_id,)).fetchone()
    conn.close()
    
    if not estadistica:
        flash('Estadística no encontrada', 'error')
        return redirect(url_for('admin_estadisticas'))
    
    return render_template('admin/estadistica_form.html', estadistica=estadistica)

@app.route('/admin/estadisticas/<int:estadistica_id>/eliminar', methods=['POST'])
@login_required
@csrf_required
def admin_estadistica_eliminar(estadistica_id):
    conn = get_db()
    conn.execute('DELETE FROM estadisticas WHERE id = ?', (estadistica_id,))
    conn.commit()
    conn.close()
    flash('Estadística eliminada', 'success')
    return redirect(url_for('admin_estadisticas'))

# ============================================
# GESTIÓN DE TARJETAS DESTACADAS
# ============================================

@app.route('/admin/tarjetas-destacadas')
@login_required
def admin_tarjetas_destacadas():
    conn = get_db()
    tarjetas = conn.execute('SELECT * FROM tarjetas_destacadas ORDER BY pagina, orden, id').fetchall()
    conn.close()
    return render_template('admin/tarjetas_destacadas.html', tarjetas=tarjetas)

@app.route('/admin/tarjetas-destacadas/nuevo', methods=['GET', 'POST'])
@login_required
def admin_tarjeta_destacada_nuevo():
    if request.method == 'POST':
        try:
            conn = get_db()
            # El checkbox envía 'on' si está marcado, sino no envía nada
            activo = 1 if request.form.get('activo') == 'on' else 1  # Por defecto activo
            conn.execute('''
                INSERT INTO tarjetas_destacadas (pagina, titulo, titulo_en, contenido, contenido_en, enlace, texto_enlace, texto_enlace_en, orden, activo)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                request.form.get('pagina', '').strip(),
                request.form.get('titulo', '').strip(),
                request.form.get('titulo_en', '').strip() or None,
                request.form.get('contenido', '').strip(),
                request.form.get('contenido_en', '').strip() or None,
                request.form.get('enlace', '').strip() or None,
                request.form.get('texto_enlace', '').strip() or None,
                request.form.get('texto_enlace_en', '').strip() or None,
                int(request.form.get('orden', 0) or 0),
                activo
            ))
            conn.commit()
            conn.close()
            flash('Tarjeta destacada creada correctamente', 'success')
            return redirect(url_for('admin_tarjetas_destacadas'))
        except Exception as e:
            flash(f'Error al crear tarjeta destacada: {str(e)}', 'error')
            return render_template('admin/tarjeta_destacada_form.html')
    
    return render_template('admin/tarjeta_destacada_form.html')

@app.route('/admin/tarjetas-destacadas/<int:tarjeta_id>/editar', methods=['GET', 'POST'])
@login_required
def admin_tarjeta_destacada_editar(tarjeta_id):
    conn = get_db()
    
    if request.method == 'POST':
        conn.execute('''
            UPDATE tarjetas_destacadas 
            SET pagina=?, titulo=?, titulo_en=?, contenido=?, contenido_en=?, enlace=?, texto_enlace=?, texto_enlace_en=?, orden=?, activo=?, updated_at=CURRENT_TIMESTAMP
            WHERE id=?
        ''', (
            request.form.get('pagina', '').strip(),
            request.form.get('titulo', '').strip(),
            request.form.get('titulo_en', '').strip() or None,
            request.form.get('contenido', '').strip(),
            request.form.get('contenido_en', '').strip() or None,
            request.form.get('enlace', '').strip() or None,
            request.form.get('texto_enlace', '').strip() or None,
            request.form.get('texto_enlace_en', '').strip() or None,
            int(request.form.get('orden', 0) or 0),
            1 if request.form.get('activo') == 'on' else 0,
            tarjeta_id
        ))
        conn.commit()
        conn.close()
        flash('Tarjeta destacada actualizada correctamente', 'success')
        return redirect(url_for('admin_tarjetas_destacadas'))
    
    tarjeta = conn.execute('SELECT * FROM tarjetas_destacadas WHERE id = ?', (tarjeta_id,)).fetchone()
    conn.close()
    
    if not tarjeta:
        flash('Tarjeta destacada no encontrada', 'error')
        return redirect(url_for('admin_tarjetas_destacadas'))
    
    return render_template('admin/tarjeta_destacada_form.html', tarjeta=tarjeta)

@app.route('/admin/tarjetas-destacadas/<int:tarjeta_id>/eliminar', methods=['POST'])
@login_required
@csrf_required
def admin_tarjeta_destacada_eliminar(tarjeta_id):
    conn = get_db()
    conn.execute('DELETE FROM tarjetas_destacadas WHERE id = ?', (tarjeta_id,))
    conn.commit()
    conn.close()
    flash('Tarjeta destacada eliminada', 'success')
    return redirect(url_for('admin_tarjetas_destacadas'))

# ============================================
# GESTIÓN DE EVENTOS
# ============================================

@app.route('/admin/eventos')
@login_required
def admin_eventos():
    conn = get_db()
    eventos = conn.execute('SELECT * FROM eventos ORDER BY orden, id').fetchall()
    conn.close()
    return render_template('admin/eventos.html', eventos=eventos)

@app.route('/admin/eventos/nuevo', methods=['GET', 'POST'])
@login_required
def admin_evento_nuevo():
    if request.method == 'POST':
        try:
            conn = get_db()
            activo = 1 if request.form.get('activo') == 'on' or request.form.get('activo') == '' else 0
            
            conn.execute('''
                INSERT INTO eventos (titulo, fecha, meta, descripcion, enlace, texto_boton, orden, activo, titulo_en, descripcion_en, meta_en, texto_boton_en)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                request.form.get('titulo', '').strip(),
                request.form.get('fecha', '').strip(),
                request.form.get('meta', '').strip(),
                request.form.get('descripcion', '').strip(),
                request.form.get('enlace', '').strip(),
                request.form.get('texto_boton', 'Ver más').strip(),
                int(request.form.get('orden', 0) or 0),
                activo,
                request.form.get('titulo_en', '').strip() or None,
                request.form.get('descripcion_en', '').strip() or None,
                request.form.get('meta_en', '').strip() or None,
                request.form.get('texto_boton_en', '').strip() or None
            ))
            conn.commit()
            conn.close()
            flash('Evento creado correctamente', 'success')
            return redirect(url_for('admin_eventos'))
        except Exception as e:
            flash(f'Error al crear evento: {str(e)}', 'error')
            return render_template('admin/evento_form.html')
    
    return render_template('admin/evento_form.html')

@app.route('/admin/eventos/<int:evento_id>/editar', methods=['GET', 'POST'])
@login_required
def admin_evento_editar(evento_id):
    conn = get_db()
    
    if request.method == 'POST':
        conn.execute('''
            UPDATE eventos 
            SET titulo=?, fecha=?, meta=?, descripcion=?, enlace=?, texto_boton=?, orden=?, activo=?, 
                titulo_en=?, descripcion_en=?, meta_en=?, texto_boton_en=?, updated_at=CURRENT_TIMESTAMP
            WHERE id=?
        ''', (
            request.form.get('titulo'),
            request.form.get('fecha'),
            request.form.get('meta'),
            request.form.get('descripcion'),
            request.form.get('enlace'),
            request.form.get('texto_boton', 'Ver más'),
            int(request.form.get('orden', 0)),
            1 if request.form.get('activo') == 'on' else 0,
            request.form.get('titulo_en', '').strip() or None,
            request.form.get('descripcion_en', '').strip() or None,
            request.form.get('meta_en', '').strip() or None,
            request.form.get('texto_boton_en', '').strip() or None,
            evento_id
        ))
        conn.commit()
        conn.close()
        flash('Evento actualizado correctamente', 'success')
        return redirect(url_for('admin_eventos'))
    
    evento = conn.execute('SELECT * FROM eventos WHERE id = ?', (evento_id,)).fetchone()
    conn.close()
    
    if not evento:
        flash('Evento no encontrado', 'error')
        return redirect(url_for('admin_eventos'))
    
    return render_template('admin/evento_form.html', evento=evento)

@app.route('/admin/eventos/<int:evento_id>/eliminar', methods=['POST'])
@login_required
@csrf_required
def admin_evento_eliminar(evento_id):
    conn = get_db()
    conn.execute('DELETE FROM eventos WHERE id = ?', (evento_id,))
    conn.commit()
    conn.close()
    flash('Evento eliminado', 'success')
    return redirect(url_for('admin_eventos'))

# Inicializar base de datos automáticamente (también para Gunicorn)
# Solo inicializar si no existe la base de datos o si está vacía
try:
    conn = get_db()
    # Intentar consultar una tabla para verificar si la BD está inicializada
    conn.execute('SELECT 1 FROM admins LIMIT 1').fetchone()
    conn.close()
except (sqlite3.OperationalError, sqlite3.DatabaseError):
    # La base de datos no existe o no está inicializada
    init_db()
    print("✅ Base de datos inicializada automáticamente")

if __name__ == '__main__':
    print("✅ Base de datos inicializada")
    print("🌐 Servidor iniciado en http://localhost:5000")
    print("🔐 Panel de administración: http://localhost:5000/admin/login")
    print("   Usuario: admin")
    print("   Contraseña: admin123")
    app.run(debug=True, host='0.0.0.0', port=5000)

