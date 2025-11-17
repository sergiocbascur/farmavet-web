# 🌐 Configuración DNS en Cloudflare - test.farmavet-bodega.cl

## 🔍 ¿Activar Proxy Status (naranja) o dejarlo OFF (gris)?

### ⚠️ **Para pruebas: Proxy Status OFF (Gris)** - RECOMENDADO

**Ventajas:**
- ✅ Más simple y directo
- ✅ No interfiere con certificados SSL de Let's Encrypt
- ✅ Menos problemas de configuración
- ✅ Mejor para desarrollo/pruebas

**Desventajas:**
- ❌ No tienes protección DDoS de Cloudflare
- ❌ No tienes CDN de Cloudflare

---

### 🟠 **Para producción: Proxy Status ON (Naranja)** - Opcional

**Ventajas:**
- ✅ Protección DDoS automática
- ✅ CDN (contenido más rápido)
- ✅ Analytics de Cloudflare
- ✅ Firewall de Cloudflare

**Desventajas:**
- ⚠️ Requiere configuración SSL en Cloudflare
- ⚠️ Puede causar problemas con Let's Encrypt si no está bien configurado
- ⚠️ Más complejo para pruebas

---

## 📝 Configuración DNS en Cloudflare

### Opción 1: Proxy OFF (Gris) - RECOMENDADO PARA PRUEBAS

1. En Cloudflare Dashboard → DNS → Records
2. Agregar registro:
   - **Tipo:** `A` (o `CNAME` si prefieres)
   - **Nombre:** `test`
   - **IPv4 address:** `TU_IP_DEL_VPS` (la misma IP de farmavet-bodega.cl)
   - **Proxy status:** 🟦 **OFF (Gris)** ← Dejar desactivado
   - **TTL:** Auto

3. Guardar

**Resultado:** El tráfico va directo a tu VPS, sin pasar por Cloudflare.

---

### Opción 2: Proxy ON (Naranja) - Para Producción

Si activas el proxy (naranja), necesitas:

1. **Configurar SSL en Cloudflare:**
   - SSL/TLS → Overview
   - Modo: **"Full"** o **"Full (strict)"**
   - Esto permite que Cloudflare se comunique con tu servidor usando HTTPS

2. **En tu VPS, usar certificado de Cloudflare:**
   - O mantener Let's Encrypt pero configurar correctamente

3. **Agregar registro DNS:**
   - **Tipo:** `A`
   - **Nombre:** `test`
   - **IPv4 address:** `TU_IP_DEL_VPS`
   - **Proxy status:** 🟠 **ON (Naranja)** ← Activado

---

## 🎯 Recomendación para tu caso

**Deja Proxy Status OFF (Gris)** porque:

1. ✅ Es un subdominio de **pruebas** (`test.farmavet-bodega.cl`)
2. ✅ Más simple de configurar
3. ✅ Let's Encrypt funcionará sin problemas
4. ✅ No necesitas protección DDoS para pruebas
5. ✅ Puedes activarlo después cuando pases a producción

---

## 📋 Pasos Completos

### 1. En Cloudflare DNS:

```
Tipo: A
Nombre: test
Contenido: TU_IP_DEL_VPS (ej: 192.168.1.100)
Proxy: 🟦 OFF (Gris)
TTL: Auto
```

### 2. Esperar propagación DNS:
- 1-5 minutos normalmente
- Verificar: `nslookup test.farmavet-bodega.cl`

### 3. En tu VPS, configurar Nginx:
- Ya tienes `nginx_subdomain.conf` listo
- Solo actualizar rutas si usaste usuario "web"

### 4. Obtener certificado SSL:
```bash
sudo certbot --nginx -d test.farmavet-bodega.cl
```

### 5. Probar:
```bash
curl -I https://test.farmavet-bodega.cl
```

---

## 🔄 ¿Cambiar después?

**Sí, puedes cambiar fácilmente:**
- Ahora: Proxy OFF (pruebas)
- Después: Proxy ON (producción) - solo activar el switch naranja

---

## ⚠️ Importante

Si activas Proxy ON (naranja):
- Necesitas configurar SSL/TLS en Cloudflare → Modo "Full"
- Tu servidor debe tener certificado válido (Let's Encrypt funciona)
- Cloudflare se comunicará con tu servidor vía HTTPS

Si dejas Proxy OFF (gris):
- Todo funciona directo
- Let's Encrypt funciona sin problemas
- Más simple para empezar

---

## ✅ Resumen

**Para `test.farmavet-bodega.cl` (pruebas):**
- 🟦 **Proxy Status: OFF (Gris)** ← Recomendado

**Para producción futura:**
- 🟠 **Proxy Status: ON (Naranja)** ← Cuando esté listo

¿Necesitas ayuda con algún otro paso de la configuración?

