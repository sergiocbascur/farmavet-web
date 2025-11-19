# 🔒 Seguridad de Credenciales - FARMAVET Web

## ⚠️ Alerta de GitHub sobre Credenciales Expuestas

Si recibiste una alerta de GitHub sobre credenciales expuestas, sigue estos pasos:

## 🚨 Acciones Inmediatas

### 1. Revisar qué se expuso

GitHub te habrá indicado qué tipo de credencial se encontró. Revisa:
- ¿Fue una contraseña?
- ¿Fue una API key?
- ¿Fue un token?
- ¿En qué archivo estaba?

### 2. Rotar credenciales expuestas

**SI SE EXPUSO:**
- ✅ **Contraseña de Gmail/SMTP**: Cambiar inmediatamente
- ✅ **App Password de Gmail**: Revocar y generar una nueva
- ✅ **SECRET_KEY**: Generar una nueva y actualizar en el VPS
- ✅ **API Keys**: Revocar y generar nuevas
- ✅ **Tokens**: Revocar y generar nuevos

### 3. Limpiar historial de Git (si es necesario)

Si las credenciales están en el historial de commits:

```bash
# OPCIÓN 1: Usar git-filter-repo (recomendado)
# Instalar: pip install git-filter-repo
git filter-repo --invert-paths --path "archivo-con-credenciales" --force

# OPCIÓN 2: Usar BFG Repo-Cleaner
# Descargar: https://rtyley.github.io/bfg-repo-cleaner/
java -jar bfg.jar --delete-files archivo-con-credenciales
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# OPCIÓN 3: Si es muy reciente, hacer un commit que elimine el archivo
# y luego hacer force push (solo si es necesario y aceptas el riesgo)
```

**⚠️ ADVERTENCIA:** Limpiar el historial de Git es destructivo. Hazlo solo si es absolutamente necesario y después de hacer backup.

## 🔍 Verificación de Seguridad

### Archivos que NO deben estar en Git:

- ❌ `.env` - Variables de entorno
- ❌ `*.key` - Archivos de claves
- ❌ `*.pem` - Certificados
- ❌ `config.json` con credenciales
- ❌ `credentials.json`
- ❌ `secrets.json`
- ❌ Bases de datos (`*.db`, `*.sqlite`)
- ❌ Archivos con contraseñas hardcodeadas

### Verificar que están protegidos:

```bash
# Ver qué archivos están siendo rastreados
git ls-files | grep -E "\.(env|key|pem|json)$"

# Buscar posibles credenciales en el código
grep -r "password.*=" --include="*.py" --include="*.js" | grep -v "password_hash"
grep -r "api.*key" --include="*.py" --include="*.js" -i
grep -r "secret.*=" --include="*.py" | grep -v "SECRET_KEY"
```

## ✅ Estado Actual del Proyecto

### ✅ Seguro (No expone credenciales):

1. **SECRET_KEY**: Se obtiene de variable de entorno, no está hardcodeada
2. **SMTP_PASSWORD**: Se obtiene de variable de entorno
3. **Contraseña admin por defecto**: Solo para desarrollo inicial, debe cambiarse
4. **Archivos .env**: Están en .gitignore

### ⚠️ A tener en cuenta:

1. **`farmavet-web.service`**: Tiene un placeholder `REEMPLAZAR_CON_TU_SECRET_KEY_AQUI`
   - ✅ Ya corregido: Ahora está comentado con instrucciones
   - ✅ No expone credenciales reales

2. **Contraseña por defecto `admin123`**:
   - ⚠️ Está en el código para desarrollo inicial
   - ✅ Es solo para la primera instalación
   - ✅ Debe cambiarse inmediatamente después del primer login
   - ✅ No es un riesgo si se cambia en producción

## 🛡️ Mejores Prácticas Implementadas

### 1. Variables de Entorno

Todas las credenciales se obtienen de variables de entorno:

```python
# ✅ CORRECTO - Usa variable de entorno
smtp_password = os.environ.get('SMTP_PASSWORD', '')
secret_key = os.environ.get('SECRET_KEY', '')
```

### 2. .gitignore Configurado

El `.gitignore` protege:
- `.env` - Variables de entorno
- `*.db` - Bases de datos
- `instance/` - Carpeta de instancia Flask
- `venv/` - Entornos virtuales
- `*.log` - Logs

### 3. Sin Credenciales Hardcodeadas

No hay contraseñas reales en el código fuente.

## 🔧 Configuración Segura en VPS

### 1. Variables de Entorno en systemd

```ini
[Service]
# ✅ CORRECTO - Variables de entorno
Environment="SECRET_KEY=clave-generada-segura"
Environment="SMTP_HOST=smtp.gmail.com"
Environment="SMTP_PORT=587"
Environment="SMTP_USER=tu-email@gmail.com"
Environment="SMTP_PASSWORD=xxxxxxxxxxxxxxxx"
```

**⚠️ IMPORTANTE:** Reemplaza `xxxxxxxxxxxxxxxx` con tu App Password real. Nunca subas este archivo con credenciales reales a Git.

### 2. Permisos del archivo de servicio

```bash
# Solo root puede leer/escribir
sudo chmod 600 /etc/systemd/system/farmavet-web.service
```

### 3. Generar SECRET_KEY segura

```bash
python -c "import secrets; print(secrets.token_urlsafe(50))"
```

## 📋 Checklist de Seguridad

Antes de hacer commit:

- [ ] No hay contraseñas en el código
- [ ] No hay API keys en el código
- [ ] No hay tokens en el código
- [ ] Archivos `.env` están en `.gitignore`
- [ ] Bases de datos están en `.gitignore`
- [ ] Variables de entorno se usan correctamente
- [ ] No hay credenciales en logs
- [ ] No hay credenciales en comentarios

## 🚨 Si Encontraste Credenciales Expuestas

### Paso 1: Identificar
- ¿Qué tipo de credencial?
- ¿En qué archivo?
- ¿En qué commit?

### Paso 2: Rotar
- Cambiar/revocar la credencial inmediatamente
- Generar nuevas credenciales

### Paso 3: Limpiar (si es necesario)
- Eliminar del historial de Git
- Hacer force push (solo si es crítico)

### Paso 4: Prevenir
- Revisar `.gitignore`
- Usar variables de entorno siempre
- No hardcodear credenciales

## 📞 Soporte

Si necesitas ayuda para:
- Rotar credenciales
- Limpiar historial de Git
- Configurar variables de entorno
- Verificar seguridad

Revisa la documentación o contacta al equipo de desarrollo.

