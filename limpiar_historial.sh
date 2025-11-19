#!/bin/bash
# Script para limpiar el historial de Git eliminando credenciales expuestas
# ADVERTENCIA: Esto reescribe el historial de Git

set -e

echo "⚠️  ADVERTENCIA: Este script reescribirá el historial de Git"
echo "Esto afectará a todos los que tengan el repositorio clonado"
echo ""
read -p "¿Estás seguro de continuar? (escribe 'SI' para confirmar): " CONFIRM

if [ "$CONFIRM" != "SI" ]; then
    echo "Operación cancelada"
    exit 1
fi

echo ""
echo "📦 Creando backup del repositorio..."
git clone --mirror . ../farmavet-web-backup-$(date +%Y%m%d_%H%M%S).git
echo "✅ Backup creado"

echo ""
echo "🧹 Limpiando historial de Git..."

# Opción 1: Reemplazar contraseñas en todo el historial
# Si conoces la contraseña expuesta, puedes reemplazarla:
# git filter-branch --force --tree-filter \
#   "if [ -f CONFIGURACION_CORREO_VPS.md ]; then sed -i 's/CONTRASEÑA_EXPUESTA/xxxxxxxxxxxxxxxx/g' CONFIGURACION_CORREO_VPS.md; fi" \
#   --prune-empty --tag-name-filter cat -- --all

# Opción 2: Eliminar el archivo del historial completo (más seguro)
echo "Eliminando CONFIGURACION_CORREO_VPS.md del historial..."
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch CONFIGURACION_CORREO_VPS.md" \
  --prune-empty --tag-name-filter cat -- --all

echo ""
echo "✅ Historial limpiado"
echo ""
echo "📋 Próximos pasos:"
echo "1. Revisa los cambios: git log --oneline"
echo "2. Si todo está bien, fuerza el push:"
echo "   git push origin --force --all"
echo "   git push origin --force --tags"
echo ""
echo "⚠️  IMPORTANTE: Notifica a todos los colaboradores que deben:"
echo "   git fetch origin"
echo "   git reset --hard origin/main"

