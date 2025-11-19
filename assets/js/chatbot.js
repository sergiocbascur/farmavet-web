/**
 * Chatbot inteligente para búsqueda de metodologías analíticas
 * Versión 1.0 - Búsqueda semántica avanzada
 */

class MetodologiasChatbot {
    constructor() {
        this.isOpen = false;
        this.metodologias = [];
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
                        <h3>Asistente de Metodologías</h3>
                        <p class="chatbot-subtitle">Busca metodologías analíticas de forma inteligente</p>
                    </div>
                </div>
                <button class="chatbot-close" id="chatbot-close" aria-label="Cerrar chatbot">
                    <i class="bi bi-x-lg"></i>
                </button>
            </div>
            <div class="chatbot-messages" id="chatbot-messages">
                <div class="chatbot-message bot-message">
                    <div class="message-content">
                        <p>¡Hola! 👋 Soy tu asistente para buscar metodologías analíticas.</p>
                        <p>Puedes preguntarme cosas como:</p>
                        <ul class="chatbot-examples">
                            <li>"Busca metodologías para antibióticos en salmón"</li>
                            <li>"¿Qué técnicas usan para micotoxinas?"</li>
                            <li>"Metodologías acreditadas para leche"</li>
                            <li>"LC-MS/MS en carne"</li>
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
                <div class="chatbot-suggestions" id="chatbot-suggestions"></div>
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
            this.showSuggestions(e.target.value);
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
        this.hideSuggestions();

        // Mostrar "escribiendo..."
        const typingId = this.showTyping();

        // Procesar consulta
        setTimeout(async () => {
            this.hideTyping(typingId);
            const results = this.searchMetodologias(query);
            await this.showResults(query, results);
        }, 500);
    }

