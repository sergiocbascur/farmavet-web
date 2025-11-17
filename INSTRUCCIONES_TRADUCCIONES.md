# Instrucciones para Traducciones - FARMAVET Web

## Instalación

Primero, instala las dependencias:

```bash
pip install -r requirements.txt
```

## Configuración Inicial

1. **Extraer strings para traducir** (primera vez):
```bash
pybabel extract -F babel.cfg -k _l -o messages.pot .
```

2. **Inicializar traducciones** (si no existen):
```bash
pybabel init -i messages.pot -d translations -l en
```

## Flujo de Trabajo Normal

### 1. Marcar strings en templates

En los templates, marca los strings que quieres traducir con `{{ _('Texto a traducir') }}`:

```jinja2
<h1>{{ _('Bienvenido a FARMAVET') }}</h1>
<p>{{ _('Laboratorio de Farmacología Veterinaria') }}</p>
```

### 2. Extraer strings actualizados

Después de agregar nuevos strings, extrae los cambios:

```bash
pybabel extract -F babel.cfg -k _l -o messages.pot .
```

### 3. Actualizar archivos de traducción

Actualiza los archivos `.po` con los nuevos strings:

```bash
pybabel update -i messages.pot -d translations
```

### 4. Traducir

Edita los archivos `.po` en `translations/en/LC_MESSAGES/messages.po` y agrega las traducciones:

```po
msgid "Bienvenido a FARMAVET"
msgstr "Welcome to FARMAVET"
```

### 5. Compilar traducciones

Compila los archivos `.po` a `.mo` (binarios):

```bash
python compile_translations.py
```

O manualmente:
```bash
pybabel compile -d translations
```

### 6. Reiniciar servidor

Reinicia el servidor Flask para que los cambios surtan efecto.

## Traducción de Contenido Dinámico (Base de Datos)

Para traducir contenido que viene de la base de datos (noticias, programas, etc.), tienes dos opciones:

### Opción 1: Campos adicionales en la misma tabla

Agrega columnas `_en` para cada campo traducible:

```sql
ALTER TABLE noticias ADD COLUMN titulo_en TEXT;
ALTER TABLE noticias ADD COLUMN descripcion_en TEXT;
ALTER TABLE noticias ADD COLUMN contenido_en TEXT;
```

Luego en los templates, usa la función helper:

```jinja2
<h2>{{ get_translated_field(noticia, 'titulo') }}</h2>
<p>{{ get_translated_field(noticia, 'descripcion') }}</p>
```

### Opción 2: Tabla de traducciones separada (Recomendado)

Crea una tabla de traducciones para mayor flexibilidad:

```sql
CREATE TABLE traducciones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tabla TEXT NOT NULL,
    registro_id INTEGER NOT NULL,
    campo TEXT NOT NULL,
    idioma TEXT NOT NULL,
    valor TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(tabla, registro_id, campo, idioma)
);
```

## Ejemplo Completo

### En el template:

```jinja2
<!-- Contenido estático -->
<h1>{{ _('Nuestros Servicios') }}</h1>

<!-- Contenido dinámico -->
{% for noticia in noticias %}
  <article>
    <h2>{{ get_translated_field(noticia, 'titulo') }}</h2>
    <p>{{ get_translated_field(noticia, 'descripcion') }}</p>
  </article>
{% endfor %}
```

### En la base de datos:

```sql
-- Noticia en español (por defecto)
INSERT INTO noticias (titulo, descripcion) 
VALUES ('Nueva investigación', 'Descripción en español');

-- Traducción en inglés
UPDATE noticias SET titulo_en = 'New Research', descripcion_en = 'Description in English' 
WHERE id = 1;
```

## Comandos Rápidos

```bash
# Extraer strings
pybabel extract -F babel.cfg -k _l -o messages.pot .

# Actualizar traducciones
pybabel update -i messages.pot -d translations

# Compilar
pybabel compile -d translations

# O usar el script
python compile_translations.py
```

## Notas Importantes

- **No edites los archivos `.mo`** - Son binarios generados automáticamente
- **Edita solo los archivos `.po`** - Son los archivos de texto con las traducciones
- **Reinicia Flask después de compilar** - Los cambios solo se aplican después de reiniciar
- **En producción (VPS)**: Compila las traducciones antes de desplegar
- **Backup**: Mantén backups de tus archivos `.po` - Son tu fuente de verdad

## Próximos Pasos

1. ✅ Sistema básico configurado
2. ⏳ Marcar strings estáticos en templates
3. ⏳ Agregar campos de traducción en BD para contenido dinámico
4. ⏳ Traducir todo al inglés
5. ⏳ Configurar detección automática de idioma del navegador

