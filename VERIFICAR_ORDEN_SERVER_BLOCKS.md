# 🔍 Verificar Orden de Server Blocks en Nginx

## ❓ Problema

El subdominio `test.farmavet-bodega.cl` muestra el contenido del dominio principal `www.farmavet-bodega.cl`.

## 🔍 Diagnóstico

### Paso 1: Verificar Orden de Procesamiento

Nginx procesa los `server` blocks en orden alfabético de los archivos en `sites-enabled/`.

```bash
# Ver orden de archivos activos
sudo ls -la /etc/nginx/sites-enabled/ | grep -E "bodega|test"
```

**Problema potencial:** Si `bodega-farmavet` se procesa antes que `test.farmavet-bodega.cl`, y tiene un `server_name` que coincide, capturará las peticiones.

### Paso 2: Verificar server_name del Dominio Principal

```bash
# Ver el server_name exacto del dominio principal
sudo grep "server_name" /etc/nginx/sites-available/bodega-farmavet
```

**Verificar que NO tenga:**
- `server_name *.farmavet-bodega.cl;` (captura todos los subdominios)
- `server_name _;` (captura todo)

**Debe tener solo:**
- `server_name farmavet-bodega.cl www.farmavet-bodega.cl;`

### Paso 3: Verificar Configuración Activa Completa

```bash
# Ver todos los server blocks activos en orden
sudo nginx -T 2>/dev/null | grep -E "^[[:space:]]*server_name" | head -10
```

### Paso 4: Verificar que el Subdominio Esté Primero

Para asegurar que el subdominio se procese primero, puedes renombrar el archivo:

```bash
# Opción 1: Renombrar para que esté primero alfabéticamente
sudo mv /etc/nginx/sites-enabled/test.farmavet-bodega.cl /etc/nginx/sites-enabled/00-test.farmavet-bodega.cl

# Opción 2: O renombrar el dominio principal para que esté después
sudo mv /etc/nginx/sites-enabled/bodega-farmavet /etc/nginx/sites-enabled/z-bodega-farmavet
```

Luego recargar Nginx:

```bash
sudo nginx -t
sudo systemctl reload nginx
```

---

## 🔧 Solución: Verificar Prioridad

El `server_name` más específico tiene prioridad. `test.farmavet-bodega.cl` es más específico que `*.farmavet-bodega.cl`, pero si el dominio principal tiene `server_name farmavet-bodega.cl www.farmavet-bodega.cl;`, NO debería capturar el subdominio.

**Verificar que el dominio principal NO tenga wildcard:**

```bash
sudo cat /etc/nginx/sites-available/bodega-farmavet | grep -A 2 "server_name"
```

---

## 💡 Solución Rápida

Si el problema persiste, verifica que el bloque HTTPS del subdominio esté descomentado y tenga el `proxy_pass` correcto:

```bash
# Ver bloque HTTPS del subdominio
sudo sed -n '/listen 443/,/^}/p' /etc/nginx/sites-available/test.farmavet-bodega.cl | grep -E "server_name|proxy_pass"
```

Debe mostrar:
- `server_name test.farmavet-bodega.cl;`
- `proxy_pass http://127.0.0.1:5001;`

---

## 🔄 Recargar Nginx

Después de cualquier cambio:

```bash
# Probar configuración
sudo nginx -t

# Si está bien, recargar
sudo systemctl reload nginx

# Verificar logs
sudo tail -f /var/log/nginx/farmavet-web-error.log
```

---

¿Qué muestra `sudo cat /etc/nginx/sites-available/bodega-farmavet | grep -A 2 "server_name"`?

