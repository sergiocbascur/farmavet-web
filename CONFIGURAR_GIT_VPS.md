# 🔧 Configurar Git en el VPS

## ⚠️ Problemas Encontrados

1. **Autor de Git no configurado:** Git necesita saber quién eres para hacer commits
2. **Autenticación fallida:** GitHub ya no acepta contraseñas, necesita un token personal

## ✅ Solución Paso a Paso

### Paso 1: Configurar Identidad de Git

```bash
# En el VPS
cd ~/farmavet-web

# Configurar email (usar el mismo que en GitHub)
git config --global user.email "tu-email@ejemplo.com"

# Configurar nombre
git config --global user.name "Tu Nombre"

# Verificar configuración
git config --global --list
```

### Paso 2: Crear Token Personal en GitHub

1. **Ve a GitHub:**
   - https://github.com/settings/tokens
   - O: GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)

2. **Generar nuevo token:**
   - Click en "Generate new token" → "Generate new token (classic)"
   - **Note:** "VPS farmavet-web"
   - **Expiration:** Elige una duración (90 días, 1 año, o sin expiración)
   - **Scopes:** Marca `repo` (acceso completo a repositorios)
   - Click en "Generate token"

3. **Copiar el token:**
   - ⚠️ **IMPORTANTE:** Copia el token inmediatamente, solo se muestra una vez
   - Ejemplo: `ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

### Paso 3: Configurar Autenticación en el VPS

#### Opción A: Usar Token en URL (Más Simple)

```bash
# En el VPS
cd ~/farmavet-web

# Configurar URL remota con token
git remote set-url origin https://TU_TOKEN@github.com/sergiocbascur/farmavet-web.git

# Reemplazar TU_TOKEN con el token que copiaste
# Ejemplo: git remote set-url origin https://ghp_abc123...@github.com/sergiocbascur/farmavet-web.git

# Verificar
git remote -v
```

#### Opción B: Usar Git Credential Helper (Más Seguro)

```bash
# En el VPS
cd ~/farmavet-web

# Configurar credential helper para guardar el token
git config --global credential.helper store

# Hacer un push (te pedirá usuario y contraseña)
git push origin main
# Username: sergiocbascur
# Password: [pegar el token aquí, NO tu contraseña de GitHub]

# El token se guardará automáticamente
```

#### Opción C: Usar SSH (Más Seguro a Largo Plazo)

```bash
# En el VPS - Generar clave SSH
ssh-keygen -t ed25519 -C "tu-email@ejemplo.com"
# Presionar Enter para usar ubicación por defecto
# Opcional: agregar passphrase

# Ver la clave pública
cat ~/.ssh/id_ed25519.pub

# Copiar el contenido completo (empieza con ssh-ed25519...)

# En GitHub:
# 1. Ve a: https://github.com/settings/keys
# 2. Click en "New SSH key"
# 3. Title: "VPS farmavet-bodega"
# 4. Key: Pega el contenido de ~/.ssh/id_ed25519.pub
# 5. Click en "Add SSH key"

# Cambiar URL remota a SSH
cd ~/farmavet-web
git remote set-url origin git@github.com:sergiocbascur/farmavet-web.git

# Verificar
git remote -v
```

### Paso 4: Hacer Commit y Push

```bash
# Si ya hiciste el commit pero falló el push
cd ~/farmavet-web

# Verificar estado
git status

# Si el commit ya está hecho, solo hacer push
git push origin main

# Si necesitas hacer el commit de nuevo
git add configurar_correo.sh
git commit -m "fix: Restaurar cambios locales en configurar_correo.sh"
git push origin main
```

## 🔒 Seguridad

### Si usas Token en URL:

⚠️ **ADVERTENCIA:** El token quedará visible en `git remote -v`

Para ocultarlo:
```bash
# Usar variable de entorno
export GIT_TOKEN="tu-token-aqui"
git remote set-url origin https://${GIT_TOKEN}@github.com/sergiocbascur/farmavet-web.git
```

O mejor, usar credential helper (Opción B) que guarda el token de forma segura.

### Si usas SSH:

✅ **Recomendado:** Más seguro y no necesitas tokens que expiran.

## 📋 Checklist

- [ ] Configurar `user.email` y `user.name` en Git
- [ ] Crear token personal en GitHub
- [ ] Configurar autenticación (Token o SSH)
- [ ] Hacer commit de `configurar_correo.sh` (si es necesario)
- [ ] Hacer push exitoso
- [ ] Verificar que el push funcionó en GitHub

## 🆘 Solución Rápida (Token en URL)

Si quieres la solución más rápida:

```bash
# 1. Configurar Git
git config --global user.email "sergioc.bascur@icloud.com"
git config --global user.name "sergiocbascur"

# 2. Obtener token de GitHub (ve a https://github.com/settings/tokens)

# 3. Configurar URL con token
git remote set-url origin https://TU_TOKEN_AQUI@github.com/sergiocbascur/farmavet-web.git

# 4. Hacer push
git push origin main
```

## 🔍 Verificar Configuración

```bash
# Ver configuración de Git
git config --global --list

# Ver URL remota (sin mostrar token completo)
git remote -v | sed 's/\/\/.*@/\/\/***@/'

# Verificar conexión
git fetch origin
```

