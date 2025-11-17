# 🖥️ Guía de Despliegue en VPS - FARMAVET Web

## ✅ Respuestas Rápidas

1. **¿Puedo tener ambos proyectos en el mismo VPS?** 
   - ✅ **SÍ**, perfectamente. Pueden coexistir sin problemas.

2. **¿Puedo usar un subdominio para probar?**
   - ✅ **SÍ**, `test.farmavet-bodega.cl` es perfecto para pruebas.

---

## 📁 Estructura Recomendada en el VPS

```
/home/usuario/
├── farmavet-bodega/          # Tu proyecto actual
│   ├── app.py
│   └── ...
└── farmavet-web/             # Nuevo proyecto
    ├── app.py
    ├── templates/
    └── ...
```

**Cada proyecto en su propia carpeta** - No se mezclan.

---

## 🔧 Opción 1: Usar Nginx como Reverse Proxy (RECOMENDADO)

Esta es la mejor opción si ya tienes Nginx configurado para `farmavet-bodega`.

### Estructura:
- `farmavet-bodega.cl` → Puerto 5000 (o el que uses)
- `test.farmavet-bodega.cl` → Puerto 5001 (farmavet-web)

### Paso 1: Instalar farmavet-web en el VPS

```bash
# Conectarte al VPS
ssh usuario@tu-vps

# Ir a la carpeta donde está farmavet-bodega
cd /home/usuario  # o donde tengas los proyectos

# Clonar farmavet-web
git clone https://github.com/sergiocbascur/farmavet-web.git
cd farmavet-web

# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate  # Linux
# o: venv\Scripts\activate  # Windows

# Instalar dependencias
pip install -r requirements.txt
```

### Paso 2: Configurar farmavet-web para producción

Crea un archivo `run_production.py`:

```python
#!/usr/bin/env python3
"""Script para ejecutar la app en producción con Gunicorn"""
import os

# Configurar variables de entorno
os.environ['FLASK_ENV'] = 'production'
os.environ['SECRET_KEY'] = 'tu-secret-key-aqui'  # Cambiar!

if __name__ == '__main__':
    from app import app
    import gunicorn.app.wsgiapp as wsgi
    
    # Ejecutar con Gunicorn
    wsgi.run()
```

O mejor, usar Gunicorn directamente:

```bash
# Crear archivo de configuración gunicorn_config.py
cat > gunicorn_config.py << EOF
bind = "127.0.0.1:5001"  # Puerto diferente a farmavet-bodega
workers = 2
timeout = 120
worker_class = "sync"
EOF
```

### Paso 3: Crear servicio systemd para farmavet-web

```bash
sudo nano /etc/systemd/system/farmavet-web.service
```

Contenido:

```ini
[Unit]
Description=FARMAVET Web Gunicorn daemon
After=network.target

[Service]
User=tu-usuario
Group=www-data
WorkingDirectory=/home/tu-usuario/farmavet-web
Environment="PATH=/home/tu-usuario/farmavet-web/venv/bin"
Environment="FLASK_ENV=production"
Environment="SECRET_KEY=tu-secret-key-aqui"
ExecStart=/home/tu-usuario/farmavet-web/venv/bin/gunicorn \
          --config gunicorn_config.py \
          app:app

[Install]
WantedBy=multi-user.target
```

Activar el servicio:

```bash
sudo systemctl daemon-reload
sudo systemctl enable farmavet-web
sudo systemctl start farmavet-web
sudo systemctl status farmavet-web
```

### Paso 4: Configurar Nginx para el subdominio

```bash
sudo nano /etc/nginx/sites-available/test.farmavet-bodega.cl
```

Contenido:

```nginx
server {
    listen 80;
    server_name test.farmavet-bodega.cl;

    # Redirigir a HTTPS (opcional pero recomendado)
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name test.farmavet-bodega.cl;

    # Certificado SSL (usar Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/test.farmavet-bodega.cl/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/test.farmavet-bodega.cl/privkey.pem;

    # Logs
    access_log /var/log/nginx/farmavet-web-access.log;
    error_log /var/log/nginx/farmavet-web-error.log;

    # Archivos estáticos (si los sirves directamente)
    location /static {
        alias /home/tu-usuario/farmavet-web/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location /assets {
        alias /home/tu-usuario/farmavet-web/assets;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location /logos {
        alias /home/tu-usuario/farmavet-web/logos;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Proxy a Gunicorn
    location / {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Tamaño máximo de upload
    client_max_body_size 16M;
}
```

