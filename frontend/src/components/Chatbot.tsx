import React, { useState, useEffect, useRef } from 'react';
import { useLanguage } from '../contexts/LanguageContext';
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

// SVG Icons
const Icons = {
  beach: () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10 10-4.5 10-10S17.5 2 12 2z" />
      <path d="M12 2v20M2 12h20" />
      <path d="M12 2C9.5 2 7.5 6.5 7.5 12s2 10 4.5 10M12 2c2.5 0 4.5 4.5 4.5 10s-2 10-4.5 10" />
    </svg>
  ),
  home: () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
      <polyline points="9 22 9 12 15 12 15 22" />
    </svg>
  ),
  luxury: () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
    </svg>
  ),
  user: () => (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
      <circle cx="12" cy="7" r="4" />
    </svg>
  ),
  bot: () => (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
      <path d="M7 11V7a5 5 0 0 1 10 0v4" />
    </svg>
  ),
  send: () => (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <line x1="22" y1="2" x2="11" y2="13" />
      <polygon points="22 2 15 22 11 13 2 9 22 2" />
    </svg>
  ),
  book: () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
      <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
    </svg>
  ),
  plus: () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <line x1="12" y1="5" x2="12" y2="19" />
      <line x1="5" y1="12" x2="19" y2="12" />
    </svg>
  ),
  message: () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
    </svg>
  ),
  globe: () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <circle cx="12" cy="12" r="10" />
      <line x1="2" y1="12" x2="22" y2="12" />
      <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
    </svg>
  ),
};

