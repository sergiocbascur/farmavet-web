# 🔒 Solución Error SSL - NET::ERR_CERT_COMMON_NAME_INVALID

## 🔍 Diagnóstico

El error `NET::ERR_CERT_COMMON_NAME_INVALID` significa que:
- El certificado SSL no existe aún, O
- El certificado es para otro dominio, O
- El certificado está mal configurado

## ✅ Solución Paso a Paso

### Paso 1: Verificar que el Servicio Esté Corriendo

```bash
# Verificar estado
sudo systemctl status farmavet-web

# Si no está corriendo, iniciarlo
sudo systemctl start farmavet-web
```

### Paso 2: Verificar que Nginx Esté Configurado

```bash
# Verificar configuración
sudo nginx -t

# Ver si el sitio está activo
ls -la /etc/nginx/sites-enabled/ | grep test.farmavet-bodega.cl
```

### Paso 3: Probar HTTP Primero (sin SSL)

```bash
# Desde el VPS
curl -I http://test.farmavet-bodega.cl

# O desde tu navegador, acceder a:
# http://test.farmavet-bodega.cl (sin la 's' de https)
```

**Si HTTP funciona:** Continúa al paso 4.

**Si HTTP no funciona:** Revisa la configuración de Nginx primero.

### Paso 4: Obtener Certificado SSL con Let's Encrypt

```bash
# Instalar certbot si no lo tienes
sudo apt update
sudo apt install certbot python3-certbot-nginx -y

# Obtener certificado para el subdominio
sudo certbot --nginx -d test.farmavet-bodega.cl

# Seguir las instrucciones:
# 1. Email: tu email
# 2. Aceptar términos (A)
# 3. Compartir email (opcional, Y o N)
# 4. Redirigir HTTP a HTTPS: Elegir opción 2 (Redirect)
```

### Paso 5: Verificar Certificado

```bash
# Ver certificados instalados
sudo certbot certificates

# Verificar que el certificado existe
sudo ls -la /etc/letsencrypt/live/test.farmavet-bodega.cl/
```

### Paso 6: Recargar Nginx

```bash
sudo systemctl reload nginx
```

### Paso 7: Probar HTTPS

```bash
# Desde el VPS
curl -I https://test.farmavet-bodega.cl

# Deberías ver: HTTP/2 200
```

---

## 🔧 Si Certbot Falla

### Error: "Could not find a virtual host"

**Solución:** Asegúrate de que Nginx tenga la configuración correcta:

```bash
# Verificar que el archivo existe
sudo ls -la /etc/nginx/sites-available/test.farmavet-bodega.cl

# Verificar que está enlazado
sudo ls -la /etc/nginx/sites-enabled/ | grep test

# Si no está, crearlo:
sudo ln -s /etc/nginx/sites-available/test.farmavet-bodega.cl /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### Error: "Domain not pointing to this server"

**Solución:** Verificar DNS:

```bash
# Verificar DNS
nslookup test.farmavet-bodega.cl

# Debería mostrar la IP de tu VPS
# Si no, espera más tiempo para propagación DNS (hasta 48 horas)
```

### Error: "Connection refused"

**Solución:** Verificar que el servicio esté corriendo:

```bash
# Verificar puerto
sudo netstat -tlnp | grep 5001

# Si no aparece, el servicio no está corriendo
sudo systemctl start farmavet-web
sudo systemctl status farmavet-web
```

---

## 🚨 Solución Temporal: Acceder vía HTTP

Mientras configuras SSL, puedes acceder vía HTTP:

```
http://test.farmavet-bodega.cl
```

**Nota:** El navegador mostrará "No seguro" pero funcionará.

---

## 📋 Checklist Rápido

- [ ] Servicio farmavet-web corriendo (puerto 5001)
- [ ] Nginx configurado y recargado
- [ ] HTTP funciona (http://test.farmavet-bodega.cl)
- [ ] Certbot instalado
- [ ] Certificado obtenido con certbot
- [ ] Nginx recargado después del certificado
- [ ] HTTPS funciona (https://test.farmavet-bodega.cl)

---

## 🔍 Comandos de Diagnóstico

```bash
# Ver logs del servicio
sudo journalctl -u farmavet-web -n 50

# Ver logs de Nginx
sudo tail -f /var/log/nginx/error.log

# Verificar puerto
sudo ss -tlnp | grep 5001

# Verificar DNS
dig test.farmavet-bodega.cl

# Probar conexión local
curl http://127.0.0.1:5001
```

---

## 💡 Recomendación

1. **Primero prueba HTTP** (sin 's'): `http://test.farmavet-bodega.cl`
2. Si HTTP funciona, **obtén el certificado SSL** con certbot
3. Luego prueba HTTPS: `https://test.farmavet-bodega.cl`

¿En qué paso estás? ¿HTTP funciona o también da error?

