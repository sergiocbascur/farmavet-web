# 🔧 Corregir Error de Nginx

## ❌ Problema

El comando `ln -s` se truncó. Necesitas crear el enlace simbólico correctamente.

## ✅ Solución

### Paso 1: Verificar que el archivo existe

```bash
# Verificar que el archivo de configuración existe
sudo ls -la /etc/nginx/sites-available/test.farmavet-bodega.cl
```

**Si NO existe**, créalo primero:

```bash
# Copiar desde el proyecto
sudo cp /home/web/farmavet-web/nginx_subdomain.conf /etc/nginx/sites-available/test.farmavet-bodega.cl

# Editar y verificar rutas
sudo nano /etc/nginx/sites-available/test.farmavet-bodega.cl
```

### Paso 2: Eliminar enlace roto (si existe)

```bash
# Verificar si hay un enlace roto
sudo ls -la /etc/nginx/sites-enabled/ | grep test

# Si existe pero está roto, eliminarlo
sudo rm /etc/nginx/sites-enabled/test.farmavet-bodega.cl
```

### Paso 3: Crear enlace simbólico CORRECTAMENTE

```bash
# Comando completo (sin truncar)
sudo ln -s /etc/nginx/sites-available/test.farmavet-bodega.cl /etc/nginx/sites-enabled/test.farmavet-bodega.cl
```

### Paso 4: Verificar configuración

```bash
# Verificar sintaxis
sudo nginx -t

# Debería decir: "syntax is ok" y "test is successful"
```

### Paso 5: Recargar Nginx

```bash
# Si la verificación fue exitosa
sudo systemctl reload nginx

# Verificar estado
sudo systemctl status nginx
```

---

## 🔍 Si el archivo no existe en sites-available

Crea el archivo de configuración:

```bash
# Crear archivo
sudo nano /etc/nginx/sites-available/test.farmavet-bodega.cl
```

Y pega esta configuración (ajustar rutas si es necesario):

```nginx
server {
    listen 80;
    server_name test.farmavet-bodega.cl;

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

    location / {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
        
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    client_max_body_size 16M;
}
```

Guardar: `Ctrl+X`, luego `Y`, luego `Enter`

---

## 📋 Comandos Completos (Copia y Pega)

```bash
# 1. Verificar archivo
sudo ls -la /etc/nginx/sites-available/test.farmavet-bodega.cl

# 2. Si no existe, crearlo desde el proyecto
sudo cp /home/web/farmavet-web/nginx_subdomain.conf /etc/nginx/sites-available/test.farmavet-bodega.cl

# 3. Editar rutas si es necesario
sudo nano /etc/nginx/sites-available/test.farmavet-bodega.cl

# 4. Eliminar enlace roto si existe
sudo rm -f /etc/nginx/sites-enabled/test.farmavet-bodega.cl

# 5. Crear enlace correcto
sudo ln -s /etc/nginx/sites-available/test.farmavet-bodega.cl /etc/nginx/sites-enabled/test.farmavet-bodega.cl

# 6. Verificar
sudo nginx -t

# 7. Recargar
sudo systemctl reload nginx
```

---

## ✅ Verificación Final

```bash
# Verificar que el enlace existe
ls -la /etc/nginx/sites-enabled/ | grep test

# Verificar que Nginx está corriendo
sudo systemctl status nginx

# Probar HTTP
curl -I http://test.farmavet-bodega.cl
```

