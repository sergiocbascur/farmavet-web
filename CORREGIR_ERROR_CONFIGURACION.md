# 🔧 Corregir Error "unknown directive Configuración"

## ❓ Problema

```
nginx: [emerg] unknown directive "Configuración" in /etc/nginx/sites-enabled/test.farmavet-bodega.cl:50
```

Esto significa que hay un comentario que no está correctamente formateado (falta el `#` al inicio).

## 🔧 Solución

### Paso 1: Ver la línea 50

```bash
sudo sed -n '45,55p' /etc/nginx/sites-available/test.farmavet-bodega.cl
```

Esto mostrará las líneas alrededor de la 50 para ver qué está mal.

### Paso 2: Editar el archivo

```bash
sudo nano /etc/nginx/sites-available/test.farmavet-bodega.cl
```

Busca alrededor de la línea 50. Probablemente verás algo como:

```
Configuración HTTPS (descomentar después de obtener certificado SSL)
```

O:

```
# Configuración HTTPS
```

**Si la línea NO tiene `#` al inicio, agrégaselo:**

```
# Configuración HTTPS
```

### Paso 3: Verificar todos los comentarios

Asegúrate de que TODOS los comentarios tengan `#` al inicio. Los comentarios válidos en Nginx son:

```
# Este es un comentario válido
```

NO válido:
```
Este no es un comentario (causará error)
```

### Paso 4: Verificar sintaxis

```bash
sudo nginx -t
```

Si hay más errores, te dirá en qué línea están.

---

## 💡 Regla General

En archivos de configuración de Nginx:
- ✅ **Comentarios:** Deben empezar con `#`
- ✅ **Directivas:** Son palabras clave de Nginx (server, location, proxy_pass, etc.)
- ❌ **Cualquier otra cosa sin `#`:** Causará error

---

## 🔍 Buscar todos los comentarios mal formateados

```bash
# Buscar líneas que empiezan con palabras en español (probablemente comentarios mal formateados)
sudo grep -n "^[A-Z]" /etc/nginx/sites-available/test.farmavet-bodega.cl | grep -v "^[0-9]*:#"
```

Esto puede ayudar a encontrar otros comentarios mal formateados.

