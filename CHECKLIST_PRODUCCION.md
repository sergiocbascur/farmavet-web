# ✅ Checklist para Poner FARMAVET Web en Producción

## 📋 Lo que ya tienes
- ✅ Código de la aplicación
- ✅ Dominio propio
- ✅ Repositorio en GitHub

## 🔧 Lo que necesitas hacer

### 1. **Elegir Plataforma de Hosting**
Recomendado: **Render.com** o **Railway.app**

### 2. **Configurar Variables de Entorno**

Necesitas configurar estas variables en tu plataforma de hosting:

#### **SECRET_KEY** (OBLIGATORIO)
```bash
# Genera una clave secreta segura:
python -c "import secrets; print(secrets.token_hex(32))"
```
- **¿Para qué?** Encripta sesiones, cookies, tokens
- **¿Dónde?** En el panel de tu hosting (Render/Railway) → Environment Variables

#### **FLASK_ENV** (Recomendado)
```
FLASK_ENV=production
```
- **¿Para qué?** Activa modo producción (cookies seguras, mejor rendimiento)

#### **DATABASE_URL** (Opcional - solo si migras a PostgreSQL)
```
DATABASE_URL=postgresql://user:pass@host:5432/dbname
```
- **Nota:** SQLite funciona sin esto, pero PostgreSQL es mejor para producción

---

### 3. **Configurar DNS del Dominio**

Necesitas apuntar tu dominio al hosting. Pasos:

#### Si usas **Render.com**:
1. En Render, ve a tu servicio → Settings → Custom Domains
2. Agrega tu dominio (ej: `www.laboratoriofarmavet.cl`)
3. Render te dará un registro CNAME o A
4. En tu proveedor de dominio, agrega:
   - **Tipo:** CNAME
   - **Nombre:** www (o @ para dominio raíz)
   - **Valor:** El que te dio Render (ej: `farmavet-web.onrender.com`)
5. Para dominio raíz (sin www), Render te dará un registro A con IP

#### Si usas **Railway.app**:
1. Similar proceso, Railway te dará instrucciones específicas

**Tiempo de propagación DNS:** 15 minutos a 48 horas (normalmente 1-2 horas)

---

### 4. **SSL/HTTPS (Certificado)**

✅ **Automático en Render/Railway**
- Ambos proveen SSL gratuito automáticamente
- Se activa cuando configuras el dominio personalizado
- No necesitas hacer nada extra

---

### 5. **Base de Datos Inicial**

#### Opción A: SQLite (Simple, pero limitado)
- ✅ Se crea automáticamente al iniciar la app
- ⚠️ En Render gratis: puede perder datos si el servicio se reinicia
- ⚠️ No recomendado para producción seria

#### Opción B: PostgreSQL (Recomendado para producción)
1. En Render: New → PostgreSQL (gratis disponible)
2. En Railway: Add Service → Database → PostgreSQL
3. Obtendrás un `DATABASE_URL`
4. Necesitarás modificar `app.py` para usar PostgreSQL (te puedo ayudar)

**Para empezar:** SQLite está bien. Migra a PostgreSQL cuando crezca el tráfico.

---

### 6. **Crear Usuario Administrador**

Después del primer despliegue:

1. Accede a tu sitio: `https://tu-dominio.com/login`
2. Necesitarás crear el primer usuario admin

**Opciones:**
- **Opción 1:** Agregar script de inicialización (te puedo ayudar)
- **Opción 2:** Crear manualmente en la base de datos
- **Opción 3:** Agregar ruta temporal de registro (solo para primera vez)

---

### 7. **Configurar Uploads/Archivos Estáticos**

**Problema:** Los archivos en `static/uploads/` se perderán en reinicios (en hosting gratuito)

**Soluciones:**

#### Opción A: Volúmenes Persistentes (Fly.io)
- Los archivos persisten entre reinicios

#### Opción B: Servicio de Almacenamiento (Recomendado)
- **Cloudinary** (gratis hasta 25GB): Para imágenes
- **AWS S3**: Más profesional
- **Render Disk**: $0.25/GB/mes (solo Render)

**Para empezar:** Puedes usar el sistema de archivos local, pero haz backups.

---

### 8. **Configuración de Seguridad Adicional**

Ya tienes implementado:
- ✅ Rate limiting en login
- ✅ Validación de contraseñas
- ✅ Sesiones seguras
- ✅ Protección CSRF

**Revisar:**
- ✅ `SECRET_KEY` debe ser única y secreta
- ✅ Cambiar contraseña por defecto del admin
- ✅ Considerar 2FA para admin (futuro)

---

### 9. **Backups**

**Configurar backups automáticos:**

#### SQLite:
- Script que copie `instance/database.db` periódicamente
- Subir a Google Drive/Dropbox/S3

#### PostgreSQL (Render/Railway):
- Backups automáticos incluidos
- Configurar frecuencia en el panel

---

### 10. **Monitoreo y Logs**

**Render/Railway incluyen:**
- ✅ Logs en tiempo real
- ✅ Métricas básicas
- ✅ Alertas de errores

**Para producción seria, considera:**
- Sentry (errores)
- Google Analytics (tráfico)
- Uptime monitoring (UptimeRobot - gratis)

---

## 🚀 Pasos Rápidos para Desplegar

### Con Render.com:

1. **Crear cuenta:** https://render.com (conectar GitHub)

2. **Nuevo servicio:**
   - New → Web Service
   - Conectar repositorio `farmavet-web`
   - Render detectará Flask automáticamente

3. **Configurar:**
   - Name: `farmavet-web`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`
   - Plan: Free (para empezar)

4. **Variables de entorno:**
   ```
   SECRET_KEY=tu-clave-generada-aqui
   FLASK_ENV=production
   ```

5. **Crear servicio:** Click "Create Web Service"

6. **Esperar despliegue:** 2-5 minutos

7. **Configurar dominio:**
   - Settings → Custom Domains
   - Agregar tu dominio
   - Configurar DNS en tu proveedor

8. **¡Listo!** Tu sitio estará en `https://tu-dominio.com`

---

## 📝 Resumen de lo que Necesitas

| Item | Estado | Acción Requerida |
|------|--------|-----------------|
| Código | ✅ Listo | - |
| Dominio | ✅ Tienes | Configurar DNS |
| Hosting | ⏳ Pendiente | Elegir Render/Railway |
| SECRET_KEY | ⏳ Pendiente | Generar y configurar |
| SSL | ✅ Automático | Se activa con dominio |
| Base de datos | ✅ Auto-crea | SQLite funciona |
| Usuario admin | ⏳ Pendiente | Crear después del deploy |
| Backups | ⏳ Pendiente | Configurar después |

---

## 🆘 ¿Necesitas Ayuda con Algo Específico?

Puedo ayudarte con:
- ✅ Generar SECRET_KEY
- ✅ Modificar app.py para PostgreSQL
- ✅ Script de creación de usuario admin
- ✅ Configuración de Cloudinary para uploads
- ✅ Cualquier otra configuración específica

**¿Qué plataforma elegiste?** (Render/Railway/Fly.io)

