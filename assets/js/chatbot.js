/**
 * Chatbot inteligente para búsqueda de metodologías analíticas
 * Versión 1.0 - Búsqueda semántica avanzada
 */

class MetodologiasChatbot {
    constructor() {
        this.isOpen = false;
        this.metodologias = [];
        this.lastResults = null; // Guardar último resultado para preguntas de seguimiento
        this.lastQuery = null;
        this.conversationHistory = [];
        this.loadAttempts = 0;
        this.maxLoadAttempts = 3;
        this.init();
    }

    init() {
        this.createChatbotUI();
        this.loadMetodologias();
        this.setupEventListeners();
    }

    createChatbotUI() {
        // Botón flotante
        const chatbotButton = document.createElement('button');
        chatbotButton.id = 'chatbot-toggle';
        chatbotButton.className = 'chatbot-toggle';
        chatbotButton.setAttribute('aria-label', 'Abrir chatbot de búsqueda');
        chatbotButton.innerHTML = '<i class="bi bi-chat-dots"></i>';
        document.body.appendChild(chatbotButton);

        // Ventana del chatbot
        const chatbotWindow = document.createElement('div');
        chatbotWindow.id = 'chatbot-window';
        chatbotWindow.className = 'chatbot-window';
        chatbotWindow.innerHTML = `
            <div class="chatbot-header">
                <div class="chatbot-header-content">
                    <i class="bi bi-robot"></i>
                    <div>
                        <h3>FARMA</h3>
                        <p class="chatbot-subtitle">Asistente virtual de FARMAVET</p>
                    </div>
                </div>
                <button class="chatbot-close" id="chatbot-close" aria-label="Cerrar chatbot">
                    <i class="bi bi-x-lg"></i>
                </button>
            </div>
            <div class="chatbot-messages" id="chatbot-messages">
                <div class="chatbot-message bot-message">
                    <div class="message-content">
                        <p>¡Hola! Soy FARMA, tu asistente virtual de FARMAVET. Estoy aquí para ayudarte con tus consultas sobre metodologías analíticas, contacto, ubicación, horarios, formularios y más.</p>
                        <p>Puedes preguntarme sobre:</p>
                        <ul class="chatbot-examples">
                            <li>Metodologías analíticas (ej: "¿hacen análisis de diquat?")</li>
                            <li>Contacto y ubicación (ej: "¿cuál es la dirección?")</li>
                            <li>Horarios de atención</li>
                            <li>Formulario de consultas (ej: "¿cómo envío una consulta?")</li>
                            <li>Preguntas frecuentes</li>
                        </ul>
                        <p>¿En qué puedo ayudarte?</p>
                    </div>
                </div>
            </div>
            <div class="chatbot-input-container">
                <div class="chatbot-input-wrapper">
                    <input 
                        type="text" 
                        id="chatbot-input" 
                        class="chatbot-input" 
                        placeholder="Escribe tu consulta aquí..."
                        autocomplete="off"
                    />
                    <button id="chatbot-send" class="chatbot-send" aria-label="Enviar mensaje">
                        <i class="bi bi-send-fill"></i>
                    </button>
                </div>
            </div>
        `;
        document.body.appendChild(chatbotWindow);
    }

    async loadMetodologias() {
        // Incrementar contador de intentos
        this.loadAttempts++;
        
        try {
            // Siempre cargar desde la API - esto funciona en todas las páginas
            const apiUrl = '/api/metodologias';
            console.log(`🔄 Chatbot: Intentando cargar metodologías desde ${apiUrl} (intento ${this.loadAttempts}/${this.maxLoadAttempts})`);
            
            const response = await fetch(apiUrl, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                cache: 'no-cache'
            });
            
            console.log(`📡 Chatbot: Respuesta recibida - Status: ${response.status}, OK: ${response.ok}`);
            
            if (response.ok) {
                try {
                    const data = await response.json();
                    console.log(`📦 Chatbot: Datos recibidos:`, typeof data, Array.isArray(data) ? `Array de ${data.length} elementos` : 'No es array');
                    
                    if (Array.isArray(data)) {
                        if (data.length > 0) {
                            this.metodologias = data;
                            console.log(`✅ Chatbot: ${this.metodologias.length} metodologías cargadas desde API`);
                            this.loadAttempts = 0; // Reset contador en caso de éxito
                            return;
                        } else {
                            console.warn('⚠️ Chatbot: La API devolvió un array vacío. Puede que no haya metodologías activas.');
                            // Si no hay metodologías, intentar fallback solo en página de servicios
                            if (document.querySelector('#tabla-metodologias')) {
                                console.log('🔄 Chatbot: Intentando fallback DOM...');
                                this.loadFromDOM();
                                return;
                            }
                        }
                    } else {
                        console.error('❌ Chatbot: La API no devolvió un array válido. Tipo recibido:', typeof data, data);
                    }
                } catch (jsonError) {
                    console.error('❌ Chatbot: Error al parsear JSON de la respuesta:', jsonError);
                    const text = await response.text();
                    console.error('❌ Chatbot: Respuesta recibida (texto):', text.substring(0, 500));
                }
            } else {
                // Intentar leer el mensaje de error
                let errorText = '';
                try {
                    const errorData = await response.json();
                    errorText = JSON.stringify(errorData);
                } catch (e) {
                    errorText = await response.text();
                }
                console.error(`❌ Chatbot: Error HTTP ${response.status}:`, response.statusText);
                console.error(`❌ Chatbot: Detalles del error:`, errorText);
            }
        } catch (error) {
            console.error('❌ Chatbot: Error de red al cargar metodologías desde API:', error);
            console.error('❌ Chatbot: Detalles del error:', error.message, error.stack);
            
            // Intentar de nuevo si no hemos alcanzado el límite
            if (this.loadAttempts < this.maxLoadAttempts) {
                const delay = this.loadAttempts * 1000; // Delay progresivo: 1s, 2s, 3s
                console.log(`🔄 Chatbot: Reintentando carga en ${delay/1000} segundos... (intento ${this.loadAttempts}/${this.maxLoadAttempts})`);
                setTimeout(() => {
                    this.loadMetodologias();
                }, delay);
                return;
            }
        }
        
