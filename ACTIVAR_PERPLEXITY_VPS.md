# 🚀 Activar Perplexity API en VPS

Guía paso a paso para activar la API de Perplexity en tu servidor VPS.

## 📋 Requisitos Previos

1. ✅ Tener acceso SSH al VPS
2. ✅ Tener la clave API de Perplexity lista
3. ✅ Tener permisos sudo en el servidor

## 🔧 Pasos para Activar

### Paso 1: Conectar al VPS

```bash
ssh tu-usuario@tu-servidor-ip
```

### Paso 2: Actualizar el Código desde GitHub

```bash
# Navegar al directorio del proyecto (ajusta la ruta según tu configuración)
cd /home/web/farmavet-web
# O
cd /var/www/farmavet-web

# Asegurarse de estar en la rama main
git checkout main

# Descargar los últimos cambios
git pull origin main
```

### Paso 3: Instalar la Nueva Dependencia

```bash
# Activar el entorno virtual (si existe)
source venv/bin/activate

# Instalar requests (nueva dependencia para Perplexity)
pip install requests==2.31.0

# O instalar todas las dependencias actualizadas
pip install -r requirements.txt

# Si usas un entorno virtual global, instalar sin activar:
# pip install --user requests==2.31.0
```

### Paso 4: Configurar la Clave API en el Servicio Systemd

Editar el archivo de servicio systemd:

```bash
sudo nano /etc/systemd/system/farmavet-web.service
```

**Agregar la variable de entorno PERPLEXITY_API_KEY** en la sección `[Service]`, después de las otras variables `Environment`:

```ini
[Unit]
Description=FARMAVET Web Gunicorn daemon
After=network.target

[Service]
User=web
Group=www-data
WorkingDirectory=/home/web/farmavet-web
Environment="PATH=/home/web/farmavet-web/venv/bin"
Environment="FLASK_ENV=production"
Environment="PERPLEXITY_API_KEY=tu-clave-api-aqui"  # ← AGREGAR ESTA LÍNEA
# Environment="SECRET_KEY=GENERAR_UNA_CLAVE_SECRETA_SEGURA"

ExecStart=/home/web/farmavet-web/venv/bin/gunicorn \
          --config /home/web/farmavet-web/gunicorn_config.py \
          app:app

Restart=always
RestartSec=3
LimitNOFILE=65535

[Install]
WantedBy=multi-user.target
```

**⚠️ IMPORTANTE:**
- Reemplaza `tu-clave-api-aqui` con tu clave API real de Perplexity
- Mantén las comillas dobles alrededor del valor
- No agregues espacios extra antes o después del `=`

### Paso 5: Recargar Systemd

Después de editar el archivo de servicio, necesitas recargar systemd para que reconozca los cambios:

```bash
sudo systemctl daemon-reload
```

### Paso 6: Reiniciar el Servicio

```bash
sudo systemctl restart farmavet-web
```

### Paso 7: Verificar que el Servicio Está Funcionando

```bash
# Ver estado del servicio
sudo systemctl status farmavet-web

# Ver logs recientes
sudo journalctl -u farmavet-web -n 50 -f
```

Deberías ver que el servicio está activo (active) y ejecutándose (running).

## ✅ Verificación

### Verificar que la Variable de Entorno Está Configurada

```bash
# Ver las variables de entorno del servicio
sudo systemctl show farmavet-web --property=Environment

# O verificar en los logs si Perplexity está configurado
sudo journalctl -u farmavet-web | grep -i perplexity
```

Si ves `PERPLEXITY_API_KEY no configurada`, significa que la variable no se está leyendo correctamente. Verifica:

1. ✅ Que agregaste la línea en el archivo de servicio
2. ✅ Que recargaste systemd (`sudo systemctl daemon-reload`)
3. ✅ Que reiniciaste el servicio (`sudo systemctl restart farmavet-web`)

### Probar el Chatbot

1. Abre tu sitio web en el navegador
2. Abre el chatbot
3. Busca algo que NO esté en la base de datos local (ej: "¿qué es HPLC-DAD?")
4. Si está configurado correctamente, deberías ver información adicional de Perplexity

