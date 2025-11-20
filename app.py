"""
Backend Flask para panel de administración de FARMAVET Web
Permite editar contenido sin tocar código HTML
"""

from flask import Flask, render_template, request, redirect, url_for, flash, session, send_from_directory, send_file, jsonify
from flask_babel import Babel, gettext as _, get_locale, lazy_gettext as _l
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from urllib.parse import unquote
import sqlite3
import os
import json
import time
import secrets
from datetime import datetime, timedelta
from functools import wraps
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
import requests
import re

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

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
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size (para videos)
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg', 'pdf', 'mp4', 'webm', 'mov'}

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
os.makedirs('static/uploads/certificados', exist_ok=True)
os.makedirs('static/uploads/hero-media', exist_ok=True)
os.makedirs('static/uploads/galeria', exist_ok=True)
os.makedirs('static/uploads/infografias', exist_ok=True)
os.makedirs('static/uploads/proyectos', exist_ok=True)

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
    
    # Campos adicionales para proyectos FONDECYT/FONDEF
    try:
        conn.execute('ALTER TABLE proyectos ADD COLUMN codigo_proyecto TEXT')
    except:
        pass
    try:
        conn.execute('ALTER TABLE proyectos ADD COLUMN año_inicio INTEGER')
    except:
        pass
    try:
        conn.execute('ALTER TABLE proyectos ADD COLUMN año_fin INTEGER')
    except:
        pass
    try:
        conn.execute('ALTER TABLE proyectos ADD COLUMN investigadores TEXT')
    except:
        pass
    try:
        conn.execute('ALTER TABLE proyectos ADD COLUMN presupuesto TEXT')
    except:
        pass
    try:
        conn.execute('ALTER TABLE proyectos ADD COLUMN resultados TEXT')
    except:
        pass
    try:
        conn.execute('ALTER TABLE proyectos ADD COLUMN estado TEXT DEFAULT "en_curso"')
    except:
        pass
    try:
        conn.execute('ALTER TABLE proyectos ADD COLUMN financiador TEXT')
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
    
    # Campos adicionales para publicaciones científicas
    try:
        conn.execute('ALTER TABLE publicaciones ADD COLUMN doi TEXT')
    except:
        pass
    try:
        conn.execute('ALTER TABLE publicaciones ADD COLUMN autores TEXT')
    except:
        pass
    try:
        conn.execute('ALTER TABLE publicaciones ADD COLUMN volumen TEXT')
    except:
        pass
    try:
        conn.execute('ALTER TABLE publicaciones ADD COLUMN numero TEXT')
    except:
        pass
    try:
        conn.execute('ALTER TABLE publicaciones ADD COLUMN paginas TEXT')
    except:
        pass
    try:
        conn.execute('ALTER TABLE publicaciones ADD COLUMN tipo_publicacion TEXT')
    except:
        pass
    try:
        conn.execute('ALTER TABLE publicaciones ADD COLUMN factor_impacto TEXT')
    except:
        pass
    try:
        conn.execute('ALTER TABLE publicaciones ADD COLUMN base_datos TEXT')
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
            biografia_en TEXT,
            email TEXT,
            imagen TEXT,
            imagen_zoom REAL DEFAULT 1.0,  -- Zoom de la imagen (0.5 a 5.0)
            imagen_x REAL DEFAULT 0.0,  -- Posición X de la imagen
            imagen_y REAL DEFAULT 0.0,  -- Posición Y de la imagen
            tags TEXT,  -- JSON array de tags
            redes_sociales TEXT,  -- JSON object con redes sociales
            orden INTEGER DEFAULT 0,
            activo INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (cargo_id) REFERENCES organigrama(id)
        )
    ''')
    # Migración: agregar campos de traducción si no existen (para bases de datos existentes)
    try:
        conn.execute('ALTER TABLE equipo ADD COLUMN biografia_en TEXT')
    except:
        pass  # La columna ya existe
    
    # Tabla de configuración de redes sociales (gratuito)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS configuracion_redes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            instagram_username TEXT,  -- Usuario de Instagram (sin @)
            linkedin_company_id TEXT,  -- ID numérico de la página de LinkedIn
            linkedin_page_url TEXT,  -- URL completa de la página de LinkedIn (alternativa)
            activo INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
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
    
    # Agregar campo para referenciar imágenes de la galería
    try:
        conn.execute('ALTER TABLE hero_media ADD COLUMN usar_galeria INTEGER DEFAULT 0')
    except:
        pass
    try:
        conn.execute('ALTER TABLE hero_media ADD COLUMN categoria_galeria TEXT')
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
            destacada INTEGER DEFAULT 0,
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
    except sqlite3.OperationalError:
        pass  # La columna ya existe
    try:
        conn.execute('ALTER TABLE eventos ADD COLUMN destacada INTEGER DEFAULT 0')
    except sqlite3.OperationalError:
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
    
    # Tabla de correos de destino para formulario de contacto
    conn.execute('''
        CREATE TABLE IF NOT EXISTS correos_contacto (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo_consulta TEXT NOT NULL,  -- 'analisis', 'servicios', 'capacitacion', 'investigacion', 'otra'
            email TEXT NOT NULL,
            activo INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(tipo_consulta, email)
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
    
    # Agregar campo imagen a proyectos si no existe
    try:
        conn.execute('ALTER TABLE proyectos ADD COLUMN imagen TEXT')
    except:
        pass
    
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
    
    # Tabla de preguntas frecuentes (FAQ)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS faq (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pregunta TEXT NOT NULL,
            pregunta_en TEXT,
            respuesta TEXT NOT NULL,
            respuesta_en TEXT,
            categoria TEXT,  -- 'servicios', 'proceso', 'tiempos', 'costos', 'tecnicas', 'certificaciones'
            orden INTEGER DEFAULT 0,
            activo INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabla de galería de imágenes del laboratorio e infografías
    conn.execute('''
        CREATE TABLE IF NOT EXISTS galeria_imagenes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            descripcion TEXT,
            archivo TEXT NOT NULL,  -- Nombre del archivo
            categoria TEXT,  -- 'laboratorio', 'equipamiento', 'personal', 'proceso', 'infografia', 'instalaciones'
            tipo TEXT DEFAULT 'imagen',  -- 'imagen' o 'infografia'
            orden INTEGER DEFAULT 0,
            activo INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Agregar campo pagina a galeria_imagenes si no existe
    try:
        conn.execute('ALTER TABLE galeria_imagenes ADD COLUMN pagina TEXT')
    except:
        pass
    
    # Agregar campo es_video a galeria_imagenes si no existe
    try:
        conn.execute('ALTER TABLE galeria_imagenes ADD COLUMN es_video INTEGER DEFAULT 0')
    except:
        pass
    
    # Tabla de certificados y reconocimientos
    conn.execute('''
        CREATE TABLE IF NOT EXISTS certificados (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            titulo_en TEXT,
            organismo TEXT NOT NULL,  -- 'ISO', 'OMSA', 'SAG', 'SERNAPESCA', 'INN', etc.
            numero_certificado TEXT,
            fecha_emision TEXT,
            fecha_vencimiento TEXT,
            imagen TEXT,  -- Ruta a imagen del certificado
            enlace_externo TEXT,  -- URL a certificado oficial si existe
            descripcion TEXT,
            descripcion_en TEXT,
            orden INTEGER DEFAULT 0,
            activo INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabla de metodologías analíticas
    conn.execute('''
        CREATE TABLE IF NOT EXISTS metodologias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT,  -- Código interno de la metodología
            nombre TEXT NOT NULL,  -- Nombre de la metodología
            nombre_en TEXT,
            categoria TEXT NOT NULL,  -- 'residuos', 'contaminantes', 'microbiologia', 'otros'
            analito TEXT NOT NULL,  -- Sustancia que se analiza
            analito_en TEXT,
            matriz TEXT NOT NULL,  -- Tipo de muestra (carne, leche, pescado, etc.)
            matriz_en TEXT,
            tecnica TEXT,  -- LC-MS/MS, GC-MS, HPLC, etc.
            tecnica_en TEXT,
            limite_deteccion TEXT,  -- LOD
            limite_cuantificacion TEXT,  -- LOQ
            norma_referencia TEXT,  -- Norma o guía que sigue
            vigencia TEXT,  -- Fecha de vigencia de la acreditación
            acreditada INTEGER DEFAULT 1,  -- Si está acreditada ISO 17025
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
            flash('Por favor, inicia sesión para acceder a esta sección', 'warning')
            # Guardar la URL a la que quería acceder para redirigir después del login
            if request.path:
                session['next_url'] = request.path
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
    # Decodificar espacios y caracteres especiales en el nombre del archivo
    decoded_filename = unquote(filename)
    
    # Intentar primero desde static/logos (recomendado)
    static_logos_dir = os.path.join('static', 'logos')
    static_logo_path = os.path.join(static_logos_dir, decoded_filename)
    
    if os.path.exists(static_logo_path) and os.path.isfile(static_logo_path):
        return send_from_directory(static_logos_dir, decoded_filename)
    
    # Si no está en static, buscar en la carpeta logos raíz (legacy)
    base_dir = os.path.dirname(os.path.abspath(__file__))
    logos_dir = os.path.join(base_dir, 'logos')
    logo_path = os.path.join(logos_dir, decoded_filename)
    
    if os.path.exists(logo_path) and os.path.isfile(logo_path):
        return send_from_directory(logos_dir, decoded_filename)
    
    # Si no existe, intentar buscar el archivo real (puede tener espacios codificados diferente)
    import glob
    base_name = os.path.basename(decoded_filename)
    
    # Buscar en static/logos primero
    static_patterns = [
        os.path.join(static_logos_dir, base_name),
        os.path.join(static_logos_dir, base_name.replace('_', ' ')),
        os.path.join(static_logos_dir, base_name.replace(' ', '_')),
        os.path.join(static_logos_dir, base_name.replace('_', '*')),
        os.path.join(static_logos_dir, base_name.replace(' ', '*')),
    ]
    
    for pattern in static_patterns:
        matches = glob.glob(pattern)
        if matches:
            actual_filename = os.path.basename(matches[0])
            return send_from_directory(static_logos_dir, actual_filename)
    
    # Buscar en logos raíz (legacy)
    patterns = [
        os.path.join(logos_dir, base_name),
        os.path.join(logos_dir, base_name.replace('_', ' ')),
        os.path.join(logos_dir, base_name.replace(' ', '_')),
        os.path.join(logos_dir, base_name.replace('_', '*')),
        os.path.join(logos_dir, base_name.replace(' ', '*')),
    ]
    
    for pattern in patterns:
        matches = glob.glob(pattern)
        if matches:
            actual_filename = os.path.basename(matches[0])
            return send_from_directory(logos_dir, actual_filename)
    
    # Si no se encuentra, devolver 404
    return f"Logo no encontrado: {decoded_filename}", 404

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
    # SIEMPRE usar template, Flask lo buscará automáticamente en templates/
    conn = get_db()
    estadisticas = conn.execute('''
        SELECT * FROM estadisticas WHERE activo = 1 
        ORDER BY orden, id
    ''').fetchall()
    noticias = conn.execute('''
        SELECT * FROM noticias WHERE activa = 1 AND destacada = 1 
        ORDER BY fecha DESC, id DESC LIMIT 3
    ''').fetchall()
    eventos = conn.execute('''
        SELECT * FROM eventos WHERE activo = 1 AND destacada = 1 
        ORDER BY orden, id
        LIMIT 3
    ''').fetchall()
    clientes = conn.execute('''
        SELECT * FROM clientes WHERE activo = 1 AND mostrar_en_index = 1 
        ORDER BY orden, id
    ''').fetchall()
    tarjetas_destacadas = conn.execute('''
        SELECT * FROM tarjetas_destacadas WHERE pagina = 'index' AND activo = 1 
        ORDER BY orden, id
    ''').fetchall()
    # Cargar imágenes de la galería para el hero slider
    imagenes_hero = conn.execute('''
        SELECT * FROM galeria_imagenes 
        WHERE activo = 1 AND (pagina = 'index' OR pagina IS NULL OR pagina = '')
        ORDER BY orden, id DESC
        LIMIT 10
    ''').fetchall()
    conn.close()
    lang = get_language()
    locale = get_locale()
    return render_template('index.html', estadisticas=estadisticas, noticias=noticias, eventos=eventos, clientes=clientes, tarjetas_destacadas=tarjetas_destacadas, imagenes_hero=imagenes_hero, lang=lang, locale=locale)

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
    # Cargar imágenes de la galería para el hero slider
    imagenes_hero = conn.execute('''
        SELECT * FROM galeria_imagenes 
        WHERE activo = 1 AND (pagina = 'equipo' OR pagina IS NULL OR pagina = '')
        ORDER BY orden, id DESC
        LIMIT 10
    ''').fetchall()
    conn.close()
    return render_template('equipo.html', organigrama=organigrama_organizado, direccion=direccion, tarjetas_destacadas=tarjetas_destacadas, imagenes_hero=imagenes_hero, lang=lang, locale=locale)

@app.route('/<page>.html')
def page(page):
    """Rutas dinámicas para páginas HTML - SIEMPRE prioriza templates"""
    # Obtener idioma actual
    lang = get_language()
    locale = get_locale()
    
    # Verificar primero si existe template (para evitar servir archivos estáticos con Jinja2)
    template_file = f'{page}.html'
    template_path = os.path.join(app.root_path, 'templates', template_file)
    
    if os.path.exists(template_path):
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
            # Cargar imágenes de la galería para el hero slider
            imagenes_hero = conn.execute('''
                SELECT * FROM galeria_imagenes 
                WHERE activo = 1 AND (pagina = 'docencia' OR pagina IS NULL OR pagina = '')
                ORDER BY orden, id DESC
                LIMIT 10
            ''').fetchall()
            conn.close()
            return render_template('docencia.html', programas=programas, testimonios=testimonios, tarjetas_destacadas=tarjetas_destacadas, imagenes_hero=imagenes_hero, lang=lang, locale=locale)
        
        elif page == 'noticias':
            conn = get_db()
            noticias = conn.execute('''
                SELECT * FROM noticias WHERE activa = 1 AND destacada = 1 
                ORDER BY fecha DESC, id DESC
            ''').fetchall()
            eventos = conn.execute('''
                SELECT * FROM eventos WHERE activo = 1 AND destacada = 1 
                ORDER BY orden, id
            ''').fetchall()
            tarjetas_destacadas = conn.execute('''
                SELECT * FROM tarjetas_destacadas WHERE pagina = 'noticias' AND activo = 1 
                ORDER BY orden, id
            ''').fetchall()
            # Cargar imágenes de la galería para el hero slider
            imagenes_hero = conn.execute('''
                SELECT * FROM galeria_imagenes 
                WHERE activo = 1 AND (pagina = 'noticias' OR pagina IS NULL OR pagina = '')
                ORDER BY orden, id DESC
                LIMIT 10
            ''').fetchall()
            # Cargar configuración de redes sociales
            config_redes = conn.execute('''
                SELECT * FROM configuracion_redes WHERE activo = 1 LIMIT 1
            ''').fetchone()
            instagram_username = None
            linkedin_company_id = None
            linkedin_page_url = None
            if config_redes:
                try:
                    instagram_username = config_redes['instagram_username'] if config_redes['instagram_username'] else None
                except (KeyError, IndexError):
                    instagram_username = None
                try:
                    linkedin_company_id = config_redes['linkedin_company_id'] if config_redes['linkedin_company_id'] else None
                except (KeyError, IndexError):
                    linkedin_company_id = None
                try:
                    linkedin_page_url = config_redes['linkedin_page_url'] if config_redes['linkedin_page_url'] else None
                except (KeyError, IndexError):
                    linkedin_page_url = None
            conn.close()
            return render_template('noticias.html', noticias=noticias, eventos=eventos, tarjetas_destacadas=tarjetas_destacadas, imagenes_hero=imagenes_hero, instagram_username=instagram_username, linkedin_company_id=linkedin_company_id, linkedin_page_url=linkedin_page_url, lang=lang, locale=locale)
        
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
            # Cargar imágenes de la galería para el hero slider
            imagenes_hero = conn.execute('''
                SELECT * FROM galeria_imagenes 
                WHERE activo = 1 AND (pagina = 'equipo' OR pagina IS NULL OR pagina = '')
                ORDER BY orden, id DESC
                LIMIT 10
            ''').fetchall()
            conn.close()
            return render_template('equipo.html', organigrama=organigrama_organizado, direccion=direccion, tarjetas_destacadas=tarjetas_destacadas, imagenes_hero=imagenes_hero, lang=lang, locale=locale)
        
        elif page == 'convenios':
            conn = get_db()
            convenios = conn.execute('''
                SELECT * FROM convenios WHERE activo = 1 
                ORDER BY orden, id
            ''').fetchall()
            # Cargar imágenes de la galería para el hero slider
            imagenes_hero = conn.execute('''
                SELECT * FROM galeria_imagenes 
                WHERE activo = 1 AND (pagina = 'convenios' OR pagina IS NULL OR pagina = '')
                ORDER BY orden, id DESC
                LIMIT 10
            ''').fetchall()
            conn.close()
            return render_template('convenios.html', convenios=convenios, imagenes_hero=imagenes_hero, lang=lang, locale=locale)
        
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
            # Cargar imágenes de la galería para el hero slider
            imagenes_hero = conn.execute('''
                SELECT * FROM galeria_imagenes 
                WHERE activo = 1 AND (pagina = 'casa-omsa' OR pagina IS NULL OR pagina = '')
                ORDER BY orden, id DESC
                LIMIT 10
            ''').fetchall()
            conn.close()
            return render_template('casa-omsa.html', aliados_casa_omsa=aliados_casa_omsa, tarjetas_destacadas=tarjetas_destacadas, imagenes_hero=imagenes_hero, lang=lang, locale=locale)
        
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
            # Cargar imágenes de la galería para el hero slider
            imagenes_hero = conn.execute('''
                SELECT * FROM galeria_imagenes 
                WHERE activo = 1 AND (pagina = 'investigacion' OR pagina IS NULL OR pagina = '')
                ORDER BY orden, id DESC
                LIMIT 10
            ''').fetchall()
            conn.close()
            return render_template('investigacion.html', proyectos=proyectos, publicaciones=publicaciones, tarjetas_destacadas=tarjetas_destacadas, imagenes_hero=imagenes_hero, lang=lang, locale=locale)
        
        elif page == 'faq':
            conn = get_db()
            faqs = conn.execute('''
                SELECT * FROM faq WHERE activo = 1 
                ORDER BY categoria, orden, id
            ''').fetchall()
            tarjetas_destacadas = conn.execute('''
                SELECT * FROM tarjetas_destacadas WHERE pagina = 'faq' AND activo = 1 
                ORDER BY orden, id
            ''').fetchall()
            # Cargar imágenes de la galería para el hero slider
            imagenes_hero = conn.execute('''
                SELECT * FROM galeria_imagenes 
                WHERE activo = 1 AND (pagina = 'faq' OR pagina IS NULL OR pagina = '')
                ORDER BY orden, id DESC
                LIMIT 10
            ''').fetchall()
            conn.close()
            # Organizar FAQs por categoría
            faqs_por_categoria = {}
            categorias_nombres = {
                'servicios': 'Servicios',
                'proceso': 'Proceso',
                'tiempos': 'Tiempos y Plazos',
                'costos': 'Costos',
                'tecnicas': 'Técnicas y Metodologías',
                'certificaciones': 'Certificaciones'
            }
            for faq in faqs:
                categoria = faq['categoria'] or 'general'
                if categoria not in faqs_por_categoria:
                    faqs_por_categoria[categoria] = []
                faqs_por_categoria[categoria].append(faq)
            return render_template('faq.html', faqs_por_categoria=faqs_por_categoria, categorias_nombres=categorias_nombres, imagenes_hero=imagenes_hero, lang=lang, locale=locale)
        
        elif page == 'quienes-somos':
            conn = get_db()
            certificados = conn.execute('''
                SELECT * FROM certificados WHERE activo = 1 
                ORDER BY organismo, orden, id
            ''').fetchall()
            tarjetas_destacadas = conn.execute('''
                SELECT * FROM tarjetas_destacadas WHERE pagina = 'quienes-somos' AND activo = 1 
                ORDER BY orden, id
            ''').fetchall()
            # Cargar imágenes de la galería para el hero slider (solo las asignadas a esta página)
            imagenes_hero = conn.execute('''
                SELECT * FROM galeria_imagenes 
                WHERE activo = 1 AND (pagina = 'quienes-somos' OR pagina IS NULL OR pagina = '')
                ORDER BY orden, id DESC
                LIMIT 10
            ''').fetchall()
            conn.close()
            return render_template('quienes-somos.html', certificados=certificados, tarjetas_destacadas=tarjetas_destacadas, imagenes_hero=imagenes_hero, lang=lang, locale=locale)
        
        elif page == 'servicios':
            conn = get_db()
            metodologias = conn.execute('''
                SELECT * FROM metodologias WHERE activo = 1 
                ORDER BY categoria, orden, nombre
            ''').fetchall()
            tarjetas_destacadas = conn.execute('''
                SELECT * FROM tarjetas_destacadas WHERE pagina = 'servicios' AND activo = 1 
                ORDER BY orden, id
            ''').fetchall()
            # Cargar imágenes de la galería para el hero slider (solo las asignadas a esta página)
            imagenes_hero = conn.execute('''
                SELECT * FROM galeria_imagenes 
                WHERE activo = 1 AND (pagina = 'servicios' OR pagina IS NULL OR pagina = '')
                ORDER BY orden, id DESC
                LIMIT 10
            ''').fetchall()
            conn.close()
            # Organizar metodologías por categoría y agrupar por similitudes
            metodologias_por_categoria = {}
            categorias_nombres = {
                'residuos': 'Residuos de Medicamentos Veterinarios',
                'contaminantes': 'Contaminantes Químicos',
                'microbiologia': 'Microbiología',
                'otros': 'Otros Análisis'
            }
            
            # Función para crear clave de agrupación (sin analito)
            def get_group_key(metodologia):
                nombre = get_translated_field(metodologia, 'nombre') or metodologia['nombre'] or ''
                matriz = get_translated_field(metodologia, 'matriz') or metodologia['matriz'] or ''
                tecnica = get_translated_field(metodologia, 'tecnica') or metodologia['tecnica'] or ''
                lod = metodologia['limite_deteccion'] or ''
                loq = metodologia['limite_cuantificacion'] or ''
                acreditada = metodologia['acreditada'] or False
                return (nombre, matriz, tecnica, lod, loq, acreditada)
            
            # Agrupar metodologías por nombre de método
            metodologias_agrupadas = {}
            for metodologia in metodologias:
                categoria = metodologia['categoria'] or 'otros'
                if categoria not in metodologias_agrupadas:
                    metodologias_agrupadas[categoria] = {}
                
                # Usar nombre del método como clave principal
                nombre_metodo = get_translated_field(metodologia, 'nombre') or metodologia['nombre'] or ''
                
                if nombre_metodo not in metodologias_agrupadas[categoria]:
                    metodologias_agrupadas[categoria][nombre_metodo] = {}
                
                # Crear clave de agrupación (mismo método, misma matriz, técnica, LOD, LOQ)
                group_key = get_group_key(metodologia)
                
                if group_key not in metodologias_agrupadas[categoria][nombre_metodo]:
                    metodologias_agrupadas[categoria][nombre_metodo][group_key] = []
                
                metodologias_agrupadas[categoria][nombre_metodo][group_key].append(metodologia)
            
            # Convertir a lista para el template
            metodologias_por_categoria = {}
            for categoria, metodos in metodologias_agrupadas.items():
                metodologias_por_categoria[categoria] = []
                for nombre_metodo, grupos in metodos.items():
                    for group_key, items in grupos.items():
                        # Si hay más de un analito con los mismos valores (excepto analito), agrupar
                        if len(items) > 1:
                            # Extraer analitos únicos
                            analitos_unicos = []
                            for item in items:
                                analito = get_translated_field(item, 'analito') or item['analito'] or ''
                                if analito and analito not in analitos_unicos:
                                    analitos_unicos.append(analito)
                            metodologias_por_categoria[categoria].append({
                                'agrupado': True,
                                'metodologias': items,
                                'analitos': analitos_unicos,
                                'metodologia_representativa': items[0]  # Primera metodología como representante
                            })
                        else:
                            # Un solo analito
                            metodologias_por_categoria[categoria].append({
                                'agrupado': False,
                                'metodologias': items,
                                'analitos': [get_translated_field(items[0], 'analito') or items[0]['analito'] or ''],
                                'metodologia_representativa': items[0]
                            })
            return render_template('servicios.html', metodologias_por_categoria=metodologias_por_categoria, categorias_nombres=categorias_nombres, tarjetas_destacadas=tarjetas_destacadas, imagenes_hero=imagenes_hero, lang=lang, locale=locale)
        
        # Si existe template pero no necesita datos especiales, renderizarlo con lang
        # Incluir tarjetas destacadas e imágenes hero para todas las páginas
        conn = get_db()
        tarjetas_destacadas = conn.execute('''
            SELECT * FROM tarjetas_destacadas WHERE pagina = ? AND activo = 1 
            ORDER BY orden, id
        ''', (page,)).fetchall()
        # Cargar imágenes de la galería para el hero slider
        imagenes_hero = conn.execute('''
            SELECT * FROM galeria_imagenes 
            WHERE activo = 1 AND (pagina = ? OR pagina IS NULL OR pagina = '')
            ORDER BY orden, id DESC
            LIMIT 10
        ''', (page,)).fetchall()
        conn.close()
        return render_template(template_file, tarjetas_destacadas=tarjetas_destacadas, imagenes_hero=imagenes_hero, lang=lang, locale=locale)
    
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
            
            # Redirigir a la URL que el usuario intentaba acceder antes del login
            next_url = session.pop('next_url', None)
            if next_url:
                return redirect(next_url)
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

# Gestión de FAQ
@app.route('/admin/faq')
@login_required
def admin_faq():
    conn = get_db()
    faqs = conn.execute('SELECT * FROM faq ORDER BY categoria, orden, id DESC').fetchall()
    conn.close()
    return render_template('admin/faq.html', faqs=faqs)

@app.route('/admin/faq/nuevo', methods=['GET', 'POST'])
@login_required
def admin_faq_nuevo():
    if request.method == 'POST':
        conn = get_db()
        conn.execute('''
            INSERT INTO faq (pregunta, pregunta_en, respuesta, respuesta_en, categoria, orden, activo)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            request.form.get('pregunta'),
            request.form.get('pregunta_en', '').strip() or None,
            request.form.get('respuesta'),
            request.form.get('respuesta_en', '').strip() or None,
            request.form.get('categoria'),
            int(request.form.get('orden', 0)),
            1 if request.form.get('activo') == 'on' else 0
        ))
        conn.commit()
        conn.close()
        flash('FAQ creada correctamente', 'success')
        return redirect(url_for('admin_faq'))
    
    return render_template('admin/faq_form.html')

@app.route('/admin/faq/<int:faq_id>/editar', methods=['GET', 'POST'])
@login_required
def admin_faq_editar(faq_id):
    conn = get_db()
    
    if request.method == 'POST':
        conn.execute('''
            UPDATE faq 
            SET pregunta=?, pregunta_en=?, respuesta=?, respuesta_en=?, 
                categoria=?, orden=?, activo=?, updated_at=CURRENT_TIMESTAMP
            WHERE id=?
        ''', (
            request.form.get('pregunta'),
            request.form.get('pregunta_en', '').strip() or None,
            request.form.get('respuesta'),
            request.form.get('respuesta_en', '').strip() or None,
            request.form.get('categoria'),
            int(request.form.get('orden', 0)),
            1 if request.form.get('activo') == 'on' else 0,
            faq_id
        ))
        conn.commit()
        conn.close()
        flash('FAQ actualizada correctamente', 'success')
        return redirect(url_for('admin_faq'))
    
    faq = conn.execute('SELECT * FROM faq WHERE id = ?', (faq_id,)).fetchone()
    conn.close()
    
    if not faq:
        flash('FAQ no encontrada', 'error')
        return redirect(url_for('admin_faq'))
    
    return render_template('admin/faq_form.html', faq=dict(faq))

@app.route('/admin/faq/<int:faq_id>/eliminar', methods=['POST'])
@login_required
@csrf_required
def admin_faq_eliminar(faq_id):
    conn = get_db()
    conn.execute('DELETE FROM faq WHERE id = ?', (faq_id,))
    conn.commit()
    conn.close()
    flash('FAQ eliminada', 'success')
    return redirect(url_for('admin_faq'))

# Gestión de Certificados
@app.route('/admin/certificados')
@login_required
def admin_certificados():
    conn = get_db()
    certificados = conn.execute('SELECT * FROM certificados ORDER BY organismo, orden, id DESC').fetchall()
    conn.close()
    return render_template('admin/certificados.html', certificados=certificados)

@app.route('/admin/certificados/nuevo', methods=['GET', 'POST'])
@login_required
def admin_certificado_nuevo():
    if request.method == 'POST':
        conn = get_db()
        conn.execute('''
            INSERT INTO certificados (titulo, titulo_en, organismo, numero_certificado, fecha_emision, fecha_vencimiento, imagen, enlace_externo, descripcion, descripcion_en, orden, activo)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            request.form.get('titulo'),
            request.form.get('titulo_en', '').strip() or None,
            request.form.get('organismo'),
            request.form.get('numero_certificado', '').strip() or None,
            request.form.get('fecha_emision', '').strip() or None,
            request.form.get('fecha_vencimiento', '').strip() or None,
            request.form.get('imagen', '').strip() or None,
            (lambda x: None if not x or x.strip().lower() == 'none' else x.strip())(request.form.get('enlace_externo', '')),
            request.form.get('descripcion', '').strip() or None,
            request.form.get('descripcion_en', '').strip() or None,
            int(request.form.get('orden', 0)),
            1 if request.form.get('activo') == 'on' else 0
        ))
        conn.commit()
        conn.close()
        flash('Certificado creado correctamente', 'success')
        return redirect(url_for('admin_certificados'))
    
    return render_template('admin/certificado_form.html')

@app.route('/admin/certificados/<int:certificado_id>/editar', methods=['GET', 'POST'])
@login_required
def admin_certificado_editar(certificado_id):
    conn = get_db()
    
    if request.method == 'POST':
        conn.execute('''
            UPDATE certificados 
            SET titulo=?, titulo_en=?, organismo=?, numero_certificado=?, fecha_emision=?, fecha_vencimiento=?, 
                imagen=?, enlace_externo=?, descripcion=?, descripcion_en=?, orden=?, activo=?, updated_at=CURRENT_TIMESTAMP
            WHERE id=?
        ''', (
            request.form.get('titulo'),
            request.form.get('titulo_en', '').strip() or None,
            request.form.get('organismo'),
            request.form.get('numero_certificado', '').strip() or None,
            request.form.get('fecha_emision', '').strip() or None,
            request.form.get('fecha_vencimiento', '').strip() or None,
            request.form.get('imagen', '').strip() or None,
            (lambda x: None if not x or x.strip().lower() == 'none' else x.strip())(request.form.get('enlace_externo', '')),
            request.form.get('descripcion', '').strip() or None,
            request.form.get('descripcion_en', '').strip() or None,
            int(request.form.get('orden', 0)),
            1 if request.form.get('activo') == 'on' else 0,
            certificado_id
        ))
        conn.commit()
        conn.close()
        flash('Certificado actualizado correctamente', 'success')
        return redirect(url_for('admin_certificados'))
    
    certificado = conn.execute('SELECT * FROM certificados WHERE id = ?', (certificado_id,)).fetchone()
    conn.close()
    
    if not certificado:
        flash('Certificado no encontrado', 'error')
        return redirect(url_for('admin_certificados'))
    
    return render_template('admin/certificado_form.html', certificado=dict(certificado))

@app.route('/admin/certificados/<int:certificado_id>/eliminar', methods=['POST'])
@login_required
@csrf_required
def admin_certificado_eliminar(certificado_id):
    conn = get_db()
    conn.execute('DELETE FROM certificados WHERE id = ?', (certificado_id,))
    conn.commit()
    conn.close()
    flash('Certificado eliminado', 'success')
    return redirect(url_for('admin_certificados'))

# Gestión de Metodologías Analíticas
@app.route('/api/metodologias')
def api_metodologias():
    """API endpoint para obtener todas las metodologías activas (para el chatbot)"""
    conn = None
    try:
        conn = get_db()
        
        # Verificar si la tabla existe
        try:
            table_check = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='metodologias'").fetchone()
            if not table_check:
                app.logger.warning('API metodologias: La tabla metodologias no existe')
                if conn:
                    conn.close()
                return jsonify({'error': 'La tabla de metodologías no existe', 'result': []}), 200
        except Exception as e:
            app.logger.error(f'API metodologias: Error al verificar tabla: {str(e)}', exc_info=True)
            if conn:
                conn.close()
            return jsonify({'error': 'Error al verificar la base de datos', 'result': []}), 200
        
        # Intentar consulta simple primero
        try:
            # Consulta básica que debería funcionar siempre
            metodologias = conn.execute('''
                SELECT nombre, nombre_en, categoria, analito, analito_en, matriz, matriz_en, 
                       tecnica, tecnica_en, limite_deteccion, limite_cuantificacion, acreditada
                FROM metodologias
            ''').fetchall()
            
            # Filtrar por activo si existe la columna
            filtered_metodologias = []
            for met in metodologias:
                try:
                    # Intentar acceder a 'activo' - si no existe, incluir todas
                    if 'activo' in met.keys():
                        if met['activo'] == 1:
                            filtered_metodologias.append(met)
                    else:
                        # Si no existe columna activo, incluir todas
                        filtered_metodologias.append(met)
                except:
                    # Si hay error, incluir de todas formas
                    filtered_metodologias.append(met)
            
            metodologias = filtered_metodologias
            app.logger.info(f'API metodologias: Encontradas {len(metodologias)} metodologías')
            
        except sqlite3.OperationalError as e:
            error_msg = str(e)
            app.logger.error(f'API metodologias: Error SQL: {error_msg}', exc_info=True)
            
            # Si falla por columna faltante, intentar consulta más simple
            if 'no such column' in error_msg.lower():
                try:
                    app.logger.warning('API metodologias: Intentando consulta simplificada...')
                    metodologias = conn.execute('''
                        SELECT nombre, categoria, analito, matriz, tecnica, limite_deteccion, limite_cuantificacion, acreditada
                        FROM metodologias
                    ''').fetchall()
                    app.logger.info(f'API metodologias: Consulta simplificada exitosa, {len(metodologias)} resultados')
                except Exception as e2:
                    app.logger.error(f'API metodologias: Error en consulta simplificada: {str(e2)}', exc_info=True)
                    if conn:
                        conn.close()
                    return jsonify({
                        'error': 'Error al consultar metodologías',
                        'details': str(e2) if app.debug else 'Error en la base de datos',
                        'result': []
                    }), 500
            else:
                if conn:
                    conn.close()
                return jsonify({
                    'error': 'Error en la consulta SQL',
                    'details': error_msg if app.debug else 'Error al consultar metodologías',
                    'result': []
                }), 500
        
        # Convertir a lista de diccionarios
        # sqlite3.Row no tiene método .get(), se accede con [] o con 'in'
        result = []
        for met in metodologias:
            try:
                # Acceder a campos de sqlite3.Row usando [] en lugar de .get()
                result.append({
                    'nombre': met['nombre'] if 'nombre' in met.keys() else '',
                    'nombre_en': met['nombre_en'] if 'nombre_en' in met.keys() else '',
                    'categoria': met['categoria'] if 'categoria' in met.keys() else '',
                    'analito': met['analito'] if 'analito' in met.keys() else '',
                    'analito_en': met['analito_en'] if 'analito_en' in met.keys() else '',
                    'matriz': met['matriz'] if 'matriz' in met.keys() else '',
                    'matriz_en': met['matriz_en'] if 'matriz_en' in met.keys() else '',
                    'tecnica': met['tecnica'] if 'tecnica' in met.keys() else '',
                    'tecnica_en': met['tecnica_en'] if 'tecnica_en' in met.keys() else '',
                    'lod': met['limite_deteccion'] if 'limite_deteccion' in met.keys() else '',
                    'loq': met['limite_cuantificacion'] if 'limite_cuantificacion' in met.keys() else '',
                    'acreditada': bool(met['acreditada'] if 'acreditada' in met.keys() else 0)
                })
            except KeyError as e:
                app.logger.warning(f'API metodologias: Columna faltante: {str(e)}')
                continue
            except Exception as e:
                app.logger.warning(f'API metodologias: Error al procesar metodología: {str(e)}')
                continue
        
        # Cerrar conexión antes de retornar
        if conn:
            conn.close()
        
        # Respuesta con headers para caché
        response = jsonify(result)
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        app.logger.info(f'API metodologias: Devolviendo {len(result)} metodologías activas')
        
        # Si no hay metodologías, loguear una advertencia
        if len(result) == 0:
            app.logger.warning('API metodologias: No hay metodologías activas en la base de datos')
        
        return response
    except sqlite3.OperationalError as e:
        error_msg = f'Error SQL en API metodologias: {str(e)}'
        app.logger.error(error_msg, exc_info=True)
        if conn:
            try:
                conn.close()
            except:
                pass
        return jsonify({
            'error': 'Error en la base de datos',
            'details': str(e) if app.debug else 'Error al acceder a la base de datos'
        }), 500
    except Exception as e:
        error_msg = f'Error en API metodologias: {str(e)}'
        error_type = type(e).__name__
        app.logger.error(f'{error_msg} (Tipo: {error_type})', exc_info=True)
        if conn:
            try:
                conn.close()
            except:
                pass
        # En desarrollo, devolver detalles del error; en producción, mensaje genérico
        error_details = str(e) if app.debug else 'Error interno del servidor'
        return jsonify({
            'error': 'Error al cargar metodologías',
            'details': error_details,
            'type': error_type if app.debug else None
        }), 500

# API para obtener contexto general del sitio (contacto, FAQ, etc.)
@app.route('/api/chatbot/context', methods=['GET'])
def api_chatbot_context():
    """API endpoint para obtener información general del sitio para el chatbot"""
    try:
        conn = get_db()
        context_info = {
            'contacto': {
                'direccion': 'Av. Santa Rosa 11735, La Pintana, Santiago, Chile',
                'telefono': '+56 2 2978 XXXX',
                'email': 'farmavet@uchile.cl',
                'email_programas': 'postitulo@veterinaria.uchile.cl',
                'horario': 'Lunes a viernes, 09:00 a 17:30 hrs',
                'horario_atencion': 'Atención presencial con agendamiento previo'
            },
            'faqs': [],
            'servicios': []
        }
        
        # Obtener FAQ activas
        try:
            faqs = conn.execute('''
                SELECT pregunta, respuesta, categoria 
                FROM faq 
                WHERE activo = 1 
                ORDER BY categoria, orden
                LIMIT 20
            ''').fetchall()
            
            for faq in faqs:
                pregunta = faq['pregunta'] if 'pregunta' in faq.keys() else ''
                respuesta = faq['respuesta'] if 'respuesta' in faq.keys() else ''
                categoria = faq['categoria'] if 'categoria' in faq.keys() else 'general'
                if pregunta and respuesta:
                    context_info['faqs'].append({
                        'pregunta': pregunta,
                        'respuesta': respuesta,
                        'categoria': categoria
                    })
        except Exception as e:
            app.logger.warning(f'Error al obtener FAQ: {str(e)}')
        
        # Obtener servicios principales
        try:
            tarjetas = conn.execute('''
                SELECT titulo, contenido FROM tarjetas_destacadas 
                WHERE activo = 1 
                LIMIT 10
            ''').fetchall()
            
            for tarjeta in tarjetas:
                titulo = tarjeta['titulo'] if 'titulo' in tarjeta.keys() else ''
                contenido = tarjeta['contenido'] if 'contenido' in tarjeta.keys() else ''
                if titulo:
                    context_info['servicios'].append({
                        'titulo': titulo,
                        'contenido': contenido[:200] if contenido else ''  # Limitar contenido
                    })
        except Exception as e:
            app.logger.warning(f'Error al obtener servicios: {str(e)}')
        
        conn.close()
        
        return jsonify(context_info), 200
        
    except Exception as e:
        app.logger.error(f'Error en API contexto: {str(e)}', exc_info=True)
        return jsonify({
            'error': 'Error al obtener contexto',
            'details': str(e) if app.debug else 'Error interno del servidor'
        }), 500

# API de Perplexity para búsquedas inteligentes
@app.route('/api/chatbot/search', methods=['POST'])
def api_chatbot_search():
    """API endpoint para búsquedas inteligentes usando Perplexity como motor principal de razonamiento"""
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        include_local = data.get('include_local', True)  # Incluir contexto local
        local_results = data.get('local_results', [])  # Resultados de búsqueda local para contexto
        
        if not query:
            return jsonify({'error': 'Query vacía'}), 400
        
        perplexity_api_key = os.environ.get('PERPLEXITY_API_KEY')
        
        if not perplexity_api_key:
            app.logger.warning('PERPLEXITY_API_KEY no configurada')
            return jsonify({
                'error': 'API de Perplexity no configurada',
                'message': 'La funcionalidad de búsqueda inteligente no está disponible'
            }), 503
        
        # Obtener información del contexto local (metodologías, servicios, contacto, FAQ, etc.)
        local_context = ""
        
        # SIEMPRE incluir información de contacto (necesaria para consultas generales)
        local_context += "\n\nINFORMACIÓN DE CONTACTO DE FARMAVET:"
        local_context += "\n- Dirección: Av. Santa Rosa 11735, La Pintana, Santiago, Chile"
        local_context += "\n- Teléfono: +56 2 2978 XXXX"
        local_context += "\n- Email general: farmavet@uchile.cl"
        local_context += "\n- Email programas académicos: postitulo@veterinaria.uchile.cl"
        local_context += "\n- Horario: Lunes a viernes, 09:00 a 17:30 hrs"
        local_context += "\n- Atención presencial con agendamiento previo"
        local_context += "\n- Para enviar consultas, usar el formulario de contacto en la página de contacto"
        
        # Si hay resultados locales, agregarlos como contexto relevante
        if local_results and len(local_results) > 0:
            local_context += "\n\nMETODOLOGÍAS RELEVANTES ENCONTRADAS EN LA BASE DE DATOS:"
            # Agrupar por método para mostrar de forma más natural
            grupos = {}
            for met in local_results[:50]:  # Limitar a 50 para no sobrecargar
                nombre = met.get('nombre', '') or ''
                matriz = met.get('matriz', '') or ''
                tecnica = met.get('tecnica', '') or ''
                grupo_key = f"{nombre}|{matriz}|{tecnica}"
                
                if grupo_key not in grupos:
                    grupos[grupo_key] = {
                        'nombre': nombre,
                        'matriz': matriz,
                        'tecnica': tecnica,
                        'acreditada': met.get('acreditada', False),
                        'analitos': [],
                        'lods': [],
                        'loqs': []
                    }
                
                analito = met.get('analito', '')
                if analito and analito not in grupos[grupo_key]['analitos']:
                    grupos[grupo_key]['analitos'].append(analito)
                
                lod = met.get('lod', '') or met.get('limite_deteccion', '')
                loq = met.get('loq', '') or met.get('limite_cuantificacion', '')
                
                if lod:
                    try:
                        import re
                        lod_num = re.search(r'[\d.]+', str(lod))
                        if lod_num:
                            grupos[grupo_key]['lods'].append(float(lod_num.group()))
                    except:
                        pass
                
                if loq:
                    try:
                        import re
                        loq_num = re.search(r'[\d.]+', str(loq))
                        if loq_num:
                            grupos[grupo_key]['loqs'].append(float(loq_num.group()))
                    except:
                        pass
            
            # Formatear grupos de manera natural
            for grupo in list(grupos.values())[:10]:  # Máximo 10 grupos
                analitos_str = ', '.join(grupo['analitos'][:5])
                if len(grupo['analitos']) > 5:
                    analitos_str += f" y {len(grupo['analitos']) - 5} más"
                
                lod_range = ""
                if grupo['lods']:
                    min_lod = min(grupo['lods'])
                    max_lod = max(grupo['lods'])
                    if min_lod == max_lod:
                        lod_range = f"LOD: {min_lod}"
                    else:
                        lod_range = f"LOD: {min_lod}-{max_lod}"
                
                loq_range = ""
                if grupo['loqs']:
                    min_loq = min(grupo['loqs'])
                    max_loq = max(grupo['loqs'])
                    if min_loq == max_loq:
                        loq_range = f"LOQ: {min_loq}"
                    else:
                        loq_range = f"LOQ: {min_loq}-{max_loq}"
                
                metodo_info = f"- {grupo['nombre']}: {analitos_str} en {grupo['matriz']}"
                if grupo['tecnica']:
                    metodo_info += f" mediante {grupo['tecnica']}"
                if lod_range or loq_range:
                    metodo_info += f" ({lod_range}" + (f", {loq_range}" if loq_range else "") + ")"
                if grupo['acreditada']:
                    metodo_info += " [Acreditada ISO 17025]"
                
                local_context += "\n" + metodo_info
        
        if include_local and not local_results:
            try:
                conn = get_db()
                
                # Obtener metodologías disponibles
                metodologias = conn.execute('''
                    SELECT DISTINCT analito, matriz, tecnica, categoria 
                    FROM metodologias 
                    WHERE activo = 1 
                    LIMIT 20
                ''').fetchall()
                
                if metodologias:
                    met_list = []
                    for m in metodologias[:10]:
                        analito = m['analito'] if 'analito' in m.keys() else ''
                        matriz = m['matriz'] if 'matriz' in m.keys() else ''
                        tecnica = m['tecnica'] if 'tecnica' in m.keys() and m['tecnica'] else 'técnica variada'
                        met_list.append(f"{analito} en {matriz} ({tecnica})")
                    if met_list:
                        local_context = f"\n\nMetodologías disponibles en FARMAVET:\n- " + "\n- ".join(met_list) + local_context
                
                # Obtener servicios principales
                try:
                    tarjetas = conn.execute('''
                        SELECT titulo, contenido FROM tarjetas_destacadas 
                        WHERE activo = 1 
                        LIMIT 5
                    ''').fetchall()
                    
                    if tarjetas:
                        servicios = []
                        for t in tarjetas:
                            titulo = t['titulo'] if 'titulo' in t.keys() else ''
                            if titulo:
                                servicios.append(titulo)
                        if servicios:
                            local_context += f"\n\nServicios principales: {', '.join(servicios)}"
                except:
                    pass
                
                # Obtener FAQ activas
                try:
                    faqs = conn.execute('''
                        SELECT pregunta, respuesta 
                        FROM faq 
                        WHERE activo = 1 
                        ORDER BY categoria, orden
                        LIMIT 10
                    ''').fetchall()
                    
                    if faqs:
                        local_context += "\n\nPREGUNTAS FRECUENTES (FAQ):"
                        for faq in faqs:
                            pregunta = faq['pregunta'] if 'pregunta' in faq.keys() else ''
                            respuesta = faq['respuesta'] if 'respuesta' in faq.keys() else ''
                            # Limpiar HTML de la respuesta (remover tags)
                            import re
                            respuesta_limpia = re.sub(r'<[^>]+>', '', respuesta) if respuesta else ''
                            if pregunta and respuesta_limpia:
                                local_context += f"\n- P: {pregunta}"
                                local_context += f"\n  R: {respuesta_limpia[:150]}..."  # Limitar longitud
                except Exception as e:
                    app.logger.warning(f'Error al obtener FAQ para contexto: {str(e)}')
                    pass
                
                conn.close()
            except Exception as e:
                app.logger.warning(f'Error al obtener contexto local: {str(e)}')
        
        # Construir el prompt contextual para Perplexity - Motor principal de razonamiento
        # Perplexity debe razonar de manera natural e inteligente sobre la consulta
        context = f"""Eres FARMA, el asistente virtual inteligente del Laboratorio FARMAVET de la Universidad de Chile.

Tu rol es responder preguntas de manera natural, conversacional e inteligente, pero CONCISA.

PERSONALIDAD Y ESTILO:
- Responde de forma amable, profesional y natural, pero DIRECTA y CONCISA
- Razona sobre la pregunta antes de responder, pensando en qué busca realmente el usuario
- Responde SOLO lo que se pregunta, sin agregar información adicional a menos que sea relevante
- Si hay múltiples metodologías relacionadas, agrupa la información de forma coherente y natural
- Usa un lenguaje claro y accesible, evitando jerga técnica innecesaria

REGLAS OBLIGATORIAS - CONCISIÓN:
1. SOLO usa la información que te proporciono a continuación sobre FARMAVET
2. NO busques información en internet - usa SOLO el contexto proporcionado
3. NO des explicaciones generales o educativas fuera del contexto proporcionado
4. Responde de manera CONCISA: 1-2 oraciones para preguntas simples, máximo 2-3 oraciones para preguntas más complejas
5. Para preguntas simples como "algún correo de contacto?", responde DIRECTAMENTE con el correo (ej: "Sí, puedes contactarnos al email farmavet@uchile.cl")
6. NO agregues información extra como dirección, horarios, etc. a menos que se pregunte específicamente
7. Para metodologías: menciona qué analizan, en qué matriz, con qué técnica, y si es acreditada. Solo menciona LOD/LOQ si se pregunta específicamente sobre límites
8. NO incluyas referencias, citas, notas o números entre corchetes como [1], [2], etc.
9. NO uses formato de citas como <...> o [...]
10. NO des consejos adicionales como "puedes contactarnos" o "usa el formulario" a menos que se pregunte específicamente cómo contactar
11. Si la pregunta requiere información que NO está en el contexto, responde amablemente: "No tengo esa información disponible. Te recomiendo contactarnos al email farmavet@uchile.cl o usar el formulario de contacto en nuestra página web."

CONTEXTO DISPONIBLE DE FARMAVET:
{local_context}

INSTRUCCIONES ESPECIALES:
- Si preguntan sobre metodologías específicas (ej: "hacen tetraciclinas?"), responde CONCISO: "Sí, tenemos metodología acreditada para analizar Tetraciclina, Epi-tetraciclina, Oxitetraciclina y Clortetraciclina en productos de origen animal mediante HPLC-MS/MS."
- Si preguntan sobre límites (LOD/LOQ) específicamente, entonces sí incluye esa información
- Si preguntan con negación (ej: "no hacen X en Y?"), razona y busca metodologías que coincidan con los términos mencionados, responde de forma directa
- Para preguntas simples de contacto, responde solo con la información solicitada
- Si preguntan sobre metodologías que SÍ existen, sé positivo y directo
- Si preguntan sobre metodologías que NO existen en el contexto, sé honesto pero amable y conciso

IMPORTANTE: Menos es más. Responde lo esencial de forma natural pero breve.

Ahora, razona sobre la siguiente pregunta y responde de manera natural, inteligente, conversacional PERO CONCISA:
"""
        
        system_message = context
        
        # Llamar a la API de Perplexity
        perplexity_url = "https://api.perplexity.ai/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {perplexity_api_key}",
            "Content-Type": "application/json"
        }
        
        # Verificar que el system_message no sea demasiado largo
        # Perplexity permite hasta ~32000 tokens en el contexto, pero limitamos a 8000 caracteres para ser seguros
        if len(system_message) > 8000:
            app.logger.warning(f'Chatbot Perplexity: System message demasiado largo ({len(system_message)} caracteres), truncando...')
            system_message = system_message[:8000] + "..."
        
        # Modelos disponibles de Perplexity (ordenados por preferencia):
        # - sonar-pro (más potente, mejor razonamiento)
        # - sonar (más rápido)  
        # - llama-3.1-sonar-large-128k-online (legacy, más contexto)
        # - llama-3.1-sonar-small-128k-online (legacy, más rápido)
        # Nota: Estos modelos pueden hacer búsqueda web, pero con el prompt restringimos su uso
        # El payload base con el primer modelo que intentaremos
        base_payload = {
            "messages": [
                {
                    "role": "system",
                    "content": system_message
                },
                {
                    "role": "user",
                    "content": query
                }
            ],
            "temperature": 0.3,  # Un poco más alto para respuestas más naturales
            "max_tokens": 500
        }
        
        app.logger.info(f'Chatbot Perplexity: Buscando - {query[:100]}...')
        app.logger.debug(f'Chatbot Perplexity: System message length: {len(system_message)} caracteres')
        
        # Intentar primero con sonar-pro (modelo más reciente y potente)
        # Nota: sonar-pro y sonar son modelos online (buscadores web), pero podemos usarlos con contexto local
        # Para evitar búsqueda web, usamos solo el contexto proporcionado
        models_to_try = [
            "sonar-pro",  # Modelo más reciente, mejor para razonamiento (preferido)
            "sonar",      # Modelo rápido (alternativa)
            "llama-3.1-sonar-small-128k-online"  # Modelo legacy (último recurso)
        ]
        
        response = None
        last_error = None
        
        for model_name in models_to_try:
            try:
                # Construir payload para este modelo
                payload = base_payload.copy()
                payload["model"] = model_name
                app.logger.info(f'Chatbot Perplexity: Intentando con modelo {model_name}...')
                response = requests.post(perplexity_url, headers=headers, json=payload, timeout=20)
                
                if response.status_code == 200:
                    app.logger.info(f'Chatbot Perplexity: Éxito con modelo {model_name}')
                    break
                elif response.status_code == 400:
                    error_data = {}
                    try:
                        error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
                    except:
                        error_text = response.text[:500]
                        app.logger.warning(f'Chatbot Perplexity: Error 400 con modelo {model_name}: {error_text}')
                    
                    last_error = error_data.get('error', {}).get('message', f'Error 400 con modelo {model_name}')
                    app.logger.warning(f'Chatbot Perplexity: Modelo {model_name} falló (400), intentando siguiente...')
                    continue
                else:
                    app.logger.warning(f'Chatbot Perplexity: Error {response.status_code} con modelo {model_name}')
                    last_error = f'Error {response.status_code}'
                    continue
                    
            except requests.exceptions.RequestException as e:
                app.logger.error(f'Chatbot Perplexity: Error de conexión con modelo {model_name}: {str(e)}')
                last_error = str(e)
                continue
        
        # Verificar si todos los modelos fallaron
        if not response:
            app.logger.error(f'Chatbot Perplexity: Todos los modelos fallaron. Último error: {last_error}')
            return jsonify({
                'error': 'Error al procesar la consulta con Perplexity',
                'details': f'No se pudo procesar con ningún modelo disponible. Último error: {last_error}' if app.debug else 'Error al procesar la consulta'
            }), 503
        
        if response.status_code == 200:
            result = response.json()
            
            # Extraer la respuesta del modelo
            if 'choices' in result and len(result['choices']) > 0:
                answer = result['choices'][0]['message']['content']
                
                # Extraer fuentes si están disponibles
                sources = []
                if 'citations' in result:
                    sources = result['citations']
                
                app.logger.info(f'Chatbot Perplexity: Respuesta recibida ({len(answer)} caracteres)')
                
                return jsonify({
                    'answer': answer,
                    'sources': sources,
                    'query': query
                })
            else:
                app.logger.warning('Chatbot Perplexity: Respuesta sin choices')
                return jsonify({'error': 'Respuesta inválida de Perplexity'}), 500
        else:
            error_text = response.text
            app.logger.error(f'Chatbot Perplexity: Error {response.status_code}: {error_text}')
            return jsonify({
                'error': f'Error en Perplexity API: {response.status_code}',
                'details': error_text[:200] if app.debug else 'Error al procesar la consulta'
            }), response.status_code
            
    except requests.exceptions.Timeout:
        app.logger.error('Chatbot Perplexity: Timeout al conectar con la API')
        return jsonify({'error': 'Timeout al conectar con el servicio de búsqueda'}), 504
    except requests.exceptions.RequestException as e:
        app.logger.error(f'Chatbot Perplexity: Error de conexión: {str(e)}')
        return jsonify({'error': 'Error de conexión con el servicio de búsqueda'}), 503
    except Exception as e:
        error_msg = f'Error en chatbot search: {str(e)}'
        app.logger.error(error_msg, exc_info=True)
        return jsonify({
            'error': 'Error al procesar la búsqueda',
            'details': str(e) if app.debug else 'Error interno del servidor'
        }), 500

@app.route('/admin/metodologias')
@login_required
def admin_metodologias():
    conn = get_db()
    metodologias = conn.execute('SELECT * FROM metodologias ORDER BY categoria, orden, id DESC').fetchall()
    conn.close()
    return render_template('admin/metodologias.html', metodologias=metodologias)

@app.route('/admin/metodologias/nuevo', methods=['GET', 'POST'])
@login_required
def admin_metodologia_nuevo():
    if request.method == 'POST':
        conn = get_db()
        
        # Datos comunes para todos los analitos
        codigo = request.form.get('codigo', '').strip() or None
        nombre = request.form.get('nombre')
        nombre_en = (lambda x: None if not x or x.strip().lower() == 'none' else x.strip())(request.form.get('nombre_en', ''))
        categoria = request.form.get('categoria')
        matriz = request.form.get('matriz')
        matriz_en = (lambda x: None if not x or x.strip().lower() == 'none' else x.strip())(request.form.get('matriz_en', ''))
        tecnica = request.form.get('tecnica', '').strip() or None
        tecnica_en = (lambda x: None if not x or x.strip().lower() == 'none' else x.strip())(request.form.get('tecnica_en', ''))
        norma_referencia = request.form.get('norma_referencia', '').strip() or None
        vigencia = request.form.get('vigencia', '').strip() or None
        acreditada = 1 if request.form.get('acreditada') == 'on' else 0
        orden = int(request.form.get('orden', 0))
        activo = 1 if request.form.get('activo') == 'on' else 0
        
        # Obtener analitos del formulario (pueden venir como array o como campos simples)
        analitos_data = []
        
        # Buscar todos los keys que siguen el patrón analitos[índice][campo]
        analitos_dict = {}
        for key in request.form:
            match = re.match(r'analitos\[(\d+)\]\[(\w+)\]', key)
            if match:
                index = int(match.group(1))
                field = match.group(2)
                
                if index not in analitos_dict:
                    analitos_dict[index] = {}
                
                value = request.form.get(key, '').strip() or None
                if field == 'analito_en' and value:
                    # Normalizar valores vacíos o 'none'
                    value = None if value.strip().lower() in ['none', ''] else value.strip()
                
                analitos_dict[index][field] = value
        
        # Convertir dict a lista ordenada
        if analitos_dict:
            max_index = max(analitos_dict.keys())
            for i in range(max_index + 1):
                if i in analitos_dict:
                    analitos_data.append(analitos_dict[i])
        
        # Si no hay analitos en formato array, usar formato simple (compatibilidad hacia atrás)
        if not analitos_data:
            analito = request.form.get('analito', '').strip()
            analito_en = (lambda x: None if not x or x.strip().lower() == 'none' else x.strip())(request.form.get('analito_en', ''))
            limite_deteccion = request.form.get('limite_deteccion', '').strip() or None
            limite_cuantificacion = request.form.get('limite_cuantificacion', '').strip() or None
            
            if analito:
                analitos_data.append({
                    'analito': analito,
                    'analito_en': analito_en,
                    'limite_deteccion': limite_deteccion,
                    'limite_cuantificacion': limite_cuantificacion
                })
        
        # Insertar cada analito como una metodología separada
        if not analitos_data:
            flash('Debe ingresar al menos un analito', 'error')
            return render_template('admin/metodologia_form.html')
        
        created_count = 0
        for analito_data in analitos_data:
            if not analito_data.get('analito'):
                continue  # Saltar analitos sin nombre
            
            conn.execute('''
                INSERT INTO metodologias (codigo, nombre, nombre_en, categoria, analito, analito_en, matriz, matriz_en, 
                                         tecnica, tecnica_en, limite_deteccion, limite_cuantificacion, norma_referencia, 
                                         vigencia, acreditada, orden, activo)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                codigo,
                nombre,
                nombre_en,
                categoria,
                analito_data.get('analito'),
                analito_data.get('analito_en'),
                matriz,
                matriz_en,
                tecnica,
                tecnica_en,
                analito_data.get('limite_deteccion'),
                analito_data.get('limite_cuantificacion'),
                norma_referencia,
                vigencia,
                acreditada,
                orden,
                activo
            ))
            created_count += 1
        
        conn.commit()
        conn.close()
        
        if created_count > 1:
            flash(f'Metodología creada con {created_count} analitos correctamente', 'success')
        else:
            flash('Metodología creada correctamente', 'success')
        return redirect(url_for('admin_metodologias'))
    
    return render_template('admin/metodologia_form.html')

@app.route('/admin/metodologias/<int:metodologia_id>/editar', methods=['GET', 'POST'])
@login_required
def admin_metodologia_editar(metodologia_id):
    conn = get_db()
    
    if request.method == 'POST':
        conn.execute('''
            UPDATE metodologias 
            SET codigo=?, nombre=?, nombre_en=?, categoria=?, analito=?, analito_en=?, matriz=?, matriz_en=?,
                tecnica=?, tecnica_en=?, limite_deteccion=?, limite_cuantificacion=?, norma_referencia=?,
                vigencia=?, acreditada=?, orden=?, activo=?, updated_at=CURRENT_TIMESTAMP
            WHERE id=?
        ''', (
            request.form.get('codigo', '').strip() or None,
            request.form.get('nombre'),
            (lambda x: None if not x or x.strip().lower() == 'none' else x.strip())(request.form.get('nombre_en', '')),
            request.form.get('categoria'),
            request.form.get('analito'),
            (lambda x: None if not x or x.strip().lower() == 'none' else x.strip())(request.form.get('analito_en', '')),
            request.form.get('matriz'),
            (lambda x: None if not x or x.strip().lower() == 'none' else x.strip())(request.form.get('matriz_en', '')),
            request.form.get('tecnica', '').strip() or None,
            (lambda x: None if not x or x.strip().lower() == 'none' else x.strip())(request.form.get('tecnica_en', '')),
            request.form.get('limite_deteccion', '').strip() or None,
            request.form.get('limite_cuantificacion', '').strip() or None,
            request.form.get('norma_referencia', '').strip() or None,
            request.form.get('vigencia', '').strip() or None,
            1 if request.form.get('acreditada') == 'on' else 0,
            int(request.form.get('orden', 0)),
            1 if request.form.get('activo') == 'on' else 0,
            metodologia_id
        ))
        conn.commit()
        conn.close()
        flash('Metodología actualizada correctamente', 'success')
        return redirect(url_for('admin_metodologias'))
    
    metodologia = conn.execute('SELECT * FROM metodologias WHERE id = ?', (metodologia_id,)).fetchone()
    conn.close()
    
    if not metodologia:
        flash('Metodología no encontrada', 'error')
        return redirect(url_for('admin_metodologias'))
    
    return render_template('admin/metodologia_form.html', metodologia=metodologia)

@app.route('/admin/metodologias/<int:metodologia_id>/eliminar', methods=['POST'])
@login_required
@csrf_required
def admin_metodologia_eliminar(metodologia_id):
    conn = get_db()
    conn.execute('DELETE FROM metodologias WHERE id = ?', (metodologia_id,))
    conn.commit()
    conn.close()
    flash('Metodología eliminada', 'success')
    return redirect(url_for('admin_metodologias'))

# ============================================
# GESTIÓN DE GALERÍA DE IMÁGENES E INFOGRAFÍAS
# ============================================

@app.route('/admin/galeria')
@login_required
def admin_galeria():
    conn = get_db()
    tipo_filtro = request.args.get('tipo', '').strip()
    
    if tipo_filtro == 'video':
        # Filtrar solo videos
        imagenes = conn.execute('''
            SELECT * FROM galeria_imagenes 
            WHERE es_video = 1 
            ORDER BY es_video DESC, tipo, categoria, orden, id DESC
        ''').fetchall()
    elif tipo_filtro == 'imagen':
        # Filtrar solo imágenes (no videos, no infografías)
        imagenes = conn.execute('''
            SELECT * FROM galeria_imagenes 
            WHERE es_video = 0 AND (tipo IS NULL OR tipo = 'imagen' OR tipo = '')
            ORDER BY es_video DESC, tipo, categoria, orden, id DESC
        ''').fetchall()
    elif tipo_filtro == 'infografia':
        # Filtrar solo infografías
        imagenes = conn.execute('''
            SELECT * FROM galeria_imagenes 
            WHERE tipo = 'infografia' 
            ORDER BY es_video DESC, tipo, categoria, orden, id DESC
        ''').fetchall()
    else:
        # Mostrar todos
        imagenes = conn.execute('''
            SELECT * FROM galeria_imagenes 
            ORDER BY es_video DESC, tipo, categoria, orden, id DESC
        ''').fetchall()
    
    conn.close()
    return render_template('admin/galeria.html', imagenes=imagenes)

@app.route('/admin/galeria/nuevo', methods=['GET', 'POST'])
@login_required
@csrf_required
def admin_galeria_nuevo():
    if request.method == 'POST':
        conn = get_db()
        file = request.files.get('archivo')
        
        if not file or file.filename == '':
            flash('Debes seleccionar un archivo', 'error')
            return render_template('admin/galeria_form.html', csrf_token=generate_csrf_token())
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
            filename = timestamp + filename
            
            tipo = request.form.get('tipo', 'imagen')
            folder = 'infografias' if tipo == 'infografia' else 'galeria'
            upload_path = os.path.join(app.config['UPLOAD_FOLDER'], folder)
            os.makedirs(upload_path, exist_ok=True)
            
            filepath = os.path.join(upload_path, filename)
            file.save(filepath)
            
            # Detectar si es video
            extension = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
            es_video = 1 if extension in ['mp4', 'webm', 'mov'] else 0
            
            conn.execute('''
                INSERT INTO galeria_imagenes (titulo, descripcion, archivo, categoria, tipo, pagina, orden, activo, es_video)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                request.form.get('titulo'),
                request.form.get('descripcion', '').strip() or None,
                filename,
                request.form.get('categoria', '').strip() or None,
                tipo,
                request.form.get('pagina', '').strip() or None,
                int(request.form.get('orden', 0)),
                1 if request.form.get('activo') == 'on' else 0,
                es_video
            ))
            conn.commit()
            conn.close()
            flash('Imagen agregada correctamente', 'success')
            return redirect(url_for('admin_galeria'))
        else:
            flash('Tipo de archivo no permitido', 'error')
            return render_template('admin/galeria_form.html', csrf_token=generate_csrf_token())
    
    return render_template('admin/galeria_form.html', csrf_token=generate_csrf_token())

@app.route('/admin/galeria/<int:imagen_id>/editar', methods=['GET', 'POST'])
@login_required
@csrf_required
def admin_galeria_editar(imagen_id):
    conn = get_db()
    
    if request.method == 'POST':
        file = request.files.get('archivo')
        imagen = conn.execute('SELECT * FROM galeria_imagenes WHERE id = ?', (imagen_id,)).fetchone()
        
        filename = imagen['archivo']  # Mantener el archivo actual por defecto
        
        # Si se sube un nuevo archivo, reemplazar el anterior
        if file and file.filename != '':
            if allowed_file(file.filename):
                # Eliminar archivo anterior si existe
                tipo_actual = imagen['tipo']
                folder_actual = 'infografias' if tipo_actual == 'infografia' else 'galeria'
                old_filepath = os.path.join(app.config['UPLOAD_FOLDER'], folder_actual, imagen['archivo'])
                if os.path.exists(old_filepath):
                    try:
                        os.remove(old_filepath)
                    except:
                        pass
                
                # Guardar nuevo archivo
                new_filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
                new_filename = timestamp + new_filename
                
                tipo = request.form.get('tipo', 'imagen')
                folder = 'infografias' if tipo == 'infografia' else 'galeria'
                upload_path = os.path.join(app.config['UPLOAD_FOLDER'], folder)
                os.makedirs(upload_path, exist_ok=True)
                
                filepath = os.path.join(upload_path, new_filename)
                file.save(filepath)
                filename = new_filename
            else:
                flash('Tipo de archivo no permitido', 'error')
                return redirect(url_for('admin_galeria_editar', imagen_id=imagen_id))
        
        # Detectar si es video (usar el archivo nuevo o el actual)
        archivo_actual = filename
        extension = archivo_actual.rsplit('.', 1)[1].lower() if '.' in archivo_actual else ''
        es_video = 1 if extension in ['mp4', 'webm', 'mov'] else 0
        
        conn.execute('''
            UPDATE galeria_imagenes 
            SET titulo=?, descripcion=?, archivo=?, categoria=?, tipo=?, pagina=?, orden=?, activo=?, es_video=?, updated_at=CURRENT_TIMESTAMP
            WHERE id=?
        ''', (
            request.form.get('titulo'),
            request.form.get('descripcion', '').strip() or None,
            filename,
            request.form.get('categoria', '').strip() or None,
            request.form.get('tipo', 'imagen'),
            request.form.get('pagina', '').strip() or None,
            int(request.form.get('orden', 0)),
            1 if request.form.get('activo') == 'on' else 0,
            es_video,
            imagen_id
        ))
        conn.commit()
        conn.close()
        flash('Imagen actualizada correctamente', 'success')
        return redirect(url_for('admin_galeria'))
    
    imagen = conn.execute('SELECT * FROM galeria_imagenes WHERE id = ?', (imagen_id,)).fetchone()
    conn.close()
    
    if not imagen:
        flash('Imagen no encontrada', 'error')
        return redirect(url_for('admin_galeria'))
    
    return render_template('admin/galeria_form.html', imagen=dict(imagen), csrf_token=generate_csrf_token())

@app.route('/admin/galeria/<int:imagen_id>/eliminar', methods=['POST'])
@login_required
@csrf_required
def admin_galeria_eliminar(imagen_id):
    conn = get_db()
    imagen = conn.execute('SELECT * FROM galeria_imagenes WHERE id = ?', (imagen_id,)).fetchone()
    
    if imagen:
        # Eliminar archivo físico
        tipo = imagen['tipo']
        folder = 'infografias' if tipo == 'infografia' else 'galeria'
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], folder, imagen['archivo'])
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except:
                pass
        
        conn.execute('DELETE FROM galeria_imagenes WHERE id = ?', (imagen_id,))
        conn.commit()
    
    conn.close()
    flash('Imagen eliminada', 'success')
    return redirect(url_for('admin_galeria'))

@app.route('/static/uploads/proyectos/<path:filename>')
def serve_proyecto_image(filename):
    """Sirve imágenes de proyectos"""
    upload_folder = os.path.abspath(os.path.join(app.config['UPLOAD_FOLDER'], 'proyectos'))
    file_path = os.path.join(upload_folder, filename)
    file_path = os.path.normpath(file_path)
    upload_folder = os.path.normpath(upload_folder)
    
    if not file_path.startswith(upload_folder):
        return "Acceso denegado", 403
    
    if os.path.exists(file_path):
        return send_file(file_path)
    return "Archivo no encontrado", 404

@app.route('/static/uploads/galeria/<path:filename>')
@app.route('/static/uploads/infografias/<path:filename>')
def serve_galeria_image(filename):
    """Sirve imágenes de la galería e infografías"""
    # Determinar la carpeta basándose en la ruta
    if 'infografias' in request.path:
        folder = 'infografias'
    else:
        folder = 'galeria'
    
    upload_folder = os.path.abspath(os.path.join(app.config['UPLOAD_FOLDER'], folder))
    file_path = os.path.join(upload_folder, filename)
    
    # Normalizar rutas para seguridad
    file_path = os.path.normpath(file_path)
    upload_folder = os.path.normpath(upload_folder)
    
    # Verificar que el archivo está dentro del directorio permitido
    if not file_path.startswith(upload_folder):
        return "Acceso denegado", 403
    
    if os.path.exists(file_path):
        return send_file(file_path)
    return "Archivo no encontrado", 404

@app.route('/galeria/<path:filename>')
def serve_galeria_image_simple(filename):
    """Ruta simplificada para servir imágenes de la galería - busca en ambas carpetas"""
    # Buscar primero en galeria, luego en infografias
    for folder in ['galeria', 'infografias']:
        upload_folder = os.path.abspath(os.path.join(app.config['UPLOAD_FOLDER'], folder))
        file_path = os.path.join(upload_folder, filename)
        file_path = os.path.normpath(file_path)
        upload_folder = os.path.normpath(upload_folder)
        
        if file_path.startswith(upload_folder) and os.path.exists(file_path):
            return send_file(file_path)
    
    return "Archivo no encontrado", 404

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
        
        # Retornar URL relativa para que funcione correctamente
        url = f'/static/uploads/{folder}/{filename}'
        return jsonify({'url': url, 'filename': filename})
    
    return jsonify({'error': 'Tipo de archivo no permitido'}), 400

@app.route('/static/uploads/<path:filename>')
def uploaded_file(filename):
    """Sirve archivos subidos desde static/uploads"""
    try:
        # Construir la ruta completa del archivo usando ruta absoluta
        upload_folder = os.path.abspath(app.config['UPLOAD_FOLDER'])
        file_path = os.path.join(upload_folder, filename)
        
        # Normalizar la ruta para evitar problemas con ../
        file_path = os.path.normpath(file_path)
        upload_folder = os.path.normpath(upload_folder)
        
        # Verificar que el archivo está dentro del directorio de uploads (seguridad)
        if not file_path.startswith(upload_folder):
            return "Acceso denegado", 403
        
        # Verificar que el archivo existe
        if not os.path.exists(file_path):
            # Intentar con ruta relativa también
            rel_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            if os.path.exists(rel_path):
                file_path = os.path.abspath(rel_path)
            else:
                return f"Archivo no encontrado: {filename}<br>Ruta absoluta probada: {file_path}<br>Ruta relativa probada: {rel_path}", 404
        
        # Usar send_file para mayor control
        return send_file(file_path, as_attachment=False)
    except Exception as e:
        import traceback
        return f"Error al servir archivo: {str(e)}<br><pre>{traceback.format_exc()}</pre>", 500

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
        # Manejar imagen si se sube
        imagen_filename = None
        if 'imagen' in request.files:
            file = request.files['imagen']
            if file and file.filename != '' and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
                filename = timestamp + filename
                upload_path = os.path.join(app.config['UPLOAD_FOLDER'], 'proyectos')
                os.makedirs(upload_path, exist_ok=True)
                filepath = os.path.join(upload_path, filename)
                file.save(filepath)
                imagen_filename = filename
        
        conn.execute('''
            INSERT INTO proyectos (titulo, descripcion, tipo, enlace, orden, activo, titulo_en, descripcion_en, tipo_en,
                                   codigo_proyecto, año_inicio, año_fin, investigadores, presupuesto, resultados, estado, financiador, imagen)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            request.form.get('codigo_proyecto', '').strip() or None,
            int(request.form.get('año_inicio')) if request.form.get('año_inicio') else None,
            int(request.form.get('año_fin')) if request.form.get('año_fin') else None,
            request.form.get('investigadores', '').strip() or None,
            request.form.get('presupuesto', '').strip() or None,
            request.form.get('resultados', '').strip() or None,
            request.form.get('estado', 'en_curso'),
            request.form.get('financiador', '').strip() or None,
            imagen_filename
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
        # Manejar imagen si se sube
        proyecto_actual = conn.execute('SELECT * FROM proyectos WHERE id = ?', (proyecto_id,)).fetchone()
        # sqlite3.Row no tiene .get(), usar acceso directo con manejo de errores
        imagen_filename = None
        if proyecto_actual:
            try:
                imagen_filename = proyecto_actual['imagen']
            except (KeyError, IndexError):
                imagen_filename = None
        
        if 'imagen' in request.files:
            file = request.files['imagen']
            if file and file.filename != '' and allowed_file(file.filename):
                # Eliminar imagen anterior si existe
                if imagen_filename:
                    old_filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'proyectos', imagen_filename)
                    if os.path.exists(old_filepath):
                        try:
                            os.remove(old_filepath)
                        except:
                            pass
                
                # Guardar nueva imagen
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
                filename = timestamp + filename
                upload_path = os.path.join(app.config['UPLOAD_FOLDER'], 'proyectos')
                os.makedirs(upload_path, exist_ok=True)
                filepath = os.path.join(upload_path, filename)
                file.save(filepath)
                imagen_filename = filename
        
        conn.execute('''
            UPDATE proyectos 
            SET titulo=?, descripcion=?, tipo=?, enlace=?, orden=?, activo=?, 
                titulo_en=?, descripcion_en=?, tipo_en=?, updated_at=CURRENT_TIMESTAMP,
                codigo_proyecto=?, año_inicio=?, año_fin=?, investigadores=?, presupuesto=?, resultados=?, estado=?, financiador=?, imagen=?
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
            request.form.get('codigo_proyecto', '').strip() or None,
            int(request.form.get('año_inicio')) if request.form.get('año_inicio') else None,
            int(request.form.get('año_fin')) if request.form.get('año_fin') else None,
            request.form.get('investigadores', '').strip() or None,
            request.form.get('presupuesto', '').strip() or None,
            request.form.get('resultados', '').strip() or None,
            request.form.get('estado', 'en_curso'),
            request.form.get('financiador', '').strip() or None,
            imagen_filename,
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
            INSERT INTO publicaciones (titulo, descripcion, revista, año, enlace, tags, orden, activo, titulo_en, descripcion_en,
                                     doi, autores, volumen, numero, paginas, tipo_publicacion, factor_impacto, base_datos)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            request.form.get('doi', '').strip() or None,
            request.form.get('autores', '').strip() or None,
            request.form.get('volumen', '').strip() or None,
            request.form.get('numero', '').strip() or None,
            request.form.get('paginas', '').strip() or None,
            request.form.get('tipo_publicacion', '').strip() or None,
            request.form.get('factor_impacto', '').strip() or None,
            request.form.get('base_datos', '').strip() or None
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
                titulo_en=?, descripcion_en=?, updated_at=CURRENT_TIMESTAMP,
                doi=?, autores=?, volumen=?, numero=?, paginas=?, tipo_publicacion=?, factor_impacto=?, base_datos=?
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
            request.form.get('doi', '').strip() or None,
            request.form.get('autores', '').strip() or None,
            request.form.get('volumen', '').strip() or None,
            request.form.get('numero', '').strip() or None,
            request.form.get('paginas', '').strip() or None,
            request.form.get('tipo_publicacion', '').strip() or None,
            request.form.get('factor_impacto', '').strip() or None,
            request.form.get('base_datos', '').strip() or None,
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
            # Asegurar que la columna destacada existe
            try:
                conn.execute('ALTER TABLE eventos ADD COLUMN destacada INTEGER DEFAULT 0')
                conn.commit()
            except sqlite3.OperationalError:
                pass  # La columna ya existe
            
            activo = 1 if request.form.get('activo') == 'on' or request.form.get('activo') == '' else 0
            destacada = 1 if request.form.get('destacada') == 'on' else 0
            
            conn.execute('''
                INSERT INTO eventos (titulo, fecha, meta, descripcion, enlace, texto_boton, orden, destacada, activo, titulo_en, descripcion_en, meta_en, texto_boton_en)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                request.form.get('titulo', '').strip(),
                request.form.get('fecha', '').strip(),
                request.form.get('meta', '').strip(),
                request.form.get('descripcion', '').strip(),
                request.form.get('enlace', '').strip(),
                request.form.get('texto_boton', 'Ver más').strip(),
                int(request.form.get('orden', 0) or 0),
                destacada,
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
    try:
        conn = get_db()
        
        # Asegurar que la columna destacada existe
        try:
            conn.execute('ALTER TABLE eventos ADD COLUMN destacada INTEGER DEFAULT 0')
            conn.commit()
        except sqlite3.OperationalError:
            pass  # La columna ya existe
        
        if request.method == 'POST':
            destacada = 1 if request.form.get('destacada') == 'on' else 0
            conn.execute('''
                UPDATE eventos 
                SET titulo=?, fecha=?, meta=?, descripcion=?, enlace=?, texto_boton=?, orden=?, destacada=?, activo=?, 
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
                destacada,
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
        
        # Asegurar que el campo destacada existe (para eventos antiguos)
        evento_dict = dict(evento)
        if 'destacada' not in evento_dict:
            evento_dict['destacada'] = 0
        
        return render_template('admin/evento_form.html', evento=evento_dict)
    except Exception as e:
        import traceback
        traceback.print_exc()
        flash(f'Error al cargar evento: {str(e)}', 'error')
        return redirect(url_for('admin_eventos'))

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

# ============================================
# GESTIÓN DE CORREOS DE CONTACTO
# ============================================

def enviar_correo_contacto(nombre, email, telefono, tipo_consulta, mensaje, institucion=None):
    """
    Envía un correo con la consulta del formulario de contacto
    a los correos configurados para ese tipo de consulta
    """
    # Obtener correos de destino para este tipo de consulta
    conn = get_db()
    correos_destino = conn.execute(
        'SELECT email FROM correos_contacto WHERE tipo_consulta = ? AND activo = 1',
        (tipo_consulta,)
    ).fetchall()
    conn.close()
    
    if not correos_destino:
        return False, "No hay correos configurados para este tipo de consulta"
    
    # Configuración SMTP desde variables de entorno
    smtp_host = os.environ.get('SMTP_HOST', '')
    smtp_port = int(os.environ.get('SMTP_PORT', '587'))
    smtp_user = os.environ.get('SMTP_USER', '')
    smtp_password = os.environ.get('SMTP_PASSWORD', '')
    smtp_from = os.environ.get('SMTP_FROM', smtp_user)
    
    if not smtp_host or not smtp_user or not smtp_password:
        return False, "Configuración SMTP no encontrada"
    
    # Mapeo de tipos de consulta a nombres legibles
    tipos_consulta = {
        'analisis': 'Solicitud de análisis',
        'servicios': 'Consulta sobre servicios',
        'capacitacion': 'Capacitación y docencia',
        'investigacion': 'Investigación y colaboración',
        'otra': 'Otra consulta'
    }
    
    tipo_nombre = tipos_consulta.get(tipo_consulta, tipo_consulta)
    
    # Crear mensaje
    msg = MIMEMultipart()
    msg['From'] = smtp_from
    msg['To'] = ', '.join([row['email'] for row in correos_destino])
    msg['Subject'] = f'Nueva consulta: {tipo_nombre} - FARMAVET'
    msg['Reply-To'] = email
    
    # Cuerpo del mensaje
    cuerpo = f"""
Nueva consulta recibida desde el formulario de contacto de FARMAVET

Tipo de consulta: {tipo_nombre}
Nombre: {nombre}
Email: {email}
Teléfono: {telefono or 'No proporcionado'}
Institución/Empresa: {institucion or 'No proporcionado'}

Mensaje:
{mensaje}

---
Este correo fue enviado automáticamente desde el sitio web de FARMAVET.
Para responder, use el email del remitente: {email}
"""
    
    msg.attach(MIMEText(cuerpo, 'plain', 'utf-8'))
    
    # Enviar correo
    try:
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"Intentando conectar a SMTP: {smtp_host}:{smtp_port}")
        server = smtplib.SMTP(smtp_host, smtp_port)
        logger.info("Conexión SMTP establecida")
        
        server.starttls()
        logger.info("TLS iniciado")
        
        logger.info(f"Intentando login con usuario: {smtp_user}")
        server.login(smtp_user, smtp_password)
        logger.info("Login SMTP exitoso")
        
        logger.info(f"Enviando correo a: {msg['To']}")
        server.send_message(msg)
        logger.info("Correo enviado exitosamente")
        
        server.quit()
        return True, "Correo enviado correctamente"
    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"Error de autenticación SMTP: {str(e)}")
        return False, f"Error de autenticación: Verifica usuario y contraseña SMTP"
    except smtplib.SMTPConnectError as e:
        logger.error(f"Error de conexión SMTP: {str(e)}")
        return False, f"Error de conexión: No se pudo conectar al servidor SMTP"
    except smtplib.SMTPException as e:
        logger.error(f"Error SMTP: {str(e)}")
        return False, f"Error SMTP: {str(e)}"
    except Exception as e:
        logger.error(f"Error inesperado al enviar correo: {str(e)}")
        return False, f"Error al enviar correo: {str(e)}"

@app.route('/contacto/enviar', methods=['POST'])
@csrf_required
def contacto_enviar():
    """Procesa el formulario de contacto y envía correos"""
    nombre = request.form.get('nombre', '').strip()
    email = request.form.get('email', '').strip()
    telefono = request.form.get('telefono', '').strip()
    institucion = request.form.get('institucion', '').strip()
    tipo_consulta = request.form.get('tipo', '').strip()
    mensaje = request.form.get('mensaje', '').strip()
    
    # Validaciones
    if not nombre or not email or not tipo_consulta or not mensaje:
        flash('Por favor completa todos los campos requeridos', 'error')
        return redirect('/contacto.html#contacto-form')
    
    # Validar formato de email
    if '@' not in email or '.' not in email.split('@')[1]:
        flash('Por favor ingresa un email válido', 'error')
        return redirect('/contacto.html#contacto-form')
    
    # Enviar correo
    exito, mensaje_resultado = enviar_correo_contacto(nombre, email, telefono, tipo_consulta, mensaje, institucion)
    
    # Si la petición es AJAX, retornar JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
        if exito:
            return jsonify({
                'success': True,
                'message': 'Tu consulta ha sido enviada correctamente. Nos pondremos en contacto contigo pronto.'
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': f'Hubo un error al enviar tu consulta. Por favor intenta nuevamente o contáctanos directamente. Error: {mensaje_resultado}'
            }), 400
    
    # Si no es AJAX, usar flash y redirect (compatibilidad)
    if exito:
        flash('Tu consulta ha sido enviada correctamente. Nos pondremos en contacto contigo pronto.', 'success')
    else:
        flash(f'Hubo un error al enviar tu consulta. Por favor intenta nuevamente o contáctanos directamente. Error: {mensaje_resultado}', 'error')
    
    return redirect('/contacto.html#contacto-form')

@app.route('/admin/redes-sociales', methods=['GET', 'POST'])
@login_required
@csrf_required
def admin_redes_sociales():
    """Configuración de redes sociales para feeds (gratuito)"""
    conn = get_db()
    
    if request.method == 'POST':
        instagram_username = request.form.get('instagram_username', '').strip()
        linkedin_company_id = request.form.get('linkedin_company_id', '').strip()
        linkedin_page_url = request.form.get('linkedin_page_url', '').strip()
        
        # Limpiar @ si lo incluyeron
        if instagram_username and instagram_username.startswith('@'):
            instagram_username = instagram_username[1:]
        
        # Verificar si ya existe configuración
        config_existente = conn.execute('SELECT * FROM configuracion_redes WHERE activo = 1 LIMIT 1').fetchone()
        
        if config_existente:
            # Actualizar existente
            conn.execute('''
                UPDATE configuracion_redes 
                SET instagram_username = ?, linkedin_company_id = ?, linkedin_page_url = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (instagram_username or None, linkedin_company_id or None, linkedin_page_url or None, config_existente['id']))
        else:
            # Crear nueva
            conn.execute('''
                INSERT INTO configuracion_redes (instagram_username, linkedin_company_id, linkedin_page_url, activo)
                VALUES (?, ?, ?, 1)
            ''', (instagram_username or None, linkedin_company_id or None, linkedin_page_url or None))
        
        conn.commit()
        conn.close()
        flash('Configuración de redes sociales actualizada correctamente', 'success')
        return redirect(url_for('admin_redes_sociales'))
    
    # GET: Mostrar formulario
    config = conn.execute('SELECT * FROM configuracion_redes WHERE activo = 1 LIMIT 1').fetchone()
    conn.close()
    return render_template('admin/redes_sociales.html', config=config)

@app.route('/admin/correos-contacto')
@login_required
def admin_correos_contacto():
    """Lista los correos configurados para cada tipo de consulta"""
    conn = get_db()
    
    # Obtener todos los correos agrupados por tipo
    correos = conn.execute('''
        SELECT id, tipo_consulta, email, activo, created_at
        FROM correos_contacto
        ORDER BY tipo_consulta, email
    ''').fetchall()
    
    # Agrupar por tipo
    correos_por_tipo = {}
    tipos_consulta = {
        'analisis': 'Solicitud de análisis',
        'servicios': 'Consulta sobre servicios',
        'capacitacion': 'Capacitación y docencia',
        'investigacion': 'Investigación y colaboración',
        'otra': 'Otra consulta'
    }
    
    for tipo in tipos_consulta.keys():
        correos_por_tipo[tipo] = [row for row in correos if row['tipo_consulta'] == tipo]
    
    conn.close()
    return render_template('admin/correos_contacto.html', correos_por_tipo=correos_por_tipo, tipos_consulta=tipos_consulta)

@app.route('/admin/correos-contacto/nuevo', methods=['GET', 'POST'])
@login_required
@csrf_required
def admin_correo_contacto_nuevo():
    """Agrega un nuevo correo de destino"""
    if request.method == 'POST':
        tipo_consulta = request.form.get('tipo_consulta', '').strip()
        email = request.form.get('email', '').strip()
        activo = 1 if request.form.get('activo') == 'on' else 0
        
        if not tipo_consulta or not email:
            flash('Todos los campos son requeridos', 'error')
            tipos_consulta = {
                'analisis': 'Solicitud de análisis',
                'servicios': 'Consulta sobre servicios',
                'capacitacion': 'Capacitación y docencia',
                'investigacion': 'Investigación y colaboración',
                'otra': 'Otra consulta'
            }
            return render_template('admin/correo_contacto_form.html', tipos_consulta=tipos_consulta)
        
        # Validar formato de email
        if '@' not in email or '.' not in email.split('@')[1]:
            flash('Por favor ingresa un email válido', 'error')
            tipos_consulta = {
                'analisis': 'Solicitud de análisis',
                'servicios': 'Consulta sobre servicios',
                'capacitacion': 'Capacitación y docencia',
                'investigacion': 'Investigación y colaboración',
                'otra': 'Otra consulta'
            }
            return render_template('admin/correo_contacto_form.html', tipos_consulta=tipos_consulta)
        
        conn = get_db()
        try:
            conn.execute('''
                INSERT INTO correos_contacto (tipo_consulta, email, activo, updated_at)
                VALUES (?, ?, ?, ?)
            ''', (tipo_consulta, email, activo, datetime.now().isoformat()))
            conn.commit()
            conn.close()
            flash('Correo agregado correctamente', 'success')
            return redirect(url_for('admin_correos_contacto'))
        except sqlite3.IntegrityError:
            conn.close()
            flash('Este correo ya está configurado para este tipo de consulta', 'error')
            tipos_consulta = {
                'analisis': 'Solicitud de análisis',
                'servicios': 'Consulta sobre servicios',
                'capacitacion': 'Capacitación y docencia',
                'investigacion': 'Investigación y colaboración',
                'otra': 'Otra consulta'
            }
            return render_template('admin/correo_contacto_form.html', tipos_consulta=tipos_consulta)
    
    tipos_consulta = {
        'analisis': 'Solicitud de análisis',
        'servicios': 'Consulta sobre servicios',
        'capacitacion': 'Capacitación y docencia',
        'investigacion': 'Investigación y colaboración',
        'otra': 'Otra consulta'
    }
    return render_template('admin/correo_contacto_form.html', tipos_consulta=tipos_consulta)

@app.route('/admin/correos-contacto/<int:correo_id>/editar', methods=['GET', 'POST'])
@login_required
@csrf_required
def admin_correo_contacto_editar(correo_id):
    """Edita un correo de destino"""
    conn = get_db()
    
    if request.method == 'POST':
        tipo_consulta = request.form.get('tipo_consulta', '').strip()
        email = request.form.get('email', '').strip()
        activo = 1 if request.form.get('activo') == 'on' else 0
        
        if not tipo_consulta or not email:
            flash('Todos los campos son requeridos', 'error')
            correo = conn.execute('SELECT * FROM correos_contacto WHERE id = ?', (correo_id,)).fetchone()
            conn.close()
            tipos_consulta = {
                'analisis': 'Solicitud de análisis',
                'servicios': 'Consulta sobre servicios',
                'capacitacion': 'Capacitación y docencia',
                'investigacion': 'Investigación y colaboración',
                'otra': 'Otra consulta'
            }
            return render_template('admin/correo_contacto_form.html', correo=correo, tipos_consulta=tipos_consulta)
        
        # Validar formato de email
        if '@' not in email or '.' not in email.split('@')[1]:
            flash('Por favor ingresa un email válido', 'error')
            correo = conn.execute('SELECT * FROM correos_contacto WHERE id = ?', (correo_id,)).fetchone()
            conn.close()
            tipos_consulta = {
                'analisis': 'Solicitud de análisis',
                'servicios': 'Consulta sobre servicios',
                'capacitacion': 'Capacitación y docencia',
                'investigacion': 'Investigación y colaboración',
                'otra': 'Otra consulta'
            }
            return render_template('admin/correo_contacto_form.html', correo=correo, tipos_consulta=tipos_consulta)
        
        try:
            conn.execute('''
                UPDATE correos_contacto
                SET tipo_consulta = ?, email = ?, activo = ?, updated_at = ?
                WHERE id = ?
            ''', (tipo_consulta, email, activo, datetime.now().isoformat(), correo_id))
            conn.commit()
            conn.close()
            flash('Correo actualizado correctamente', 'success')
            return redirect(url_for('admin_correos_contacto'))
        except sqlite3.IntegrityError:
            conn.close()
            flash('Este correo ya está configurado para este tipo de consulta', 'error')
            correo = conn.execute('SELECT * FROM correos_contacto WHERE id = ?', (correo_id,)).fetchone()
            tipos_consulta = {
                'analisis': 'Solicitud de análisis',
                'servicios': 'Consulta sobre servicios',
                'capacitacion': 'Capacitación y docencia',
                'investigacion': 'Investigación y colaboración',
                'otra': 'Otra consulta'
            }
            return render_template('admin/correo_contacto_form.html', correo=correo, tipos_consulta=tipos_consulta)
    
    correo = conn.execute('SELECT * FROM correos_contacto WHERE id = ?', (correo_id,)).fetchone()
    conn.close()
    
    if not correo:
        flash('Correo no encontrado', 'error')
        return redirect(url_for('admin_correos_contacto'))
    
    tipos_consulta = {
        'analisis': 'Solicitud de análisis',
        'servicios': 'Consulta sobre servicios',
        'capacitacion': 'Capacitación y docencia',
        'investigacion': 'Investigación y colaboración',
        'otra': 'Otra consulta'
    }
    return render_template('admin/correo_contacto_form.html', correo=correo, tipos_consulta=tipos_consulta)

@app.route('/admin/correos-contacto/<int:correo_id>/eliminar', methods=['POST'])
@login_required
@csrf_required
def admin_correo_contacto_eliminar(correo_id):
    """Elimina un correo de destino"""
    conn = get_db()
    conn.execute('DELETE FROM correos_contacto WHERE id = ?', (correo_id,))
    conn.commit()
    conn.close()
    flash('Correo eliminado', 'success')
    return redirect(url_for('admin_correos_contacto'))

# Inicializar base de datos automáticamente (también para Gunicorn)
# ============================================
# SEO: SITEMAP Y ROBOTS.TXT
# ============================================

@app.route('/sitemap.xml')
def sitemap():
    """Genera sitemap.xml dinámico para SEO"""
    from flask import Response
    from datetime import datetime
    
    base_url = "https://www.laboratoriofarmavet.cl"
    pages = [
        {'loc': '/', 'changefreq': 'weekly', 'priority': '1.0'},
        {'loc': '/quienes-somos.html', 'changefreq': 'monthly', 'priority': '0.9'},
        {'loc': '/servicios.html', 'changefreq': 'weekly', 'priority': '1.0'},
        {'loc': '/investigacion.html', 'changefreq': 'weekly', 'priority': '0.9'},
        {'loc': '/docencia.html', 'changefreq': 'monthly', 'priority': '0.8'},
        {'loc': '/casa-omsa.html', 'changefreq': 'monthly', 'priority': '0.8'},
        {'loc': '/noticias.html', 'changefreq': 'weekly', 'priority': '0.7'},
        {'loc': '/faq.html', 'changefreq': 'monthly', 'priority': '0.8'},
        {'loc': '/contacto.html', 'changefreq': 'monthly', 'priority': '0.9'},
    ]
    
    sitemap_xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    sitemap_xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    
    for page in pages:
        sitemap_xml += '  <url>\n'
        sitemap_xml += f'    <loc>{base_url}{page["loc"]}</loc>\n'
        sitemap_xml += f'    <changefreq>{page["changefreq"]}</changefreq>\n'
        sitemap_xml += f'    <priority>{page["priority"]}</priority>\n'
        sitemap_xml += '  </url>\n'
    
    sitemap_xml += '</urlset>'
    
    return Response(sitemap_xml, mimetype='application/xml')

@app.route('/robots.txt')
def robots():
    """Genera robots.txt para SEO"""
    from flask import Response
    
    robots_txt = """User-agent: *
Allow: /
Disallow: /admin/
Disallow: /static/uploads/

Sitemap: https://www.laboratoriofarmavet.cl/sitemap.xml
"""
    return Response(robots_txt, mimetype='text/plain')

# Ejecutar init_db() siempre para asegurar que todas las tablas existan
# (usa CREATE TABLE IF NOT EXISTS, así que es seguro)
init_db()
print("✅ Base de datos verificada e inicializada")

if __name__ == '__main__':
    print("✅ Base de datos inicializada")
    print("🌐 Servidor iniciado en http://localhost:5000")
    print("🔐 Panel de administración: http://localhost:5000/admin/login")
    print("   Usuario: admin")
    print("   ⚠️  Contraseña por defecto: admin123 - CAMBIAR INMEDIATAMENTE")
    app.run(debug=True, host='0.0.0.0', port=5000)