        // Si llegamos aquí después de todos los intentos, usar fallback
        if (this.loadAttempts >= this.maxLoadAttempts) {
            console.warn(`⚠️ Chatbot: Se agotaron los intentos (${this.maxLoadAttempts}). Intentando fallback...`);
            
            // Intentar fallback solo en la página de servicios (donde existe la tabla)
            if (document.querySelector('#tabla-metodologias')) {
                console.warn('⚠️ Chatbot: Usando fallback DOM (solo disponible en página de servicios)');
                this.loadFromDOM();
            } else {
                console.error('❌ Chatbot: No se pudieron cargar metodologías. La API no está disponible y no hay tabla en esta página.');
                this.metodologias = [];
                // Mostrar mensaje al usuario si intenta buscar
                this.showErrorMessage = true;
            }
        }
    }

    loadFromDOM() {
        // Fallback: cargar metodologías desde la tabla en el DOM (solo en página de servicios)
        const rows = document.querySelectorAll('#tabla-metodologias tbody tr');
        if (rows.length === 0) {
            console.warn('⚠️ Chatbot: No se encontró tabla de metodologías en el DOM');
            this.metodologias = [];
            return;
        }
        
        this.metodologias = Array.from(rows).map(row => {
            const cells = row.querySelectorAll('td');
            return {
                nombre: cells[0]?.textContent.trim() || '',
                nombre_en: '',
                analito: cells[1]?.textContent.trim() || '',
                analito_en: '',
                matriz: cells[2]?.textContent.trim() || '',
                matriz_en: '',
                tecnica: cells[3]?.textContent.trim() || '',
                tecnica_en: '',
                lod: cells[4]?.textContent.trim() || '',
                loq: cells[5]?.textContent.trim() || '',
                acreditada: cells[6]?.textContent.includes('Sí') || false,
                categoria: row.dataset.categoria || ''
            };
        });
        console.log(`⚠️ Chatbot: ${this.metodologias.length} metodologías cargadas desde DOM (fallback)`);
    }

    setupEventListeners() {
        const toggle = document.getElementById('chatbot-toggle');
        const close = document.getElementById('chatbot-close');
        const send = document.getElementById('chatbot-send');
        const input = document.getElementById('chatbot-input');

        toggle?.addEventListener('click', () => this.toggle());
        close?.addEventListener('click', () => this.close());
        send?.addEventListener('click', () => this.sendMessage());
        
        input?.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        input?.addEventListener('input', (e) => {
            // Sugerencias deshabilitadas - usando búsqueda inteligente
        });
    }

    toggle() {
        this.isOpen = !this.isOpen;
        const window = document.getElementById('chatbot-window');
        if (this.isOpen) {
            window.classList.add('open');
            document.getElementById('chatbot-input')?.focus();
        } else {
            window.classList.remove('open');
        }
    }

    close() {
        this.isOpen = false;
        document.getElementById('chatbot-window')?.classList.remove('open');
    }

    async sendMessage() {
        const input = document.getElementById('chatbot-input');
        const query = input?.value.trim();
        if (!query) return;

        // Agregar mensaje del usuario
        this.addMessage(query, 'user');
        input.value = '';

        // Mostrar "escribiendo..."
        const typingId = this.showTyping();

        // Procesar consulta
        setTimeout(async () => {
            this.hideTyping(typingId);
            
            // Detectar si la consulta es sobre metodologías o información general
            const queryLower = query.toLowerCase();
            const isGeneralQuery = /\b(horario|horarios|dirección|direccion|ubicación|ubicacion|ubicados|ubicadas|donde|dónde|se encuentran|contacto|email|correo|teléfono|telefono|formulario|envío|envio|consultas|preguntas frecuentes|faq|atencion|atención|agendar|reunión|reunion|solicitar|solicitud|informe|informes|ingles|english|idioma|lang)\b/i.test(query);
            
            // Si es una consulta general (no sobre metodologías), ir directamente a Perplexity
            if (isGeneralQuery) {
                await this.searchWithPerplexity(query, false, true); // true = es consulta general
                return;
            }
            
            // Para consultas sobre metodologías, buscar localmente primero usando el query procesado
            const results = await this.searchMetodologias(searchQuery);
            
            // Si encuentra resultados locales, mostrarlos
            if (results.length > 0) {
                await this.showResults(query, results);
            } else {
                // Si no encuentra localmente, usar Perplexity (mostrará mensaje apropiado)
                await this.showResults(query, results);
                // showResults ya llama a searchWithPerplexity si no hay resultados
            }
        }, 500);
    }

    addMessage(content, type = 'bot') {
        const messages = document.getElementById('chatbot-messages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `chatbot-message ${type}-message`;
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        
        if (typeof content === 'string') {
            // Si es string y parece HTML (contiene tags), renderizar como HTML
            if (content.includes('<p>') || content.includes('<strong>') || content.includes('<div>')) {
                contentDiv.innerHTML = content;
            } else {
                // Si es texto plano, escapar HTML y envolver en <p>
                contentDiv.innerHTML = `<p>${this.escapeHtml(content)}</p>`;
            }
        } else {
            // Si ya es HTML formateado, renderizar directamente
            contentDiv.innerHTML = content;
        }
        
        messageDiv.appendChild(contentDiv);
        messages.appendChild(messageDiv);
        messages.scrollTop = messages.scrollHeight;
    }

    showTyping() {
        const messages = document.getElementById('chatbot-messages');
        const typingDiv = document.createElement('div');
        typingDiv.className = 'chatbot-message bot-message typing';
        typingDiv.id = 'chatbot-typing';
        typingDiv.innerHTML = `
            <div class="message-content">
                <div class="typing-indicator">
                    <span></span><span></span><span></span>
                </div>
            </div>
        `;
        messages.appendChild(typingDiv);
        messages.scrollTop = messages.scrollHeight;
        return 'chatbot-typing';
    }

    hideTyping(id) {
        const typing = document.getElementById(id);
        if (typing) typing.remove();
    }

    normalizeText(text) {
        // Normalizar texto: quitar acentos, convertir a minúsculas, quitar caracteres especiales
        if (!text) return '';
        return text.toString()
            .toLowerCase()
            .normalize('NFD')
            .replace(/[\u0300-\u036f]/g, '') // Quitar acentos
            .replace(/[^\w\s]/g, ' ') // Reemplazar caracteres especiales con espacios
            .replace(/\s+/g, ' ') // Normalizar espacios
            .trim();
    }
    
    // Capitalizar texto (primera letra mayúscula, resto minúsculas)
    capitalize(text) {
        if (!text) return '';
        const str = text.toString();
        return str.charAt(0).toUpperCase() + str.slice(1).toLowerCase();
    }
    
    // Formatear lista de analitos de forma natural con capitalización correcta
    formatAnalitos(analitos) {
        if (!analitos || analitos.length === 0) return 'varios analitos';
        
        // Capitalizar cada analito correctamente (primera letra mayúscula)
        const analitosCapitalizados = analitos.map(a => {
            if (!a) return '';
            // Si contiene guiones (como "EPI-TETRACICLINA"), capitalizar cada palabra
            if (a.includes('-')) {
                return a.split('-').map(word => this.capitalize(word)).join('-');
            }
            return this.capitalize(a);
        });
        
        if (analitosCapitalizados.length === 1) return analitosCapitalizados[0];
        if (analitosCapitalizados.length === 2) return `${analitosCapitalizados[0]} y ${analitosCapitalizados[1]}`;
        if (analitosCapitalizados.length <= 5) {
            const ultimos = analitosCapitalizados.slice(-1)[0];
            const anteriores = analitosCapitalizados.slice(0, -1).join(', ');
            return `${anteriores} y ${ultimos}`;
        }
        // Si hay más de 5, mostrar los primeros 5 y decir "y X más"
        const primeros = analitosCapitalizados.slice(0, 5).join(', ');
        const restantes = analitosCapitalizados.length - 5;
        return `${primeros} y ${restantes} más`;
    }
    
    // Extraer número de un string como "30 ng/g" -> 30
    extractNumber(text) {
        if (!text) return null;
        const match = text.toString().match(/[\d.]+/);
        if (match) {
            const num = parseFloat(match[0]);
            return isNaN(num) ? null : num;
        }
        return null;
    }
    
    // Formatear rango de valores (min-max)
    formatRange(values) {
        if (!values || values.length === 0) return null;
        const uniqueValues = [...new Set(values)].sort((a, b) => a - b);
        if (uniqueValues.length === 0) return null;
        if (uniqueValues.length === 1) return String(uniqueValues[0]);
        const min = Math.min(...uniqueValues);
        const max = Math.max(...uniqueValues);
        if (min === max) return String(min);
        // Incluir la unidad si está disponible (ej: "30-50 ng/g")
        return `${min}-${max}`;
    }
    
    // Función de distancia de Levenshtein simplificada (para typos)
    levenshteinDistance(str1, str2) {
        const len1 = str1.length;
        const len2 = str2.length;
        
        if (len1 === 0) return len2;
        if (len2 === 0) return len1;
        
        const matrix = [];
        for (let i = 0; i <= len1; i++) {
            matrix[i] = [i];
        }
        for (let j = 0; j <= len2; j++) {
            matrix[0][j] = j;
        }
        
        for (let i = 1; i <= len1; i++) {
            for (let j = 1; j <= len2; j++) {
                const cost = str1[i - 1] === str2[j - 1] ? 0 : 1;
                matrix[i][j] = Math.min(
                    matrix[i - 1][j] + 1,     // Eliminación
                    matrix[i][j - 1] + 1,     // Inserción
                    matrix[i - 1][j - 1] + cost // Sustitución
                );
            }
        }
        
        return matrix[len1][len2];
    }
    
    // Verificar si dos strings son similares (considerando typos)
    isSimilar(str1, str2, threshold = 2) {
        const normalized1 = this.normalizeText(str1);
        const normalized2 = this.normalizeText(str2);
        
        // Si son iguales después de normalizar, son similares
        if (normalized1 === normalized2) return true;
        
        // Si uno contiene al otro, son similares
        if (normalized1.includes(normalized2) || normalized2.includes(normalized1)) {
            return true;
        }
        
        // Si la distancia de Levenshtein es pequeña (typo de 1-2 caracteres)
        const distance = this.levenshteinDistance(normalized1, normalized2);
        const maxLen = Math.max(normalized1.length, normalized2.length);
        
        // Permitir hasta 2 errores o 15% de diferencia para strings largos
        if (distance <= threshold || (maxLen > 6 && distance / maxLen <= 0.15)) {
            return true;
        }
        
        return false;
    }

    extractKeywords(query) {
        // Extraer palabras clave de la consulta, eliminando palabras comunes
        const stopWords = ['el', 'la', 'los', 'las', 'un', 'una', 'de', 'en', 'para', 'con', 'por', 
                          'que', 'qué', 'hacen', 'hace', 'busca', 'buscar', 'metodos', 'metodologias',
                          'metodología', 'metodologías', 'analisis', 'análisis', 'en', 'de', 'del',
                          'tienen', 'tiene', 'tener', 'metodo', 'metodo', 'uso', 'usan', 'usa',
                          'tecnica', 'tecnicas', 'tecnología', 'tecnologías'];
        
        const normalized = this.normalizeText(query);
        // Extraer palabras de 3+ caracteres, incluyendo términos químicos
        const words = normalized.split(/\s+/).filter(w => w.length >= 3);
        
        // Filtrar stop words pero mantener términos químicos importantes
        const keywords = words.filter(word => !stopWords.includes(word));
        
        // Si no hay keywords pero hay palabras, tomar la primera palabra significativa
        if (keywords.length === 0 && words.length > 0) {
            // Tomar la última palabra (probablemente el término buscado)
            return [words[words.length - 1]];
        }
        
        return keywords;
    }

    async searchMetodologias(query) {
        const normalizedQuery = this.normalizeText(query);
        const keywords = this.extractKeywords(query);
        
        // Diccionario de sinónimos y términos relacionados (sin acentos)
        const synonyms = {
            'tetraciclina': ['tetraciclinas', 'tetracilinas', 'tetraciclina', 'tetraciclinas', 'tetraciclina', 'tetraciclina', 'oxitetraciclina', 'clortetraciclina', 'doxiciclina', 'minociclina'],
            'tetraciclinas': ['tetraciclina', 'tetracilinas', 'oxitetraciclina', 'epi-tetraciclina', 'clortetraciclina', 'epi-oxitetraciclina', 'epi-clortetraciclina'],
            'tetracilinas': ['tetraciclinas', 'tetraciclina', 'oxitetraciclina', 'clortetraciclina'],
            'macrolido': ['macrolidos', 'macrolido', 'eritromicina', 'tilmicosina', 'tilosina', 'espiramicina', 'tulatromicina', 'azitromicina'],
            'macrolidos': ['macrolido', 'eritromicina', 'tilmicosina', 'tilosina', 'espiramicina', 'tulatromicina', 'azitromicina'],
            'aminoglucosido': ['aminoglucosidos', 'aminoglucosido', 'estreptomicina', 'neomicina', 'gentamicina', 'kanamicina', 'espectinomicina', 'apramicina'],
            'aminoglucosidos': ['aminoglucosido', 'estreptomicina', 'neomicina', 'gentamicina', 'kanamicina', 'espectinomicina', 'apramicina'],
            'beta-lactamico': ['betalactamico', 'betalactamicos', 'beta-lactamicos', 'penicilina', 'ampicilina', 'amoxicilina', 'cefalosporina', 'ceftiofur'],
            'betalactamico': ['beta-lactamico', 'betalactamicos', 'beta-lactamicos', 'penicilina', 'ampicilina', 'amoxicilina', 'cefalosporina', 'ceftiofur'],
            'betalactamicos': ['betalactamico', 'beta-lactamico', 'beta-lactamicos', 'penicilina', 'ampicilina', 'amoxicilina', 'cefalosporina', 'ceftiofur'],
            'antibiotico': ['antimicrobiano', 'antimicrobianos', 'fluoroquinolona', 'tetraciclina', 'sulfonamida', 'macrolido', 'aminoglucosido', 'betalactamico'],
            'antibioticos': ['antimicrobiano', 'antimicrobianos', 'fluoroquinolona', 'tetraciclinas', 'sulfonamidas', 'macrolidos', 'aminoglucosidos', 'betalactamicos'],
            'micotoxina': ['aflatoxina', 'ocratoxina', 'fumonisina', 'zearalenona', 'deoxinivalenol', 'toxina t-2', 'patulina'],
            'aflatoxina': ['aflatoxinas', 'aflatoxina b1', 'aflatoxina b2', 'aflatoxina g1', 'aflatoxina g2', 'aflatoxinas'],
            'pesticida': ['plaguicida', 'organoclorado', 'organofosforado', 'diquat', 'paraquat', 'glifosato', 'herbicida', 'insecticida', 'fungicida'],
            'salmon': ['salmones', 'salmonidos', 'salmonideos', 'trucha', 'truchas', 'pez', 'peces', 'hidrobiologico', 'hidrobiológico', 'productos hidrobiologicos'],
            'carne': ['carnes', 'bovino', 'bovina', 'porcino', 'porcina', 'cerdo', 'cerdos', 'ave', 'aves', 'pollo', 'pollos', 'productos pecuarios', 'pecuarios', 'producto animal'],
            'leche': ['lacteo', 'lacteos', 'dairy', 'producto lacteo'],
            'lcmsms': ['lc-ms/ms', 'lc-ms', 'lcms', 'cromatografia liquida', 'espectrometria de masas', 'liquid chromatography'],
            'gcms': ['gc-ms', 'cromatografia de gases', 'gas chromatography'],
            'hplc': ['cromatografia liquida', 'high performance liquid chromatography', 'hplc-dad', 'hplc-fl'],
            'metodo': ['metodologia', 'metodologias', 'tecnica', 'tecnicas', 'analisis', 'ensayo', 'ensayos', 'metodos'],
            'productos pecuarios': ['producto pecuario', 'pecuarios', 'carne', 'carnes', 'leche', 'huevos', 'huevo', 'productos de origen animal'],
            'productos hidrobiologicos': ['producto hidrobiologico', 'hidrobiologicos', 'salmon', 'salmones', 'trucha', 'truchas', 'pez', 'peces'],
            'diquat': ['diquat', 'paraquat', 'herbicida', 'bipiridilo'],
            'amprolio': ['amprolio', 'amprolium', 'anticoccidiano', 'antiparasitario']
        };
        
        // Diccionario de correcciones de typos comunes
        const typoCorrections = {
            'tetracilinas': 'tetraciclinas',
            'tetracilina': 'tetraciclina',
            'tetraciclinas': 'tetraciclinas',
            'macrolidos': 'macrolidos',
            'macrolido': 'macrolidos',
            'aminoglucosidos': 'aminoglucosidos',
            'aminoglucosido': 'aminoglucosidos',
            'betalactamicos': 'betalactamicos',
            'betalactamico': 'betalactamicos'
        };

        // Expandir búsqueda con sinónimos
        const expandedTerms = new Set();
        expandedTerms.add(normalizedQuery);
        keywords.forEach(kw => {
            expandedTerms.add(kw);
            // Corregir typos comunes
            const corrected = typoCorrections[kw] || kw;
            if (corrected !== kw) {
                expandedTerms.add(corrected);
            }
        });
        
        // Para cada keyword, buscar en sinónimos y expandir
        for (const keyword of keywords) {
            // Agregar el keyword original
            expandedTerms.add(keyword);
            
            // Buscar coincidencias exactas o parciales en las claves de sinónimos
            for (const [key, values] of Object.entries(synonyms)) {
                const normalizedKey = this.normalizeText(key);
                
                // Si el keyword coincide con la clave o viceversa
                if (keyword === normalizedKey || keyword.includes(normalizedKey) || normalizedKey.includes(keyword)) {
                    // Agregar todos los sinónimos
                    values.forEach(v => expandedTerms.add(this.normalizeText(v)));
                    expandedTerms.add(normalizedKey);
                }
                
                // Si el keyword coincide con alguno de los valores de sinónimos
                for (const value of values) {
                    const normalizedValue = this.normalizeText(value);
                    if (keyword === normalizedValue || keyword.includes(normalizedValue) || normalizedValue.includes(keyword)) {
                        // Agregar la clave y todos sus sinónimos
                        expandedTerms.add(normalizedKey);
                        values.forEach(v => expandedTerms.add(this.normalizeText(v)));
                    }
                }
            }
        }
        
        // Convertir Set a Array
        const expandedTermsArray = Array.from(expandedTerms);

        // Búsqueda con sistema de scoring/prioridad
        const scoredResults = this.metodologias.map(met => {
            let score = 0;
            const maxScore = 1000;
            
            // Normalizar campos individuales para búsqueda específica
            const nombreNorm = this.normalizeText(met.nombre || '');
            const nombreEnNorm = this.normalizeText(met.nombre_en || '');
            const analitoNorm = this.normalizeText(met.analito || '');
            const analitoEnNorm = this.normalizeText(met.analito_en || '');
            const matrizNorm = this.normalizeText(met.matriz || '');
            const tecnicaNorm = this.normalizeText(met.tecnica || '');
            
            // Crear un texto de búsqueda combinando todos los campos
            const searchFields = [
                nombreNorm, nombreEnNorm, analitoNorm, analitoEnNorm,
                matrizNorm, this.normalizeText(met.matriz_en || ''),
                tecnicaNorm, this.normalizeText(met.tecnica_en || ''),
                this.normalizeText(met.categoria || '')
            ].join(' ');
            
            // Normalizar también la query completa
            const cleanQuery = normalizedQuery.replace(/[?¿!¡.,;:]/g, '').trim();
            
            // PRIORIDAD 1: Coincidencia exacta en analito (máxima prioridad)
            // Contador de keywords que coinciden para priorizar coincidencias múltiples
            let keywordsMatched = 0;
            let keywordsInAnalito = 0;
            let keywordsInNombre = 0;
            let keywordsInMatriz = 0;
            
            if (keywords.length > 0) {
                for (const keyword of keywords) {
                    const cleanKeyword = keyword.replace(/[?¿!¡.,;:]/g, '').trim();
                    if (cleanKeyword.length >= 3) {
                        let keywordMatched = false;
                        
                        // Coincidencia exacta en analito
                        if (analitoNorm === cleanKeyword || analitoEnNorm === cleanKeyword) {
                            score += maxScore * 2; // Bonus extra por coincidencia exacta
                            keywordsMatched++;
                            keywordsInAnalito++;
                            keywordMatched = true;
                            continue;
                        }
                        
                        // Coincidencia como palabra completa en analito
                        const analitoRegex = new RegExp(`\\b${cleanKeyword.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\b`, 'i');
                        if (analitoRegex.test(analitoNorm) || analitoRegex.test(analitoEnNorm)) {
                            score += maxScore * 1.5;
                            keywordsMatched++;
                            keywordsInAnalito++;
                            keywordMatched = true;
                            continue;
                        }
                        
                        // Coincidencia flexible con typos en analito
                        const analitoWords = (analitoNorm + ' ' + analitoEnNorm).split(/\s+/).filter(w => w.length >= 3);
                        for (const word of analitoWords) {
                            if (this.isSimilar(cleanKeyword, word, 2)) {
                                score += maxScore * 1.2;
                                keywordsMatched++;
                                keywordsInAnalito++;
                                keywordMatched = true;
                                break;
                            }
                        }
                        if (keywordMatched) continue;
                        
                        // Coincidencia exacta en nombre del método
                        if (nombreNorm === cleanKeyword || nombreEnNorm === cleanKeyword) {
                            score += maxScore * 1.3;
                            keywordsMatched++;
                            keywordsInNombre++;
                            keywordMatched = true;
                            continue;
                        }
                        
                        // Coincidencia como palabra completa en nombre
                        const nombreRegex = new RegExp(`\\b${cleanKeyword.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\b`, 'i');
                        if (nombreRegex.test(nombreNorm) || nombreRegex.test(nombreEnNorm)) {
                            score += maxScore * 1.1;
                            keywordsMatched++;
                            keywordsInNombre++;
                            keywordMatched = true;
                            continue;
                        }
                        
                        // Coincidencia en analito o nombre como substring (menor prioridad)
                        if (analitoNorm.includes(cleanKeyword) || analitoEnNorm.includes(cleanKeyword)) {
                            score += maxScore * 0.8;
                            keywordsMatched++;
                            keywordsInAnalito++;
                            keywordMatched = true;
                            continue;
                        }
                        if (nombreNorm.includes(cleanKeyword) || nombreEnNorm.includes(cleanKeyword)) {
                            score += maxScore * 0.7;
                            keywordsMatched++;
                            keywordsInNombre++;
                            keywordMatched = true;
                            continue;
                        }
                        
                        // Coincidencia en matriz (solo si también hay coincidencia en analito/nombre)
                        const matrizRegex = new RegExp(`\\b${cleanKeyword.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\b`, 'i');
                        if (matrizRegex.test(matrizNorm)) {
                            keywordsMatched++;
                            keywordsInMatriz++;
                            // Solo dar puntos si ya hay alguna coincidencia en analito/nombre
                            if (keywordsInAnalito > 0 || keywordsInNombre > 0) {
                                score += maxScore * 0.3; // Bonus por coincidencia múltiple
                            }
                            keywordMatched = true;
                            continue;
                        }
                    }
                }
                
                // BONUS: Si TODOS los keywords coinciden (coincidencia múltiple), dar bonus extra
                if (keywords.length > 1 && keywordsMatched === keywords.length) {
                    score += maxScore * 0.5; // Bonus por coincidencia completa
                }
                
                // BONUS: Si hay coincidencias en múltiples campos (analito Y nombre Y matriz)
                if (keywordsInAnalito > 0 && keywordsInNombre > 0) {
                    score += maxScore * 0.4; // Bonus por coincidencia en múltiples campos
                }
            }
            
            // PRIORIDAD 2: Términos expandidos (sinónimos) en analito o nombre
            // IMPORTANTE: Solo si NO hay coincidencia directa en keywords, considerar sinónimos
            // Pero solo si el sinónimo está específicamente relacionado con el término buscado
            if (score === 0 && keywords.length > 0) {
                for (const keyword of keywords) {
                    const cleanKeyword = keyword.replace(/[?¿!¡.,;:]/g, '').trim();
                    if (cleanKeyword.length >= 3) {
                        // Buscar en términos expandidos si el keyword está relacionado con sinónimos
                        for (const term of expandedTermsArray) {
                            const cleanTerm = term.replace(/[?¿!¡.,;:]/g, '').trim();
                            if (cleanTerm.length >= 3 && cleanTerm !== cleanKeyword) {
                                // Solo considerar si está en analito o nombre, NO en matriz o técnica
                                if (analitoNorm.includes(cleanTerm) || analitoEnNorm.includes(cleanTerm) ||
                                    nombreNorm.includes(cleanTerm) || nombreEnNorm.includes(cleanTerm)) {
                                    // Verificar que el término expandido sea realmente un sinónimo del keyword buscado
                                    // Revisar si el término expandido está en la lista de sinónimos del keyword
                                    let isRelated = false;
                                    for (const [synKey, synValues] of Object.entries(synonyms)) {
                                        const normalizedSynKey = this.normalizeText(synKey);
                                        if ((normalizedSynKey === cleanKeyword || cleanKeyword.includes(normalizedSynKey) || normalizedSynKey.includes(cleanKeyword)) &&
                                            synValues.some(v => this.normalizeText(v) === cleanTerm)) {
                                            isRelated = true;
                                            break;
                                        }
                                        if (synValues.some(v => this.normalizeText(v) === cleanKeyword) &&
                                            (normalizedSynKey === cleanTerm || cleanTerm.includes(normalizedSynKey) || normalizedSynKey.includes(cleanTerm))) {
                                            isRelated = true;
                                            break;
                                        }
                                    }
                                    
                                    if (isRelated) {
                                        score += maxScore * 0.6; // Menor prioridad que coincidencia directa
                                        break; // Solo contar una vez por keyword
                                    }
                                }
                            }
                        }
                    }
                }
            }
            
            // PRIORIDAD 3: Coincidencia en otros campos (matriz, técnica) - MUY BAJA prioridad
            // SOLO como bonus adicional si ya hay coincidencia fuerte en analito/nombre
            // NUNCA debe ser suficiente por sí sola para aparecer en resultados
            if (score >= maxScore * 0.5 && keywords.length > 0) {
                for (const keyword of keywords) {
                    const cleanKeyword = keyword.replace(/[?¿!¡.,;:]/g, '').trim();
                    if (cleanKeyword.length >= 4) {
                        if (matrizNorm.includes(cleanKeyword) || tecnicaNorm.includes(cleanKeyword)) {
                            score += maxScore * 0.05; // Muy pequeño bonus adicional
                        }
                    }
                }
            }
            
            // FILTRO CRÍTICO: Solo mantener metodologías con coincidencia en analito o nombre
            // Descarta completamente metodologías que solo coinciden en matriz o técnica
            let hasMatchInAnalitoOrNombre = false;
            
            if (keywords.length > 0) {
                for (const keyword of keywords) {
                    const cleanKeyword = keyword.replace(/[?¿!¡.,;:]/g, '').trim();
                    if (cleanKeyword.length >= 3) {
                        // Verificar coincidencia directa en analito o nombre
                        if (analitoNorm.includes(cleanKeyword) || analitoEnNorm.includes(cleanKeyword) ||
                            nombreNorm.includes(cleanKeyword) || nombreEnNorm.includes(cleanKeyword)) {
                            hasMatchInAnalitoOrNombre = true;
                            break;
                        }
                        
                        // Verificar coincidencia flexible (typos) en analito o nombre
                        const analitoWords = (analitoNorm + ' ' + analitoEnNorm).split(/\s+/).filter(w => w.length >= 3);
                        const nombreWords = (nombreNorm + ' ' + nombreEnNorm).split(/\s+/).filter(w => w.length >= 3);
                        
                        for (const word of [...analitoWords, ...nombreWords]) {
                            if (this.isSimilar(cleanKeyword, word, 2)) {
                                hasMatchInAnalitoOrNombre = true;
                                break;
                            }
                        }
                        
                        if (hasMatchInAnalitoOrNombre) break;
                    }
                }
                
                // Si hay términos expandidos, verificar también
                if (!hasMatchInAnalitoOrNombre) {
                    for (const term of expandedTermsArray) {
                        const cleanTerm = term.replace(/[?¿!¡.,;:]/g, '').trim();
                        if (cleanTerm.length >= 3) {
                            // Solo considerar si está en analito o nombre
                            if (analitoNorm.includes(cleanTerm) || analitoEnNorm.includes(cleanTerm) ||
                                nombreNorm.includes(cleanTerm) || nombreEnNorm.includes(cleanTerm)) {
                                // Verificar que el término expandido sea realmente relacionado con el keyword buscado
                                let isRelated = false;
                                for (const keyword of keywords) {
                                    const cleanKeyword = keyword.replace(/[?¿!¡.,;:]/g, '').trim();
                                    // Verificar si el término expandido está en los sinónimos del keyword
                                    for (const [synKey, synValues] of Object.entries(synonyms)) {
                                        const normalizedSynKey = this.normalizeText(synKey);
                                        if ((normalizedSynKey === cleanKeyword || cleanKeyword.includes(normalizedSynKey) || normalizedSynKey.includes(cleanKeyword)) &&
                                            synValues.some(v => this.normalizeText(v) === cleanTerm)) {
                                            isRelated = true;
                                            break;
                                        }
                                        if (synValues.some(v => this.normalizeText(v) === cleanKeyword) &&
                                            (normalizedSynKey === cleanTerm || cleanTerm.includes(normalizedSynKey) || normalizedSynKey.includes(cleanTerm))) {
                                            isRelated = true;
                                            break;
                                        }
                                    }
                                    if (isRelated) break;
                                }
                                
                                if (isRelated) {
                                    hasMatchInAnalitoOrNombre = true;
                                    break;
                                }
                            }
                        }
                    }
                }
            }
            
            // Si no hay coincidencia en analito o nombre, descartar completamente (score = 0)
            if (!hasMatchInAnalitoOrNombre) {
                score = 0;
            }
            
            return { metodologia: met, score: score, keywordsMatched: keywordsMatched || 0 };
        })
        .filter(item => item.score > 0) // Solo mantener resultados con score > 0 (ya filtrado por coincidencia en analito/nombre)
        .sort((a, b) => {
            // Ordenar primero por número de keywords que coinciden (descendente)
            if (b.keywordsMatched !== a.keywordsMatched) {
                return b.keywordsMatched - a.keywordsMatched;
            }
            // Si tienen el mismo número de keywords, ordenar por score descendente
            return b.score - a.score;
        })
        .slice(0, 20) // Limitar a los 20 mejores resultados
        .map(item => item.metodologia); // Devolver solo las metodologías

        return scoredResults;
    }

    async showResults(query, results) {
        // Verificar si hay metodologías cargadas
        if (this.metodologias.length === 0) {
            console.warn('⚠️ Chatbot: No hay metodologías cargadas para buscar');
            let message = `
                <p>⚠️ No se pudieron cargar las metodologías en este momento.</p>
                <p>Por favor, intenta recargar la página o contacta al administrador.</p>
            `;
            
            // Si estamos en la página de servicios, sugerir buscar en la tabla
            if (document.querySelector('#tabla-metodologias')) {
                message += `<p>Puedes buscar directamente en la tabla de metodologías más abajo.</p>`;
            }
            
            message += `<p><small>💡 Abre la consola del navegador (F12) para ver más detalles del error.</small></p>`;
            
            this.addMessage(message);
            return;
        }
        
        if (results.length === 0) {
            // Detectar si es una consulta sobre metodologías específicamente
            const queryLower = query.toLowerCase();
            // Consultas generales sobre métodos disponibles (no buscan una metodología específica)
            const isGeneralMethodsQuery = /\b(que|qué|cuantos|cuántos|cuantas|cuántas|tienen|tiene|disponible|disponibles|metodos|métodos|metodologias|metodologías|tecnicas|técnicas)\s*(metodo|metodo|metodologias|metodologías|tecnicas|técnicas|tienen|tiene|hay|disponible|disponibles)\b/i.test(query);
            
            // Si pregunta "qué métodos tienen" o similar, ir directamente a Perplexity sin mensaje
            if (isGeneralMethodsQuery) {
                await this.searchWithPerplexity(query, false, false);
                return;
            }
            
            // Solo mostrar mensaje de "no encontré metodologías" si la consulta es claramente sobre una metodología específica
            const isMethodologyQuery = /\b(metodología|metodologia|análisis|analisis|analito|matriz|técnica|tecnica|hacen|realizan|detectan|analizan|cuantifican|determinan|diquat|amprolio|antibiotico|antibiótico|micotoxina|residuo|plaguicida|herbicida|en\s+(salmon|cerdo|carne|leche|huevo))\b/i.test(query);
            
            if (isMethodologyQuery) {
                this.addMessage(`
                    <p>No encontré metodologías que coincidan con "<strong>${this.escapeHtml(query)}</strong>" en nuestra base de datos.</p>
                    <p><small>Búsqueda en <strong>${this.metodologias.length}</strong> metodologías disponibles</small></p>
                `);
            }
            
            // Intentar búsqueda inteligente con Perplexity
            await this.searchWithPerplexity(query, false);
            return;
        }

        // Agrupar metodologías similares (mismo método, misma matriz, misma técnica, etc.)
        const grupos = {};
        
        results.forEach(met => {
            // Crear clave de agrupación: nombre del método + matriz + técnica + acreditada
            const nombre = this.normalizeText(met.nombre || '');
            const matriz = this.normalizeText(met.matriz || '');
            const tecnica = this.normalizeText(met.tecnica || '');
            const acreditada = met.acreditada || false;
            
            const grupoKey = `${nombre}|${matriz}|${tecnica}|${acreditada}`;
            
            if (!grupos[grupoKey]) {
                grupos[grupoKey] = {
                    nombre: met.nombre || '',
                    matriz: met.matriz || '',
                    tecnica: met.tecnica || '',
                    acreditada: acreditada,
                    analitos: [],
                    lods: [],
                    loqs: []
                };
            }
            
            // Agregar analito y límites
            const analito = met.analito || '';
            if (analito && !grupos[grupoKey].analitos.includes(analito)) {
                grupos[grupoKey].analitos.push(analito);
            }
            
            // Extraer valores numéricos de LOD y LOQ
            const lod = met.limite_deteccion || '';
            const loq = met.limite_cuantificacion || '';
            
            if (lod) {
                const lodNum = this.extractNumber(lod);
                if (lodNum !== null) {
                    grupos[grupoKey].lods.push(lodNum);
                }
            }
            
            if (loq) {
                const loqNum = this.extractNumber(loq);
                if (loqNum !== null) {
                    grupos[grupoKey].loqs.push(loqNum);
                }
            }
        });
        
        const gruposArray = Object.values(grupos);
        
        // Generar respuesta en formato natural y agrupado
        let message = '';
        
        if (gruposArray.length === 1) {
            // Un solo método con múltiples analitos
            const grupo = gruposArray[0];
            const numAnalitos = grupo.analitos.length;
            
            message = `<p><strong>Sí, tenemos una metodología acreditada</strong> para analizar <strong>${this.formatAnalitos(grupo.analitos)}</strong>`;
            
            if (grupo.matriz) {
                message += ` en <strong>${grupo.matriz.toLowerCase()}</strong>`;
            }
            
            if (grupo.tecnica) {
                message += ` mediante <strong>${grupo.tecnica}</strong>`;
            }
            
            message += '.</p>';
            
            // Agregar información de límites si está disponible
            const lodRange = this.formatRange(grupo.lods);
            const loqRange = this.formatRange(grupo.loqs);
            
            // Obtener unidades de LOD/LOQ del primer resultado (si hay)
            let lodUnit = '';
            let loqUnit = '';
            if (results.length > 0) {
                const firstResult = results.find(r => r.limite_deteccion);
                if (firstResult && firstResult.limite_deteccion) {
                    const lodMatch = firstResult.limite_deteccion.toString().match(/[\d.]+(.+)/);
                    if (lodMatch) lodUnit = lodMatch[1].trim();
                }
                const firstLoq = results.find(r => r.limite_cuantificacion);
                if (firstLoq && firstLoq.limite_cuantificacion) {
                    const loqMatch = firstLoq.limite_cuantificacion.toString().match(/[\d.]+(.+)/);
                    if (loqMatch) loqUnit = loqMatch[1].trim();
                }
            }
            
            if (lodRange || loqRange) {
                message += '<p><strong>Límites de detección y cuantificación:</strong></p><ul>';
                if (lodRange) {
                    message += `<li>LOD: ${lodRange}${lodUnit || ''}</li>`;
                }
                if (loqRange) {
                    message += `<li>LOQ: ${loqRange}${loqUnit || ''}</li>`;
                }
                message += '</ul>';
            }
            
            if (grupo.acreditada) {
                message += '<p>✓ <strong>Metodología acreditada ISO 17025</strong></p>';
            }
            
            // Guardar contexto para preguntas de seguimiento
            this.lastResults = [grupo];
            this.lastQuery = query;
        } else {
            // Múltiples métodos
            message = `<p>Encontré <strong>${gruposArray.length} metodologías</strong> relacionadas con tu búsqueda:</p>`;
            
            gruposArray.forEach((grupo, index) => {
                const numAnalitos = grupo.analitos.length;
                const analitosText = numAnalitos > 1 
                    ? this.formatAnalitos(grupo.analitos)
                    : this.capitalize(grupo.analitos[0] || 'varios analitos');
                
                message += `<p><strong>${index + 1}. ${this.capitalize(grupo.nombre || 'Metodología')}</strong></p>`;
                message += `<p>Analitos: <strong>${analitosText}</strong></p>`;
                
                if (grupo.matriz) {
                    message += `<p>Matriz: ${this.capitalize(grupo.matriz)}</p>`;
                }
                
                if (grupo.tecnica) {
                    message += `<p>Técnica: ${grupo.tecnica}</p>`;
                }
                
                // Obtener unidades de LOD/LOQ
                let lodUnit = '';
                let loqUnit = '';
                const grupoResults = results.filter(r => 
                    this.normalizeText(r.nombre || '') === this.normalizeText(grupo.nombre || '') &&
                    this.normalizeText(r.matriz || '') === this.normalizeText(grupo.matriz || '')
                );
                if (grupoResults.length > 0) {
                    const firstLod = grupoResults.find(r => r.limite_deteccion);
                    if (firstLod && firstLod.limite_deteccion) {
                        const lodMatch = firstLod.limite_deteccion.toString().match(/[\d.]+(.+)/);
                        if (lodMatch) lodUnit = lodMatch[1].trim();
                    }
                    const firstLoq = grupoResults.find(r => r.limite_cuantificacion);
                    if (firstLoq && firstLoq.limite_cuantificacion) {
                        const loqMatch = firstLoq.limite_cuantificacion.toString().match(/[\d.]+(.+)/);
                        if (loqMatch) loqUnit = loqMatch[1].trim();
                    }
                }
                
                const lodRange = this.formatRange(grupo.lods);
                const loqRange = this.formatRange(grupo.loqs);
                
                if (lodRange || loqRange) {
                    message += '<p><strong>Límites:</strong> ';
                    if (lodRange && loqRange) {
                        message += `LOD ${lodRange}${lodUnit || ''}, LOQ ${loqRange}${loqUnit || ''}`;
                    } else if (lodRange) {
                        message += `LOD ${lodRange}${lodUnit || ''}`;
                    } else if (loqRange) {
                        message += `LOQ ${loqRange}${loqUnit || ''}`;
                    }
                    message += '</p>';
                }
                
                if (grupo.acreditada) {
                    message += '<p>✓ <strong>Acreditada ISO 17025</strong></p>';
                }
                
                if (index < gruposArray.length - 1) {
                    message += '<hr style="margin: 10px 0; border: none; border-top: 1px solid #ddd;">';
                }
            });
        }
        
        this.addMessage(message);
    }

    async searchWithPerplexity(query, includeLocal = true, isGeneralQuery = false) {
        const typingId = this.showTyping();
        try {
            console.log('🔄 Chatbot: Buscando con Perplexity API...');
            const perplexityResponse = await fetch('/api/chatbot/search', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ 
                    query: query,
                    include_local: includeLocal
                })
            });
            
            this.hideTyping(typingId);
            
            console.log(`📡 Chatbot Perplexity: Status ${perplexityResponse.status}`);
            
            if (perplexityResponse.ok) {
                const data = await perplexityResponse.json();
                console.log('✅ Chatbot Perplexity: Respuesta recibida', data);
                
                if (data.answer) {
                    let message = `
                        <div class="chatbot-results-text">
                            ${this.formatPerplexityAnswer(data.answer)}
                        </div>
                    `;
                    
                    // No mostrar información de fuentes para simplificar la respuesta
                    
                    if (!includeLocal && !isGeneralQuery) {
                        message += '<p><small>Para consultas específicas sobre metodologías de FARMAVET, contacta directamente con el laboratorio.</small></p>';
                    }
                    
                    this.addMessage(message);
                } else {
                    console.warn('⚠️ Chatbot Perplexity: Respuesta sin answer');
                    if (isGeneralQuery) {
                        this.showGeneralInfoHelp();
                    } else {
                        this.showNoResultsHelp(query);
                    }
                }
            } else {
                // Si Perplexity falla, mostrar ayuda apropiada
                const errorData = await perplexityResponse.json().catch(() => ({}));
                console.error('❌ Chatbot Perplexity: Error', perplexityResponse.status, errorData);
                
                if (perplexityResponse.status === 503 && errorData.error === 'API de Perplexity no configurada') {
                    // API no configurada, mostrar información básica para consultas generales
                    if (isGeneralQuery) {
                        this.showGeneralInfoHelp();
                    } else {
                        this.showNoResultsHelp(query);
                    }
                } else {
                    // Otro error
                    if (isGeneralQuery) {
                        this.showGeneralInfoHelp();
                    } else {
                        this.showNoResultsHelp(query);
                    }
                }
            }
        } catch (error) {
            console.error('❌ Chatbot Perplexity: Error de red', error);
            this.hideTyping(typingId);
            if (isGeneralQuery) {
                this.showGeneralInfoHelp();
            } else {
                this.showNoResultsHelp(query);
            }
        }
    }

    showNoResultsHelp(query) {
        // Mostrar ayuda cuando no se encuentra nada ni con Perplexity (para metodologías)
        this.addMessage(`
            <p>Intenta con términos como:</p>
            <ul class="chatbot-examples">
                <li>Nombre del analito (ej: "tetraciclinas", "aflatoxinas", "diquat", "amprolio")</li>
                <li>Tipo de matriz (ej: "salmón", "carne", "leche")</li>
                <li>Técnica analítica (ej: "LC-MS/MS", "GC-MS")</li>
                <li>Categoría (ej: "residuos", "contaminantes")</li>
            </ul>
            <p><small>💡 También puedes contactar directamente con FARMAVET para consultas específicas.</small></p>
        `);
    }
    
    showGeneralInfoHelp() {
        // Mostrar información de contacto cuando Perplexity no está disponible para consultas generales
        this.addMessage(`
            <p>Información de contacto de FARMAVET:</p>
            <ul class="chatbot-examples">
                <li><strong>Dirección:</strong> Av. Santa Rosa 11735, La Pintana, Santiago, Chile</li>
                <li><strong>Teléfono:</strong> +56 2 2978 XXXX</li>
                <li><strong>Email:</strong> farmavet@uchile.cl</li>
                <li><strong>Email programas:</strong> postitulo@veterinaria.uchile.cl</li>
                <li><strong>Horario:</strong> Lunes a viernes, 09:00 a 17:30 hrs</li>
                <li><strong>Atención:</strong> Presencial con agendamiento previo</li>
            </ul>
            <p><small>Para enviar consultas, puedes usar el formulario de contacto en nuestra página web.</small></p>
        `);
    }

    formatPerplexityAnswer(answer) {
        if (!answer) return '';
        
        // NO escapar HTML todavía - primero limpiar referencias
        let formatted = answer;
        
        // Limpiar referencias a citas y notas ANTES de formatear
        formatted = formatted
            .replace(/\[(\d+)\]/g, '') // Eliminar referencias como [1], [2], etc.
            .replace(/\[\d+\]/g, '') // Eliminar referencias con múltiples números
            .replace(/<\.\.\.>/g, '') // Eliminar <...>
            .replace(/\[\.\.\.\]/g, '') // Eliminar [...]
            .replace(/\(fuente[^)]*\)/gi, '') // Eliminar (fuente: ...)
            .replace(/\(referencia[^)]*\)/gi, '') // Eliminar (referencia: ...)
            .replace(/\(ver[^)]*\)/gi, '') // Eliminar (ver: ...)
            .replace(/\(consulta[^)]*\)/gi, '') // Eliminar (consulta: ...)
            .replace(/\s+/g, ' ') // Normalizar espacios múltiples
            .trim();
        
        // Ahora escapar HTML para seguridad, pero preservar formato básico
        formatted = this.escapeHtml(formatted);
        
        // Aplicar formato después de escapar
        formatted = formatted
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>') // Negrita **texto**
            .replace(/\*(.*?)\*/g, '<em>$1</em>') // Cursiva *texto* (solo si no es lista)
            .replace(/\[([^\]]+)\]\([^\)]+\)/g, '$1'); // Eliminar enlaces [texto](url)
        
        // Convertir saltos de línea dobles en párrafos
        let paragraphs = formatted.split(/\n\s*\n/).filter(p => p.trim().length > 0);
        
        // Si no hay párrafos separados, dividir por saltos de línea simples
        if (paragraphs.length === 1 && formatted.includes('\n')) {
            paragraphs = formatted.split(/\n/).filter(p => p.trim().length > 0);
        }
        
        // Formatear cada párrafo
        formatted = paragraphs.map(para => {
            para = para.trim();
            
            // Limpiar referencias que puedan quedar al inicio o final
            para = para.replace(/^\[[\d\s,]+\]\s*/, '').replace(/\s*\[[\d\s,]+\]$/, '');
            
            // Si es una lista numerada
            if (/^\d+\.\s/.test(para)) {
                const items = para.split(/\n(?=\d+\.\s)/);
                if (items.length > 1) {
                    const listItems = items.map(item => {
                        item = item.replace(/^\d+\.\s*/, '').trim();
                        item = item.replace(/\[[\d\s,]+\]/g, ''); // Limpiar referencias en items
                        return `<li>${item}</li>`;
                    }).join('');
                    return `<ol>${listItems}</ol>`;
                }
                // Un solo item numerado, convertirlo en párrafo normal
                para = para.replace(/^\d+\.\s*/, '');
            }
            
            // Si es una lista con viñetas
            if (/^[-*•]\s/.test(para)) {
                const items = para.split(/\n(?=[-*•]\s)/);
                if (items.length > 1) {
                    const listItems = items.map(item => {
                        item = item.replace(/^[-*•]\s*/, '').trim();
                        item = item.replace(/\[[\d\s,]+\]/g, ''); // Limpiar referencias en items
                        return `<li>${item}</li>`;
                    }).join('');
                    return `<ul>${listItems}</ul>`;
                }
                // Un solo item, convertirlo en párrafo normal
                para = para.replace(/^[-*•]\s*/, '');
            }
            
            // Limpiar espacios múltiples antes de procesar
            para = para.replace(/\s+/g, ' ').trim();
            
            // Si no empieza con una etiqueta HTML, envolver en <p>
            if (!para.match(/^<(p|ul|ol|li|h[1-6]|div|strong|em)/i)) {
                // No convertir saltos de línea en <br> si ya está en un párrafo
                // Solo envolver en <p>
                return `<p>${para}</p>`;
            }
            
            return para;
        }).join('');
        
        // Limpiar párrafos vacíos o con solo espacios
        formatted = formatted.replace(/<p>\s*<\/p>/g, '');
        
        return formatted;
    }

    showSuggestions(query) {
        if (!query || query.length < 2) {
            this.hideSuggestions();
            return;
        }

        const suggestions = this.generateSuggestions(query);
        const container = document.getElementById('chatbot-suggestions');
        if (!container) return;

        if (suggestions.length === 0) {
            container.style.display = 'none';
            return;
        }

        container.innerHTML = suggestions.map(sug => 
            `<button class="chatbot-suggestion" onclick="document.getElementById('chatbot-input').value='${this.escapeHtml(sug)}'; document.getElementById('chatbot-input').focus(); this.parentElement.style.display='none';">${this.escapeHtml(sug)}</button>`
        ).join('');
        container.style.display = 'flex';
    }

    generateSuggestions(query) {
        const normalizedQuery = this.normalizeText(query);
        const keywords = this.extractKeywords(query);
        const suggestions = new Set();
        
        // Buscar términos relacionados en metodologías (normalizados)
        this.metodologias.forEach(met => {
            const fields = [
                met.nombre, met.nombre_en,
                met.analito, met.analito_en,
                met.matriz, met.matriz_en,
                met.tecnica, met.tecnica_en
            ].filter(f => f);
            
            fields.forEach(field => {
                const normalizedField = this.normalizeText(field);
                // Si el campo contiene alguna palabra clave, agregarlo
                if (keywords.length > 0) {
                    for (const keyword of keywords) {
                        if (normalizedField.includes(keyword) || keyword.includes(normalizedField.substring(0, keyword.length))) {
                            suggestions.add(field);
                            break;
                        }
                    }
                } else if (normalizedField.includes(normalizedQuery) || normalizedQuery.includes(normalizedField.substring(0, normalizedQuery.length))) {
                    suggestions.add(field);
                }
            });
        });

        // Sugerencias comunes basadas en la consulta
        const commonQueries = [
            'Buscar metodologías para antibióticos',
            'Metodologías en salmón',
            'LC-MS/MS acreditadas',
            'Análisis en leche',
            'Micotoxinas en alimentos',
            'Diquat en salmón',
            'Amprolio en alimentos',
            'Metodologías para residuos',
            'Análisis de contaminantes',
            'Plaguicidas en matrices alimentarias'
        ];

        commonQueries.forEach(cq => {
            const normalizedCq = this.normalizeText(cq);
            if (normalizedCq.includes(normalizedQuery) || normalizedQuery.includes(normalizedCq.substring(0, normalizedQuery.length))) {
                suggestions.add(cq);
            }
        });

        return Array.from(suggestions).slice(0, 5);
    }

    hideSuggestions() {
        const container = document.getElementById('chatbot-suggestions');
        if (container) container.style.display = 'none';
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Inicializar chatbot cuando el DOM esté listo (en todas las páginas)
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.chatbot = new MetodologiasChatbot();
    });
} else {
    window.chatbot = new MetodologiasChatbot();
}

