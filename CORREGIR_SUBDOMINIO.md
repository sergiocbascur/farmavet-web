# 🔧 Corregir Subdominio - test.farmavet-bodega.cl

## ❌ Problema

`test.farmavet-bodega.cl` muestra la misma página que `farmavet-bodega.cl`

**Causa:** Nginx está usando la configuración incorrecta o el proxy_pass apunta al puerto equivocado.

## ✅ Solución

### Paso 1: Verificar Configuración Actual

```bash
# Ver configuración del subdominio
sudo cat /etc/nginx/sites-available/test.farmavet-bodega.cl

# Verificar que el proxy_pass apunta al puerto 5001
grep -A 2 "proxy_pass" /etc/nginx/sites-available/test.farmavet-bodega.cl
```

**Debe mostrar:**
```nginx
proxy_pass http://127.0.0.1:5001;
```

**NO debe mostrar:**
```nginx
proxy_pass http://127.0.0.1:5000;  # ← Este es el puerto de farmavet-bodega
```

### Paso 2: Verificar que el Sitio Está Activo

```bash
# Ver sitios activos
ls -la /etc/nginx/sites-enabled/

# Debe mostrar test.farmavet-bodega.cl
```

### Paso 3: Verificar Orden de Configuración

Nginx procesa los sitios en orden. Si `farmavet-bodega.cl` tiene `server_name` con wildcard o está primero, puede estar capturando todas las peticiones.

```bash
# Ver configuración del dominio principal
sudo cat /etc/nginx/sites-available/farmavet-bodega.cl | grep -A 5 "server_name"
```

**El dominio principal NO debe tener:**
```nginx
server_name farmavet-bodega.cl *.farmavet-bodega.cl;  # ← Esto capturaría test.farmavet-bodega.cl
```

**Debe tener solo:**
```nginx
server_name farmavet-bodega.cl www.farmavet-bodega.cl;
```

### Paso 4: Verificar que farmavet-web Está Corriendo

```bash
# Verificar puerto 5001
sudo netstat -tlnp | grep 5001

# Debe mostrar que está escuchando en 127.0.0.1:5001
```

### Paso 5: Corregir Configuración si es Necesario

```bash
# Editar configuración del subdominio
sudo nano /etc/nginx/sites-available/test.farmavet-bodega.cl
```

**Verificar que tenga:**

```nginx
server {
    listen 80;
    server_name test.farmavet-bodega.cl;  # ← Debe ser específico para test

    location / {
        proxy_pass http://127.0.0.1:5001;  # ← Puerto 5001 (farmavet-web)
        ...
    }
}

server {
    listen 443 ssl http2;
    server_name test.farmavet-bodega.cl;  # ← Debe ser específico para test

    location / {
        proxy_pass http://127.0.0.1:5001;  # ← Puerto 5001 (farmavet-web)
        ...
    }
}
```

### Paso 6: Verificar y Recargar

```bash
# Verificar configuración
sudo nginx -t

# Ver qué sitios están activos
sudo nginx -T 2>/dev/null | grep "server_name"

# Recargar
sudo systemctl reload nginx
```

### Paso 7: Probar

```bash
# Probar directamente el puerto 5001
curl http://127.0.0.1:5001

# Probar vía subdominio
curl -H "Host: test.farmavet-bodega.cl" http://localhost
```

---

## 🔍 Diagnóstico Rápido

```bash
# 1. Ver qué puerto usa cada configuración
sudo grep -r "proxy_pass" /etc/nginx/sites-enabled/

# 2. Ver qué server_name tiene cada sitio
sudo grep -r "server_name" /etc/nginx/sites-enabled/

# 3. Ver logs de acceso
sudo tail -f /var/log/nginx/access.log
# Acceder al sitio y ver qué configuración se está usando
```

---

## 💡 Posibles Causas

1. **Proxy_pass apunta al puerto 5000** (farmavet-bodega) en lugar de 5001
2. **server_name incorrecto** en el dominio principal (captura todos los subdominios)
3. **Sitio no activo** (falta el enlace simbólico)
4. **Orden de configuración** (Nginx usa la primera coincidencia)

---

## ✅ Solución Rápida

```bash
# 1. Ver configuración actual
sudo cat /etc/nginx/sites-available/test.farmavet-bodega.cl | grep -A 3 "proxy_pass"

# 2. Si muestra puerto 5000, cambiarlo a 5001
sudo nano /etc/nginx/sites-available/test.farmavet-bodega.cl
# Buscar: proxy_pass http://127.0.0.1:5000;
# Cambiar a: proxy_pass http://127.0.0.1:5001;

# 3. Verificar y recargar
sudo nginx -t
sudo systemctl reload nginx

# 4. Probar
curl -I http://test.farmavet-bodega.cl
```

---

¿Qué muestra `sudo grep -r "proxy_pass" /etc/nginx/sites-enabled/`?

