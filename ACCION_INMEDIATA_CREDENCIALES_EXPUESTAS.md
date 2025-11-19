# 🚨 ACCIÓN INMEDIATA: Credenciales Expuestas en GitHub

**Fecha de detección:** 19 de noviembre de 2025  
**Alerta:** GitGuardian detectó contraseña de correo corporativo expuesta

## ⚠️ SITUACIÓN CRÍTICA

GitGuardian ha detectado que una contraseña de correo corporativo fue expuesta en el repositorio `sergiocbascur/farmavet-web` el 19 de noviembre de 2025 a las 11:46:37 UTC.

## 🔍 ANÁLISIS REALIZADO

He revisado el historial de Git y encontré que:

1. **Commits relacionados con SMTP del 19 de noviembre:**
   - `35d02b1` - docs: Agregar guia de configuracion de correo para VPS
   - `211607a` - feat: Agregar script de configuracion de correo SMTP para VPS
   - `9dc28f9` - security: Reemplazar credenciales de ejemplo con placeholders

2. **Estado actual del código:**
   - ✅ Los archivos actuales solo contienen placeholders (`xxxxxxxxxxxxxxxx`)
   - ✅ No hay contraseñas hardcodeadas en el código actual
   - ⚠️ **PERO:** El historial de Git puede contener la contraseña real en commits anteriores

## 🎯 ACCIONES INMEDIATAS REQUERIDAS

### 1. ROTAR LA CONTRASEÑA SMTP (CRÍTICO - HACER PRIMERO)

**Si usas Gmail:**
1. Ve a: https://myaccount.google.com/apppasswords
2. **REVOCA** la App Password que se expuso
3. Genera una **NUEVA** App Password
4. Actualiza la contraseña en el VPS:

```bash
# En el VPS
sudo nano /etc/systemd/system/farmavet-web.service
# Actualizar la línea SMTP_PASSWORD con la nueva contraseña
sudo systemctl daemon-reload
sudo systemctl restart farmavet-web
```

**Si usas correo institucional (UChile):**
1. Cambia la contraseña de la cuenta de correo
2. Actualiza la contraseña en el VPS (mismo proceso arriba)

**Si usas SendGrid u otro servicio:**
1. Ve al dashboard del servicio
2. **REVOCA** la API Key expuesta
3. Genera una **NUEVA** API Key
4. Actualiza en el VPS

### 2. VERIFICAR EL HISTORIAL DE GIT

Para encontrar exactamente dónde se expuso la contraseña:

```bash
# Buscar en todo el historial
git log --all -p | grep -i "SMTP_PASSWORD" -A 5 -B 5

# Buscar en commits específicos del 19 de noviembre
git log --since="2025-11-19" --until="2025-11-20" -p | grep -i "password" -A 3 -B 3
```

### 3. LIMPIAR EL HISTORIAL (OPCIONAL PERO RECOMENDADO)

**⚠️ ADVERTENCIA:** Esto reescribe el historial de Git. Solo hazlo si:
- Tienes acceso completo al repositorio
- Todos los colaboradores están de acuerdo
- Puedes forzar push (`git push --force`)

**Opción A: Usar BFG Repo-Cleaner (Recomendado)**

```bash
# Instalar BFG (si no lo tienes)
# Windows: choco install bfg
# Linux/Mac: brew install bfg

# Crear backup del repo
cd farmavet-web
git clone --mirror https://github.com/sergiocbascur/farmavet-web.git farmavet-web-backup.git

# Reemplazar contraseñas expuestas (reemplaza CONTRASEÑA_EXPUESTA con la real)
bfg --replace-text passwords.txt farmavet-web.git

# O eliminar archivos específicos del historial
bfg --delete-files CONFIGURACION_CORREO_VPS.md farmavet-web.git
```

**Opción B: Usar git filter-branch (Más complejo)**

```bash
# Eliminar archivo del historial completo
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch CONFIGURACION_CORREO_VPS.md" \
  --prune-empty --tag-name-filter cat -- --all

# Forzar push (CUIDADO: esto reescribe el historial)
git push origin --force --all
git push origin --force --tags
```

**Opción C: Crear nuevo repositorio (Más seguro)**

Si el historial no es crítico:
1. Crea un nuevo repositorio
2. Copia solo los archivos actuales (sin historial)
3. Haz un commit inicial limpio
4. Actualiza las referencias remotas

### 4. VERIFICAR OTROS ARCHIVOS SENSIBLES

```bash
# Buscar posibles contraseñas en el código actual
grep -r "password.*=" --include="*.py" --include="*.sh" --include="*.md" | grep -v "password_hash" | grep -v "xxxxxxxx"

# Buscar variables de entorno con valores
grep -r "SMTP_PASSWORD\|SMTP_USER\|SECRET_KEY" --include="*.py" --include="*.sh" --include="*.md" | grep -v "os.environ.get" | grep -v "xxxxxxxx"
```

### 5. CONFIGURAR GITGUARDIAN PARA PREVENIR FUTUROS INCIDENTES

1. Ve a: https://dashboard.gitguardian.com/
2. Configura webhooks para alertas automáticas
3. Revisa las políticas de escaneo
4. Considera habilitar bloqueo de commits con secretos

## 📋 CHECKLIST DE SEGURIDAD

- [ ] **ROTAR** la contraseña SMTP expuesta (HACER PRIMERO)
- [ ] Actualizar contraseña en el VPS
- [ ] Verificar que el servicio funciona con la nueva contraseña
- [ ] Revisar el historial de Git para encontrar el commit exacto
- [ ] Decidir si limpiar el historial (opcional)
- [ ] Verificar que no hay otras credenciales expuestas
- [ ] Configurar alertas de GitGuardian
- [ ] Revisar `.gitignore` para asegurar que archivos sensibles estén excluidos
- [ ] Documentar el incidente (opcional, para aprendizaje)

## 🔒 PREVENCIÓN FUTURA

### 1. Nunca subir credenciales reales

**❌ NUNCA HACER:**
```bash
# En código o documentación
SMTP_PASSWORD=mi-contraseña-real-123
```

**✅ SIEMPRE HACER:**
```bash
# En código
smtp_password = os.environ.get('SMTP_PASSWORD', '')

# En documentación
SMTP_PASSWORD=xxxxxxxxxxxxxxxx  # Reemplazar con contraseña real
```

### 2. Usar variables de entorno

Siempre usar variables de entorno para credenciales:
- En desarrollo: archivo `.env` (agregado a `.gitignore`)
- En producción: variables de entorno del sistema o servicio

### 3. Pre-commit hooks

Instalar `git-secrets` o `pre-commit` con hooks para detectar secretos:

```bash
# Instalar git-secrets
git secrets --install
git secrets --register-aws

# O usar pre-commit
pip install pre-commit
pre-commit install
```

### 4. Revisar antes de commit

```bash
# Antes de cada commit, revisar cambios
git diff --cached | grep -i "password\|secret\|key\|token"
```

## 📞 SOPORTE

Si necesitas ayuda adicional:
- [GitGuardian Documentation](https://docs.gitguardian.com/)
- [GitHub Security Best Practices](https://docs.github.com/en/code-security)
- [OWASP Secrets Management](https://owasp.org/www-community/vulnerabilities/Use_of_hard-coded_cryptographic_key)

---

**⚠️ RECUERDA:** La rotación de contraseñas es la acción MÁS IMPORTANTE. Hazlo inmediatamente antes de cualquier otra acción.

