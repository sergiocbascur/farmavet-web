# 🔧 Verificar y Corregir Entorno Virtual

## 🔍 Verificar Estado Actual

Ejecuta estos comandos en tu VPS:

```bash
# 1. Verificar si existe el venv
ls -la /home/web/farmavet-web/venv/bin/gunicorn

# 2. Ver qué hay en el directorio del proyecto
ls -la /home/web/farmavet-web/ | grep -E "venv|requirements"

# 3. Verificar si gunicorn está instalado globalmente
which gunicorn
gunicorn --version
```

---

## 🔧 Solución: Crear Entorno Virtual e Instalar Dependencias

Si el venv no existe o no tiene gunicorn:

```bash
# 1. Ir al directorio del proyecto
cd /home/web/farmavet-web

# 2. Crear entorno virtual (si no existe)
python3 -m venv venv

# 3. Activar el entorno virtual
source venv/bin/activate

# 4. Actualizar pip
pip install --upgrade pip

# 5. Instalar dependencias
pip install -r requirements.txt

# 6. Verificar que gunicorn está instalado
venv/bin/gunicorn --version

# 7. Si funciona, recargar systemd y reiniciar el servicio
sudo systemctl daemon-reload
sudo systemctl restart farmavet-web

# 8. Verificar estado
sudo systemctl status farmavet-web
```

---

## 🔧 Solución Alternativa: Usar Gunicorn Global

Si prefieres no usar venv o si gunicorn está instalado globalmente:

```bash
# 1. Editar el archivo de servicio
sudo nano /etc/systemd/system/farmavet-web.service

# 2. Cambiar la línea ExecStart de:
#    ExecStart=/home/web/farmavet-web/venv/bin/gunicorn \
#    A:
#    ExecStart=/usr/bin/gunicorn --config /home/web/farmavet-web/gunicorn_config.py app:app
#    O si está en /usr/local/bin:
#    ExecStart=/usr/local/bin/gunicorn --config /home/web/farmavet-web/gunicorn_config.py app:app

# 3. También cambiar la línea Environment PATH de:
#    Environment="PATH=/home/web/farmavet-web/venv/bin"
#    A:
#    Environment="PATH=/usr/bin:/usr/local/bin"

# 4. Guardar (Ctrl+O, Enter, Ctrl+X)

# 5. Recargar systemd
sudo systemctl daemon-reload

# 6. Reiniciar el servicio
sudo systemctl restart farmavet-web

# 7. Verificar estado
sudo systemctl status farmavet-web
```

---

## 🔧 Solución con Python -m gunicorn (Más Compatible)

Si no estás seguro de dónde está gunicorn:

```bash
# 1. Editar el archivo de servicio
sudo nano /etc/systemd/system/farmavet-web.service

# 2. Cambiar ExecStart a:
ExecStart=/usr/bin/python3 -m gunicorn --config /home/web/farmavet-web/gunicorn_config.py app:app

# 3. Cambiar Environment PATH a:
Environment="PATH=/usr/bin:/usr/local/bin"

# 4. Guardar, recargar y reiniciar
sudo systemctl daemon-reload
sudo systemctl restart farmavet-web
sudo systemctl status farmavet-web
```

---

## ✅ Verificación Final

Después de aplicar cualquier solución:

```bash
# Verificar que el servicio está corriendo
sudo systemctl status farmavet-web

# Verificar que está escuchando en el puerto 5001
sudo netstat -tlnp | grep 5001

# Probar conexión
curl http://127.0.0.1:5001/

# Ver logs si hay problemas
sudo journalctl -u farmavet-web -n 30 --no-pager
```

---

## 💡 Recomendación

**La mejor opción es crear el entorno virtual** porque:
- Aísla las dependencias del proyecto
- Evita conflictos con otros proyectos
- Es más fácil de mantener

Ejecuta la primera solución (crear venv) y luego comparte el resultado.

