#!/bin/bash
# Script para sincronizar el VPS con GitHub
# Uso: ./sincronizar_vps.sh

cd ~/farmavet-web

echo "🔄 Sincronizando con GitHub..."

# Obtener cambios del remoto
git fetch origin

# Verificar si hay cambios locales
if [ -n "$(git status --porcelain)" ]; then
    echo "⚠️  Hay cambios locales no commiteados"
    echo "¿Deseas descartarlos y alinear con remoto? (s/n)"
    read -r respuesta
    if [ "$respuesta" = "s" ] || [ "$respuesta" = "S" ]; then
        git reset --hard origin/main
        git clean -fd
        echo "✅ Cambios locales descartados, alineado con remoto"
    else
        echo "❌ Operación cancelada"
        exit 1
    fi
else
    # Si no hay cambios locales, hacer pull
    git pull origin main
    echo "✅ Sincronización completada"
fi

# Reiniciar servicio si es necesario
echo ""
echo "¿Deseas reiniciar el servicio farmavet-web? (s/n)"
read -r reiniciar
if [ "$reiniciar" = "s" ] || [ "$reiniciar" = "S" ]; then
    sudo systemctl restart farmavet-web
    echo "✅ Servicio reiniciado"
fi


