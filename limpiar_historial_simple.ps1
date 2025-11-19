# Script simple para limpiar el historial de Git
# Elimina CONFIGURACION_CORREO_VPS.md del historial completo

Write-Host "=== LIMPIEZA DE HISTORIAL DE GIT ===" -ForegroundColor Yellow
Write-Host ""

# Verificar que estamos en el directorio correcto
if (-not (Test-Path ".git")) {
    Write-Host "❌ Error: No se encontró el directorio .git" -ForegroundColor Red
    Write-Host "Ejecuta este script desde el directorio farmavet-web" -ForegroundColor Red
    exit 1
}

# Verificar que no hay cambios sin commitear
$status = git status --porcelain
if ($status) {
    Write-Host "⚠️  ADVERTENCIA: Hay cambios sin commitear" -ForegroundColor Yellow
    Write-Host "Es recomendable hacer commit o stash antes de continuar" -ForegroundColor Yellow
    $continue = Read-Host "¿Deseas continuar de todos modos? (s/n)"
    if ($continue -ne "s" -and $continue -ne "S") {
        exit 0
    }
}

# Crear backup
Write-Host "📦 Creando backup del repositorio..." -ForegroundColor Cyan
$backupDir = "../farmavet-web-backup-$(Get-Date -Format 'yyyyMMdd_HHmmss')"
git clone --mirror . $backupDir
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Backup creado en: $backupDir" -ForegroundColor Green
} else {
    Write-Host "❌ Error al crear backup" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Eliminar archivo del historial
Write-Host "🔄 Eliminando CONFIGURACION_CORREO_VPS.md del historial completo..." -ForegroundColor Cyan
Write-Host "Esto puede tardar varios minutos dependiendo del tamaño del repositorio..." -ForegroundColor Yellow
Write-Host ""

git filter-branch --force --index-filter `
    "git rm --cached --ignore-unmatch CONFIGURACION_CORREO_VPS.md" `
    --prune-empty --tag-name-filter cat -- --all

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅ Archivo eliminado del historial" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "❌ Error al eliminar archivo del historial" -ForegroundColor Red
    exit 1
}

# Limpiar referencias
Write-Host ""
Write-Host "🧹 Limpiando referencias y optimizando repositorio..." -ForegroundColor Cyan
git for-each-ref --format="delete %(refname)" refs/original | git update-ref --stdin
git reflog expire --expire=now --all
git gc --prune=now --aggressive

Write-Host "✅ Limpieza completada" -ForegroundColor Green
Write-Host ""

# Verificar que el archivo ya no está en el historial
Write-Host "🔍 Verificando que el archivo fue eliminado..." -ForegroundColor Cyan
$check = git log --all --full-history -- CONFIGURACION_CORREO_VPS.md
if (-not $check) {
    Write-Host "✅ Confirmado: El archivo ya no está en el historial" -ForegroundColor Green
} else {
    Write-Host "⚠️  El archivo aún aparece en el historial" -ForegroundColor Yellow
    Write-Host "Puede ser necesario usar git-filter-repo en lugar de filter-branch" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=== PRÓXIMOS PASOS ===" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. Verifica que el historial esté limpio:" -ForegroundColor Cyan
Write-Host "   git log --all --full-history -- CONFIGURACION_CORREO_VPS.md" -ForegroundColor White
Write-Host ""
Write-Host "2. Si no aparece nada, el archivo fue eliminado correctamente" -ForegroundColor Green
Write-Host ""
Write-Host "3. Para actualizar GitHub, ejecuta:" -ForegroundColor Cyan
Write-Host "   git push origin --force --all" -ForegroundColor White
Write-Host "   git push origin --force --tags" -ForegroundColor White
Write-Host ""
Write-Host "⚠️  ADVERTENCIA: Force push reescribirá el historial en GitHub" -ForegroundColor Yellow
Write-Host "   Asegúrate de que nadie más esté trabajando en el repositorio" -ForegroundColor Yellow
Write-Host "   Todos los colaboradores necesitarán hacer 'git fetch' y 'git reset --hard origin/main'" -ForegroundColor Yellow
Write-Host ""
$confirm = Read-Host "¿Deseas hacer el force push ahora? (s/n)"

if ($confirm -eq "s" -or $confirm -eq "S") {
    Write-Host ""
    Write-Host "🚀 Haciendo force push..." -ForegroundColor Cyan
    git push origin --force --all
    if ($LASTEXITCODE -eq 0) {
        git push origin --force --tags
        if ($LASTEXITCODE -eq 0) {
            Write-Host ""
            Write-Host "✅ Historial limpiado y actualizado en GitHub" -ForegroundColor Green
            Write-Host ""
            Write-Host "🎉 ¡Completado! El historial ha sido limpiado y las credenciales ya no están expuestas." -ForegroundColor Green
        } else {
            Write-Host ""
            Write-Host "⚠️  Error al hacer push de tags" -ForegroundColor Yellow
        }
    } else {
        Write-Host ""
        Write-Host "❌ Error al hacer force push" -ForegroundColor Red
        Write-Host "Verifica que tengas permisos y que el repositorio remoto esté accesible" -ForegroundColor Yellow
    }
} else {
    Write-Host ""
    Write-Host "⏸️  Push cancelado. Puedes hacerlo manualmente más tarde con:" -ForegroundColor Yellow
    Write-Host "   git push origin --force --all" -ForegroundColor White
    Write-Host "   git push origin --force --tags" -ForegroundColor White
}

Write-Host ""
Write-Host "=== COMPLETADO ===" -ForegroundColor Green

