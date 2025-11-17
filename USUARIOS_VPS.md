# 👤 Gestión de Usuarios en VPS - farmavet-web

## 🤔 ¿Crear usuario nuevo o usar el mismo?

### ✅ **RECOMENDADO: Crear usuario "web"** (Mejor práctica)

**Ventajas:**
- ✅ **Seguridad**: Separación de responsabilidades (principio de menor privilegio)
- ✅ **Aislamiento**: Si un proyecto es comprometido, no afecta al otro
- ✅ **Auditoría**: Más fácil rastrear qué usuario hizo qué
- ✅ **Permisos**: Puedes dar permisos específicos a cada usuario
- ✅ **Mantenimiento**: Más fácil de mantener y depurar

**Desventajas:**
- ⚠️ Un poco más de configuración inicial

---

### ⚠️ **Alternativa: Usar usuario "bodega"** (Más simple)

**Ventajas:**
- ✅ Más simple, menos configuración
- ✅ Ya tienes todo configurado

**Desventajas:**
- ❌ Menos seguro
- ❌ Si un proyecto tiene problemas, puede afectar al otro
- ❌ Más difícil de auditar

---

## 🚀 Opción 1: Crear Usuario "web" (RECOMENDADO)

### Paso 1: Crear el usuario

```bash
# Conectarte como root o con sudo
sudo adduser web

# Seguir las instrucciones para crear contraseña
# Puedes dejar los demás campos en blanco (presionar Enter)
```

### Paso 2: Agregar a grupo www-data (para servir archivos)

```bash
sudo usermod -a -G www-data web
```

### Paso 3: Configurar permisos de carpetas

```bash
# Crear estructura de directorios
sudo mkdir -p /home/web/farmavet-web
sudo chown web:web /home/web/farmavet-web

# Si necesitas que Nginx acceda a archivos estáticos
sudo chmod 755 /home/web
sudo chmod 755 /home/web/farmavet-web
```

### Paso 4: Clonar el proyecto como usuario "web"

```bash
# Cambiar al usuario web
sudo su - web

# Clonar el proyecto
cd /home/web
git clone https://github.com/sergiocbascur/farmavet-web.git
cd farmavet-web

# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Paso 5: Actualizar archivo de servicio systemd

Editar `/etc/systemd/system/farmavet-web.service`:

```ini
[Unit]
Description=FARMAVET Web Gunicorn daemon
After=network.target

[Service]
User=web                    # ← Cambiar aquí
Group=www-data
WorkingDirectory=/home/web/farmavet-web    # ← Cambiar aquí
Environment="PATH=/home/web/farmavet-web/venv/bin"  # ← Cambiar aquí
Environment="FLASK_ENV=production"
Environment="SECRET_KEY=tu-secret-key-aqui"
ExecStart=/home/web/farmavet-web/venv/bin/gunicorn \  # ← Cambiar aquí
          --config /home/web/farmavet-web/gunicorn_config.py \
          app:app

Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

### Paso 6: Actualizar configuración de Nginx

Editar `/etc/nginx/sites-available/test.farmavet-bodega.cl`:

```nginx
location /static {
    alias /home/web/farmavet-web/static;  # ← Cambiar aquí
    ...
}

location /assets {
    alias /home/web/farmavet-web/assets;  # ← Cambiar aquí
    ...
}
```

---

## 🔧 Opción 2: Usar Usuario "bodega" (Más Simple)

Si prefieres usar el mismo usuario:

### Paso 1: Clonar en la carpeta del usuario bodega

```bash
# Cambiar al usuario bodega
sudo su - bodega

# Clonar el proyecto
cd /home/bodega
git clone https://github.com/sergiocbascur/farmavet-web.git
cd farmavet-web

# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Paso 2: Actualizar archivo de servicio systemd

Editar `/etc/systemd/system/farmavet-web.service`:

```ini
[Service]
User=bodega                    # ← Usuario existente
Group=www-data
WorkingDirectory=/home/bodega/farmavet-web    # ← Ruta del usuario bodega
Environment="PATH=/home/bodega/farmavet-web/venv/bin"
...
```

### Paso 3: Actualizar configuración de Nginx

```nginx
location /static {
    alias /home/bodega/farmavet-web/static;  # ← Ruta del usuario bodega
    ...
}
```

---

## 📊 Comparación

| Aspecto | Usuario Separado "web" | Usuario "bodega" |
|---------|----------------------|------------------|
| **Seguridad** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Aislamiento** | ⭐⭐⭐⭐⭐ | ⭐⭐ |
| **Simplicidad** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Mantenimiento** | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Auditoría** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |

---

## 🎯 Recomendación Final

**Para producción:** Usa usuario separado "web"
- Mejor seguridad
- Mejor organización
- Mejor práctica

**Para pruebas rápidas:** Puedes usar "bodega"
- Más rápido de configurar
- Funciona perfectamente

---

## 🔐 Permisos Recomendados

### Si usas usuario "web":

```bash
# Permisos para el usuario web
sudo chown -R web:web /home/web/farmavet-web
sudo chmod -R 755 /home/web/farmavet-web

# Permisos para archivos estáticos (Nginx necesita leer)
sudo chmod -R 644 /home/web/farmavet-web/static
sudo chmod -R 644 /home/web/farmavet-web/assets
sudo chmod -R 644 /home/web/farmavet-web/logos

# Permisos para uploads (la app necesita escribir)
sudo chmod -R 755 /home/web/farmavet-web/static/uploads
```

### Si usas usuario "bodega":

```bash
# Similar, pero con usuario bodega
sudo chown -R bodega:www-data /home/bodega/farmavet-web
sudo chmod -R 755 /home/bodega/farmavet-web
```

---

## 🆘 Comandos Útiles

```bash
# Ver qué usuario está ejecutando el proceso
ps aux | grep gunicorn

# Cambiar propietario de archivos
sudo chown -R web:web /home/web/farmavet-web

# Ver permisos
ls -la /home/web/farmavet-web

# Cambiar de usuario
sudo su - web
```

---

## 💡 Mi Recomendación

**Crea el usuario "web"** - Es la mejor práctica y solo toma 2 minutos extra. Te dará:
- Mejor seguridad
- Mejor organización
- Separación clara entre proyectos

¿Quieres que te guíe paso a paso para crear el usuario "web"?

