# 🔧 Corregir Error 203/EXEC en Servicio

## ❓ Problema

```
status=203/EXEC
Main process exited, code=exited, status=203/EXEC
```

**Significado:** El ejecutable especificado en `ExecStart` no se encuentra o no se puede ejecutar.

**Causa común:** La ruta del entorno virtual (`venv`) es incorrecta o no existe.

## 🔍 Diagnóstico

### Paso 1: Verificar si Existe el Entorno Virtual

```bash
# Verificar si existe el venv
ls -la /home/web/farmavet-web/venv/bin/gunicorn

# Si no existe, ver qué hay en el directorio
ls -la /home/web/farmavet-web/
```

### Paso 2: Verificar Dónde Está Gunicorn

```bash
# Buscar gunicorn en el sistema
which gunicorn

# O como usuario web
sudo -u web which gunicorn

# O buscar en el proyecto
find /home/web/farmavet-web -name gunicorn 2>/dev/null
```

### Paso 3: Verificar el Archivo de Servicio

```bash
# Ver el archivo de servicio actual
sudo cat /etc/systemd/system/farmavet-web.service
```

---

## 🔧 Soluciones

### Solución 1: Si NO Existe el Entorno Virtual

Si no tienes un entorno virtual, puedes usar el gunicorn del sistema o crear uno:

```bash
# Opción A: Usar gunicorn del sistema (si está instalado globalmente)
# Editar el archivo de servicio para usar gunicorn directamente
sudo nano /etc/systemd/system/farmavet-web.service

# Cambiar la línea ExecStart de:
# ExecStart=/home/web/farmavet-web/venv/bin/gunicorn ...
# A:
# ExecStart=/usr/local/bin/gunicorn --config /home/web/farmavet-web/gunicorn_config.py app:app
# O:
# ExecStart=/usr/bin/gunicorn --config /home/web/farmavet-web/gunicorn_config.py app:app

# Opción B: Crear entorno virtual
cd /home/web/farmavet-web
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Solución 2: Si el Entorno Virtual Está en Otra Ubicación

```bash
# Buscar dónde está realmente
find /home/web -name gunicorn 2>/dev/null

# Luego actualizar el archivo de servicio con la ruta correcta
sudo nano /etc/systemd/system/farmavet-web.service
```

### Solución 3: Usar Python Directamente (Recomendado)

Si no tienes venv o prefieres no usarlo, puedes usar Python directamente:

```bash
# Editar el archivo de servicio
sudo nano /etc/systemd/system/farmavet-web.service

# Cambiar ExecStart a:
ExecStart=/usr/bin/python3 -m gunicorn --config /home/web/farmavet-web/gunicorn_config.py app:app
```

O si gunicorn está instalado globalmente:

```bash
ExecStart=/usr/bin/gunicorn --config /home/web/farmavet-web/gunicorn_config.py app:app
```

### Solución 4: Verificar Permisos del Ejecutable

```bash
# Dar permisos de ejecución
chmod +x /home/web/farmavet-web/venv/bin/gunicorn

# Verificar que el usuario web puede ejecutarlo
sudo -u web /home/web/farmavet-web/venv/bin/gunicorn --version
```

---

## ✅ Solución Rápida (Recomendada)

### Opción A: Usar Python con -m gunicorn

```bash
# Editar el archivo de servicio
sudo nano /etc/systemd/system/farmavet-web.service

# Cambiar la línea ExecStart a:
ExecStart=/usr/bin/python3 -m gunicorn --config /home/web/farmavet-web/gunicorn_config.py app:app

# Guardar y salir (Ctrl+O, Enter, Ctrl+X)

# Recargar systemd
sudo systemctl daemon-reload

# Reiniciar el servicio
sudo systemctl restart farmavet-web

# Verificar estado
sudo systemctl status farmavet-web
```

### Opción B: Crear/Usar Entorno Virtual

```bash
# Ir al directorio del proyecto
cd /home/web/farmavet-web

# Crear entorno virtual (si no existe)
python3 -m venv venv

# Activar y instalar dependencias
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Verificar que gunicorn está instalado
venv/bin/gunicorn --version

# Si funciona, el servicio debería funcionar también
sudo systemctl daemon-reload
sudo systemctl restart farmavet-web
```

---

## 🔍 Verificar la Ruta Correcta

Antes de editar el servicio, verifica dónde está gunicorn:

```bash
# Como usuario web
sudo -u web bash -c "cd /home/web/farmavet-web && source venv/bin/activate 2>/dev/null && which gunicorn"

# O buscar en el sistema
find /home/web -name gunicorn -type f 2>/dev/null

# O verificar si está instalado globalmente
gunicorn --version
```

---

## 💡 Nota sobre Entornos Virtuales

Si usas un entorno virtual, asegúrate de que:
1. El venv existe en la ruta especificada
2. Gunicorn está instalado en el venv (`pip install gunicorn`)
3. El usuario `web` tiene permisos para ejecutar el venv

Si prefieres no usar venv, puedes instalar gunicorn globalmente:
```bash
sudo pip3 install gunicorn
```

Y luego usar `/usr/local/bin/gunicorn` o `/usr/bin/gunicorn` en el servicio.

