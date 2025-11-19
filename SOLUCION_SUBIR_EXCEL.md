# Solución: Error "Connection refused" al subir Excel

## Problema
El puerto 22 (SSH estándar) está rechazando la conexión. Puede ser:
- Puerto SSH diferente
- Firewall bloqueando
- Servicio SSH no activo

## Soluciones

### Opción 1: Probar con puerto diferente

Si tu VPS usa un puerto SSH diferente (ej: 2222, 2200):

```powershell
# Desde PowerShell en Windows
scp -P 2222 "RESUMEN CLIENTES-LAB.xlsx" web@farmavet-bodega.cl:~/farmavet-web/
```

### Opción 2: Usar WinSCP (Recomendado - Más fácil)

WinSCP detecta automáticamente el puerto correcto:

1. **Descarga WinSCP**: https://winscp.net/eng/download.php
2. **Instala y abre WinSCP**
3. **Configura la conexión**:
   - **Host name**: `farmavet-bodega.cl`
   - **User name**: `web`
   - **Password**: tu contraseña
   - **Port**: Deja en blanco o prueba 22, 2222, 2200
   - **Protocol**: SFTP
4. Click en **Login**
5. Navega a: `/home/web/farmavet-web/`
6. **Arrastra** el archivo `RESUMEN CLIENTES-LAB.xlsx` desde tu Windows al VPS

### Opción 3: Verificar puerto SSH en el VPS

Conéctate al VPS y verifica:

```bash
# En el VPS
sudo netstat -tlnp | grep ssh
# O
sudo ss -tlnp | grep ssh
```

Esto te mostrará en qué puerto está escuchando SSH.

### Opción 4: Subir desde el panel web del VPS

Si tu proveedor de VPS tiene un panel web (cPanel, Plesk, etc.):
1. Accede al panel
2. Usa el administrador de archivos
3. Sube el archivo directamente

### Opción 5: Usar el editor de archivos del VPS

Si tienes acceso web al VPS, puedes:
1. Conectarte por SSH normalmente (desde otra herramienta que funcione)
2. Crear el archivo usando `nano` o `vi` y copiar el contenido (no recomendado para Excel)

## Después de subir

Una vez que el archivo esté en el VPS:

```bash
# En el VPS
cd ~/farmavet-web
ls -la "RESUMEN CLIENTES-LAB.xlsx"  # Verificar
python importar_metodologias_excel.py "RESUMEN CLIENTES-LAB.xlsx" --yes
```

