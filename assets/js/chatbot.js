/**
 * Chatbot inteligente para búsqueda de metodologías analíticas
 * Versión 1.0 - Búsqueda semántica avanzada
 */

class MetodologiasChatbot {
    constructor() {
        this.isOpen = false;
        this.metodologias = [];
        this.conversationHistory = [];
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
        try {
            // Siempre intentar cargar desde la API primero
            const response = await fetch('/api/metodologias');
            if (response.ok) {
                this.metodologias = await response.json();
                console.log(`✅ Chatbot: ${this.metodologias.length} metodologías cargadas desde API`);
            } else {
                // Fallback: cargar desde el DOM si la API no existe
                this.loadFromDOM();
            }
        } catch (error) {
            console.warn('No se pudo cargar desde API, usando DOM:', error);
            this.loadFromDOM();
        }
    }

    loadFromDOM() {
        // Cargar metodologías desde la tabla en el DOM
        const rows = document.querySelectorAll('#tabla-metodologias tbody tr');
        this.metodologias = Array.from(rows).map(row => {
            const cells = row.querySelectorAll('td');
            return {
                nombre: cells[0]?.textContent.trim() || '',
                analito: cells[1]?.textContent.trim() || '',
                matriz: cells[2]?.textContent.trim() || '',
                tecnica: cells[3]?.textContent.trim() || '',
                lod: cells[4]?.textContent.trim() || '',
                loq: cells[5]?.textContent.trim() || '',
                acreditada: cells[6]?.textContent.trim() || '',
                categoria: row.dataset.categoria || ''
            };
        });
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
        setTimeout(() => {
            this.hideTyping(typingId);
            const results = this.searchMetodologias(query);
            this.showResults(query, results);
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
                          'metodología', 'metodologías', 'analisis', 'análisis', 'en', 'de', 'del'];
        
        const normalized = this.normalizeText(query);
        const words = normalized.split(/\s+/).filter(w => w.length > 2);
        return words.filter(word => !stopWords.includes(word));
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
            'diquat': ['diquat', 'paraquat', 'herbicida']
        };

        // Expandir búsqueda con sinónimos
        const expandedTerms = [normalizedQuery, ...keywords];
        for (const keyword of keywords) {
            for (const [key, values] of Object.entries(synonyms)) {
                const normalizedKey = this.normalizeText(key);
                if (keyword.includes(normalizedKey) || normalizedKey.includes(keyword)) {
                    expandedTerms.push(...values.map(v => this.normalizeText(v)));
                }
                for (const value of values) {
                    const normalizedValue = this.normalizeText(value);
                    if (keyword.includes(normalizedValue) || normalizedValue.includes(keyword)) {
                        expandedTerms.push(normalizedKey, ...values.map(v => this.normalizeText(v)));
                    }
                }
            }
        }

        // Búsqueda semántica mejorada
        const results = this.metodologias.filter(met => {
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
            
            // Búsqueda exacta en texto normalizado
            if (searchFields.includes(normalizedQuery)) return true;
            
            // Búsqueda con sinónimos expandidos
            for (const term of expandedTerms) {
                if (term.length > 2 && searchFields.includes(term)) return true;
            }
            
            // Búsqueda por palabras clave individuales
            if (keywords.length > 0) {
                const matchCount = keywords.filter(keyword => {
                    if (keyword.length <= 2) return false;
                    return searchFields.includes(keyword);
                }).length;
                
                // Si al menos una palabra clave coincide, incluir el resultado
                if (matchCount > 0) return true;
            }
            
            // Búsqueda parcial (substring) para términos cortos importantes
            for (const keyword of keywords) {
                if (keyword.length >= 3) {
                    if (searchFields.includes(keyword)) return true;
                }
            }
            
            return false;
        });

        return results;
    }

    showResults(query, results) {
        if (results.length === 0) {
            this.addMessage(`
                <p>No encontré metodologías que coincidan con "<strong>${this.escapeHtml(query)}</strong>".</p>
                <p>Intenta con términos como:</p>
                <ul class="chatbot-examples">
                    <li>Nombre del analito (ej: "tetraciclinas", "aflatoxinas")</li>
                    <li>Tipo de matriz (ej: "salmón", "carne", "leche")</li>
                    <li>Técnica analítica (ej: "LC-MS/MS", "GC-MS")</li>
                    <li>Categoría (ej: "residuos", "contaminantes")</li>
                </ul>
            `);
            return;
        }

        let message = `<p>Encontré <strong>${results.length}</strong> metodología${results.length > 1 ? 's' : ''} relacionada${results.length > 1 ? 's' : ''} con "<strong>${this.escapeHtml(query)}</strong>":</p>`;
        message += '<div class="chatbot-results">';
        
        results.slice(0, 5).forEach(met => {
            message += `
                <div class="chatbot-result-item">
                    <h4>${this.escapeHtml(met.nombre)}</h4>
                    <div class="chatbot-result-details">
                        <span><strong>Analito:</strong> ${this.escapeHtml(met.analito)}</span>
                        <span><strong>Matriz:</strong> ${this.escapeHtml(met.matriz)}</span>
                        <span><strong>Técnica:</strong> ${this.escapeHtml(met.tecnica)}</span>
                        ${met.acreditada ? `<span class="badge-acreditada">✓ Acreditada</span>` : ''}
                    </div>
                </div>
            `;
        });

        if (results.length > 5) {
            message += `<p class="chatbot-more">Y ${results.length - 5} metodología${results.length - 5 > 1 ? 's' : ''} más. <a href="#metodologias-completas" onclick="document.getElementById('chatbot-window').classList.remove('open'); document.getElementById('search-metodologias').value='${this.escapeHtml(query)}'; document.getElementById('search-metodologias').dispatchEvent(new Event('input')); document.getElementById('metodologias-completas').scrollIntoView({behavior: 'smooth'});">Ver todas</a></p>`;
        }

        message += '</div>';
        this.addMessage(message);
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
            'Metodologías para residuos',
            'Análisis de contaminantes'
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

