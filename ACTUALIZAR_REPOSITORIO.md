# 🔄 Actualizar Repositorio en VPS

## Pasos para obtener los archivos nuevos

```bash
# Conectarte como usuario web
sudo su - web

# Ir a la carpeta del proyecto
cd /home/web/farmavet-web

# Actualizar desde GitHub
git pull origin main

# Verificar que el script existe
ls -la INSTALAR_SERVICIO.sh

# Salir del usuario web
exit
```

## Luego ejecutar el script

```bash
# Como root
cd /home/web/farmavet-web
sudo bash INSTALAR_SERVICIO.sh
```

