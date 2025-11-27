# Script para limpiar el historial de Git y eliminar credenciales expuestas
# Ejecutar desde el directorio farmavet-web

Write-Host "=== LIMPIEZA DE HISTORIAL DE GIT ===" -ForegroundColor Yellow
Write-Host ""

# Verificar que estamos en el directorio correcto
if (-not (Test-Path ".git")) {
    Write-Host "❌ Error: No se encontró el directorio .git" -ForegroundColor Red
    Write-Host "Ejecuta este script desde el directorio farmavet-web" -ForegroundColor Red
    exit 1
}

# Crear backup antes de proceder
Write-Host "📦 Creando backup del repositorio..." -ForegroundColor Cyan
$backupDir = "../farmavet-web-backup-$(Get-Date -Format 'yyyyMMdd_HHmmss')"
git clone --mirror . $backupDir
Write-Host "✅ Backup creado en: $backupDir" -ForegroundColor Green
Write-Host ""

# Opción 1: Reemplazar contraseñas específicas en todo el historial
Write-Host "¿Qué método prefieres?" -ForegroundColor Yellow
Write-Host "1. Reemplazar contraseñas específicas en todo el historial (recomendado)"
Write-Host "2. Eliminar archivo CONFIGURACION_CORREO_VPS.md del historial completo"
Write-Host ""
$opcion = Read-Host "Ingresa el número de opción (1 o 2)"

if ($opcion -eq "1") {
    Write-Host ""
    Write-Host "⚠️  IMPORTANTE: Necesitas saber la contraseña exacta que se expuso" -ForegroundColor Yellow
    Write-Host "Si no la recuerdas, usa la opción 2 para eliminar el archivo completo" -ForegroundColor Yellow
    Write-Host ""
    $passwordExposed = Read-Host "Ingresa la contraseña que se expuso (se ocultará)"
    
    if ([string]::IsNullOrWhiteSpace($passwordExposed)) {
        Write-Host "❌ No se ingresó contraseña. Cancelando..." -ForegroundColor Red
        exit 1
    }
    
    Write-Host ""
    Write-Host "🔄 Reemplazando contraseña en todo el historial..." -ForegroundColor Cyan
    Write-Host "Esto puede tardar varios minutos..." -ForegroundColor Yellow
    
    # Crear archivo temporal con el reemplazo
    $replaceFile = "replace-passwords.txt"
    "$passwordExposed==>xxxxxxxxxxxxxxxx" | Out-File -FilePath $replaceFile -Encoding UTF8
    
    # Usar git filter-branch para reemplazar
    git filter-branch --force --tree-filter "
        if [ -f CONFIGURACION_CORREO_VPS.md ]; then
            sed -i 's/$passwordExposed/xxxxxxxxxxxxxxxx/g' CONFIGURACION_CORREO_VPS.md
        fi
        if [ -f OPCIONES_CORREO.md ]; then
            sed -i 's/$passwordExposed/xxxxxxxxxxxxxxxx/g' OPCIONES_CORREO.md
        fi
        if [ -f SOLUCION_ERROR_SMTP.md ]; then
            sed -i 's/$passwordExposed/xxxxxxxxxxxxxxxx/g' SOLUCION_ERROR_SMTP.md
        fi
    " --prune-empty --tag-name-filter cat -- --all
    
    Remove-Item $replaceFile -ErrorAction SilentlyContinue
    
} elseif ($opcion -eq "2") {
    Write-Host ""
    Write-Host "🔄 Eliminando CONFIGURACION_CORREO_VPS.md del historial completo..." -ForegroundColor Cyan
    Write-Host "Esto puede tardar varios minutos..." -ForegroundColor Yellow
    
    # Eliminar archivo del historial usando filter-branch
    git filter-branch --force --index-filter `
        "git rm --cached --ignore-unmatch CONFIGURACION_CORREO_VPS.md" `
        --prune-empty --tag-name-filter cat -- --all
    
} else {
    Write-Host "❌ Opción inválida. Cancelando..." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "✅ Limpieza del historial completada" -ForegroundColor Green
Write-Host ""

# Limpiar referencias
Write-Host "🧹 Limpiando referencias..." -ForegroundColor Cyan
git for-each-ref --format="delete %(refname)" refs/original | git update-ref --stdin
git reflog expire --expire=now --all
git gc --prune=now --aggressive

Write-Host "✅ Referencias limpiadas" -ForegroundColor Green
Write-Host ""

Write-Host "=== PRÓXIMOS PASOS ===" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. Verifica que el historial esté limpio:" -ForegroundColor Cyan
Write-Host "   git log --all -p | Select-String -Pattern 'SMTP_PASSWORD' -Context 2" -ForegroundColor White
Write-Host ""
Write-Host "2. Si todo está bien, fuerza el push al repositorio remoto:" -ForegroundColor Cyan
Write-Host "   git push origin --force --all" -ForegroundColor White
Write-Host "   git push origin --force --tags" -ForegroundColor White
Write-Host ""
Write-Host "⚠️  ADVERTENCIA: Forzar push reescribirá el historial en GitHub" -ForegroundColor Yellow
Write-Host "   Asegúrate de que nadie más esté trabajando en el repositorio" -ForegroundColor Yellow
Write-Host ""
$confirm = Read-Host "¿Deseas hacer el force push ahora? (s/n)"

if ($confirm -eq "s" -or $confirm -eq "S") {
    Write-Host ""
    Write-Host "🚀 Haciendo force push..." -ForegroundColor Cyan
    git push origin --force --all
    git push origin --force --tags
    Write-Host ""
    Write-Host "✅ Historial limpiado y actualizado en GitHub" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "⏸️  Push cancelado. Puedes hacerlo manualmente más tarde" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=== COMPLETADO ===" -ForegroundColor Green


