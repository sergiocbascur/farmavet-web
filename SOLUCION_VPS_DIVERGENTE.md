# 🔧 Solución: Ramas Divergentes en VPS (Caso Específico)

## 📊 Situación Actual

El VPS muestra:
- **Ramas divergentes:** 14 commits locales y 14 commits remotos diferentes
- **Archivo modificado:** `configurar_correo.sh`

## ✅ Solución Paso a Paso

### Paso 1: Guardar el archivo modificado (si es importante)

```bash
# En el VPS
cd ~/farmavet-web

# Ver qué cambios tiene el archivo
git diff configurar_correo.sh

# Si los cambios son importantes, guardarlos
cp configurar_correo.sh configurar_correo.sh.backup

# O si prefieres, hacer commit temporal
git add configurar_correo.sh
git commit -m "temp: Guardar cambios locales antes de reset"
```

### Paso 2: Alinear con el remoto

```bash
# Obtener el historial actualizado del remoto
git fetch origin

# Descartar todos los cambios locales y alinear con remoto
git reset --hard origin/main

# Verificar que todo está bien
git status
git log --oneline -5
```

### Paso 3: Restaurar el archivo si era importante

```bash
# Si guardaste el backup, restaurarlo
cp configurar_correo.sh.backup configurar_correo.sh

# Verificar los cambios
git diff configurar_correo.sh

# Si quieres mantener los cambios, hacer commit
git add configurar_correo.sh
git commit -m "fix: Restaurar cambios locales en configurar_correo.sh"
git push origin main
```

## 🚀 Comando Rápido (Si no necesitas los cambios locales)

Si el archivo `configurar_correo.sh` no tiene cambios importantes:

```bash
cd ~/farmavet-web
git fetch origin
git reset --hard origin/main
git clean -fd  # Limpiar archivos no rastreados (opcional)
```

## ⚠️ ¿Qué hace `git reset --hard`?

- **Elimina** todos los cambios locales no commiteados
- **Reescribe** el historial local para que coincida con `origin/main`
- **Descarta** los 14 commits locales divergentes

Esto es seguro porque:
- El historial remoto es el correcto (fue limpiado intencionalmente)
- Los commits locales son del historial antiguo que ya no existe

## 🔍 Verificar Cambios en configurar_correo.sh

Antes de hacer reset, puedes ver qué cambió:

```bash
git diff configurar_correo.sh
```

Si los cambios son solo ajustes menores o comentarios, puedes descartarlos.
Si son configuraciones importantes del VPS, guárdalos primero.

## 📝 Después del Reset

Una vez alineado, verifica que todo funciona:

```bash
# Verificar estado
git status

# Ver últimos commits
git log --oneline -5

# Reiniciar servicio si es necesario
sudo systemctl restart farmavet-web

# Verificar que el servicio está corriendo
sudo systemctl status farmavet-web
```

