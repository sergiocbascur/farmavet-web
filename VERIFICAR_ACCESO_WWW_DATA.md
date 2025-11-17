# 🔍 Verificar Acceso Real de www-data

## ❓ Problema

Los permisos parecen correctos, pero Nginx sigue dando errores 403.

## 🔍 Diagnóstico

### Paso 1: Probar Acceso Directo como www-data

```bash
# Probar si www-data puede leer el archivo
sudo -u www-data cat /home/web/farmavet-web/assets/css/style.css | head -5

# Si funciona, debería mostrar las primeras líneas del CSS
# Si falla, mostrará el error exacto
```

### Paso 2: Verificar Usuario de Nginx

```bash
# Ver qué usuario está usando Nginx
sudo grep "^user" /etc/nginx/nginx.conf

# Debe mostrar algo como: user www-data;
```

### Paso 3: Verificar Procesos de Nginx

```bash
# Ver procesos de Nginx y su usuario
ps aux | grep nginx

# Todos los procesos worker deben ser www-data
```

### Paso 4: Verificar SELinux (si está activo)

```bash
# Verificar si SELinux está activo
getenforce

# Si está en "Enforcing", puede estar bloqueando
```

### Paso 5: Recargar Nginx Completamente

```bash
# Reiniciar Nginx (no solo recargar)
sudo systemctl restart nginx

# Verificar que está corriendo
sudo systemctl status nginx
```

### Paso 6: Verificar Logs Después de Reiniciar

```bash
# Limpiar logs anteriores
sudo truncate -s 0 /var/log/nginx/farmavet-web-error.log

# Intentar acceder desde el navegador
# Luego ver los nuevos errores
sudo tail -20 /var/log/nginx/farmavet-web-error.log
```

---

## 🔧 Soluciones Alternativas

### Opción 1: Cambiar Usuario de Nginx (Temporal)

Si www-data no puede acceder, puedes cambiar temporalmente el usuario de Nginx:

```bash
# Editar configuración principal de Nginx
sudo nano /etc/nginx/nginx.conf

# Cambiar la línea:
# user www-data;
# Por:
# user web;

# Probar configuración
sudo nginx -t

# Reiniciar
sudo systemctl restart nginx
```

**⚠️ Nota:** Esto es menos seguro, pero puede funcionar para diagnóstico.

### Opción 2: Agregar www-data al Grupo web

```bash
# Agregar www-data al grupo web
sudo usermod -a -G web www-data

# Verificar
groups www-data

# Cambiar permisos para que el grupo tenga acceso
sudo chmod -R 750 /home/web/farmavet-web/
sudo chmod g+r /home/web/farmavet-web/ -R
sudo find /home/web/farmavet-web -type d -exec chmod g+x {} \;

# Reiniciar Nginx
sudo systemctl restart nginx
```

### Opción 3: Cambiar Propietario a www-data (Solo para Diagnóstico)

```bash
# Cambiar propietario a www-data temporalmente
sudo chown -R www-data:www-data /home/web/farmavet-web/

# Reiniciar Nginx
sudo systemctl restart nginx

# Si funciona, el problema es de permisos
# Luego puedes revertir y usar otra solución
```

---

## ✅ Verificación Final

Después de aplicar cualquier solución:

```bash
# 1. Verificar que Nginx puede leer
sudo -u www-data ls /home/web/farmavet-web/assets/css/style.css

# 2. Verificar que Nginx está corriendo
sudo systemctl status nginx

# 3. Limpiar caché del navegador y recargar página
# 4. Verificar logs
sudo tail -f /var/log/nginx/farmavet-web-error.log
```

---

## 🔍 Comando de Diagnóstico Completo

Ejecuta esto para ver todo:

```bash
echo "=== Usuario de Nginx ==="
sudo grep "^user" /etc/nginx/nginx.conf

echo "=== Procesos de Nginx ==="
ps aux | grep nginx | grep -v grep

echo "=== Permisos de /home/web ==="
ls -ld /home/web

echo "=== Permisos del proyecto ==="
ls -ld /home/web/farmavet-web

echo "=== Permisos de assets ==="
ls -ld /home/web/farmavet-web/assets

echo "=== Permisos de style.css ==="
ls -la /home/web/farmavet-web/assets/css/style.css

echo "=== Test de acceso como www-data ==="
sudo -u www-data ls /home/web/farmavet-web/assets/css/style.css 2>&1

echo "=== Estado de Nginx ==="
sudo systemctl status nginx --no-pager | head -10
```

