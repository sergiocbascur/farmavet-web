# 📧 Opciones de Correo para FARMAVET

## ¿Necesitas un correo especial?

**Respuesta corta:** No es estrictamente necesario, pero **es altamente recomendable** para producción.

## 🎯 Opciones Disponibles

### Opción 1: Correo Personal/Institucional Existente ⚠️

**Puedes usar:**
- Tu correo personal de Gmail
- Correo institucional de la Universidad de Chile (si tienes acceso)

**Ventajas:**
- ✅ No requiere configuración adicional
- ✅ Funciona inmediatamente
- ✅ Gratis

**Desventajas:**
- ❌ No es profesional (aparece tu email personal como remitente)
- ❌ Límites de envío de Gmail (500 emails/día)
- ❌ Si cambias de cuenta, debes reconfigurar
- ❌ No es ideal para producción

**Cuándo usarlo:**
- Pruebas y desarrollo
- Volumen bajo de consultas
- Solución temporal

---

### Opción 2: Correo Institucional de la Universidad ⭐ (Recomendado)

**Ejemplo:** `farmavet@uchile.cl` o `contacto@laboratoriofarmavet.cl`

**Ventajas:**
- ✅ Profesional y oficial
- ✅ Confianza institucional
- ✅ Sin costos adicionales (si ya tienes acceso)
- ✅ Usa infraestructura de la universidad

**Desventajas:**
- ⚠️ Requiere acceso a servidor SMTP de la universidad
- ⚠️ Puede tener restricciones de configuración

**Cómo obtenerlo:**
1. Contactar al área de TI de la Universidad de Chile
2. Solicitar una cuenta de correo para el laboratorio
3. Obtener credenciales SMTP del servidor de la universidad

**Configuración típica:**
```bash
SMTP_HOST=smtp.uchile.cl
SMTP_PORT=587
SMTP_USER=farmavet@uchile.cl
SMTP_PASSWORD=contraseña-asignada
SMTP_FROM=farmavet@uchile.cl
```

---

### Opción 3: Servicio de Email Transaccional 🚀 (Mejor para Producción)

**Servicios recomendados:**

#### SendGrid (Gratis hasta 100 emails/día)
- **Registro:** https://sendgrid.com
- **Gratis:** 100 emails/día
- **Pago:** Desde $15/mes para más volumen

**Configuración:**
```bash
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=SG.tu-api-key-aqui
SMTP_FROM=noreply@laboratoriofarmavet.cl
```

#### Mailgun (Gratis hasta 5,000 emails/mes)
- **Registro:** https://www.mailgun.com
- **Gratis:** 5,000 emails/mes (primeros 3 meses)
- **Pago:** Desde $35/mes después

**Configuración:**
```bash
SMTP_HOST=smtp.mailgun.org
SMTP_PORT=587
SMTP_USER=postmaster@tu-dominio.mailgun.org
SMTP_PASSWORD=contraseña-de-mailgun
SMTP_FROM=noreply@laboratoriofarmavet.cl
```

#### Amazon SES (Muy económico)
- **Costo:** $0.10 por cada 1,000 emails
- **Ideal para:** Alto volumen
- **Requisito:** Cuenta AWS

---

### Opción 4: Correo con Dominio Propio 📧

Si tienes el dominio `laboratoriofarmavet.cl`:

**Opciones:**
1. **Google Workspace** (antes G Suite)
   - $6 USD/usuario/mes
   - Correo profesional: `contacto@laboratoriofarmavet.cl`
   - Incluye Gmail, Drive, etc.

2. **Microsoft 365**
   - Desde $5 USD/usuario/mes
   - Correo profesional con Outlook

3. **Zoho Mail**
   - Gratis para hasta 5 usuarios
   - Correo profesional con dominio propio

**Configuración (ejemplo Google Workspace):**
```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=contacto@laboratoriofarmavet.cl
SMTP_PASSWORD=app-password-generada
SMTP_FROM=contacto@laboratoriofarmavet.cl
```

---

## 🎯 Recomendación por Escenario

### Para empezar (Desarrollo/Pruebas):
✅ **Usa tu correo personal de Gmail** con App Password
- Rápido de configurar
- Gratis
- Funciona inmediatamente

### Para producción (Corto plazo):
✅ **Correo institucional de la Universidad**
- Profesional
- Sin costos adicionales
- Confiable

### Para producción (Largo plazo/Alto volumen):
✅ **Servicio de email transaccional (SendGrid/Mailgun)**
- Escalable
- Estadísticas y tracking
- Mejor deliverability
- Precio razonable

---

## 📝 Pasos para Configurar

### Si usas Gmail personal (rápido):

1. **Activar 2FA en Gmail:**
   - https://myaccount.google.com/security
   - Activar "Verificación en 2 pasos"

2. **Generar App Password:**
   - https://myaccount.google.com/apppasswords
   - Seleccionar "Correo" y "Otro"
   - Nombre: "FARMAVET Web"
   - Copiar la contraseña de 16 caracteres

3. **Configurar en VPS:**
   ```bash
   sudo ./configurar_correo.sh
   # O manualmente:
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USER=tu-email@gmail.com
   SMTP_PASSWORD=xxxx xxxx xxxx xxxx  # App Password
   ```

### Si usas correo institucional:

1. **Contactar TI de la Universidad:**
   - Solicitar cuenta: `farmavet@uchile.cl` o similar
   - Obtener credenciales SMTP

2. **Configurar en VPS:**
   ```bash
   sudo ./configurar_correo.sh
   # Usar las credenciales proporcionadas por TI
   ```

### Si usas SendGrid (recomendado para producción):

1. **Registrarse en SendGrid:**
   - https://sendgrid.com
   - Verificar cuenta

2. **Crear API Key:**
   - Settings → API Keys → Create API Key
   - Permisos: "Mail Send" → "Full Access"
   - Copiar la API Key

3. **Verificar dominio (opcional pero recomendado):**
   - Settings → Sender Authentication
   - Agregar dominio: `laboratoriofarmavet.cl`
   - Configurar DNS según instrucciones

4. **Configurar en VPS:**
   ```bash
   sudo ./configurar_correo.sh
   SMTP_HOST=smtp.sendgrid.net
   SMTP_PORT=587
   SMTP_USER=apikey
   SMTP_PASSWORD=SG.tu-api-key-aqui
   SMTP_FROM=noreply@laboratoriofarmavet.cl
   ```

---

## ⚠️ Importante

- **Nunca uses tu contraseña personal de Gmail directamente**
- **Siempre usa App Passwords para Gmail**
- **Para producción, usa un correo profesional**
- **Considera límites de envío según el servicio**

---

## 🔍 Verificar Funcionamiento

Después de configurar:

1. **Configurar correos de destino en admin:**
   - `/admin/correos-contacto`
   - Agregar al menos un correo por tipo de consulta

2. **Probar envío:**
   - Enviar formulario de prueba desde `/contacto.html`
   - Verificar que llegue el correo

3. **Revisar logs si hay problemas:**
   ```bash
   sudo journalctl -u farmavet-web -f
   ```

