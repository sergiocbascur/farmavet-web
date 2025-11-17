# 🔧 Corregir Errores 403 (Forbidden) en Archivos Estáticos

## ❓ Problema

Los archivos estáticos (CSS, JS, imágenes) devuelven error 403 (Forbidden):
- `style.css:1 Failed to load resource: the server responded with a status of 403`
- `/logos/LOGO%20FARMAVET.png:1 Failed to load resource: the server responded with a status of 403`
- `main.js:1 Failed to load resource: the server responded with a status of 403`

**Causa:** Nginx (usuario `www-data`) no tiene permisos para leer los archivos.

## 🔧 Solución

### Paso 1: Verificar Propietario y Permisos Actuales

```bash
# Ver propietario y permisos del directorio principal
ls -la /home/web/farmavet-web/ | head -20

# Ver permisos de assets
ls -la /home/web/farmavet-web/assets/

# Ver permisos de logos
ls -la /home/web/farmavet-web/logos/
```

### Paso 2: Corregir Propietario

El usuario `web` debe ser el propietario, pero Nginx necesita poder leer:

```bash
# Asegurar que el usuario web sea propietario
sudo chown -R web:web /home/web/farmavet-web/

# Dar permisos de lectura a Nginx (www-data puede leer archivos del grupo)
sudo chmod -R 755 /home/web/farmavet-web/
```

O mejor aún, agregar `www-data` al grupo `web`:

```bash
# Agregar www-data al grupo web
sudo usermod -a -G web www-data

# Dar permisos de lectura al grupo
sudo chmod -R 750 /home/web/farmavet-web/
sudo chmod -R g+r /home/web/farmavet-web/

# Asegurar que los directorios sean ejecutables para el grupo
sudo find /home/web/farmavet-web -type d -exec chmod g+x {} \;
```

### Paso 3: Verificar Permisos Específicos

```bash
# Verificar que los archivos sean legibles
ls -la /home/web/farmavet-web/assets/css/style.css
ls -la /home/web/farmavet-web/assets/js/main.js
ls -la /home/web/farmavet-web/logos/

# Deben mostrar permisos como: -rw-r--r-- o -rw-rw-r--
```

### Paso 4: Verificar que Nginx Puede Acceder

```bash
# Probar acceso como usuario www-data
sudo -u www-data ls /home/web/farmavet-web/assets/css/style.css

# Si da error, el problema es de permisos
```

### Paso 5: Verificar Configuración de Nginx

Asegúrate de que las rutas en Nginx sean correctas:

```bash
# Ver configuración de assets
sudo grep -A 5 "location /assets" /etc/nginx/sites-available/test.farmavet-bodega.cl

# Debe mostrar:
# location /assets {
#     alias /home/web/farmavet-web/assets;
#     ...
# }
```

### Paso 6: Recargar Nginx

```bash
sudo systemctl reload nginx
```

---

## 🔍 Diagnóstico Avanzado

### Ver Logs de Nginx

```bash
# Ver errores recientes
sudo tail -20 /var/log/nginx/farmavet-web-error.log

# Ver accesos
sudo tail -20 /var/log/nginx/farmavet-web-access.log
```

Los errores 403 suelen aparecer como:
```
[error] 1234#0: *1 open() "/home/web/farmavet-web/assets/css/style.css" failed (13: Permission denied)
```

### Verificar SELinux (si está activo)

```bash
# Verificar si SELinux está activo
getenforce

# Si está en "Enforcing", puede necesitar ajustes
```

---

## ✅ Solución Rápida (Recomendada)

Ejecuta estos comandos en orden:

```bash
# 1. Corregir propietario
sudo chown -R web:web /home/web/farmavet-web/

# 2. Dar permisos de lectura
sudo chmod -R 755 /home/web/farmavet-web/

# 3. Asegurar que los directorios sean ejecutables
sudo find /home/web/farmavet-web -type d -exec chmod 755 {} \;

# 4. Asegurar que los archivos sean legibles
sudo find /home/web/farmavet-web -type f -exec chmod 644 {} \;

# 5. Recargar Nginx
sudo systemctl reload nginx
```

---

## 🔍 Verificar que Funciona

Después de aplicar los cambios:

1. **Limpiar caché del navegador** (Ctrl+Shift+R o Ctrl+F5)
2. **Recargar la página** `https://test.farmavet-bodega.cl/`
3. **Verificar en la consola del navegador** que no haya más errores 403

---

## 💡 Nota sobre Seguridad

Los permisos `755` para directorios y `644` para archivos son estándar y seguros:
- **755** (directorios): propietario puede leer/escribir/ejecutar, otros pueden leer/ejecutar
- **644** (archivos): propietario puede leer/escribir, otros pueden leer

Si necesitas más seguridad, puedes usar `750` para directorios y `640` para archivos, pero asegúrate de que `www-data` esté en el grupo `web`.

