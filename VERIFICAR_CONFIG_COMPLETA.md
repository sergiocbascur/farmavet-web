# 🔍 Verificar Configuración Completa de Nginx

## ❓ Problema

El `proxy_pass` está correcto (5001), pero el subdominio muestra el contenido del dominio principal.

**Causa probable:** El bloque HTTPS (443) no tiene la configuración correcta o el dominio principal está capturando el subdominio.

## 🔍 Verificación

### Paso 1: Ver Configuración Completa del Subdominio

```bash
# Ver toda la configuración
sudo cat /etc/nginx/sites-available/test.farmavet-bodega.cl
```

**Busca específicamente el bloque HTTPS (listen 443):**

```nginx
server {
    listen 443 ssl http2;
    server_name test.farmavet-bodega.cl;  # ← Debe ser específico
    
    # ... certificados SSL ...
    
    location / {
        proxy_pass http://127.0.0.1:5001;  # ← Debe ser 5001
        ...
    }
}
```

### Paso 2: Verificar Configuración del Dominio Principal

```bash
# Ver server_name del dominio principal
sudo grep -A 2 "server_name" /etc/nginx/sites-available/farmavet-bodega.cl
```

**NO debe tener:**
```nginx
server_name *.farmavet-bodega.cl;  # ← Esto capturaría test.farmavet-bodega.cl
server_name farmavet-bodega.cl test.farmavet-bodega.cl;  # ← Esto también
```

**Debe tener solo:**
```nginx
server_name farmavet-bodega.cl www.farmavet-bodega.cl;
```

### Paso 3: Ver Orden de Procesamiento

Nginx procesa los `server` blocks en orden. Si el dominio principal está primero y tiene un `server_name` que coincide, lo usará.

```bash
# Ver todos los server_name activos
sudo nginx -T 2>/dev/null | grep -B 2 -A 5 "server_name"
```

### Paso 4: Verificar que el Sitio Está Activo

```bash
# Ver sitios activos
ls -la /etc/nginx/sites-enabled/

# Debe mostrar test.farmavet-bodega.cl
```

### Paso 5: Probar con Host Header Específico

```bash
# Probar con header Host específico
curl -H "Host: test.farmavet-bodega.cl" http://127.0.0.1

# Comparar con el dominio principal
curl -H "Host: farmavet-bodega.cl" http://127.0.0.1
```

---

## 🔧 Solución: Verificar Bloque HTTPS

El problema más probable es que certbot modificó el bloque HTTPS y no tiene el `proxy_pass` correcto o falta la configuración.

```bash
# Ver solo el bloque HTTPS
sudo sed -n '/listen 443/,/^}/p' /etc/nginx/sites-available/test.farmavet-bodega.cl
```

**Verifica que tenga:**
1. ✅ `server_name test.farmavet-bodega.cl;` (específico, no wildcard)
2. ✅ `proxy_pass http://127.0.0.1:5001;` (puerto 5001)
3. ✅ Las rutas de archivos estáticos (`/assets`, `/logos`, `/static`)

---

## 🔧 Si el Bloque HTTPS No Tiene proxy_pass Correcto

```bash
# Editar configuración
sudo nano /etc/nginx/sites-available/test.farmavet-bodega.cl
```

**Busca el bloque `server { listen 443 ... }` y verifica que tenga:**

```nginx
server {
    listen 443 ssl http2;
    server_name test.farmavet-bodega.cl;  # ← Específico para test
    
    ssl_certificate ...;
    ssl_certificate_key ...;
    
    # Archivos estáticos
    location /assets { ... }
    location /logos { ... }
    location /static { ... }
    
    # Proxy a farmavet-web
    location / {
        proxy_pass http://127.0.0.1:5001;  # ← Puerto 5001
        proxy_set_header Host $host;
        ...
    }
}
```

**Guardar y recargar:**
```bash
sudo nginx -t
sudo systemctl reload nginx
```

---

## 🔍 Comando de Diagnóstico Completo

```bash
# Ver toda la configuración activa relacionada con test
sudo nginx -T 2>/dev/null | grep -A 20 "test.farmavet-bodega.cl"
```

Esto mostrará toda la configuración activa para el subdominio.

---

¿Qué muestra `sudo cat /etc/nginx/sites-available/test.farmavet-bodega.cl` completo?

