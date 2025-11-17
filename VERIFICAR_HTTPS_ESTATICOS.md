# 🔒 Verificar Archivos Estáticos en HTTPS

## ✅ Estado Actual

- ✅ HTTP redirige a HTTPS (301)
- ⚠️ Necesitamos verificar que los archivos estáticos funcionen vía HTTPS

## 🔍 Verificación

### Paso 1: Probar Archivos Estáticos vía HTTPS

```bash
# Probar CSS
curl -I https://test.farmavet-bodega.cl/assets/css/style.css

# Probar logo
curl -I https://test.farmavet-bodega.cl/logos/LOGO%20FARMAVET.png

# Probar JS
curl -I https://test.farmavet-bodega.cl/assets/js/main.js
```

**Si dan 404:** Necesitamos verificar la configuración HTTPS de Nginx.

### Paso 2: Verificar Configuración HTTPS de Nginx

```bash
# Ver configuración actual
sudo cat /etc/nginx/sites-available/test.farmavet-bodega.cl | grep -A 10 "listen 443"
```

**Debe tener las rutas correctas:**
```nginx
location /assets {
    alias /home/web/farmavet-web/assets;
    ...
}

location /logos {
    alias /home/web/farmavet-web/logos;
    ...
}
```

### Paso 3: Si Certbot Modificó la Configuración

Certbot puede haber modificado el archivo. Verifica:

```bash
# Ver toda la configuración
sudo cat /etc/nginx/sites-available/test.farmavet-bodega.cl
```

**Busca el bloque `server { listen 443 ... }`** y verifica que tenga las rutas correctas.

### Paso 4: Si Faltan las Rutas en HTTPS

Si el bloque HTTPS no tiene las rutas de archivos estáticos, agrégalas:

```bash
sudo nano /etc/nginx/sites-available/test.farmavet-bodega.cl
```

**Dentro del bloque `server { listen 443 ... }`, agregar:**

```nginx
    location /static {
        alias /home/web/farmavet-web/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location /assets {
        alias /home/web/farmavet-web/assets;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location /logos {
        alias /home/web/farmavet-web/logos;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
```

**ANTES del `location / {` que hace proxy_pass**

### Paso 5: Verificar y Recargar

```bash
# Verificar configuración
sudo nginx -t

# Recargar
sudo systemctl reload nginx
```

### Paso 6: Probar Nuevamente

```bash
# Probar HTTPS
curl -I https://test.farmavet-bodega.cl/assets/css/style.css

# Debería dar HTTP 200 OK
```

---

## 🔍 Ver Logs si Aún Falla

```bash
# Ver errores de Nginx
sudo tail -f /var/log/nginx/error.log

# Intentar acceder al sitio y ver qué error aparece
```

---

## 📋 Comando Rápido para Ver Configuración

```bash
# Ver solo el bloque HTTPS
sudo sed -n '/listen 443/,/^}/p' /etc/nginx/sites-available/test.farmavet-bodega.cl
```

Esto mostrará el bloque HTTPS completo para verificar que tenga las rutas correctas.

---

¿Qué muestra `curl -I https://test.farmavet-bodega.cl/assets/css/style.css`?

