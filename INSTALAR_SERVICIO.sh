#!/bin/bash
# Script para instalar el servicio systemd de farmavet-web
# Ejecutar como root: sudo bash INSTALAR_SERVICIO.sh

echo "🔧 Instalando servicio systemd para farmavet-web..."

# Verificar que estamos como root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Por favor ejecuta como root: sudo bash INSTALAR_SERVICIO.sh"
    exit 1
fi

# Verificar que el archivo existe
if [ ! -f "/home/web/farmavet-web/farmavet-web.service" ]; then
    echo "❌ No se encuentra /home/web/farmavet-web/farmavet-web.service"
    exit 1
fi

# Generar SECRET_KEY
echo "🔑 Generando SECRET_KEY..."
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))" 2>/dev/null || python -c "import secrets; print(secrets.token_hex(32))")

if [ -z "$SECRET_KEY" ]; then
    echo "⚠️  No se pudo generar SECRET_KEY automáticamente"
    echo "   Por favor, genera una manualmente:"
    echo "   python3 -c \"import secrets; print(secrets.token_hex(32))\""
    read -p "   Ingresa tu SECRET_KEY: " SECRET_KEY
fi

# Copiar archivo de servicio
echo "📋 Copiando archivo de servicio..."
cp /home/web/farmavet-web/farmavet-web.service /etc/systemd/system/farmavet-web.service

# Reemplazar SECRET_KEY en el archivo
echo "🔐 Configurando SECRET_KEY..."
sed -i "s|REEMPLAZAR_CON_TU_SECRET_KEY_AQUI|$SECRET_KEY|g" /etc/systemd/system/farmavet-web.service

# Verificar que el usuario web existe
if ! id "web" &>/dev/null; then
    echo "❌ El usuario 'web' no existe. Por favor créalo primero."
    exit 1
fi

# Verificar que la carpeta existe
if [ ! -d "/home/web/farmavet-web" ]; then
    echo "❌ La carpeta /home/web/farmavet-web no existe"
    exit 1
fi

# Verificar que el entorno virtual existe
if [ ! -d "/home/web/farmavet-web/venv" ]; then
    echo "❌ El entorno virtual no existe en /home/web/farmavet-web/venv"
    echo "   Por favor créalo: python3 -m venv venv"
    exit 1
fi

# Dar permisos correctos
echo "🔒 Configurando permisos..."
chown -R web:web /home/web/farmavet-web
chmod 755 /home/web/farmavet-web
chmod 755 /home/web/farmavet-web/static/uploads

# Recargar systemd
echo "🔄 Recargando systemd..."
systemctl daemon-reload

# Habilitar servicio
echo "✅ Habilitando servicio..."
systemctl enable farmavet-web

# Iniciar servicio
echo "🚀 Iniciando servicio..."
systemctl start farmavet-web

# Esperar un momento
sleep 2

# Verificar estado
echo ""
echo "📊 Estado del servicio:"
systemctl status farmavet-web --no-pager

echo ""
echo "✅ Instalación completada!"
echo ""
echo "🔍 Comandos útiles:"
echo "   Ver estado:    sudo systemctl status farmavet-web"
echo "   Ver logs:      sudo journalctl -u farmavet-web -f"
echo "   Reiniciar:     sudo systemctl restart farmavet-web"
echo "   Detener:       sudo systemctl stop farmavet-web"
echo ""
echo "🌐 El servicio está corriendo en: http://127.0.0.1:5001"
echo "   (Puerto 5001 - diferente a farmavet-bodega en 5000)"

