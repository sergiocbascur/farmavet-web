# 🔍 Buscar Configuración del Dominio Principal

## ❓ Problema

El subdominio está configurado correctamente, pero muestra el contenido del dominio principal.

**Causa probable:** La configuración del dominio principal está capturando el subdominio.

## 🔍 Pasos de Diagnóstico

### Paso 1: Buscar Todas las Configuraciones de Nginx

```bash
# Ver todos los archivos de configuración
sudo ls -la /etc/nginx/sites-available/

# Ver todos los sitios activos
sudo ls -la /etc/nginx/sites-enabled/

# Ver configuración por defecto
sudo ls -la /etc/nginx/sites-available/default
```

### Paso 2: Buscar Configuración del Dominio Principal

```bash
# Buscar en todos los archivos
sudo grep -r "farmavet-bodega.cl" /etc/nginx/sites-available/

# Buscar server_name que pueda capturar subdominios
sudo grep -r "server_name" /etc/nginx/sites-available/ | grep -v "test.farmavet-bodega.cl"
```

### Paso 3: Ver Configuración Activa Completa

```bash
# Ver toda la configuración activa
sudo nginx -T 2>/dev/null | grep -B 5 -A 15 "server_name.*farmavet-bodega.cl"
```

Esto mostrará todas las configuraciones activas relacionadas con farmavet-bodega.cl.

### Paso 4: Verificar Orden de Procesamiento

```bash
# Ver todos los server blocks activos
sudo nginx -T 2>/dev/null | grep -E "^(    )?server_name" | head -20
```

Nginx procesa los `server` blocks en orden. Si hay uno que coincide primero, lo usará.

---

## 🔧 Solución: Verificar server_name del Dominio Principal

El dominio principal probablemente tiene un `server_name` que captura todos los subdominios o está en un archivo diferente.

```bash
# Buscar en todos los archivos de configuración
sudo find /etc/nginx -name "*.conf" -o -name "*farmavet*" 2>/dev/null

# Ver configuración por defecto
sudo cat /etc/nginx/sites-available/default | grep -A 10 "server_name"
```

---

## 💡 Posibles Ubicaciones

1. **`/etc/nginx/sites-available/default`** - Configuración por defecto
2. **`/etc/nginx/conf.d/*.conf`** - Configuraciones adicionales
3. **`/etc/nginx/nginx.conf`** - Configuración principal (puede tener includes)
4. **Otro nombre de archivo** - Puede tener otro nombre

---

## 🔧 Solución Rápida

```bash
# 1. Ver todos los archivos de configuración
sudo find /etc/nginx -type f -name "*.conf" | xargs grep -l "farmavet-bodega.cl" 2>/dev/null

# 2. Ver qué server_name tiene cada uno
sudo find /etc/nginx -type f -name "*.conf" -exec grep -H "server_name.*farmavet" {} \;

# 3. Ver configuración activa completa
sudo nginx -T 2>/dev/null | grep -B 3 -A 10 "server_name"
```

---

¿Qué muestra `sudo ls -la /etc/nginx/sites-available/`?

