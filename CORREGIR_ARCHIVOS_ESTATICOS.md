# 🔧 Corregir Archivos Estáticos 404

## ❌ Problema

Los archivos estáticos (CSS, JS, imágenes, logos) dan error 404.

## ✅ Solución

### Paso 1: Actualizar Configuración de Nginx

```bash
# Editar configuración de Nginx
sudo nano /etc/nginx/sites-available/test.farmavet-bodega.cl
```

**Cambiar todas las rutas de:**
```
/home/tu-usuario/farmavet-web
```

**A:**
```
/home/web/farmavet-web
```

**Específicamente estas líneas:**
```nginx
location /static {
    alias /home/web/farmavet-web/static;  # ← Cambiar aquí
    ...
}

location /assets {
    alias /home/web/farmavet-web/assets;  # ← Cambiar aquí
    ...
}

location /logos {
    alias /home/web/farmavet-web/logos;  # ← Cambiar aquí
    ...
}
```

**Guardar:** `Ctrl+X`, luego `Y`, luego `Enter`

### Paso 2: Verificar que los Archivos Existen

```bash
# Verificar que los archivos existen
ls -la /home/web/farmavet-web/assets/css/style.css
ls -la /home/web/farmavet-web/assets/js/main.js
ls -la /home/web/farmavet-web/logos/LOGO\ FARMAVET.png
ls -la /home/web/farmavet-web/assets/images/hero-servicio-analisis.jpg
```

### Paso 3: Verificar Permisos

```bash
# Dar permisos de lectura a Nginx
sudo chmod -R 755 /home/web/farmavet-web/assets
sudo chmod -R 755 /home/web/farmavet-web/logos
sudo chmod -R 755 /home/web/farmavet-web/static

# Verificar que Nginx puede leer (el grupo www-data)
sudo chown -R web:www-data /home/web/farmavet-web/assets
sudo chown -R web:www-data /home/web/farmavet-web/logos
sudo chown -R web:www-data /home/web/farmavet-web/static
```

### Paso 4: Verificar y Recargar Nginx

```bash
# Verificar configuración
sudo nginx -t

# Si está OK, recargar
sudo systemctl reload nginx
```

### Paso 5: Probar

```bash
# Probar acceso directo a archivos
curl -I http://test.farmavet-bodega.cl/assets/css/style.css
curl -I http://test.farmavet-bodega.cl/logos/LOGO%20FARMAVET.png
```

**Deberían dar HTTP 200 OK**

---

## 🔍 Si Aún No Funciona

### Verificar Logs de Nginx

```bash
# Ver errores de Nginx
sudo tail -f /var/log/nginx/error.log

# Intentar acceder al sitio y ver qué error aparece
```

### Verificar que los Archivos Están en el Repositorio

```bash
# Como usuario web
sudo su - web
cd /home/web/farmavet-web

# Verificar que los archivos existen
ls -la assets/css/style.css
ls -la assets/js/main.js
ls -la logos/

# Si no existen, actualizar desde GitHub
git pull origin main
```

---

## 📋 Comandos Completos (Copia y Pega)

```bash
# 1. Editar Nginx
sudo nano /etc/nginx/sites-available/test.farmavet-bodega.cl
# Cambiar /home/tu-usuario/ a /home/web/ en todas las rutas

# 2. Verificar archivos
ls -la /home/web/farmavet-web/assets/css/style.css

# 3. Dar permisos
sudo chmod -R 755 /home/web/farmavet-web/assets
sudo chmod -R 755 /home/web/farmavet-web/logos
sudo chmod -R 755 /home/web/farmavet-web/static

# 4. Verificar y recargar
sudo nginx -t
sudo systemctl reload nginx

# 5. Probar
curl -I http://test.farmavet-bodega.cl/assets/css/style.css
```

---

¿Ya actualizaste las rutas en Nginx? ¿Qué muestra `ls -la /home/web/farmavet-web/assets/css/style.css`?