export default function Chatbot() {
  const { language, t, toggleLanguage } = useLanguage();

  const exampleQueries = [
    { text: t.chatbot.queryBeaches, icon: 'beach', label: t.chatbot.exampleBeaches },
    { text: t.chatbot.queryBedrooms, icon: 'home', label: t.chatbot.exampleBedrooms },
    { text: t.chatbot.queryLuxury, icon: 'luxury', label: t.chatbot.exampleLuxury },
  ];

  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content: t.chatbot.welcome,
      timestamp: new Date(),
    },
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [conversations, setConversations] = useState<Array<{ id: string; title: string; timestamp: Date; message_count: number }>>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const isProcessingRef = useRef(false);

  // Update welcome message when language changes
  useEffect(() => {
    setMessages(prev => [
      {
        ...prev[0],
        content: t.chatbot.welcome
      },
      ...prev.slice(1)
    ]);
  }, [language, t.chatbot.welcome]);

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
      const response = await fetch(`${API_URL.replace('/chat/', '/conversations/')}`);
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
      const response = await fetch(`${API_URL.replace('/chat/', '/conversations/')}${convId}/`);
      if (response.ok) {
        const data = await response.json();

        const loadedMessages: Message[] = data.messages.map((msg: any) => ({
          id: msg.id,
          role: msg.role,
          content: msg.content,
          sources: msg.sources,
          timestamp: new Date(msg.created_at)
        }));

        const welcomeMessage: Message = {
          id: 'welcome',
          role: 'assistant',
          content: t.chatbot.welcome,
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

    const paragraphs = content.split('\n\n');

    return paragraphs.map((para, idx) => {
      const trimmed = para.trim();

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

      const lines = para.split('\n');
      const isListItem = lines.every(line =>
        line.trim().startsWith('•') ||
        line.trim().startsWith('-') ||
        line.trim().startsWith('*') ||
        /^\d+\./.test(line.trim())
      );

      if (isListItem) {
        const items = lines.map(line => {
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

      const formatted = formatInlineElements(trimmed);
      return <p key={idx}>{formatted}</p>;
    });
  };

  const formatInlineElements = (text: string): (string | React.ReactElement)[] => {
    const parts: (string | React.ReactElement)[] = [];
    let currentIndex = 0;

    const regex = /(\*\*.*?\*\*|`[^`]+`)/g;
    let match;

    while ((match = regex.exec(text)) !== null) {
      if (match.index > currentIndex) {
        parts.push(text.substring(currentIndex, match.index));
      }

      const matched = match[0];
      if (matched.startsWith('**') && matched.endsWith('**')) {
        parts.push(<strong key={match.index}>{matched.slice(2, -2)}</strong>);
      } else if (matched.startsWith('`') && matched.endsWith('`')) {
        parts.push(<code key={match.index}>{matched.slice(1, -1)}</code>);
      }

      currentIndex = match.index + matched.length;
    }

    if (currentIndex < text.length) {
      parts.push(text.substring(currentIndex));
    }

    return parts.length > 0 ? parts : [text];
  };

  const handleSendMessage = async (messageText?: string) => {
    const text = messageText || inputValue.trim();
    if (!text || isLoading) return;

    if (isProcessingRef.current) {
      console.log('⚠️ Already processing, skipping duplicate call');
      return;
    }

    isProcessingRef.current = true;
    console.log('🚀 handleSendMessage called - PROCESSING');

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
                setMessages((prev) =>
                  prev.map((msg) =>
                    msg.id === assistantMessageId
                      ? { ...msg, id: parsed.message_id, sources }
                      : msg
                  )
                );
                loadConversations();
              } else if (parsed.type === 'error') {
                throw new Error(parsed.error);
              }
            } catch (e) {
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

      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantMessageId
            ? {
              ...msg,
              content: `Sorry, there was an error processing your request.\n\nError: ${error instanceof Error ? error.message : 'Unknown error'
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
    setTimeout(() => handleSendMessage(query), 100);
  };

  const handleNewConversation = () => {
    if (conversationId && messages.length > 1) {
      setConversations(prev => [{
        id: conversationId,
        title: messages[1]?.content.substring(0, 50) || 'New Conversation',
        timestamp: new Date(),
        message_count: messages.length - 1
      }, ...prev]);
    }
    setMessages([{
      id: 'welcome',
      role: 'assistant',
      content: t.chatbot.welcome,
      timestamp: new Date(),
    }]);
    setConversationId(null);
  };

  return (
    <div className="chatbot-container">
      {/* Left Sidebar */}
      <div className="chatbot-sidebar">
        <div className="sidebar-header">
          <div className="sidebar-title-row">
            <h2>{t.chatbot.conversations}</h2>
            <button
              className="language-toggle-btn"
              onClick={toggleLanguage}
              title={language === 'en' ? t.chatbot.changeToSpanish : t.chatbot.changeToEnglish}
            >
              <Icons.globe />
              <span>{language === 'en' ? 'ES' : 'EN'}</span>
            </button>
          </div>
          <button
            className="new-conversation-btn"
            onClick={handleNewConversation}
            title={t.chatbot.newConversation}
          >
            <Icons.plus />
            <span>{t.chatbot.newChat}</span>
          </button>
        </div>
        <div className="conversations-list">
          {conversations.length === 0 ? (
            <div className="empty-conversations">
              <Icons.message />
              <p>{t.chatbot.noConversations}</p>
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
                    {conv.timestamp.toLocaleDateString()} • {conv.message_count} {t.chatbot.messages}
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="chatbot-main">
        <div className="chatbot-messages">
          {/* Example queries at top */}
          {messages.length === 1 && (
            <div className="example-queries">
              <h3>{t.chatbot.tryAsking}</h3>
              <div className="example-queries-grid">
                {exampleQueries.map((query, idx) => {
                  const IconComponent = Icons[query.icon as keyof typeof Icons];
                  return (
                    <button
                      key={idx}
                      className="example-query-btn"
                      onClick={() => handleExampleQuery(query.text)}
                      disabled={isLoading}
                    >
                      {IconComponent && <IconComponent />}
                      <span>{query.label}</span>
                    </button>
                  );
                })}
              </div>
            </div>
          )}

          {/* Messages */}
          {messages.map((message) => (
            <div key={message.id} className={`message ${message.role}`}>
              <div className="message-avatar">
                {message.role === 'user' ? <Icons.user /> : <Icons.bot />}
              </div>
              <div className="message-content">
                {message.role === 'assistant' && message.content === '' && isLoading ? (
                  <div className="loading-dots">
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                ) : (
                  <>
                    <div className="message-text">
                      {formatMessageContent(message.content)}
                    </div>
                    {message.sources && message.sources.length > 0 && (
                      <div className="message-sources">
                        <div className="sources-title">
                          <Icons.book />
                          <span>{t.chatbot.sources}</span>
                        </div>
                        <div className="sources-list">
                          {message.sources.map((source, idx) => (
                            <div key={idx} className="source-item">
                              <div className="source-header">
                                <span className="source-type">{source.content_type}</span>
                                {source.metadata?.property_name && (
                                  <span className="source-property">{source.metadata.property_name}</span>
                                )}
                              </div>
                              <div className="source-excerpt">{source.excerpt}</div>
                              {source.metadata && (
                                <div className="source-metadata">
                                  {source.metadata.location && (
                                    <span>📍 {source.metadata.location}</span>
                                  )}
                                  {source.metadata.price_usd && (
                                    <span>💰 ${source.metadata.price_usd.toLocaleString()}</span>
                                  )}
                                  {source.metadata.bedrooms && (
                                    <span>🛏️ {source.metadata.bedrooms} {t.chatbot.bedrooms}</span>
                                  )}
                                  {source.metadata.bathrooms && (
                                    <span>🚿 {source.metadata.bathrooms} {t.chatbot.bathrooms}</span>
                                  )}
                                </div>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </>
                )}
              </div>
            </div>
          ))}

          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="chatbot-input-container">
          {/* Example queries */}
          <div className="example-queries-bottom">
            {exampleQueries.map((query, idx) => {
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
              placeholder={t.chatbot.placeholder}
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
