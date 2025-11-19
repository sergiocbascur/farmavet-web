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
            const response = await fetch('/api/metodologias');
            if (response.ok) {
                this.metodologias = await response.json();
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

    searchMetodologias(query) {
        const lowerQuery = query.toLowerCase();
        
        // Diccionario de sinónimos y términos relacionados
        const synonyms = {
            'antibiotico': ['antimicrobiano', 'antimicrobianos', 'antibiótico', 'antibióticos', 'fluoroquinolona', 'tetraciclina', 'sulfonamida'],
            'micotoxina': ['micotoxinas', 'aflatoxina', 'aflatoxinas', 'ocratoxina'],
            'pesticida': ['plaguicida', 'plaguicidas', 'pesticidas', 'organoclorado', 'organofosforado'],
            'salmón': ['salmón', 'salmones', 'salmonidos', 'salmonídeos', 'trucha', 'truchas'],
            'carne': ['carnes', 'bovino', 'bovina', 'porcino', 'porcina'],
            'leche': ['lácteo', 'lácteos', 'dairy'],
            'lc-ms/ms': ['lcmsms', 'lc-ms', 'cromatografía líquida', 'espectrometría de masas'],
            'gc-ms': ['gcms', 'cromatografía de gases', 'gas chromatography'],
            'hplc': ['cromatografía líquida', 'high performance liquid chromatography']
        };

        // Expandir búsqueda con sinónimos
        const expandedTerms = [lowerQuery];
        for (const [key, values] of Object.entries(synonyms)) {
            if (lowerQuery.includes(key)) {
                expandedTerms.push(...values);
            }
            for (const value of values) {
                if (lowerQuery.includes(value)) {
                    expandedTerms.push(key, ...values);
                }
            }
        }

        // Búsqueda semántica
        const results = this.metodologias.filter(met => {
            const searchText = `${met.nombre} ${met.analito} ${met.matriz} ${met.tecnica} ${met.categoria}`.toLowerCase();
            
            // Búsqueda exacta
            if (searchText.includes(lowerQuery)) return true;
            
            // Búsqueda con sinónimos
            for (const term of expandedTerms) {
                if (searchText.includes(term)) return true;
            }
            
            // Búsqueda por palabras individuales
            const queryWords = lowerQuery.split(/\s+/).filter(w => w.length > 2);
            const matchCount = queryWords.filter(word => searchText.includes(word)).length;
            if (matchCount >= queryWords.length * 0.5) return true; // Al menos 50% de palabras coinciden
            
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
        const lowerQuery = query.toLowerCase();
        const suggestions = new Set();
        
        // Buscar términos relacionados en metodologías
        this.metodologias.forEach(met => {
            const fields = [met.nombre, met.analito, met.matriz, met.tecnica];
            fields.forEach(field => {
                if (field && field.toLowerCase().includes(lowerQuery)) {
                    suggestions.add(field);
                }
            });
        });

        // Sugerencias comunes
        const commonQueries = [
            'Buscar metodologías para antibióticos',
            'Metodologías en salmón',
            'LC-MS/MS acreditadas',
            'Análisis en leche',
            'Micotoxinas en alimentos'
        ];

        commonQueries.forEach(cq => {
            if (cq.toLowerCase().includes(lowerQuery)) {
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

// Inicializar chatbot cuando el DOM esté listo
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        if (document.getElementById('tabla-metodologias')) {
            window.chatbot = new MetodologiasChatbot();
        }
    });
} else {
    if (document.getElementById('tabla-metodologias')) {
        window.chatbot = new MetodologiasChatbot();
    }
}

