# 🔧 Solución: Error de Autenticación SMTP

## 🚨 Error Común

```
Error de autenticación: Verifica usuario y contraseña SMTP
```

## 🔍 Diagnóstico Rápido

### Paso 1: Ejecutar Script de Diagnóstico

En el VPS, ejecuta:

```bash
cd /home/web/farmavet-web
python3 diagnosticar_smtp.py
```

Este script verificará:
- ✅ Variables de entorno configuradas
- ✅ Conexión SMTP
- ✅ Autenticación
- ✅ Envío de correo de prueba

### Paso 2: Verificar Variables de Entorno

```bash
# Ver variables del servicio
sudo systemctl show farmavet-web | grep SMTP

# O ver variables del proceso en ejecución
sudo cat /proc/$(pgrep -f "gunicorn.*app:app")/environ | tr '\0' '\n' | grep SMTP
```

### Paso 3: Revisar Logs

```bash
# Ver logs en tiempo real
sudo journalctl -u farmavet-web -f

# Ver últimos 50 logs
sudo journalctl -u farmavet-web -n 50
```

Busca mensajes como:
- `"Intentando conectar a SMTP: ..."`
- `"Error de autenticación SMTP: ..."`

## 🛠️ Soluciones por Tipo de Correo

### 📧 Gmail (Más Común)

**Problema:** Usar contraseña normal en lugar de App Password.

**Solución:**

1. **Activa verificación en 2 pasos:**
   - Ve a: https://myaccount.google.com/security
   - Activa "Verificación en 2 pasos"

2. **Genera App Password:**
   - Ve a: https://myaccount.google.com/apppasswords
   - Selecciona "Mail" y "Otro (nombre personalizado)"
   - Escribe: "FARMAVET Web"
   - Copia la contraseña de 16 caracteres (ej: `abcd efgh ijkl mnop`)

3. **Actualiza configuración en VPS:**
   ```bash
   sudo nano /etc/systemd/system/farmavet-web.service
   ```
   
   Asegúrate de tener:
   ```ini
   [Service]
   Environment="SMTP_HOST=smtp.gmail.com"
   Environment="SMTP_PORT=587"
   Environment="SMTP_USER=tu-email@gmail.com"
   Environment="SMTP_PASSWORD=abcdefghijklmnop"  # App Password (sin espacios)
   Environment="SMTP_FROM=tu-email@gmail.com"
   ```

4. **Recargar y reiniciar:**
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl restart farmavet-web
   ```

5. **Probar:**
   ```bash
   python3 diagnosticar_smtp.py
   ```

### 📧 Correo Institucional (U. de Chile)

**Problema:** Credenciales incorrectas o restricciones de firewall.

**Solución:**

1. **Verifica credenciales con TI:**
   - Contacta al departamento de TI
   - Confirma usuario, contraseña, host y puerto

2. **Configuración típica:**
   ```ini
   Environment="SMTP_HOST=smtp.uchile.cl"
   Environment="SMTP_PORT=587"
   Environment="SMTP_USER=tu-usuario@uchile.cl"
   Environment="SMTP_PASSWORD=tu-contraseña"
   Environment="SMTP_FROM=farmavet@uchile.cl"
   ```

3. **Verifica firewall:**
   ```bash
   # Probar conexión manual
   telnet smtp.uchile.cl 587
   ```

### 📧 SendGrid / Servicios Transaccionales

**Problema:** API Key incorrecta o expirada.

**Solución:**

1. **Verifica API Key en SendGrid:**
   - Ve a: https://app.sendgrid.com/settings/api_keys
   - Genera una nueva API Key si es necesario

2. **Configuración:**
   ```ini
   Environment="SMTP_HOST=smtp.sendgrid.net"
   Environment="SMTP_PORT=587"
   Environment="SMTP_USER=apikey"
   Environment="SMTP_PASSWORD=SG.tu-api-key-aqui"
   Environment="SMTP_FROM=noreply@laboratoriofarmavet.cl"
   ```

## 🔄 Usar Script Automático

Si prefieres usar el script de configuración:

```bash
cd /home/web/farmavet-web
sudo ./configurar_correo.sh
```

Este script te pedirá:
- SMTP Host
- SMTP Port
- SMTP User
- SMTP Password
- SMTP From

Y actualizará automáticamente el archivo de servicio.

## ✅ Verificación Final

1. **Ejecuta diagnóstico:**
   ```bash
   python3 diagnosticar_smtp.py
   ```

2. **Prueba el formulario:**
   - Ve a: `https://tu-dominio.com/contacto.html`
   - Completa y envía el formulario
   - Deberías ver el modal de confirmación

3. **Revisa logs:**
   ```bash
   sudo journalctl -u farmavet-web -f
   ```
   
   Deberías ver:
   ```
   ✅ Conexión SMTP establecida
   ✅ Login SMTP exitoso
   ✅ Correo enviado exitosamente
   ```

## 🆘 Si Nada Funciona

1. **Verifica que el servicio esté corriendo:**
   ```bash
   sudo systemctl status farmavet-web
   ```

2. **Revisa permisos del archivo de servicio:**
   ```bash
   sudo chmod 600 /etc/systemd/system/farmavet-web.service
   ```

3. **Verifica que las variables se carguen:**
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl restart farmavet-web
   sudo systemctl show farmavet-web | grep SMTP
   ```

4. **Prueba conexión SMTP manualmente:**
   ```python
   python3 -c "
   import smtplib
   server = smtplib.SMTP('smtp.gmail.com', 587)
   server.starttls()
   server.login('tu-email@gmail.com', 'tu-app-password')
   print('✅ Conexión exitosa')
   server.quit()
   "
   ```

## 📝 Checklist de Verificación

- [ ] Variables de entorno configuradas en `/etc/systemd/system/farmavet-web.service`
- [ ] `systemctl daemon-reload` ejecutado
- [ ] Servicio reiniciado: `systemctl restart farmavet-web`
- [ ] Variables visibles: `systemctl show farmavet-web | grep SMTP`
- [ ] Script de diagnóstico ejecutado: `python3 diagnosticar_smtp.py`
- [ ] Conexión SMTP exitosa
- [ ] Correo de prueba enviado y recibido
- [ ] Formulario de contacto funciona
- [ ] Logs muestran envío exitoso

---

**¿Necesitas más ayuda?** Revisa los logs detallados y comparte el error específico.

