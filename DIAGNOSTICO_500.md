# 🔍 Diagnóstico Error 500 - Internal Server Error

## ❌ Problema

HTTP 500 significa que Nginx está funcionando, pero la aplicación Flask está fallando.

## 🔍 Pasos de Diagnóstico

### Paso 1: Ver Logs del Servicio

```bash
# Ver logs recientes del servicio
sudo journalctl -u farmavet-web -n 50

# Ver logs en tiempo real
sudo journalctl -u farmavet-web -f
```

**Busca errores en rojo** - estos te dirán qué está fallando.

### Paso 2: Ver Logs de Nginx

```bash
# Ver errores de Nginx
sudo tail -f /var/log/nginx/error.log
```

### Paso 3: Probar Conexión Directa a Gunicorn

```bash
# Probar si Gunicorn responde directamente
curl http://127.0.0.1:5001

# Si esto también da error, el problema está en la aplicación Flask
```

### Paso 4: Verificar Permisos

```bash
# Verificar permisos de la carpeta
ls -la /home/web/farmavet-web

# Verificar permisos de la base de datos
ls -la /home/web/farmavet-web/instance/

# Dar permisos correctos si es necesario
sudo chown -R web:web /home/web/farmavet-web
sudo chmod -R 755 /home/web/farmavet-web
sudo chmod -R 755 /home/web/farmavet-web/static/uploads
```

### Paso 5: Verificar Variables de Entorno

```bash
# Ver qué variables tiene el servicio
sudo systemctl show farmavet-web | grep Environment
```

---

## 🔧 Soluciones Comunes

### Error: "No such file or directory" (Base de datos)

**Solución:** La base de datos se crea automáticamente, pero verifica permisos:

```bash
# Crear carpeta instance si no existe
sudo mkdir -p /home/web/farmavet-web/instance
sudo chown -R web:web /home/web/farmavet-web/instance
sudo chmod -R 755 /home/web/farmavet-web/instance
```

### Error: "Permission denied" (Archivos)

**Solución:**

```bash
sudo chown -R web:web /home/web/farmavet-web
sudo chmod -R 755 /home/web/farmavet-web
```

### Error: "Module not found" o "Import error"

**Solución:** Verificar que las dependencias estén instaladas:

```bash
sudo su - web
cd /home/web/farmavet-web
source venv/bin/activate
pip install -r requirements.txt
exit
```

### Error: "SECRET_KEY" o variables de entorno

**Solución:** Verificar que SECRET_KEY esté configurada:

```bash
# Ver el archivo de servicio
sudo cat /etc/systemd/system/farmavet-web.service | grep SECRET_KEY

# Si dice "REEMPLAZAR", necesitas configurarla
sudo nano /etc/systemd/system/farmavet-web.service
# Buscar SECRET_KEY y reemplazar con una clave generada
sudo systemctl daemon-reload
sudo systemctl restart farmavet-web
```

---

## 🚀 Comandos de Diagnóstico Rápido

```bash
# 1. Ver logs del servicio
sudo journalctl -u farmavet-web -n 100 --no-pager

# 2. Probar Gunicorn directamente
curl http://127.0.0.1:5001

# 3. Verificar que el proceso está corriendo
ps aux | grep gunicorn

# 4. Verificar permisos
ls -la /home/web/farmavet-web/instance/

# 5. Reiniciar servicio
sudo systemctl restart farmavet-web
sudo journalctl -u farmavet-web -f
```

---

## 📋 Checklist

- [ ] Servicio está corriendo (`sudo systemctl status farmavet-web`)
- [ ] Gunicorn escucha en puerto 5001 (`sudo netstat -tlnp | grep 5001`)
- [ ] Permisos correctos (`ls -la /home/web/farmavet-web`)
- [ ] Base de datos existe o puede crearse (`ls -la /home/web/farmavet-web/instance/`)
- [ ] SECRET_KEY configurada (no dice "REEMPLAZAR")
- [ ] Dependencias instaladas (`pip list` en el venv)

---

## 💡 Próximo Paso

**Ejecuta esto y comparte el resultado:**

```bash
sudo journalctl -u farmavet-web -n 50 --no-pager
```

Esto mostrará el error exacto que está causando el 500.

