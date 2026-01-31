# Configuración de Dominios Múltiples

## Objetivo
Hacer que la web sea accesible desde:
- `test.farmavet-bodega.cl` (ya configurado)
- `laboratoriofarmavet.cl` (nuevo)

## Pasos para aplicar en el VPS

### 1. Conectarse al VPS
```bash
ssh usuario@tu-vps
```

### 2. Hacer backup del archivo actual
```bash
sudo cp /etc/nginx/sites-available/farmavet-web /etc/nginx/sites-available/farmavet-web.backup
```

### 3. Copiar el nuevo archivo de configuración
Desde tu máquina local, copia el archivo `nginx_subdomain.conf` al VPS:

**Opción A: Desde tu máquina local (PowerShell)**
```powershell
scp nginx_subdomain.conf usuario@tu-vps:/tmp/farmavet-web.conf
```

**Opción B: Editar directamente en el VPS**
```bash
sudo nano /etc/nginx/sites-available/farmavet-web
```

Luego copia el contenido del archivo `nginx_subdomain.conf` actualizado.

### 4. Verificar la configuración de nginx
```bash
sudo nginx -t
```

Si todo está bien, verás:
```
nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
nginx: configuration file /etc/nginx/nginx.conf test is successful
```

### 5. Recargar nginx
```bash
sudo systemctl reload nginx
```

### 6. Configurar DNS para el nuevo dominio

Asegúrate de que el dominio `laboratoriofarmavet.cl` apunte a la IP de tu VPS:

**Registro DNS necesario:**
- Tipo: `A`
- Nombre: `laboratoriofarmavet.cl`
- Valor: `IP_DEL_VPS`

### 7. Obtener certificado SSL para el nuevo dominio (si usas HTTPS)

**Opción A: Certificado separado**
```bash
sudo certbot certonly --nginx -d laboratoriofarmavet.cl
```

Luego edita `/etc/nginx/sites-available/farmavet-web` y agrega las rutas del certificado para el segundo dominio.

**Opción B: Certificado multi-dominio (recomendado)**
```bash
sudo certbot certonly --nginx -d test.farmavet-bodega.cl -d laboratoriofarmavet.cl
```

Esto creará un certificado que funciona para ambos dominios. Luego actualiza las rutas en el archivo de configuración:
```nginx
ssl_certificate /etc/letsencrypt/live/test.farmavet-bodega.cl/fullchain.pem;
ssl_certificate_key /etc/letsencrypt/live/test.farmavet-bodega.cl/privkey.pem;
```

### 8. Verificar que funciona

Prueba acceder a ambos dominios:
- http://test.farmavet-bodega.cl
- http://laboratoriofarmavet.cl

Si configuraste SSL:
- https://test.farmavet-bodega.cl
- https://laboratoriofarmavet.cl

## Notas importantes

1. **Puerto del backend**: El archivo está configurado para usar el puerto `3003` (según la configuración actual del VPS). Si tu aplicación Flask corre en otro puerto, ajusta `proxy_pass` en el archivo.

2. **Certificado SSL**: Si ambos dominios están en el mismo servidor, es mejor usar un certificado multi-dominio con Certbot.

3. **Redirección HTTP a HTTPS**: Una vez que tengas SSL funcionando, descomenta la línea de redirección en el bloque `server` del puerto 80:
   ```nginx
   return 301 https://$host$request_uri;
   ```

4. **Reiniciar servicios**: Después de los cambios, puede ser necesario reiniciar nginx:
   ```bash
   sudo systemctl restart nginx
   ```

## Verificar logs si hay problemas

```bash
# Logs de acceso
sudo tail -f /var/log/nginx/farmavet-web-access.log

# Logs de errores
sudo tail -f /var/log/nginx/farmavet-web-error.log

# Estado de nginx
sudo systemctl status nginx
```