    addMessage(content, type = 'bot') {
        const messages = document.getElementById('chatbot-messages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `chatbot-message ${type}-message`;
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        
        if (typeof content === 'string') {
            contentDiv.innerHTML = `<p>${this.escapeHtml(content)}</p>`;
        } else {
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
        return text
            .toLowerCase()
            .normalize('NFD')
            .replace(/[\u0300-\u036f]/g, '') // Quitar acentos
            .replace(/[^\w\s]/g, ' ') // Reemplazar caracteres especiales con espacios
            .replace(/\s+/g, ' ') // Normalizar espacios
            .trim();
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

    searchMetodologias(query) {
        const normalizedQuery = this.normalizeText(query);
        const keywords = this.extractKeywords(query);
        
        // Diccionario de sinónimos y términos relacionados (sin acentos)
        const synonyms = {
            'antibiotico': ['antimicrobiano', 'antimicrobianos', 'fluoroquinolona', 'tetraciclina', 'sulfonamida', 'macrolido', 'aminoglucosido'],
            'micotoxina': ['aflatoxina', 'ocratoxina', 'fumonisina', 'zearalenona'],
            'pesticida': ['plaguicida', 'organoclorado', 'organofosforado', 'diquat', 'paraquat', 'glifosato'],
            'salmon': ['salmones', 'salmonidos', 'salmonideos', 'trucha', 'truchas', 'pez', 'peces', 'hidrobiologico', 'hidrobiológico'],
            'carne': ['carnes', 'bovino', 'bovina', 'porcino', 'porcina', 'ave', 'aves', 'pollo', 'pollos'],
            'leche': ['lacteo', 'lacteos', 'dairy', 'producto lacteo'],
            'lcmsms': ['lc-ms/ms', 'lc-ms', 'lcms', 'cromatografia liquida', 'espectrometria de masas', 'liquid chromatography'],
            'gcms': ['gc-ms', 'cromatografia de gases', 'gas chromatography'],
            'hplc': ['cromatografia liquida', 'high performance liquid chromatography'],
            'metodo': ['metodologia', 'tecnica', 'analisis', 'ensayo'],
            'diquat': ['diquat', 'paraquat', 'herbicida', 'bipiridilo'],
            'amprolio': ['amprolio', 'amprolium', 'anticoccidiano', 'antiparasitario']
        };

        // Expandir búsqueda con sinónimos
        const expandedTerms = new Set();
        expandedTerms.add(normalizedQuery);
        keywords.forEach(kw => expandedTerms.add(kw));
        
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

        // Búsqueda semántica mejorada
        const results = this.metodologias.filter(met => {
            // Crear un texto de búsqueda combinando todos los campos
            const searchFields = [
                this.normalizeText(met.nombre || ''),
                this.normalizeText(met.nombre_en || ''),
                this.normalizeText(met.analito || ''),
                this.normalizeText(met.analito_en || ''),
                this.normalizeText(met.matriz || ''),
                this.normalizeText(met.matriz_en || ''),
                this.normalizeText(met.tecnica || ''),
                this.normalizeText(met.tecnica_en || ''),
                this.normalizeText(met.categoria || '')
            ].join(' ');
            
            // Normalizar también la query completa
            const cleanQuery = normalizedQuery.replace(/[?¿!¡.,;:]/g, '').trim();
            
            // 1. Búsqueda exacta: si la query completa está en los campos
            if (cleanQuery.length >= 3 && searchFields.includes(cleanQuery)) {
                return true;
            }
            
            // 2. Búsqueda con términos expandidos (sinónimos)
            for (const term of expandedTermsArray) {
                const cleanTerm = term.replace(/[?¿!¡.,;:]/g, '').trim();
                if (cleanTerm.length >= 3 && searchFields.includes(cleanTerm)) {
                    return true;
                }
            }
            
            // 3. Búsqueda por palabras clave individuales (más flexible)
            if (keywords.length > 0) {
                for (const keyword of keywords) {
                    const cleanKeyword = keyword.replace(/[?¿!¡.,;:]/g, '').trim();
                    if (cleanKeyword.length >= 3) {
                        // Buscar como palabra completa o como substring
                        // Buscar como palabra completa (entre espacios o al inicio/fin)
                        const wordRegex = new RegExp(`\\b${cleanKeyword.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\b`, 'i');
                        if (wordRegex.test(searchFields)) {
                            return true;
                        }
                        // También buscar como substring para términos químicos
                        if (searchFields.includes(cleanKeyword)) {
                            return true;
                        }
                    }
                }
            }
            
            // 4. Búsqueda de similitud parcial para términos químicos (última opción)
            // Para términos de 4+ caracteres, buscar si está contenido en cualquier parte
            if (keywords.length > 0) {
                for (const keyword of keywords) {
                    const cleanKeyword = keyword.replace(/[?¿!¡.,;:]/g, '').trim();
                    if (cleanKeyword.length >= 4) {
                        // Buscar si el keyword está en algún campo individual (no solo en el texto combinado)
                        const individualFields = [
                            this.normalizeText(met.analito || ''),
                            this.normalizeText(met.analito_en || ''),
                            this.normalizeText(met.nombre || ''),
                            this.normalizeText(met.nombre_en || '')
                        ];
                        
                        for (const field of individualFields) {
                            if (field && field.includes(cleanKeyword)) {
                                return true;
                            }
                        }
                    }
                }
            }
            
            return false;
        });

        return results;
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
            // Primero mostrar mensaje de no encontrado
            this.addMessage(`
                <p>No encontré metodologías que coincidan con "<strong>${this.escapeHtml(query)}</strong>" en nuestra base de datos.</p>
                <p><small>💡 Búsqueda en <strong>${this.metodologias.length}</strong> metodologías disponibles</small></p>
            `);
            
            // Intentar búsqueda inteligente con Perplexity
            const typingId = this.showTyping();
            try {
                console.log('🔄 Chatbot: Buscando con Perplexity API...');
                const perplexityResponse = await fetch('/api/chatbot/search', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ query: query })
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
                        
                        if (data.sources && data.sources.length > 0) {
                            message += `<p><small>📚 Fuente${data.sources.length > 1 ? 's' : ''}: ${data.sources.length}</small></p>`;
                        }
                        
                        message += `<p><small>⚠️ <strong>Nota:</strong> Esta información es general. Para metodologías específicas de FARMAVET, contacta directamente con el laboratorio.</small></p>`;
                        
                        this.addMessage(message);
                    } else {
                        console.warn('⚠️ Chatbot Perplexity: Respuesta sin answer');
                        this.showNoResultsHelp(query);
                    }
                } else {
                    // Si Perplexity falla, mostrar información útil
                    const errorData = await perplexityResponse.json().catch(() => ({}));
                    console.error('❌ Chatbot Perplexity: Error', perplexityResponse.status, errorData);
                    
                    if (perplexityResponse.status === 503 && errorData.error === 'API de Perplexity no configurada') {
                        // API no configurada, no mostrar mensaje de error al usuario
                        this.showNoResultsHelp(query);
                    } else {
                        // Otro error, mostrar ayuda estándar
                        this.showNoResultsHelp(query);
                    }
                }
            } catch (error) {
                console.error('❌ Chatbot Perplexity: Error de red', error);
                this.hideTyping(typingId);
                this.showNoResultsHelp(query);
            }
            return;
        }

        // Generar respuesta en formato de frase legible
        let message = '';
        
        // Función para formatear texto de manera más legible
        const formatText = (text) => {
            if (!text) return '';
            // Convertir "Productos pecuarios" a "productos pecuarios", "HPLC-DAD" se mantiene
            return text.charAt(0).toUpperCase() + text.slice(1).toLowerCase();
        };
        
        // Función para formatear técnica analítica
        const formatTecnica = (tecnica) => {
            if (!tecnica) return 'técnica analítica estándar';
            // Mantener acrónimos en mayúsculas (LC-MS/MS, HPLC-DAD, etc.)
            return tecnica;
        };
        
