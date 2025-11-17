# 🚀 Pasos Después de Configurar DNS - test.farmavet-bodega.cl

## ✅ Lo que ya tienes
- ✅ Usuario "web" creado
- ✅ Proyecto clonado e instalado
- ✅ Subdominio "test" configurado en DNS

## 📋 Próximos Pasos

### 1. **Configurar Variables de Entorno**

```bash
# Conectarte como usuario web
sudo su - web
cd /home/web/farmavet-web

# Generar SECRET_KEY
python3 -c "import secrets; print(secrets.token_hex(32))"
# Copia el resultado (lo necesitarás)
```

### 2. **Configurar Servicio systemd**

```bash
# Salir del usuario web
exit

# Copiar archivo de servicio
sudo cp /home/web/farmavet-web/farmavet-web.service /etc/systemd/system/

# Editar el archivo
sudo nano /etc/systemd/system/farmavet-web.service
```

**Editar estas líneas:**
```ini
User=web                    # Ya está correcto
WorkingDirectory=/home/web/farmavet-web
Environment="PATH=/home/web/farmavet-web/venv/bin"
Environment="SECRET_KEY=TU_SECRET_KEY_AQUI"  # ← Pegar la clave generada
ExecStart=/home/web/farmavet-web/venv/bin/gunicorn \
          --config /home/web/farmavet-web/gunicorn_config.py \
          app:app
```

**Guardar:** `Ctrl+X`, luego `Y`, luego `Enter`

### 3. **Activar y Iniciar el Servicio**

```bash
# Recargar systemd
sudo systemctl daemon-reload

# Habilitar para que inicie al arrancar el servidor
sudo systemctl enable farmavet-web

# Iniciar el servicio
sudo systemctl start farmavet-web

# Verificar que esté corriendo
sudo systemctl status farmavet-web
```

**Deberías ver:** `Active: active (running)`

### 4. **Ver Logs (si hay errores)**

```bash
# Ver logs en tiempo real
sudo journalctl -u farmavet-web -f

# Ver últimas 50 líneas
sudo journalctl -u farmavet-web -n 50
```

### 5. **Configurar Nginx**

```bash
# Copiar configuración
sudo cp /home/web/farmavet-web/nginx_subdomain.conf /etc/nginx/sites-available/test.farmavet-bodega.cl

# Editar configuración
sudo nano /etc/nginx/sites-available/test.farmavet-bodega.cl
```

**Editar estas líneas:**
```nginx
location /static {
    alias /home/web/farmavet-web/static;  # ← Verificar ruta
    ...
}

location /assets {
    alias /home/web/farmavet-web/assets;  # ← Verificar ruta
    ...
}

location /logos {
    alias /home/web/farmavet-web/logos;  # ← Verificar ruta
    ...
}

location / {
    proxy_pass http://127.0.0.1:5001;  # ← Verificar puerto
    ...
}
```

**Guardar:** `Ctrl+X`, luego `Y`, luego `Enter`

### 6. **Activar Sitio en Nginx**

```bash
# Crear enlace simbólico
sudo ln -s /etc/nginx/sites-available/test.farmavet-bodega.cl /etc/nginx/sites-enabled/

# Verificar que la configuración sea correcta
sudo nginx -t

# Si dice "syntax is ok", recargar Nginx
sudo systemctl reload nginx
```

### 7. **Verificar que el Servicio Esté Escuchando**

```bash
# Verificar que Gunicorn esté escuchando en el puerto 5001
sudo netstat -tlnp | grep 5001
# o
sudo ss -tlnp | grep 5001

# Deberías ver algo como:
# 127.0.0.1:5001
```

### 8. **Probar HTTP (sin SSL aún)**

```bash
# Desde el VPS
curl -I http://test.farmavet-bodega.cl

# O desde tu computadora
# Abrir navegador: http://test.farmavet-bodega.cl
```

**Si funciona:** Deberías ver la página (aunque sin SSL aún)

### 9. **Obtener Certificado SSL (Let's Encrypt)**

```bash
# Instalar certbot si no lo tienes
sudo apt update
sudo apt install certbot python3-certbot-nginx -y

# Obtener certificado
sudo certbot --nginx -d test.farmavet-bodega.cl

# Seguir las instrucciones:
# - Email: tu email
# - Aceptar términos
# - Elegir redirigir HTTP a HTTPS (opción 2)
```

### 10. **Probar HTTPS**

```bash
# Desde el VPS
curl -I https://test.farmavet-bodega.cl

# O desde tu navegador
# https://test.farmavet-bodega.cl
```

### 11. **Crear Usuario Administrador**

```bash
# Conectarte como usuario web
sudo su - web
cd /home/web/farmavet-web
source venv/bin/activate

# Ejecutar script
python3 create_admin.py

# Seguir las instrucciones para crear usuario y contraseña
```

### 12. **Acceder al Panel de Admin**

1. Abrir navegador: `https://test.farmavet-bodega.cl/login`
2. Ingresar con el usuario creado
3. ¡Listo! 🎉

---

## 🔍 Solución de Problemas

### El servicio no inicia

```bash
# Ver logs detallados
sudo journalctl -u farmavet-web -n 100

# Verificar permisos
ls -la /home/web/farmavet-web
sudo chown -R web:web /home/web/farmavet-web
```

### Nginx da error 502

```bash
# Verificar que Gunicorn esté corriendo
sudo systemctl status farmavet-web

# Verificar puerto
sudo netstat -tlnp | grep 5001

# Ver logs de Nginx
sudo tail -f /var/log/nginx/error.log
```

### No se puede acceder al sitio

```bash
# Verificar DNS
nslookup test.farmavet-bodega.cl

# Verificar firewall
sudo ufw status
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
```

### Error de permisos

```bash
# Dar permisos correctos
sudo chown -R web:web /home/web/farmavet-web
sudo chmod -R 755 /home/web/farmavet-web
sudo chmod -R 755 /home/web/farmavet-web/static/uploads
```

---

## ✅ Checklist Final

- [ ] Servicio systemd configurado y corriendo
- [ ] Nginx configurado y recargado
- [ ] Sitio accesible vía HTTP
- [ ] Certificado SSL obtenido
- [ ] Sitio accesible vía HTTPS
- [ ] Usuario administrador creado
- [ ] Panel de admin accesible

---

## 🎯 Comandos Rápidos de Referencia

```bash
# Reiniciar servicio
sudo systemctl restart farmavet-web

# Ver estado
sudo systemctl status farmavet-web

# Ver logs
sudo journalctl -u farmavet-web -f

# Recargar Nginx
sudo systemctl reload nginx

# Verificar configuración Nginx
sudo nginx -t
```

---

¿En qué paso estás? ¿Necesitas ayuda con alguno específico?

