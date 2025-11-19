# 🔧 Solución: Ramas Divergentes en VPS

## ⚠️ Problema

Después de hacer `git pull origin main` en el VPS, aparece el error:
```
fatal: Need to specify how to reconcile divergent branches.
```

Esto ocurre porque:
- Se hizo un `git push --force` para limpiar el historial de Git
- El VPS tiene un historial local diferente al remoto
- Git necesita saber cómo reconciliar las diferencias

## ✅ Solución Recomendada

Como el historial fue reescrito intencionalmente, la mejor opción es **alinear completamente con el remoto**:

### Opción 1: Reset Hard (Recomendado si no hay cambios locales importantes)

```bash
# En el VPS
cd ~/farmavet-web

# Verificar si hay cambios locales importantes
git status

# Si no hay cambios importantes, hacer reset hard
git fetch origin
git reset --hard origin/main

# Verificar que todo está alineado
git status
```

### Opción 2: Si hay cambios locales que quieres conservar

```bash
# En el VPS
cd ~/farmavet-web

# Guardar cambios locales en un stash
git stash

# Hacer pull con rebase
git pull --rebase origin main

# Si hay conflictos, resolverlos y luego:
git stash pop

# O si prefieres merge:
git pull --no-rebase origin main
```

### Opción 3: Configurar estrategia por defecto

Si quieres evitar este mensaje en el futuro:

```bash
# Configurar para usar merge (por defecto)
git config pull.rebase false

# O para usar rebase
git config pull.rebase true

# O para solo fast-forward (más seguro)
git config pull.ff only
```

## 📋 Pasos Recomendados para el VPS

1. **Verificar estado actual:**
   ```bash
   cd ~/farmavet-web
   git status
   git log --oneline -5
   ```

2. **Si no hay cambios locales importantes, alinear con remoto:**
   ```bash
   git fetch origin
   git reset --hard origin/main
   ```

3. **Verificar que funciona:**
   ```bash
   git status
   git log --oneline -5
   ```

4. **Reiniciar el servicio si es necesario:**
   ```bash
   sudo systemctl restart farmavet-web
   ```

## ⚠️ Advertencia

**`git reset --hard` eliminará todos los cambios locales no commiteados.** 

Si tienes cambios importantes en el VPS que no están en Git:
1. Crea un backup primero
2. O usa `git stash` para guardarlos
3. O haz commit de los cambios antes del reset

## 🔍 Verificar Cambios Locales

Antes de hacer reset, verifica si hay cambios:

```bash
# Ver archivos modificados
git status

# Ver diferencias
git diff

# Ver commits locales que no están en remoto
git log origin/main..HEAD
```

Si no hay nada importante, puedes hacer el reset hard con seguridad.

