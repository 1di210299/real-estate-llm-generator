import { useState, useEffect, useRef } from 'react';
import './Chatbot.css';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  sources?: Source[];
  timestamp: Date;
}

interface Source {
  document_id: string;
  content_type: string;
  excerpt: string;
  relevance_score: number;
  metadata?: {
    property_name?: string;
    location?: string;
    price_usd?: number;
    bedrooms?: number;
    bathrooms?: number;
  };
}

interface ApiResponse {
  conversation_id: string;
  message_id: string;
  response: string;
  sources: Source[];
  model?: string;
  latency_ms?: number;
  cached?: boolean;
}

const API_URL = import.meta.env.VITE_API_URL 
  ? `${import.meta.env.VITE_API_URL}/chat/`
  : 'http://localhost:8000/chat/';

const EXAMPLE_QUERIES = [
  { text: '¿Propiedades en Tamarindo?', icon: '🏖️', label: 'Playas' },
  { text: 'Casas con 3 cuartos bajo $300K', icon: '🏠', label: '3 habitaciones' },
  { text: '¿Propiedades de lujo con piscina?', icon: '✨', label: 'Lujo' },
];

export default function Chatbot() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content: `¡Hola! 👋 Soy tu asistente de Kelly Properties. Puedo ayudarte a encontrar la propiedad perfecta en Costa Rica. ¿Qué estás buscando?

Puedes preguntar sobre:
• Propiedades por ubicación (Tamarindo, Manuel Antonio, etc.)
• Filtros específicos (precio, habitaciones, amenidades)
• Información sobre una propiedad en particular`,
      timestamp: new Date(),
    },
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async (messageText?: string) => {
    const text = messageText || inputValue.trim();
    if (!text || isLoading) return;

    // Add user message
    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: text,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    try {
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: text,
          conversation_id: conversationId,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data: ApiResponse = await response.json();

      // Save conversation ID
      if (data.conversation_id && !conversationId) {
        setConversationId(data.conversation_id);
      }

      // Add assistant message
      const assistantMessage: Message = {
        id: data.message_id,
        role: 'assistant',
        content: data.response,
        sources: data.sources,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Error:', error);
      
      // Add error message
      const errorMessage: Message = {
        id: Date.now().toString(),
        role: 'assistant',
        content: `Lo siento, hubo un error al procesar tu solicitud.\n\nError: ${error instanceof Error ? error.message : 'Unknown error'}`,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleExampleQuery = (query: string) => {
    setInputValue(query);
    // Auto-send the query
    setTimeout(() => handleSendMessage(query), 100);
  };

  return (
    <div className="chatbot-container">
      <div className="chatbot-wrapper">
        {/* Header */}
        <div className="chatbot-header">
          <div className="header-content">
            <h1>🏡 Kelly Properties Assistant</h1>
            <p>Tu asistente inteligente para propiedades en Costa Rica</p>
          </div>
          
          {/* Example queries */}
          <div className="example-queries">
            {EXAMPLE_QUERIES.map((query, idx) => (
              <button
                key={idx}
                className="example-query-btn"
                onClick={() => handleExampleQuery(query.text)}
                disabled={isLoading}
              >
                <span className="query-icon">{query.icon}</span>
                <span className="query-label">{query.label}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Messages */}
        <div className="chatbot-messages">
          {messages.map((message) => (
            <div key={message.id} className={`message ${message.role}`}>
              <div className="message-avatar">
                {message.role === 'user' ? 'U' : 'K'}
              </div>
              <div className="message-content">
                <div className="message-text">
                  {message.content.split('\n').map((line, idx) => (
                    <span key={idx}>
                      {line}
                      {idx < message.content.split('\n').length - 1 && <br />}
                    </span>
                  ))}
                </div>

                {/* Sources */}
                {message.sources && message.sources.length > 0 && (
                  <div className="message-sources">
                    <div className="sources-title">📚 Fuentes consultadas:</div>
                    {message.sources.map((source, idx) => {
                      const relevance = (source.relevance_score * 100).toFixed(0);
                      const metadata = source.metadata || {};
                      
                      return (
                        <div key={idx} className="source-item">
                          <strong>{idx + 1}.</strong>{' '}
                          {metadata.property_name || source.content_type}
                          {metadata.location && ` - ${metadata.location}`}
                          {metadata.price_usd && (
                            <span className="source-price">
                              {' '}($${metadata.price_usd.toLocaleString()} USD)
                            </span>
                          )}
                          <span className="source-relevance">
                            {' '}(relevancia: {relevance}%)
                          </span>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            </div>
          ))}

          {/* Loading indicator */}
          {isLoading && (
            <div className="message assistant">
              <div className="message-avatar">K</div>
              <div className="message-content">
                <div className="loading-dots">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="chatbot-input-container">
          <input
            type="text"
            className="chatbot-input"
            placeholder="Escribe tu pregunta aquí..."
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            disabled={isLoading}
          />
          <button
            className="send-button"
            onClick={() => handleSendMessage()}
            disabled={isLoading || !inputValue.trim()}
          >
            {isLoading ? '...' : 'Enviar'}
          </button>
        </div>
      </div>
    </div>
  );
}
