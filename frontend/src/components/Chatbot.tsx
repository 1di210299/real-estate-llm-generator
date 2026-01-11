import React, { useState, useEffect, useRef } from 'react';
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
  plus: () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <line x1="12" y1="5" x2="12" y2="19"/>
      <line x1="5" y1="12" x2="19" y2="12"/>
    </svg>
  ),
  message: () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
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
  const [conversations, setConversations] = useState<Array<{id: string; title: string; timestamp: Date; message_count: number}>>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const isProcessingRef = useRef(false);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Load conversations on mount
  useEffect(() => {
    loadConversations();
  }, []);

  const loadConversations = async () => {
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/chat/conversations/`);
      if (response.ok) {
        const data = await response.json();
        const formattedConversations = data.conversations.map((conv: any) => ({
          id: conv.id,
          title: conv.title,
          timestamp: new Date(conv.updated_at),
          message_count: conv.message_count
        }));
        setConversations(formattedConversations);
      }
    } catch (error) {
      console.error('Error loading conversations:', error);
    }
  };

  const loadConversation = async (convId: string) => {
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/chat/conversations/${convId}/`);
      if (response.ok) {
        const data = await response.json();
        const loadedMessages: Message[] = data.messages.map((msg: any) => ({
          id: msg.id,
          role: msg.role,
          content: msg.content,
          sources: msg.sources,
          timestamp: new Date(msg.created_at)
        }));
        
        // Add welcome message at the beginning if not present
        const welcomeMessage: Message = {
          id: 'welcome',
          role: 'assistant',
          content: `Hello! I'm your Kelly Properties assistant. I can help you find the perfect property in Costa Rica. What are you looking for?

You can ask about:
• Properties by location (Tamarindo, Manuel Antonio, etc.)
• Specific filters (price, bedrooms, amenities)
• Information about a particular property`,
          timestamp: new Date(data.messages[0]?.created_at || new Date()),
        };
        
        setMessages([welcomeMessage, ...loadedMessages]);
        setConversationId(convId);
      }
    } catch (error) {
      console.error('Error loading conversation:', error);
    }
  };

  // Format message content with proper HTML
  const formatMessageContent = (content: string) => {
    if (!content) return '';
    
    // Split by double newlines first (paragraphs)
    const paragraphs = content.split('\n\n');
    
    return paragraphs.map((para, idx) => {
      const trimmed = para.trim();
      
      // Check if it's a heading (### or ##)
      if (trimmed.startsWith('###')) {
        const text = trimmed.replace(/^###\s*/, '');
        const formatted = formatInlineElements(text);
        return <h3 key={idx}>{formatted}</h3>;
      }
      if (trimmed.startsWith('##')) {
        const text = trimmed.replace(/^##\s*/, '');
        const formatted = formatInlineElements(text);
        return <h2 key={idx}>{formatted}</h2>;
      }
      if (trimmed.startsWith('#')) {
        const text = trimmed.replace(/^#\s*/, '');
        const formatted = formatInlineElements(text);
        return <h2 key={idx}>{formatted}</h2>;
      }
      
      // Check if it's a list
      const lines = para.split('\n');
      const isListItem = lines.every(line => 
        line.trim().startsWith('•') || 
        line.trim().startsWith('-') || 
        line.trim().startsWith('*') ||
        /^\d+\./.test(line.trim())
      );
      
      if (isListItem) {
        const items = lines
          .filter(line => line.trim())
          .map(line => {
            const cleaned = line.replace(/^[•\-*]\s*/, '').replace(/^\d+\.\s*/, '').trim();
            return formatInlineElements(cleaned);
          });
        
        return (
          <ul key={idx}>
            {items.map((item, i) => (
              <li key={i}>{item}</li>
            ))}
          </ul>
        );
      }
      
      // Regular paragraph with inline formatting
      const formatted = formatInlineElements(trimmed);
      return <p key={idx}>{formatted}</p>;
    });
  };

  // Helper to format inline elements like **bold**, `code`, etc.
  const formatInlineElements = (text: string): (string | React.ReactElement)[] => {
    const parts: (string | React.ReactElement)[] = [];
    let currentIndex = 0;
    
    // Regex to match **bold**, `code`, or plain text
    const regex = /(\*\*.*?\*\*|`[^`]+`)/g;
    let match;
    
    while ((match = regex.exec(text)) !== null) {
      // Add text before match
      if (match.index > currentIndex) {
        parts.push(text.substring(currentIndex, match.index));
      }
      
      const matched = match[0];
      if (matched.startsWith('**') && matched.endsWith('**')) {
        // Bold text
        parts.push(<strong key={match.index}>{matched.slice(2, -2)}</strong>);
      } else if (matched.startsWith('`') && matched.endsWith('`')) {
        // Code text
        parts.push(<code key={match.index}>{matched.slice(1, -1)}</code>);
      }
      
      currentIndex = match.index + matched.length;
    }
    
    // Add remaining text
    if (currentIndex < text.length) {
      parts.push(text.substring(currentIndex));
    }
    
    return parts.length > 0 ? parts : [text];
  };

  const handleSendMessage = async (messageText?: string) => {
    const text = messageText || inputValue.trim();
    if (!text || isLoading) return;

    // Prevent double execution
    if (isProcessingRef.current) {
      console.log('⚠️ Already processing, skipping duplicate call');
      return;
    }

    isProcessingRef.current = true;
    console.log('🚀 handleSendMessage called - PROCESSING');

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

    // Create placeholder for assistant message
    const assistantMessageId = `assistant-${Date.now()}`;
    const assistantMessage: Message = {
      id: assistantMessageId,
      role: 'assistant',
      content: '',
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, assistantMessage]);

    try {
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: text,
          conversation_id: conversationId,
          stream: true,
        }),
      });

      console.log('📥 Response status:', response.status);
      console.log('📥 Response type:', response.headers.get('content-type'));

      if (!response.ok) {
        const errorText = await response.text();
        console.error('❌ Error response:', errorText);
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      // Handle streaming response
      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let accumulatedContent = '';
      let currentConversationId = conversationId;
      let sources: Source[] | undefined;

      if (!reader) {
        throw new Error('No reader available');
      }

      while (true) {
        const { done, value } = await reader.read();
        
        if (done) {
          console.log('✅ Stream complete');
          break;
        }

        // Decode the chunk
        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6);
            
            try {
              const parsed = JSON.parse(data);
              
              if (parsed.type === 'conversation_id') {
                currentConversationId = parsed.conversation_id;
                if (!conversationId) {
                  setConversationId(currentConversationId);
                }
              } else if (parsed.type === 'content') {
                accumulatedContent += parsed.content;
                // Update message with accumulated content
                setMessages((prev) => 
                  prev.map((msg) =>
                    msg.id === assistantMessageId
                      ? { ...msg, content: accumulatedContent }
                      : msg
                  )
                );
              } else if (parsed.type === 'sources') {
                sources = parsed.sources;
              } else if (parsed.type === 'done') {
                console.log('✅ STREAMING DONE - Final message:', {
                  totalLength: accumulatedContent.length,
                  hasNewlines: accumulatedContent.includes('\n'),
                  hasDoubleNewlines: accumulatedContent.includes('\n\n'),
                  preview: accumulatedContent.substring(0, 150)
                });
                // Final update with all data
                setMessages((prev) =>
                  prev.map((msg) =>
                    msg.id === assistantMessageId
                      ? { ...msg, id: parsed.message_id, sources }
                      : msg
                  )
                );
                // Reload conversations list to show new conversation
                loadConversations();
              } else if (parsed.type === 'error') {
                throw new Error(parsed.error);
              }
            } catch (e) {
              // Ignore JSON parse errors for incomplete chunks
              if (e instanceof SyntaxError) {
                continue;
              }
              throw e;
            }
          }
        }
      }
    } catch (error) {
      console.error('Error:', error);
      
      // Update the assistant message with error
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantMessageId
            ? {
                ...msg,
                content: `Sorry, there was an error processing your request.\n\nError: ${
                  error instanceof Error ? error.message : 'Unknown error'
                }`,
              }
            : msg
        )
      );
    } finally {
      setIsLoading(false);
      isProcessingRef.current = false;
      console.log('✅ Processing complete, ready for next message');
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

  const handleNewConversation = () => {
    // Save current conversation if it has messages
    if (conversationId && messages.length > 1) {
      setConversations(prev => [{
        id: conversationId,
        title: messages[1]?.content.substring(0, 50) || 'New Conversation',
        timestamp: new Date(),
        message_count: messages.length - 1
      }, ...prev]);
    }
    // Reset to new conversation
    setMessages([{
      id: 'welcome',
      role: 'assistant',
      content: `Hello! I'm your Kelly Properties assistant. I can help you find the perfect property in Costa Rica. What are you looking for?

You can ask about:
• Properties by location (Tamarindo, Manuel Antonio, etc.)
• Specific filters (price, bedrooms, amenities)
• Information about a particular property`,
      timestamp: new Date(),
    }]);
    setConversationId(null);
  };

  return (
    <div className="chatbot-container">
      {/* Left Sidebar */}
      <div className="chatbot-sidebar">
        <div className="sidebar-header">
          <h2>Conversations</h2>
          <button 
            className="new-conversation-btn" 
            onClick={handleNewConversation} 
            title="New conversation"
          >
            <Icons.plus />
            <span>New Chat</span>
          </button>
        </div>
        <div className="conversations-list">
          {conversations.length === 0 ? (
            <div className="empty-conversations">
              <Icons.message />
              <p>No conversations yet</p>
            </div>
          ) : (
            conversations.map((conv) => (
              <div 
                key={conv.id} 
                className={`conversation-item ${conversationId === conv.id ? 'active' : ''}`}
                onClick={() => loadConversation(conv.id)}
                style={{ cursor: 'pointer' }}
              >
                <Icons.message />
                <div className="conversation-info">
                  <div className="conversation-title">{conv.title}</div>
                  <div className="conversation-date">
                    {conv.timestamp.toLocaleDateString()} • {conv.message_count} messages
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="chatbot-wrapper">
        {/* Messages */}
        <div className="chatbot-messages">
          {messages.map((message) => (
            <div key={message.id} className={`message ${message.role}`}>
              <div className="message-avatar">
                {message.role === 'user' ? <Icons.user /> : <Icons.bot />}
              </div>
              <div className="message-content">
                <div className="message-text">
                  {formatMessageContent(message.content)}
                  {/* Show cursor when streaming and this is the last message */}
                  {isLoading && message.role === 'assistant' && messages[messages.length - 1].id === message.id && (
                    <span className="streaming-cursor"></span>
                  )}
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
          {/* Example queries */}
          <div className="example-queries-bottom">
            {EXAMPLE_QUERIES.map((query, idx) => {
              const IconComponent = Icons[query.icon as keyof typeof Icons];
              return (
                <button
                  key={idx}
                  className="example-query-btn-small"
                  onClick={() => handleExampleQuery(query.text)}
                  disabled={isLoading}
                  title={query.text}
                >
                  {IconComponent && <IconComponent />}
                  <span>{query.label}</span>
                </button>
              );
            })}
          </div>
          
          <div className="input-row">
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
    </div>
  );
}
