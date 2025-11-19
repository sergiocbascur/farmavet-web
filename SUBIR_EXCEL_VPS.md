# Instrucciones para Subir el Excel al VPS

## ⚠️ IMPORTANTE: Ejecutar desde tu MÁQUINA LOCAL (Windows), NO desde el VPS

## Opción 1: Usando SCP (desde Windows PowerShell)

```powershell
# Abre PowerShell en tu máquina local (Windows)
# Navega a la carpeta donde está el Excel
cd C:\Users\sergi\Documents\Proyectos\farmavet-web

# Sube el archivo (reemplaza los datos):
scp "RESUMEN CLIENTES-LAB.xlsx" web@farmavet-bodega.cl:~/farmavet-web/
```

**O si tu VPS tiene una IP o dominio diferente:**

```powershell
scp "RESUMEN CLIENTES-LAB.xlsx" web@tu-dominio-o-ip:~/farmavet-web/
```

## Opción 2: Usando WinSCP (GUI - Más Fácil)

1. Descarga e instala **WinSCP**: https://winscp.net/
2. Conéctate a tu VPS:
   - **Host name**: `farmavet-bodega.cl` (o tu dominio/IP)
   - **User name**: `web`
   - **Protocol**: SFTP
   - **Password**: tu contraseña
3. Navega a: `/home/web/farmavet-web/`
4. Arrastra el archivo `RESUMEN CLIENTES-LAB.xlsx` desde tu máquina al VPS

## Opción 3: Usando FileZilla (GUI - Alternativa)

1. Descarga e instala **FileZilla**: https://filezilla-project.org/
2. Conéctate a tu VPS:
   - **Host**: `sftp://farmavet-bodega.cl`
   - **Username**: `web`
   - **Password**: tu contraseña
   - **Port**: 22
3. Navega a: `/home/web/farmavet-web/`
4. Arrastra el archivo desde tu máquina al VPS

## Después de Subir

Una vez que el archivo esté en el VPS, conecta al VPS y ejecuta:

```bash
ssh web@farmavet-bodega.cl
cd ~/farmavet-web

# Verificar que el archivo esté ahí
ls -la "RESUMEN CLIENTES-LAB.xlsx"

# Probar primero (dry-run)
python importar_metodologias_excel.py "RESUMEN CLIENTES-LAB.xlsx" --dry-run

# Si todo se ve bien, importar realmente
python importar_metodologias_excel.py "RESUMEN CLIENTES-LAB.xlsx" --yes
```

