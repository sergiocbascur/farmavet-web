# INSTRUCCIONES PARA ACTUALIZACIONES FUTURAS
## FARMAVET - Laboratorio de Farmacología Veterinaria

**Fecha de creación:** 15 de enero de 2025  
**Última actualización:** 15 de enero de 2025

---

## 📋 ÍNDICE

1. [Integración de Feeds de Redes Sociales](#1-integración-de-feeds-de-redes-sociales)
2. [Actualización del Blog/CMS](#2-actualización-del-blogcms)
3. [Dominio del Sitio Web](#3-dominio-del-sitio-web)
4. [Verificación de Metadata SEO](#4-verificación-de-metadata-seo)
5. [Otros Elementos Pendientes](#5-otros-elementos-pendientes)

---

## 1. INTEGRACIÓN DE FEEDS DE REDES SOCIALES

### 📍 Ubicación
**Archivo:** `noticias.html`  
**Sección:** "Síguenos en redes sociales" (línea ~221)

### 📸 Instagram Feed

#### Opción A: SnapWidget (Recomendado - Gratuito)

**Pasos:**

1. **Accede a SnapWidget:**
   - URL: https://snapwidget.com
   - Crea una cuenta gratuita o inicia sesión

2. **Crea un nuevo widget:**
   - Haz clic en "Create Widget" o "Instagram Feed"
   - Selecciona "Instagram" como fuente

3. **Conecta tu cuenta de Instagram:**
   - Autoriza SnapWidget para acceder a tu Instagram
   - Selecciona la cuenta correcta (@farmavetuchile)

4. **Personaliza el widget:**
   - **Layout:** Selecciona "Grid" (malla)
   - **Columns:** 3 o 4 columnas (recomendado: 3)
   - **Limit:** 6-9 posts (recomendado: 9)
   - **Size:** Medium o Large
   - **Theme:** Personaliza colores para que coincidan con tu sitio
     - Color principal: #003D7A (azul institucional)
     - Color de fondo: #F5F5F5

5. **Obtén el código:**
   - Haz clic en "Get Code" o "Embed Code"
   - Se mostrará un código similar a:
     ```html
     <script src="https://snapwidget.com/js/snapwidget.js"></script>
     <iframe src="https://snapwidget.com/embed/..." class="snapwidget-widget" allowtransparency="true" frameborder="0" scrolling="no" style="border:none; overflow:hidden; width:100%;"></iframe>
     ```

6. **Pega el código en `noticias.html`:**
   - Abre `noticias.html` en tu editor
   - Busca la línea que dice: `<!-- Pega aquí el código del widget de Instagram -->`
   - Pega el código **justo después** de ese comentario (dentro del div `#instagram-feed`)
   - **Importante:** Elimina o comenta el bloque `<div class="social-feed-placeholder">` que está dentro del mismo div

**Ejemplo de código final:**
```html
<div class="social-feed-widget" id="instagram-feed">
  <!-- Pega aquí el código del widget de Instagram -->
  <script src="https://snapwidget.com/js/snapwidget.js"></script>
  <iframe src="https://snapwidget.com/embed/..." class="snapwidget-widget" allowtransparency="true" frameborder="0" scrolling="no" style="border:none; overflow:hidden; width:100%;"></iframe>
</div>
```

**Alternativas:**
- **Tagembed:** https://tagembed.com/es/instagram-widget/
- **EmbedSocial:** https://embedsocial.com/es/instagram-widget/

---

### 💼 LinkedIn Feed

#### Opción A: Elfsight (Recomendado - Versión gratuita disponible)

**Pasos:**

1. **Accede a Elfsight:**
   - URL: https://elfsight.com/es/linkedin-feed-widget/
   - Crea una cuenta gratuita o inicia sesión

2. **Crea un nuevo widget:**
   - Haz clic en "Create Widget" o "Get Started"
   - Selecciona "LinkedIn Feed Widget"

3. **Conecta tu página de LinkedIn:**
   - Autoriza Elfsight para acceder a tu página de LinkedIn
   - Selecciona la página correcta de FARMAVET
   - **Nota:** Debe ser una página de empresa, no un perfil personal

4. **Personaliza el widget:**
   - **Number of posts:** 5-10 posts (recomendado: 6)
   - **Layout:** Feed vertical
   - **Colors:** Personaliza para que coincidan con tu sitio
   - **Show:** Posts, images, descriptions
   - **Filter:** Opcional (puedes filtrar por hashtags o palabras clave)

5. **Obtén el código:**
   - Haz clic en "Get Code" o "Publish"
   - Se mostrará un código similar a:
     ```html
     <script src="https://apps.elfsight.com/p/platform.js" defer></script>
     <div class="elfsight-app-xxxx-xxxx-xxxx"></div>
     ```

6. **Pega el código en `noticias.html`:**
   - Abre `noticias.html` en tu editor
   - Busca la línea que dice: `<!-- Pega aquí el código del widget de LinkedIn -->`
   - Pega el código **justo después** de ese comentario (dentro del div `#linkedin-feed`)
   - **Importante:** Elimina o comenta el bloque `<div class="social-feed-placeholder">` que está dentro del mismo div

**Ejemplo de código final:**
```html
<div class="social-feed-widget" id="linkedin-feed">
  <!-- Pega aquí el código del widget de LinkedIn -->
  <script src="https://apps.elfsight.com/p/platform.js" defer></script>
  <div class="elfsight-app-xxxx-xxxx-xxxx"></div>
</div>
```

**Alternativas:**
- **Taggbox:** https://taggbox.com/es/blog/embed-linkedin-feed-on-website/
- **Mirror App:** https://mirror-app.com/linkedin-feed/es

---

### ✅ Verificación después de la instalación

1. **Abre `noticias.html` en tu navegador**
2. **Navega a la sección "Síguenos en redes sociales"**
3. **Verifica que:**
   - Los feeds se muestran correctamente
   - Los posts más recientes aparecen
   - El diseño se adapta bien en móvil y desktop
   - Los enlaces funcionan correctamente

4. **Si algo no funciona:**
   - Revisa que el código esté dentro del div correcto
   - Verifica que no haya conflictos con otros scripts
   - Asegúrate de que el acceso a las cuentas de redes sociales esté autorizado

---

## 2. ACTUALIZACIÓN DEL BLOG/CMS

### 📍 Ubicación
**Archivo:** `noticias.html`  
**Sección:** "Blog y publicaciones" (línea ~280)

### 📝 Estado Actual
Actualmente muestra 4 categorías con enlaces a "#" (sin destino).

### 🔄 Opciones para Implementar

#### Opción A: Sistema de Gestión de Contenidos (CMS)

**Recomendado:** WordPress, Strapi, o Contentful

**Pasos:**

1. **Elige una plataforma:**
   - **WordPress:** Más fácil de usar, requiere hosting
   - **Strapi:** Headless CMS, más técnico
   - **Contentful:** Basado en la nube, más costoso

2. **Configura el CMS:**
   - Crea categorías: Investigación, Servicios, Docencia, CASA-OMSA
   - Configura el sistema de publicaciones
   - Conecta con tu sitio web mediante API o plugins

3. **Actualiza `noticias.html`:**
   - Reemplaza las cards estáticas por contenido dinámico
   - Integra el código para cargar posts desde el CMS

#### Opción B: Blog Estático (Jekyll, Hugo, etc.)

**Para sitios estáticos:**

1. **Crea un sistema de archivos para posts:**
   ```
   /blog
     /investigacion
       post-1.md
       post-2.md
     /servicios
       post-1.md
     ...
   ```

2. **Genera las páginas dinámicamente con un generador de sitios estáticos**

#### Opción C: Manual (Temporal)

**Mientras implementas un CMS:**

1. **Crea archivos HTML individuales:**
   - `blog/investigacion.html`
   - `blog/servicios.html`
   - `blog/docencia.html`
   - `blog/casa-omsa.html`

2. **Actualiza los enlaces en `noticias.html`:**
   - Cambia `href="#"` por las rutas correctas
   - Ejemplo: `href="blog/investigacion.html"`

---

## 3. DOMINIO DEL SITIO WEB

### 🌐 Dominio Configurado
**Dominio actual en el código:** `https://www.laboratoriofarmavet.cl`

### ✅ Verificaciones Pendientes

Cuando el sitio esté en producción, verifica:

1. **HTTPS está habilitado:**
   - El sitio debe cargar con `https://` (no `http://`)
   - Certificado SSL válido

2. **Todos los meta tags tienen la URL correcta:**
   - Verifica en todas las páginas que los `og:url` y `twitter:url` apunten al dominio correcto
   - Archivos a revisar: `index.html`, `servicios.html`, `casa-omsa.html`, etc.

3. **Schema.org tiene la URL correcta:**
   - En `index.html`, verifica que el campo `"url"` en el Schema.org sea correcto

4. **Enlaces internos funcionan:**
   - Todos los enlaces relativos deben funcionar correctamente
   - Ejemplo: `href="servicios.html"` debe funcionar tanto localmente como en producción

---

## 4. VERIFICACIÓN DE METADATA SEO

### ✅ Lo que ya está implementado

- ✅ Meta tags Open Graph en todas las páginas
- ✅ Twitter Cards en todas las páginas
- ✅ Schema.org en la página principal (`index.html`)
- ✅ Meta descriptions optimizadas

### 🔍 Verificaciones Pendientes

Una vez que el sitio esté en producción, verifica:

1. **Facebook Debugger:**
   - URL: https://developers.facebook.com/tools/debug/
   - Ingresa: `https://www.laboratoriofarmavet.cl`
   - Verifica que las imágenes y descripciones se muestren correctamente
   - Si no se ve bien, haz clic en "Scrape Again" para refrescar

2. **Twitter Card Validator:**
   - URL: https://cards-dev.twitter.com/validator
   - Ingresa: `https://www.laboratoriofarmavet.cl`
   - Verifica que las tarjetas se muestren correctamente

3. **Google Rich Results Test:**
   - URL: https://search.google.com/test/rich-results
   - Ingresa: `https://www.laboratoriofarmavet.cl`
   - Verifica que el Schema.org se lea correctamente

4. **Google Search Console:**
   - Registra tu sitio en: https://search.google.com/search-console
   - Verifica la propiedad del sitio
   - Envía el sitemap.xml (si existe)

---

## 5. OTROS ELEMENTOS PENDIENTES

### 📧 Formulario de Contacto

**Ubicación:** `contacto.html`

**Estado actual:** El formulario está implementado pero necesita backend para procesar envíos.

**Opciones para implementar:**

1. **Formspree (Gratuito para uso básico):**
   - URL: https://formspree.io
   - Crea una cuenta
   - Agrega el action del formulario
   - Ejemplo: `action="https://formspree.io/f/YOUR_FORM_ID"`

2. **EmailJS (Gratuito):**
   - URL: https://www.emailjs.com
   - Configura para enviar emails directamente desde el frontend

3. **Backend propio:**
   - Implementa un servidor (Node.js, Python Flask, etc.)
   - Procesa los formularios y envía emails

### 🗺️ Mapa de Ubicación

**Ubicación:** `contacto.html` (línea ~138)

**Estado actual:** Google Maps está embebido, pero puede necesitar ajustes.

**Verificaciones:**
- Verifica que el mapa muestre la dirección correcta
- Coordenadas: Av. Santa Rosa 11735, La Pintana, Santiago, Chile
- Si el mapa no se muestra bien, actualiza el código de embed de Google Maps

### 📱 Información de Contacto

**Ubicación:** Varios archivos (footer y página de contacto)

**Actualizar cuando tengas:**
- ✅ Teléfono completo (actualmente muestra: +56 2 2978 XXXX)
- ✅ Horario de atención (no está especificado en todos los lugares)
- ✅ Email de contacto verificado

### 🖼️ Imágenes Optimizadas

**Ubicación:** `assets/images/`

**Recomendaciones futuras:**
- Convertir imágenes grandes a formato WebP para mejor rendimiento
- Optimizar imágenes de hero para carga más rápida
- Agregar imágenes reales del laboratorio (equipos, equipo humano, instalaciones)

### 🔗 Enlaces del Footer

**Ubicación:** Footer en todas las páginas

**Verificaciones:**
- Verifica que todos los enlaces funcionen
- Verifica que los enlaces a redes sociales apunten a las cuentas correctas
- Asegúrate de que los enlaces externos abran en nueva pestaña (`target="_blank"`)

---

## 📝 NOTAS IMPORTANTES

### ⚠️ Antes de hacer cambios importantes

1. **Haz backup del sitio**
2. **Prueba en un entorno de desarrollo** antes de publicar
3. **Verifica en múltiples navegadores** (Chrome, Firefox, Safari, Edge)
4. **Verifica en dispositivos móviles** antes de publicar

### 🔒 Seguridad

- No expongas credenciales en el código
- Usa variables de entorno para información sensible
- Verifica que los formularios tengan protección contra spam

### 📊 Analytics

**Considera agregar:**
- Google Analytics para seguimiento de visitantes
- Google Tag Manager para gestión de tags
- Facebook Pixel si planeas hacer publicidad en Facebook

---

## 🆘 SOPORTE

Si encuentras problemas o necesitas ayuda:

1. **Revisa la consola del navegador** (F12) para errores de JavaScript
2. **Verifica que los archivos estén guardados correctamente**
3. **Limpia la caché del navegador** (Ctrl + Shift + R)
4. **Verifica que los servicios de terceros (widgets) estén funcionando**

---

## 📅 CHECKLIST DE ACTUALIZACIÓN

Usa este checklist cuando hagas actualizaciones:

- [ ] Feeds de Instagram configurados y funcionando
- [ ] Feeds de LinkedIn configurados y funcionando
- [ ] Blog/CMS implementado (o enlaces actualizados)
- [ ] Dominio verificado y funcionando
- [ ] Metadata SEO verificada en Facebook Debugger
- [ ] Metadata SEO verificada en Twitter Card Validator
- [ ] Metadata SEO verificada en Google Rich Results Test
- [ ] Formulario de contacto funcionando
- [ ] Información de contacto actualizada (teléfono, horario)
- [ ] Mapa de ubicación verificado
- [ ] Enlaces del footer verificados
- [ ] Sitio probado en múltiples navegadores
- [ ] Sitio probado en dispositivos móviles
- [ ] Backup del sitio realizado

---

**Última actualización:** 15 de enero de 2025  
**Versión del documento:** 1.0

