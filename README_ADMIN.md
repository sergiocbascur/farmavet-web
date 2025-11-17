# Panel de Administración - FARMAVET Web

Sistema de administración de contenido para el sitio web de FARMAVET. Permite editar contenido sin necesidad de tocar código HTML.

## 🚀 Inicio Rápido

### 1. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 2. Inicializar la base de datos

Al ejecutar `app.py` por primera vez, se creará automáticamente la base de datos `farmavet_web.db` con un usuario administrador por defecto:

- **Usuario:** `admin`
- **Contraseña:** `admin123`

⚠️ **IMPORTANTE:** Cambia la contraseña después del primer login.

### 3. Ejecutar el servidor

```bash
python app.py
```

El servidor se iniciará en `http://localhost:5000`

### 4. Acceder al panel de administración

- **Panel de admin:** http://localhost:5000/admin/login
- **Sitio web:** http://localhost:5000

## 📋 Funcionalidades

### Gestión de Programas
- Crear, editar y eliminar programas de educación continua
- Campos: tipo (diplomado/curso/taller), título, descripción, modalidad, horario, patrocinio, auspicio, email de contacto
- Orden de visualización personalizable
- Activar/desactivar programas

### Gestión de Testimonios
- Crear, editar y eliminar testimonios
- Campos: título, contenido, autor, categoría, tags, imagen opcional
- Orden de visualización personalizable
- Activar/desactivar testimonios

### Gestión de Noticias
- Crear, editar y eliminar noticias y eventos
- Campos: título, resumen, contenido, imagen, categoría, fecha, enlace externo
- Marcar noticias como destacadas
- Orden de visualización personalizable
- Activar/desactivar noticias

### Gestión de Equipo
- Crear, editar y eliminar miembros del equipo
- Campos: nombre, cargo, biografía, email, imagen, área, tags
- Organización por áreas (dirección, técnico, analistas, etc.)
- Orden de visualización personalizable
- Activar/desactivar miembros

### Gestión de Convenios
- Crear, editar y eliminar convenios y alianzas
- Campos: nombre, tipo (público/privado/internacional), descripción, logo, enlace
- Orden de visualización personalizable
- Activar/desactivar convenios

### Gestión de Clientes/Aliados
- Crear, editar y eliminar clientes y aliados
- Campos: nombre, logo, enlace, categoría (cliente/aliado/patrocinador)
- Orden de visualización personalizable
- Activar/desactivar clientes

### Gestión de Estadísticas
- Crear, editar y eliminar números destacados
- Campos: número, sufijo (+, er, º), etiqueta
- Vista previa en tiempo real
- Orden de visualización personalizable
- Activar/desactivar estadísticas

### Gestor de Imágenes
- Subir imágenes para programas, testimonios, noticias y equipo
- Organización por carpetas
- Formatos permitidos: PNG, JPG, JPEG, GIF, WEBP, SVG

## 📁 Estructura del Proyecto

```
farmavet-web/
├── app.py                 # Backend Flask principal
├── requirements.txt       # Dependencias Python
├── farmavet_web.db       # Base de datos SQLite (se crea automáticamente)
├── templates/            # Templates HTML dinámicos
│   ├── docencia.html     # Página de docencia (usa datos de BD)
│   └── admin/           # Panel de administración
│       ├── login.html
│       ├── dashboard.html
│       ├── programas.html
│       ├── programa_form.html
│       ├── testimonios.html
│       └── testimonio_form.html
└── static/
    └── uploads/          # Imágenes subidas por administradores
        ├── programas/
        ├── testimonios/
        ├── noticias/
        └── equipo/
```

## 🔐 Seguridad

- Las contraseñas se almacenan con hash (Werkzeug)
- Sesiones seguras con Flask
- Protección de rutas con decorador `@login_required`
- Validación de tipos de archivo en uploads

## 📝 Uso del Panel

### Agregar un Programa

1. Inicia sesión en `/admin/login`
2. Ve a "Programas" en el menú lateral
3. Click en "Nuevo Programa"
4. Completa el formulario:
   - **Tipo:** Selecciona Diplomado, Curso o Taller
   - **Título:** Nombre del programa
   - **Descripción:** Texto que aparecerá en la tarjeta
   - **Modalidad:** Ej: "Online (Zoom)", "Presencial"
   - **Horario:** Ej: "Miércoles 17:30-19:45 y sábados 08:00-13:00"
   - **Patrocinio/Auspicio:** Organizaciones que apoyan
   - **Email de contacto:** Email para postulaciones
   - **Texto del botón:** Por defecto "Postular"
   - **Orden:** Número para ordenar (menor = primero)
5. Marca "Programa activo" para que aparezca en el sitio
6. Click en "Guardar Programa"

### Agregar un Testimonio

1. Ve a "Testimonios" en el menú lateral
2. Click en "Nuevo Testimonio"
3. Completa el formulario:
   - **Título:** Frase destacada del testimonio (entre comillas)
   - **Contenido:** Texto completo del testimonio
   - **Autor:** Nombre y cargo de quien da el testimonio
   - **Categoría:** Pregrado, Postgrado, Industria, Doctorado
   - **Tags:** Separados por comas (ej: "Investigación aplicada, Stewardship")
   - **Imagen:** URL opcional de imagen
4. Marca "Testimonio activo"
5. Click en "Guardar Testimonio"

### Agregar una Noticia

1. Ve a "Noticias" en el menú lateral
2. Click en "Nueva Noticia"
3. Completa el formulario:
   - **Título:** Título de la noticia
   - **Categoría:** Investigación, Servicios, Docencia, Eventos, Vinculación
   - **Fecha:** Formato libre (ej: "FEB 2025", "ABR 2025")
   - **Resumen:** Texto corto para tarjetas
   - **Contenido:** Texto completo (opcional)
   - **Imagen:** URL de imagen
   - **Enlace externo:** URL opcional (LinkedIn, publicación, etc.)
   - **Destacada:** Marca si quieres que aparezca primero
4. Marca "Noticia activa"
5. Click en "Guardar Noticia"

### Agregar un Miembro del Equipo

1. Ve a "Equipo" en el menú lateral
2. Click en "Nuevo Miembro"
3. Completa el formulario:
   - **Nombre:** Nombre completo
   - **Cargo:** Cargo o posición
   - **Área:** Dirección, Técnico, Analistas, Calidad, Investigación
   - **Email:** Email de contacto
   - **Biografía:** Descripción profesional
   - **Imagen:** URL de foto
   - **Tags:** Separados por comas
4. Marca "Miembro activo"
5. Click en "Guardar Miembro"

### Agregar una Estadística

1. Ve a "Estadísticas" en el menú lateral
2. Click en "Nueva Estadística"
3. Completa el formulario:
   - **Número:** El número principal (ej: 30, 70, 1)
   - **Sufijo:** Opcional (ej: "+", "er", "º")
   - **Etiqueta:** Texto descriptivo (ej: "años de experiencia")
4. Marca "Estadística activa"
5. Click en "Guardar Estadística"

## 🔄 Actualización de Contenido

Los cambios se reflejan inmediatamente en el sitio web. No es necesario reiniciar el servidor.

## 🛠️ Desarrollo

### Agregar nuevas secciones editables

1. Crear tabla en `init_db()` en `app.py`
2. Agregar rutas de administración
3. Crear templates de formularios
4. Actualizar templates públicos para usar datos de BD

### Cambiar contraseña de admin

Puedes cambiar la contraseña directamente en la base de datos o agregar una funcionalidad en el panel.

## 📞 Soporte

Para problemas o preguntas, revisa los logs del servidor o contacta al equipo de desarrollo.

