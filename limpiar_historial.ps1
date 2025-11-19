# Script PowerShell para limpiar el historial de Git eliminando credenciales expuestas
# ADVERTENCIA: Esto reescribe el historial de Git

Write-Host "⚠️  ADVERTENCIA: Este script reescribirá el historial de Git" -ForegroundColor Yellow
Write-Host "Esto afectará a todos los que tengan el repositorio clonado" -ForegroundColor Yellow
Write-Host ""
$confirm = Read-Host "¿Estás seguro de continuar? (escribe 'SI' para confirmar)"

if ($confirm -ne "SI") {
    Write-Host "Operación cancelada" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "📦 Creando backup del repositorio..." -ForegroundColor Cyan
$backupName = "farmavet-web-backup-$(Get-Date -Format 'yyyyMMdd_HHmmss')"
git clone --mirror . "../$backupName.git"
Write-Host "✅ Backup creado: $backupName" -ForegroundColor Green

Write-Host ""
Write-Host "🧹 Limpiando historial de Git..." -ForegroundColor Cyan
Write-Host "Eliminando CONFIGURACION_CORREO_VPS.md del historial..." -ForegroundColor Cyan

# Eliminar el archivo del historial completo
git filter-branch --force --index-filter `
  "git rm --cached --ignore-unmatch CONFIGURACION_CORREO_VPS.md" `
  --prune-empty --tag-name-filter cat -- --all

Write-Host ""
Write-Host "✅ Historial limpiado" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Próximos pasos:" -ForegroundColor Cyan
Write-Host "1. Revisa los cambios: git log --oneline"
Write-Host "2. Si todo está bien, fuerza el push:"
Write-Host "   git push origin --force --all"
Write-Host "   git push origin --force --tags"
Write-Host ""
Write-Host "⚠️  IMPORTANTE: Notifica a todos los colaboradores que deben:" -ForegroundColor Yellow
Write-Host "   git fetch origin"
Write-Host "   git reset --hard origin/main"

