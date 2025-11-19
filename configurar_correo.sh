#!/bin/bash
# Script para configurar variables de entorno SMTP en el servicio systemd

# Colores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}📧 Configuración de Correo SMTP para FARMAVET${NC}"
echo ""

# Verificar que se ejecute como root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}❌ Por favor ejecuta este script con sudo${NC}"
    exit 1
fi

# Solicitar información SMTP
echo -e "${YELLOW}Ingresa la configuración SMTP:${NC}"
echo ""

read -p "SMTP Host (ej: smtp.gmail.com): " SMTP_HOST
read -p "SMTP Port (ej: 587): " SMTP_PORT
read -p "SMTP User (email o usuario): " SMTP_USER
read -sp "SMTP Password: " SMTP_PASSWORD
echo ""
read -p "SMTP From (email remitente, opcional): " SMTP_FROM

# Si SMTP_FROM está vacío, usar SMTP_USER
if [ -z "$SMTP_FROM" ]; then
    SMTP_FROM="$SMTP_USER"
fi

# Validar que los campos requeridos no estén vacíos
if [ -z "$SMTP_HOST" ] || [ -z "$SMTP_PORT" ] || [ -z "$SMTP_USER" ] || [ -z "$SMTP_PASSWORD" ]; then
    echo -e "${RED}❌ Error: Todos los campos son requeridos${NC}"
    exit 1
fi

# Ruta del archivo de servicio
SERVICE_FILE="/etc/systemd/system/farmavet-web.service"

# Verificar que el archivo existe
if [ ! -f "$SERVICE_FILE" ]; then
    echo -e "${RED}❌ Error: No se encontró el archivo $SERVICE_FILE${NC}"
    echo "Asegúrate de que el servicio esté instalado correctamente."
    exit 1
fi

# Crear backup
cp "$SERVICE_FILE" "${SERVICE_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
echo -e "${GREEN}✓ Backup creado${NC}"

# Verificar si ya existen las variables de entorno
if grep -q "Environment=\"SMTP_HOST" "$SERVICE_FILE"; then
    echo -e "${YELLOW}⚠️  Ya existen variables SMTP en el archivo${NC}"
    read -p "¿Deseas reemplazarlas? (s/n): " REPLACE
    if [ "$REPLACE" != "s" ] && [ "$REPLACE" != "S" ]; then
        echo "Operación cancelada"
        exit 0
    fi
    
    # Eliminar líneas SMTP existentes
    sed -i '/Environment="SMTP_/d' "$SERVICE_FILE"
fi

# Agregar variables de entorno antes de la línea [Service] o después de otras Environment
if grep -q "^\[Service\]" "$SERVICE_FILE"; then
    # Insertar después de [Service]
    sed -i "/^\[Service\]/a Environment=\"SMTP_HOST=$SMTP_HOST\"\nEnvironment=\"SMTP_PORT=$SMTP_PORT\"\nEnvironment=\"SMTP_USER=$SMTP_USER\"\nEnvironment=\"SMTP_PASSWORD=$SMTP_PASSWORD\"\nEnvironment=\"SMTP_FROM=$SMTP_FROM\"" "$SERVICE_FILE"
else
    echo -e "${RED}❌ Error: No se encontró la sección [Service] en el archivo${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Variables de entorno agregadas${NC}"

# Recargar systemd
systemctl daemon-reload
echo -e "${GREEN}✓ Systemd recargado${NC}"

# Reiniciar servicio
read -p "¿Deseas reiniciar el servicio ahora? (s/n): " RESTART
if [ "$RESTART" = "s" ] || [ "$RESTART" = "S" ]; then
    systemctl restart farmavet-web
    echo -e "${GREEN}✓ Servicio reiniciado${NC}"
    
    # Verificar estado
    sleep 2
    if systemctl is-active --quiet farmavet-web; then
        echo -e "${GREEN}✓ Servicio está corriendo correctamente${NC}"
    else
        echo -e "${RED}❌ Error: El servicio no está corriendo${NC}"
        echo "Revisa los logs con: sudo journalctl -u farmavet-web -n 50"
    fi
fi

echo ""
echo -e "${GREEN}✅ Configuración completada${NC}"
echo ""
echo "Próximos pasos:"
echo "1. Configura los correos de destino en /admin/correos-contacto"
echo "2. Prueba el formulario de contacto en /contacto.html"
echo "3. Revisa los logs si hay problemas: sudo journalctl -u farmavet-web -f"

