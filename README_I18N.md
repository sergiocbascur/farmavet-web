# Sistema de Internacionalización (i18n) - FARMAVET Web

## Configuración

Este proyecto utiliza Flask-Babel para la internacionalización. El sistema permite traducir tanto el contenido estático de los templates como el contenido dinámico de la base de datos.

## Estructura

```
farmavet-web/
├── translations/
│   ├── es/
│   │   └── LC_MESSAGES/
│   │       ├── messages.po  (archivo de traducciones en español)
│   │       └── messages.mo  (compilado, generado automáticamente)
│   └── en/
│       └── LC_MESSAGES/
│           ├── messages.po  (archivo de traducciones en inglés)
│           └── messages.mo  (compilado, generado automáticamente)
├── babel.cfg  (configuración de Babel)
└── app.py     (configuración de Flask-Babel)
```

## Uso en Templates

### Contenido Estático

En los templates Jinja2, usa la función `_()` para marcar strings traducibles:

```jinja2
<h1>{{ _('Welcome to FARMAVET') }}</h1>
<p>{{ _('Laboratory of Veterinary Pharmacology') }}</p>
```

### Contenido Dinámico

Para contenido que viene de la base de datos, necesitas agregar campos de traducción en las tablas o usar una tabla de traducciones separada.

**Opción 1: Campos de traducción en la misma tabla**
```sql
ALTER TABLE noticias ADD COLUMN titulo_en TEXT;
ALTER TABLE noticias ADD COLUMN descripcion_en TEXT;
```

**Opción 2: Tabla de traducciones separada (recomendado para escalabilidad)**
```sql
CREATE TABLE traducciones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tabla TEXT NOT NULL,
    registro_id INTEGER NOT NULL,
    campo TEXT NOT NULL,
    idioma TEXT NOT NULL,
    valor TEXT,
    UNIQUE(tabla, registro_id, campo, idioma)
);
```

## Comandos Útiles

### Extraer strings para traducir
```bash
pybabel extract -F babel.cfg -k _l -o messages.pot .
```

### Inicializar traducciones para un nuevo idioma
```bash
pybabel init -i messages.pot -d translations -l en
```

### Actualizar traducciones después de agregar nuevos strings
```bash
pybabel update -i messages.pot -d translations
```

### Compilar traducciones (generar .mo)
```bash
pybabel compile -d translations
```

## Flujo de Trabajo

1. **Agregar nuevos strings traducibles**: Marca los strings en templates con `_()`
2. **Extraer strings**: Ejecuta `pybabel extract` para generar `messages.pot`
3. **Actualizar traducciones**: Ejecuta `pybabel update` para actualizar los archivos `.po`
4. **Traducir**: Edita los archivos `.po` con las traducciones
5. **Compilar**: Ejecuta `pybabel compile` para generar los archivos `.mo`
6. **Reiniciar servidor**: Los cambios se aplicarán después de reiniciar Flask

## Notas Importantes

- Los archivos `.mo` son binarios y se generan automáticamente. No los edites manualmente.
- Los archivos `.po` son los que debes editar con las traducciones.
- Después de compilar, reinicia el servidor Flask para que los cambios surtan efecto.
- En producción (VPS), asegúrate de compilar las traducciones antes de desplegar.

## Próximos Pasos

1. Marcar todos los strings estáticos en templates con `_()`
2. Implementar sistema de traducciones para contenido dinámico de BD
3. Agregar traducciones completas en inglés
4. Configurar detección automática de idioma basada en preferencias del navegador


