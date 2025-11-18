# 🔒 Guía para Aplicar Mejoras de Seguridad

## ✅ Mejoras Implementadas

### 1. Headers de Seguridad en Nginx
- ✅ X-Frame-Options: SAMEORIGIN
- ✅ X-Content-Type-Options: nosniff
- ✅ X-XSS-Protection: 1; mode=block
- ✅ Referrer-Policy: strict-origin-when-cross-origin
- ✅ Permissions-Policy: geolocation=(), microphone=(), camera=()
- ✅ Strict-Transport-Security (HSTS) para HTTPS

### 2. SECRET_KEY Mejorada
- ✅ Generación automática de SECRET_KEY segura si no está configurada
- ✅ Script `generar_secret_key.py` para crear claves manualmente

### 3. Protección CSRF Básica
- ✅ Funciones `generate_csrf_token()` y `validate_csrf_token()`
- ✅ Token disponible en templates como `{{ csrf_token }}`

### 4. Script de Verificación
- ✅ `verificar_seguridad.py` para verificar configuración

---

## 📋 Pasos para Aplicar en el Servidor

### Paso 1: Actualizar Nginx con Headers de Seguridad

```bash
# 1. Actualizar código
cd /home/web/farmavet-web
git pull origin main

# 2. Copiar configuración actualizada
sudo cp nginx_subdomain.conf /etc/nginx/sites-available/test.farmavet-bodega.cl

# 3. Verificar configuración
sudo nginx -t

# 4. Recargar Nginx
sudo systemctl reload nginx
```

### Paso 2: Configurar SECRET_KEY Segura

```bash
# Opción A: Generar nueva clave
cd /home/web/farmavet-web
source venv/bin/activate
python generar_secret_key.py

# Copiar la clave generada y agregarla al servicio systemd:
sudo nano /etc/systemd/system/farmavet-web.service

# Agregar esta línea en la sección [Service]:
# Environment="SECRET_KEY=TU_CLAVE_GENERADA_AQUI"

# Recargar systemd y reiniciar servicio
sudo systemctl daemon-reload
sudo systemctl restart farmavet-web
```

### Paso 3: Verificar Seguridad

```bash
cd /home/web/farmavet-web
source venv/bin/activate
python verificar_seguridad.py
```

### Paso 4: Verificar Headers de Seguridad

Puedes verificar que los headers están funcionando usando:

```bash
# Ver headers de respuesta
curl -I https://test.farmavet-bodega.cl/

# O usar herramientas online como:
# https://securityheaders.com/
# https://observatory.mozilla.org/
```

---

## 🔍 Verificación Manual

### Headers que Deberías Ver:

```
X-Frame-Options: SAMEORIGIN
X-Content-Type-Options: nosniff
X-XSS-Protection: 1; mode=block
Referrer-Policy: strict-origin-when-cross-origin
Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
```

---

## ⚠️ Notas Importantes

1. **SECRET_KEY**: Es crítico configurar una SECRET_KEY única y segura en producción. No uses la clave por defecto.

2. **CSRF**: Los tokens CSRF están disponibles en templates, pero necesitas agregarlos manualmente a los formularios críticos (eliminar, cambiar contraseña, etc.).

3. **HTTPS**: Asegúrate de que el sitio esté accesible solo por HTTPS en producción.

4. **Permisos de BD**: Verifica que `instance/database.db` tenga permisos 600 o 644.

---

## 🔄 Próximos Pasos (Opcional)

- Agregar tokens CSRF a todos los formularios POST del admin
- Implementar logging de intentos de acceso sospechosos
- Configurar backup automático de la base de datos
- Agregar Content Security Policy (CSP) headers

