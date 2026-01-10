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

// DEBUG LOGS
console.log('🔧 Chatbot Configuration:');
console.log('  - VITE_API_URL:', import.meta.env.VITE_API_URL);
console.log('  - Final API_URL:', API_URL);
console.log('  - Mode:', import.meta.env.MODE);
console.log('  - All env vars:', import.meta.env);

const EXAMPLE_QUERIES = [
  { text: 'Properties in Tamarindo?', icon: 'beach', label: 'Beaches' },
  { text: 'Houses with 3 bedrooms under $300K', icon: 'home', label: '3 bedrooms' },
  { text: 'Luxury properties with pool?', icon: 'luxury', label: 'Luxury' },
];

// SVG Icons
const Icons = {
  beach: () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10 10-4.5 10-10S17.5 2 12 2z"/>
      <path d="M12 2v20M2 12h20"/>
      <path d="M12 2C9.5 2 7.5 6.5 7.5 12s2 10 4.5 10M12 2c2.5 0 4.5 4.5 4.5 10s-2 10-4.5 10"/>
    </svg>
  ),
  home: () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>
      <polyline points="9 22 9 12 15 12 15 22"/>
    </svg>
  ),
  luxury: () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
    </svg>
  ),
  user: () => (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
      <circle cx="12" cy="7" r="4"/>
    </svg>
  ),
  bot: () => (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
      <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
    </svg>
  ),
  send: () => (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <line x1="22" y1="2" x2="11" y2="13"/>
      <polygon points="22 2 15 22 11 13 2 9 22 2"/>
    </svg>
  ),
  book: () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/>
      <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
    </svg>
  ),
};

export default function Chatbot() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content: `Hello! I'm your Kelly Properties assistant. I can help you find the perfect property in Costa Rica. What are you looking for?

You can ask about:
• Properties by location (Tamarindo, Manuel Antonio, etc.)
• Specific filters (price, bedrooms, amenities)
• Information about a particular property`,
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

    console.log('📤 Sending message to:', API_URL);
    console.log('📤 Message payload:', { message: text, conversation_id: conversationId });

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

      console.log('📥 Response status:', response.status);
      console.log('📥 Response ok:', response.ok);

      if (!response.ok) {
        const errorText = await response.text();
        console.error('❌ Error response:', errorText);
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
        content: `Sorry, there was an error processing your request.\n\nError: ${error instanceof Error ? error.message : 'Unknown error'}`,
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
            <h1>Kelly Properties Assistant</h1>
            <p>Your intelligent assistant for properties in Costa Rica</p>
          </div>
          
          {/* Example queries */}
          <div className="example-queries">
            {EXAMPLE_QUERIES.map((query, idx) => {
              const IconComponent = Icons[query.icon as keyof typeof Icons];
              return (
                <button
                  key={idx}
                  className="example-query-btn"
                  onClick={() => handleExampleQuery(query.text)}
                  disabled={isLoading}
                >
                  <span className="query-icon">{IconComponent && <IconComponent />}</span>
                  <span className="query-label">{query.label}</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Messages */}
        <div className="chatbot-messages">
          {messages.map((message) => (
            <div key={message.id} className={`message ${message.role}`}>
              <div className="message-avatar">
                {message.role === 'user' ? <Icons.user /> : <Icons.bot />}
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
                    <div className="sources-title">
                      <Icons.book /> Sources consulted:
                    </div>
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
                              {metadata.price_usd ? ` ($${metadata.price_usd.toLocaleString()} USD)` : ''}
                            </span>
                          )}
                          <span className="source-relevance">
                            {' '}(relevance: {relevance}%)
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
              <div className="message-avatar"><Icons.bot /></div>
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
            placeholder="Type your question here..."
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
            {isLoading ? '...' : <Icons.send />}
          </button>
        </div>
      </div>
    </div>
  );
}