        // Función para formatear matriz de manera más natural
        const formatMatriz = (matriz) => {
            if (!matriz) return 'diversas matrices';
            
            // Simplificar términos técnicos
            const replacements = {
                'productos pecuarios': 'productos de origen animal (carne, leche, huevos)',
                'matrices pecuarias': 'productos de origen animal',
                'productos hidrobiológicos': 'productos acuáticos (salmón, trucha, mariscos)',
                'matrices hidrobiológicas': 'productos acuáticos',
                'salmón': 'salmón',
                'trucha': 'trucha',
                'carne': 'carne',
                'leche': 'leche',
                'huevos': 'huevos'
            };
            
            const matrizLower = matriz.toLowerCase();
            for (const [key, value] of Object.entries(replacements)) {
                if (matrizLower.includes(key)) {
                    return value;
                }
            }
            
            return matriz.toLowerCase();
        };
        
        if (results.length === 1) {
            const met = results[0];
            const analito = formatText(met.analito || met.nombre);
            const matriz = formatMatriz(met.matriz);
            const tecnica = formatTecnica(met.tecnica);
            const acreditada = met.acreditada ? 'acreditada ISO 17025' : 'disponible';
            
            message = `<p>Sí, tenemos una metodología ${acreditada} para analizar <strong>${this.escapeHtml(analito)}</strong> en <strong>${this.escapeHtml(matriz)}</strong> mediante <strong>${this.escapeHtml(tecnica)}</strong>.</p>`;
            
            // Agregar información adicional si está disponible
            if (met.lod || met.loq) {
                message += '<p><small>💡 ';
                if (met.lod && met.loq) {
                    message += `Límites: LOD ${met.lod}, LOQ ${met.loq}`;
                } else if (met.lod) {
                    message += `Límite de detección: ${met.lod}`;
                } else if (met.loq) {
                    message += `Límite de cuantificación: ${met.loq}`;
                }
                message += '</small></p>';
            }
        } else {
            message = `<p>Encontré <strong>${results.length}</strong> metodología${results.length > 1 ? 's' : ''} relacionada${results.length > 1 ? 's' : ''} con tu búsqueda:</p>`;
            message += '<div class="chatbot-results-text">';
            
            results.slice(0, 5).forEach((met, index) => {
                const analito = formatText(met.analito || met.nombre);
                const matriz = formatMatriz(met.matriz);
                const tecnica = formatTecnica(met.tecnica);
                const acreditada = met.acreditada ? ' ✓ acreditada' : '';
                
                message += `<p><strong>${index + 1}.</strong> <strong>${this.escapeHtml(analito)}</strong> en ${this.escapeHtml(matriz)} (${this.escapeHtml(tecnica)})${acreditada ? this.escapeHtml(acreditada) : ''}.</p>`;
            });
            
            if (results.length > 5) {
                message += `<p class="chatbot-more"><strong>Y ${results.length - 5} metodología${results.length - 5 > 1 ? 's' : ''} más.</strong> <a href="#metodologias-completas" onclick="document.getElementById('chatbot-window').classList.remove('open'); document.getElementById('search-metodologias').value='${this.escapeHtml(query)}'; document.getElementById('search-metodologias').dispatchEvent(new Event('input')); document.getElementById('metodologias-completas').scrollIntoView({behavior: 'smooth'});">Ver todas →</a></p>`;
            }
            
            message += '</div>';
        }

        this.addMessage(message);
    }

    showNoResultsHelp(query) {
        // Mostrar ayuda cuando no se encuentra nada ni con Perplexity
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

    formatPerplexityAnswer(answer) {
        if (!answer) return '';
        
        // Escapar HTML primero
        let formatted = this.escapeHtml(answer);
        
        // Limpiar formato innecesario
        formatted = formatted
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>') // Negrita **texto**
            .replace(/\*(.*?)\*/g, '<em>$1</em>') // Cursiva *texto*
            .replace(/\[([^\]]+)\]\([^\)]+\)/g, '$1'); // Eliminar enlaces [texto](url)
        
        // Convertir saltos de línea dobles en párrafos
        let paragraphs = formatted.split(/\n\s*\n/).filter(p => p.trim().length > 0);
        
        // Formatear cada párrafo
        formatted = paragraphs.map(para => {
            para = para.trim();
            
            // Si es una lista numerada
            if (/^\d+\.\s/.test(para)) {
                const items = para.split(/\n(?=\d+\.\s)/);
                if (items.length > 1) {
                    const listItems = items.map(item => {
                        item = item.replace(/^\d+\.\s*/, '').trim();
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
                        return `<li>${item}</li>`;
                    }).join('');
                    return `<ul>${listItems}</ul>`;
                }
                // Un solo item, convertirlo en párrafo normal
                para = para.replace(/^[-*•]\s*/, '');
            }
            
            // Convertir saltos de línea simples en <br>
            para = para.replace(/\n/g, '<br>');
            
            // Si no empieza con una etiqueta HTML, envolver en <p>
            if (!para.match(/^<(p|ul|ol|li|h[1-6]|div|strong|em)/i)) {
                return `<p>${para}</p>`;
            }
            
            return para;
        }).join('');
        
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