### Ver Logs en Tiempo Real

Para monitorear si Perplexity está funcionando:

```bash
# Ver logs en tiempo real
sudo journalctl -u farmavet-web -f

# Buscar mensajes relacionados con Perplexity
sudo journalctl -u farmavet-web | grep -i "perplexity\|chatbot"
```

Deberías ver mensajes como:
- `Chatbot Perplexity: Buscando - ...`
- `Chatbot Perplexity: Respuesta recibida (...)`

Si ves `PERPLEXITY_API_KEY no configurada`, revisa la configuración.

## 🔒 Seguridad

### Proteger el Archivo de Servicio

Asegúrate de que solo el usuario root pueda leer el archivo de servicio (contiene la clave API):

```bash
sudo chmod 600 /etc/systemd/system/farmavet-web.service
```

### Verificar Permisos

```bash
ls -l /etc/systemd/system/farmavet-web.service
```

Debería mostrar algo como:
```
-rw------- 1 root root 1234 fecha farmavet-web.service
```

## 🐛 Troubleshooting

### El servicio no inicia después de agregar la variable

1. **Verificar sintaxis del archivo:**
   ```bash
   sudo systemd-analyze verify /etc/systemd/system/farmavet-web.service
   ```

2. **Ver logs de error:**
   ```bash
   sudo journalctl -u farmavet-web -n 100 --no-pager
   ```

3. **Verificar que no hay espacios extra o comillas incorrectas**

### Perplexity no funciona pero el servicio está corriendo

1. **Verificar que la clave API está configurada:**
   ```bash
   sudo systemctl show farmavet-web --property=Environment | grep PERPLEXITY
   ```

2. **Verificar logs específicos:**
   ```bash
   sudo journalctl -u farmavet-web | grep -i "perplexity\|api"
   ```

3. **Probar la clave API manualmente:**
   ```bash
   curl -X POST https://api.perplexity.ai/chat/completions \
     -H "Authorization: Bearer tu-clave-api" \
     -H "Content-Type: application/json" \
     -d '{"model":"llama-3.1-sonar-small-128k-online","messages":[{"role":"user","content":"test"}]}'
   ```

### Error: Module 'requests' not found

Si ves un error sobre que el módulo `requests` no se encuentra:

1. **Verificar que instalaste requests en el entorno virtual correcto:**
   ```bash
   cd /home/web/farmavet-web  # Ajusta la ruta
   source venv/bin/activate
   pip list | grep requests
   ```

2. **Si no está instalado:**
   ```bash
   source venv/bin/activate
   pip install requests==2.31.0
   ```

3. **Reiniciar el servicio:**
   ```bash
   sudo systemctl restart farmavet-web
   ```

## 📝 Resumen de Comandos

```bash
# 1. Conectar al VPS
ssh tu-usuario@tu-servidor

# 2. Actualizar código
cd /home/web/farmavet-web
git pull origin main

# 3. Instalar dependencias
source venv/bin/activate
pip install -r requirements.txt

# 4. Editar servicio
sudo nano /etc/systemd/system/farmavet-web.service
# Agregar: Environment="PERPLEXITY_API_KEY=tu-clave-aqui"

# 5. Recargar y reiniciar
sudo systemctl daemon-reload
sudo systemctl restart farmavet-web

# 6. Verificar
sudo systemctl status farmavet-web
sudo journalctl -u farmavet-web -f
```

## 🎯 Próximos Pasos

Después de configurar Perplexity:

1. ✅ Prueba el chatbot en el sitio web
2. ✅ Verifica que funciona buscando términos que no están en la BD local
3. ✅ Monitorea los logs por unos días para asegurar que todo funciona bien
4. ✅ Revisa los costos de Perplexity API (consulta su sitio web)

## 📞 Soporte

Si tienes problemas:

1. Revisa los logs: `sudo journalctl -u farmavet-web -n 100`
2. Verifica la configuración: `sudo systemctl show farmavet-web`
3. Consulta `CONFIGURAR_PERPLEXITY.md` para más detalles

