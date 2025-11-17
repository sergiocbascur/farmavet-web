# Guía de Despliegue - FARMAVET Web

## Opción Recomendada: Render.com (Gratis)

### Pasos para desplegar:

1. **Crear cuenta en Render.com**
   - Ve a https://render.com
   - Regístrate con GitHub (recomendado) o email

2. **Subir tu código a GitHub** (si no lo has hecho)
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/TU_USUARIO/farmavet-web.git
   git push -u origin main
   ```

3. **Crear nuevo Web Service en Render**
   - En el dashboard de Render, click en "New +" → "Web Service"
   - Conecta tu repositorio de GitHub
   - Render detectará automáticamente que es una app Flask

4. **Configuración en Render**
   - **Name**: `farmavet-web` (o el que prefieras)
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
   - **Plan**: Free (para pruebas)

5. **Variables de Entorno**
   - En la sección "Environment", agrega:
     - `SECRET_KEY`: Genera una clave secreta (puedes usar: `python -c "import secrets; print(secrets.token_hex(32))"`)
     - `FLASK_ENV`: `production`

6. **Desplegar**
   - Click en "Create Web Service"
   - Render construirá y desplegará tu app automáticamente
   - Obtendrás una URL como: `https://farmavet-web.onrender.com`

### Notas importantes:

- **Base de datos SQLite**: Funciona en Render, pero los datos se perderán si el servicio se detiene (en el plan gratuito). Para producción, considera migrar a PostgreSQL.
- **Archivos estáticos**: Los uploads se guardan en el sistema de archivos. En producción, considera usar un servicio de almacenamiento como AWS S3 o Cloudinary.
- **Primera ejecución**: La base de datos se creará automáticamente cuando se inicie la app.

---

## Alternativas Gratuitas:

### Railway.app
1. Ve a https://railway.app
2. Conecta tu repositorio GitHub
3. Railway detecta Flask automáticamente
4. Despliega con un click

### PythonAnywhere
1. Ve a https://www.pythonanywhere.com
2. Crea cuenta gratuita
3. Sube tu código vía Git o consola
4. Configura el WSGI file
5. Plan gratuito limitado a 1 app

### Fly.io
1. Instala flyctl: `curl -L https://fly.io/install.sh | sh`
2. Login: `fly auth login`
3. Inicializa: `fly launch`
4. Despliega: `fly deploy`

---

## Firebase (NO Recomendado para Flask)

Firebase Hosting **NO puede ejecutar Flask** directamente. Necesitarías:
- Migrar a Firebase Functions (requiere reescribir código)
- Usar Firebase Hosting solo para frontend estático
- Migrar base de datos a Firestore

**Conclusión**: Firebase no es práctico para esta aplicación Flask.

---

## Recomendación Final

**Usa Render.com** - Es la opción más simple y gratuita para Flask:
- ✅ Gratis
- ✅ Fácil de usar
- ✅ Soporta Flask nativamente
- ✅ Despliegue automático desde GitHub
- ✅ HTTPS incluido
- ✅ URL personalizada

