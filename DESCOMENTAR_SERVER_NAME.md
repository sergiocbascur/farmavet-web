# 🔧 Descomentar server_name en Bloque HTTPS

## ❓ Problema

El `server_name` en el bloque HTTPS del subdominio está comentado:
```
# server_name test.farmavet-bodega.cl;
```

Esto impide que Nginx enrute correctamente las peticiones HTTPS al subdominio.

## 🔧 Solución

### Opción 1: Editar Directamente en el Servidor

```bash
# Editar el archivo de configuración
sudo nano /etc/nginx/sites-available/test.farmavet-bodega.cl
```

Busca la línea:
```
#     server_name test.farmavet-bodega.cl;
```

Y cámbiala a:
```
    server_name test.farmavet-bodega.cl;
```

**Importante:** Asegúrate de que TODAS las líneas del bloque HTTPS estén descomentadas, no solo el `server_name`.

### Opción 2: Actualizar desde el Repositorio

```bash
# Ir al directorio del proyecto
cd /home/web/farmavet-web

# Actualizar desde GitHub
git pull origin main

# Copiar la configuración actualizada
sudo cp nginx_subdomain.conf /etc/nginx/sites-available/test.farmavet-bodega.cl

# Verificar que el server_name esté descomentado
sudo grep "server_name" /etc/nginx/sites-available/test.farmavet-bodega.cl | grep -v "^#"
```

Debe mostrar:
```
    server_name test.farmavet-bodega.cl;
```

### Verificar Configuración Completa

```bash
# Ver el bloque HTTPS completo
sudo sed -n '/listen 443/,/^}/p' /etc/nginx/sites-available/test.farmavet-bodega.cl
```

Debe mostrar un bloque completo sin comentarios (excepto comentarios informativos):

```nginx
server {
    listen 443 ssl http2;
    server_name test.farmavet-bodega.cl;

    ssl_certificate /etc/letsencrypt/live/test.farmavet-bodega.cl/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/test.farmavet-bodega.cl/privkey.pem;
    ...
}
```

### Probar y Recargar

```bash
# Probar configuración
sudo nginx -t

# Si está bien, recargar
sudo systemctl reload nginx

# Verificar que funciona
curl -I https://test.farmavet-bodega.cl/
```

---

## ✅ Verificación Final

Después de descomentar, verifica:

```bash
sudo sed -n '/listen 443/,/^}/p' /etc/nginx/sites-available/test.farmavet-bodega.cl | grep -E "server_name|proxy_pass"
```

Debe mostrar:
```
    server_name test.farmavet-bodega.cl;
    proxy_pass http://127.0.0.1:5001;
```

**Ambas líneas SIN el símbolo `#` al inicio.**