Activar el sitio:

```bash
sudo ln -s /etc/nginx/sites-available/test.farmavet-bodega.cl /etc/nginx/sites-enabled/
sudo nginx -t  # Verificar configuración
sudo systemctl reload nginx
```

### Paso 5: Configurar DNS

En tu proveedor de DNS (donde gestionas `farmavet-bodega.cl`):

1. Agregar registro **A** o **CNAME**:
   - **Tipo:** A (o CNAME)
   - **Nombre:** `test`
   - **Valor:** IP de tu VPS (la misma que usa `farmavet-bodega.cl`)
   - **TTL:** 3600

2. Esperar propagación DNS (15 min - 2 horas)

### Paso 6: Obtener certificado SSL (Let's Encrypt)

```bash
sudo certbot --nginx -d test.farmavet-bodega.cl
```

---

## 🔧 Opción 2: Usar Puertos Diferentes (Más Simple)

Si no quieres configurar Nginx ahora:

### farmavet-bodega: Puerto 5000
### farmavet-web: Puerto 5001

Modificar `app.py` al final:

```python
if __name__ == '__main__':
    # Para desarrollo local
    app.run(debug=True, host='0.0.0.0', port=5001)
```

O usar Gunicorn directamente:

```bash
cd /home/tu-usuario/farmavet-web
source venv/bin/activate
gunicorn -w 2 -b 0.0.0.0:5001 app:app
```

**Acceso:** `http://tu-vps-ip:5001`

---

## 🔧 Opción 3: Usar PM2 (Gestor de Procesos)

Si prefieres un gestor de procesos más simple:

```bash
# Instalar PM2
npm install -g pm2

# Crear archivo ecosystem.config.js
cat > ecosystem.config.js << EOF
module.exports = {
  apps: [
    {
      name: 'farmavet-bodega',
      script: 'gunicorn',
      args: '-w 2 -b 127.0.0.1:5000 app:app',
      cwd: '/home/tu-usuario/farmavet-bodega',
      interpreter: '/home/tu-usuario/farmavet-bodega/venv/bin/python',
      env: {
        FLASK_ENV: 'production'
      }
    },
    {
      name: 'farmavet-web',
      script: 'gunicorn',
      args: '-w 2 -b 127.0.0.1:5001 app:app',
      cwd: '/home/tu-usuario/farmavet-web',
      interpreter: '/home/tu-usuario/farmavet-web/venv/bin/python',
      env: {
        FLASK_ENV: 'production',
        SECRET_KEY: 'tu-secret-key'
      }
    }
  ]
};
EOF

# Iniciar ambos servicios
pm2 start ecosystem.config.js
pm2 save
pm2 startup  # Para iniciar al arrancar el servidor
```

---

## 📝 Checklist de Despliegue

- [ ] Clonar repositorio en VPS
- [ ] Crear entorno virtual
- [ ] Instalar dependencias
- [ ] Configurar variables de entorno (SECRET_KEY, FLASK_ENV)
- [ ] Crear servicio systemd o usar PM2
- [ ] Configurar Nginx para subdominio
- [ ] Configurar DNS (registro A/CNAME para `test`)
- [ ] Obtener certificado SSL (Let's Encrypt)
- [ ] Probar acceso: `https://test.farmavet-bodega.cl`
- [ ] Crear usuario administrador

---

## 🔐 Seguridad

1. **Firewall**: Asegúrate de que solo los puertos necesarios estén abiertos
   ```bash
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   sudo ufw enable
   ```

2. **SECRET_KEY**: Genera una única para producción:
   ```bash
   python3 -c "import secrets; print(secrets.token_hex(32))"
   ```

3. **Base de datos**: Considera usar PostgreSQL en lugar de SQLite para producción

---

## 🆘 Comandos Útiles

```bash
# Ver logs de farmavet-web
sudo journalctl -u farmavet-web -f

# Reiniciar servicio
sudo systemctl restart farmavet-web

# Ver estado
sudo systemctl status farmavet-web

# Ver logs de Nginx
sudo tail -f /var/log/nginx/farmavet-web-error.log

# Probar configuración Nginx
sudo nginx -t
```

---

## 💡 Recomendación

**Usa la Opción 1 (Nginx + systemd)** porque:
- ✅ Más profesional
- ✅ Mejor rendimiento
- ✅ SSL fácil con Let's Encrypt
- ✅ Separación clara de proyectos
- ✅ Fácil de mantener

¿Necesitas ayuda con algún paso específico?

