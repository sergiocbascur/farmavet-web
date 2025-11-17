# 🔍 Diagnóstico de Error 502 (Bad Gateway)

## ❓ Problema

```
GET https://test.farmavet-bodega.cl/ 502 (Bad Gateway)
```

**Significado:** Nginx puede acceder a los archivos estáticos, pero no puede comunicarse con la aplicación Flask/Gunicorn en el puerto 5001.

## 🔍 Diagnóstico

### Paso 1: Verificar Estado del Servicio

```bash
# Ver estado del servicio farmavet-web
sudo systemctl status farmavet-web

# Debe mostrar "Active: active (running)"
```

### Paso 2: Verificar que Gunicorn Está Escuchando

```bash
# Ver si hay algo escuchando en el puerto 5001
sudo netstat -tlnp | grep 5001

# O con ss
sudo ss -tlnp | grep 5001

# Debe mostrar algo como:
# tcp  0  0  127.0.0.1:5001  0.0.0.0:*  LISTEN  12345/gunicorn
```

### Paso 3: Ver Logs del Servicio

```bash
# Ver logs recientes del servicio
sudo journalctl -u farmavet-web -n 50 --no-pager

# Ver logs en tiempo real
sudo journalctl -u farmavet-web -f
```

### Paso 4: Probar Conexión Directa

```bash
# Probar si la aplicación responde directamente
curl http://127.0.0.1:5001/

# Si funciona, debería mostrar HTML
# Si no funciona, la aplicación no está corriendo
```

### Paso 5: Verificar Configuración de Nginx

```bash
# Verificar que proxy_pass apunta al puerto correcto
sudo grep "proxy_pass" /etc/nginx/sites-available/test.farmavet-bodega.cl

# Debe mostrar:
# proxy_pass http://127.0.0.1:5001;
```

---

## 🔧 Soluciones

### Solución 1: Reiniciar el Servicio

```bash
# Reiniciar el servicio
sudo systemctl restart farmavet-web

# Verificar que está corriendo
sudo systemctl status farmavet-web

# Ver logs
sudo journalctl -u farmavet-web -n 30 --no-pager
```

### Solución 2: Verificar que el Servicio Está Habilitado

```bash
# Verificar que el servicio está habilitado para iniciar al arrancar
sudo systemctl is-enabled farmavet-web

# Si no está habilitado, habilitarlo
sudo systemctl enable farmavet-web
```

### Solución 3: Verificar Archivo de Servicio

```bash
# Ver el archivo de servicio
sudo cat /etc/systemd/system/farmavet-web.service

# Verificar que:
# - WorkingDirectory apunta al directorio correcto
# - ExecStart apunta a gunicorn correctamente
# - User es 'web'
```

### Solución 4: Probar Gunicorn Manualmente

```bash
# Ir al directorio del proyecto
cd /home/web/farmavet-web

# Activar entorno virtual (si existe)
source venv/bin/activate  # o el nombre de tu venv

# Probar Gunicorn manualmente
gunicorn -c gunicorn_config.py app:app

# Si funciona, presiona Ctrl+C y reinicia el servicio
```

### Solución 5: Verificar Base de Datos

```bash
# Verificar que la base de datos existe
ls -la /home/web/farmavet-web/instance/database.db

# Verificar permisos
ls -la /home/web/farmavet-web/instance/
```

---

## 🔍 Errores Comunes

### Error: "Address already in use"

```bash
# Ver qué está usando el puerto 5001
sudo lsof -i :5001

# Matar el proceso si es necesario
sudo kill -9 <PID>
```

### Error: "No such file or directory"

```bash
# Verificar que todos los archivos existen
ls -la /home/web/farmavet-web/app.py
ls -la /home/web/farmavet-web/gunicorn_config.py
ls -la /home/web/farmavet-web/requirements.txt
```

### Error: "Module not found"

```bash
# Verificar que las dependencias están instaladas
cd /home/web/farmavet-web
source venv/bin/activate  # o el nombre de tu venv
pip list | grep -E "flask|gunicorn"
```

---

## ✅ Verificación Final

Después de aplicar cualquier solución:

```bash
# 1. Verificar estado
sudo systemctl status farmavet-web

# 2. Verificar puerto
sudo netstat -tlnp | grep 5001

# 3. Probar conexión
curl http://127.0.0.1:5001/

# 4. Recargar Nginx
sudo systemctl reload nginx

# 5. Probar desde el navegador
# https://test.farmavet-bodega.cl/
```

---

## 💡 Comando de Diagnóstico Completo

```bash
echo "=== Estado del Servicio ==="
sudo systemctl status farmavet-web --no-pager | head -15

echo "=== Puerto 5001 ==="
sudo netstat -tlnp | grep 5001

echo "=== Logs Recientes ==="
sudo journalctl -u farmavet-web -n 20 --no-pager

echo "=== Test de Conexión ==="
curl -I http://127.0.0.1:5001/ 2>&1 | head -5

echo "=== Configuración de Nginx ==="
sudo grep "proxy_pass" /etc/nginx/sites-available/test.farmavet-bodega.cl
```

