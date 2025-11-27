#!/bin/bash
# Script para configurar Git en el VPS

echo "🔧 Configurando Git en el VPS..."

# Configurar identidad (necesario para commits)
git config --global user.email "sergioc.bascur@icloud.com"
git config --global user.name "sergiocbascur"

echo "✅ Identidad de Git configurada"

# Verificar si ya hay credential helper configurado
if git config --global credential.helper > /dev/null 2>&1; then
    echo "✅ Credential helper ya está configurado"
    echo "   Usando: $(git config --global credential.helper)"
else
    echo "📝 Configurando credential helper..."
    git config --global credential.helper store
    echo "✅ Credential helper configurado"
fi

# Verificar URL remota actual
echo ""
echo "📋 URL remota actual:"
git remote -v

echo ""
echo "✅ Configuración completada"
echo ""
echo "Para hacer push, necesitarás:"
echo "1. Un token personal de GitHub (si no tienes uno)"
echo "2. Al hacer 'git push', usar el token como contraseña"
echo ""
echo "Obtener token: https://github.com/settings/tokens"
echo "   → Generate new token (classic)"
echo "   → Marcar 'repo'"
echo "   → Generar y copiar"


