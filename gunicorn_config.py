# Configuración de Gunicorn para producción
# Usar: gunicorn --config gunicorn_config.py app:app

# Dirección y puerto (ajustar según necesidad)
# Para farmavet-web en VPS, usar puerto diferente a farmavet-bodega
bind = "127.0.0.1:5001"  # Cambiar a 5000 si es el único proyecto

# Número de workers (ajustar según CPU)
workers = 2

# Timeout
timeout = 120

# Clase de worker
worker_class = "sync"

# Logs
accesslog = "-"  # stdout
errorlog = "-"   # stderr
loglevel = "info"

# Preload app para mejor rendimiento
preload_app = True

# Máximo de requests por worker antes de reiniciar (previene memory leaks)
max_requests = 1000
max_requests_jitter = 50


