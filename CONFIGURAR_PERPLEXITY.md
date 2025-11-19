# Configuración de API Perplexity para Chatbot

Este documento explica cómo configurar la API de Perplexity para habilitar búsquedas inteligentes en el chatbot de metodologías.

## ¿Qué hace Perplexity?

Perplexity AI permite que el chatbot realice búsquedas inteligentes en internet cuando no encuentra resultados en la base de datos local. Esto proporciona información adicional y contexto sobre metodologías analíticas, técnicas, y términos químicos.

## Configuración

### 1. Obtener Clave API de Perplexity

1. Ve a [Perplexity AI](https://www.perplexity.ai/)
2. Regístrate o inicia sesión
3. Ve a tu perfil/configuración
4. Navega a la sección de API Keys
5. Genera una nueva clave API
6. Copia la clave (la necesitarás en el siguiente paso)

### 2. Configurar la Clave API

#### Opción A: Variable de Entorno (Recomendado)

**En desarrollo local (Windows PowerShell):**
```powershell
$env:PERPLEXITY_API_KEY="tu-clave-api-aqui"
```

**En desarrollo local (Windows CMD):**
```cmd
set PERPLEXITY_API_KEY=tu-clave-api-aqui
```

**En desarrollo local (Linux/Mac):**
```bash
export PERPLEXITY_API_KEY="tu-clave-api-aqui"
```

**En producción (VPS/Linux):**
```bash
# Agregar al archivo ~/.bashrc o ~/.profile
export PERPLEXITY_API_KEY="tu-clave-api-aqui"

# O en el archivo de servicio systemd (farmavet-web.service)
# Agregar en [Service]:
Environment="PERPLEXITY_API_KEY=tu-clave-api-aqui"
```

#### Opción B: Archivo .env (No subir a Git)

1. Crear archivo `.env` en la raíz del proyecto:
```bash
PERPLEXITY_API_KEY=tu-clave-api-aqui
```

2. Asegurarse de que `.env` esté en `.gitignore`

3. Cargar variables desde `.env` en `app.py` (usando python-dotenv):
```python
from dotenv import load_dotenv
load_dotenv()
```

**Nota:** Si usas `.env`, necesitarás instalar `python-dotenv`:
```bash
pip install python-dotenv
```

### 3. Instalar Dependencias

Si aún no lo has hecho, instala las dependencias actualizadas:

```bash
pip install -r requirements.txt
```

Esto instalará `requests==2.31.0` que es necesario para las llamadas a la API.

### 4. Reiniciar el Servidor

Después de configurar la clave API, reinicia el servidor Flask:

```bash
# Desarrollo
python app.py

# Producción (si usas systemd)
sudo systemctl restart farmavet-web
```

## Verificación

Para verificar que la configuración funciona:

1. Abre el chatbot en cualquier página del sitio
2. Busca algo que no esté en la base de datos local (ej: "¿qué es la técnica HPLC-DAD?")
3. Si está configurado correctamente, verás información adicional de Perplexity
4. Si no está configurado, verás solo las sugerencias estándar

### Ver Logs del Servidor

Los logs del servidor mostrarán si Perplexity está funcionando:

```bash
# Si usas systemd
sudo journalctl -u farmavet-web -f

# O en los logs de Flask directamente
```

Busca mensajes como:
- `Chatbot Perplexity: Buscando - ...`
- `Chatbot Perplexity: Respuesta recibida (...)`
- `PERPLEXITY_API_KEY no configurada` (si no está configurada)

## Funcionamiento

1. **Búsqueda Local Primero**: El chatbot primero busca en la base de datos local de metodologías de FARMAVET.

2. **Si No Encuentra Resultados**: Si no encuentra resultados locales, automáticamente hace una búsqueda inteligente con Perplexity.

3. **Respuesta Combinada**: Muestra primero el mensaje de "no encontrado localmente", luego la información adicional de Perplexity.

4. **Advertencia**: Siempre muestra una advertencia indicando que la información de Perplexity es general y que para metodologías específicas deben contactar directamente con FARMAVET.

## Modelo de Perplexity Usado

- **Modelo**: `llama-3.1-sonar-small-128k-online`
- **Características**: Capacidad de búsqueda web en tiempo real
- **Contexto**: Configurado específicamente como asistente de FARMAVET
- **Temperatura**: 0.2 (respuestas más precisas y deterministas)
- **Max Tokens**: 500 (respuestas concisas)

## Costos

Consulta los precios actuales de Perplexity API en su sitio web oficial. El uso es bajo porque:
- Solo se usa cuando NO hay resultados locales
- Respuestas limitadas a 500 tokens
- Se usa el modelo "small" (más económico)

## Seguridad

- ✅ La clave API nunca se expone al cliente
- ✅ Todas las llamadas pasan por el servidor Flask
- ✅ La clave se almacena como variable de entorno (no en código)
- ✅ `.env` debe estar en `.gitignore` si se usa

## Troubleshooting

### El chatbot no muestra información de Perplexity

1. Verifica que la clave API esté configurada:
   ```bash
   echo $PERPLEXITY_API_KEY  # Linux/Mac
   echo %PERPLEXITY_API_KEY%  # Windows CMD
   $env:PERPLEXITY_API_KEY   # Windows PowerShell
   ```

2. Verifica los logs del servidor para errores

3. Verifica que `requests` esté instalado:
   ```bash
   pip list | grep requests
   ```

### Error 401 (Unauthorized)

- Verifica que la clave API sea correcta
- Verifica que no haya espacios extra al copiar/pegar
- Regenera la clave API si es necesario

### Error 503 (Service Unavailable)

- Verifica que la API de Perplexity esté funcionando
- Revisa si hay límites de rate limiting
- Verifica tu plan de Perplexity

### Timeout

- Verifica tu conexión a internet
- El timeout está configurado en 10 segundos
- Puedes ajustar el timeout en `app.py` si es necesario

## Soporte

Para problemas específicos con la API de Perplexity, consulta:
- [Documentación de Perplexity API](https://docs.perplexity.ai/)
- Logs del servidor Flask
- Consola del navegador (F12) para errores del frontend

