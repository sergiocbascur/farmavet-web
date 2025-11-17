# 🔧 Corregir Permisos del Directorio Padre

## ❓ Problema

Los errores 403 persisten incluso después de cambiar permisos:
```
open() "/home/web/farmavet-web/assets/css/style.css" failed (13: Permission denied)
```

**Causa probable:** El directorio padre `/home/web` no tiene permisos de ejecución para que Nginx pueda acceder a los subdirectorios.

## 🔧 Solución

### Paso 1: Verificar Permisos del Directorio Padre

```bash
# Ver permisos de /home/web
ls -ld /home/web

# Debe mostrar algo como: drwxr-xr-x o drwxrwxr-x
# Si muestra drwx------, ese es el problema
```

### Paso 2: Corregir Permisos del Directorio Padre

```bash
# Dar permisos de ejecución al directorio /home/web
sudo chmod 755 /home/web

# Verificar que se aplicó
ls -ld /home/web
```

### Paso 3: Asegurar Permisos Completos de la Ruta

```bash
# Asegurar que toda la ruta sea accesible
sudo chmod 755 /home
sudo chmod 755 /home/web
sudo chmod -R 755 /home/web/farmavet-web/

# Asegurar que los archivos sean legibles
sudo find /home/web/farmavet-web -type f -exec chmod 644 {} \;

# Asegurar que los directorios sean accesibles
sudo find /home/web/farmavet-web -type d -exec chmod 755 {} \;
```

### Paso 4: Verificar Propietario

```bash
# Asegurar que el usuario web sea propietario
sudo chown -R web:web /home/web/farmavet-web/
```

### Paso 5: Probar Acceso como www-data

```bash
# Probar si www-data puede acceder
sudo -u www-data ls /home/web/farmavet-web/assets/css/style.css

# Si funciona, debería mostrar el archivo sin error
```

---

## 🔍 Diagnóstico Completo

### Ver Permisos de Toda la Ruta

```bash
# Ver permisos de cada nivel
ls -ld /home
ls -ld /home/web
ls -ld /home/web/farmavet-web
ls -ld /home/web/farmavet-web/assets
ls -ld /home/web/farmavet-web/assets/css
ls -la /home/web/farmavet-web/assets/css/style.css
```

**Todos los directorios deben tener permisos `755` (drwxr-xr-x)**
**Todos los archivos deben tener permisos `644` (-rw-r--r--)**

---

## ✅ Solución Completa (Ejecutar Todo)

```bash
# 1. Corregir permisos del directorio padre
sudo chmod 755 /home
sudo chmod 755 /home/web

# 2. Corregir propietario
sudo chown -R web:web /home/web/farmavet-web/

# 3. Dar permisos a directorios
sudo find /home/web/farmavet-web -type d -exec chmod 755 {} \;

# 4. Dar permisos a archivos
sudo find /home/web/farmavet-web -type f -exec chmod 644 {} \;

# 5. Verificar acceso
sudo -u www-data ls /home/web/farmavet-web/assets/css/style.css

# 6. Recargar Nginx
sudo systemctl reload nginx
```

---

## 🔍 Si Aún No Funciona

### Opción 1: Agregar www-data al Grupo web

```bash
# Agregar www-data al grupo web
sudo usermod -a -G web www-data

# Verificar
groups www-data

# Dar permisos de grupo
sudo chmod -R 750 /home/web/farmavet-web/
sudo chmod g+r /home/web/farmavet-web/ -R
sudo find /home/web/farmavet-web -type d -exec chmod g+x {} \;
```

### Opción 2: Cambiar Propietario a www-data (Menos Seguro)

```bash
# Solo si nada más funciona
sudo chown -R www-data:www-data /home/web/farmavet-web/
sudo chmod -R 755 /home/web/farmavet-web/
```

---

## 💡 Explicación

En Linux, para acceder a un archivo en `/home/web/farmavet-web/assets/css/style.css`, necesitas:
1. **Permiso de ejecución** en `/home` (para entrar)
2. **Permiso de ejecución** en `/home/web` (para entrar)
3. **Permiso de ejecución** en `/home/web/farmavet-web` (para entrar)
4. **Permiso de ejecución** en `/home/web/farmavet-web/assets` (para entrar)
5. **Permiso de ejecución** en `/home/web/farmavet-web/assets/css` (para entrar)
6. **Permiso de lectura** en `style.css` (para leer el archivo)

Si cualquiera de los directorios padre no tiene permiso de ejecución, no podrás acceder al archivo, aunque el archivo mismo tenga permisos correctos.

