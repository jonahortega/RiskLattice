import { useState, useRef, useEffect } from 'react'
import { api, ChatMessage } from '../api/client'
import { MarkdownRenderer } from './MarkdownRenderer'

export function ChatAgent() {
  const [isOpen, setIsOpen] = useState(false)
  const [isMinimized, setIsMinimized] = useState(false)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [inputMessage, setInputMessage] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)
  const welcomeShownRef = useRef(false)

  // Listen for custom event to open chat from button
  useEffect(() => {
    const handleOpenChat = () => {
      setIsOpen(true)
      setIsMinimized(false)
    }
    window.addEventListener('openChatAgent', handleOpenChat)
    return () => window.removeEventListener('openChatAgent', handleOpenChat)
  }, [])

  // Removed auto-scroll - let user manually scroll to see responses

  // Only focus input when opening, don't auto-scroll on new messages
  useEffect(() => {
    if (isOpen && !isMinimized) {
      inputRef.current?.focus()
    }
  }, [isOpen, isMinimized])

  // Add welcome message when first opened (only once)
  useEffect(() => {
    if (isOpen && messages.length === 0 && !isMinimized && !welcomeShownRef.current) {
      const welcomeMessage: ChatMessage = {
        role: 'assistant',
              content: "I'm a financial AI assistant. I can help explain risk scores, volatility, market trends, and answer questions about stocks and the market. Ask me about any financial concept or stock analysis!"
      }
      setMessages([welcomeMessage])
      welcomeShownRef.current = true
    }
  }, [isOpen, isMinimized, messages.length])

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!inputMessage.trim() || isLoading) return

    const userMessage = inputMessage.trim()
    setInputMessage('')
    
    // Add user message immediately
    const newUserMessage: ChatMessage = { role: 'user', content: userMessage }
    setMessages(prev => [...prev, newUserMessage])
    setIsLoading(true)

    try {
      const response = await api.chatWithAgent({
        message: userMessage,
        conversation_history: messages
      })
      
      setMessages(response.data.conversation_history)
    } catch (error) {
      console.error('Error chatting with agent:', error)
      const errorMessage: ChatMessage = {
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.'
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const handleClear = () => {
    setMessages([])
  }

  // Don't render the floating button - it's handled by the button in the header
  if (!isOpen) {
    return null
  }

  const containerClasses = `fixed ${isMinimized ? 'top-6 right-6' : 'top-6 right-6'} z-50 transition-all duration-300`

  return (
    <div className={containerClasses}>
      <div className={`bg-slate-900/95 backdrop-blur-sm rounded-xl border border-cyan-500/20 shadow-2xl shadow-cyan-500/20 ${
        isMinimized ? 'w-80 h-16' : 'w-[500px] h-[600px]'
      } flex flex-col overflow-hidden`}>
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-cyan-500/20">
          <div className="flex items-center space-x-2">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-cyan-400">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
            </svg>
            <h3 className="text-lg font-semibold text-cyan-200 font-mono">AI Market Assistant</h3>
          </div>
          <div className="flex items-center space-x-2">
            {messages.length > 0 && (
              <button
                onClick={handleClear}
                className="text-cyan-400/70 hover:text-cyan-300 text-sm font-mono transition"
              >
                Clear
              </button>
            )}
            <button
              onClick={() => setIsMinimized(!isMinimized)}
              className="text-cyan-400/70 hover:text-cyan-300 transition"
              title={isMinimized ? "Maximize" : "Minimize"}
            >
              {isMinimized ? (
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3"></path>
                </svg>
              ) : (
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M8 3v3a2 2 0 0 1-2 2H3m18 0h-3a2 2 0 0 1-2-2V3m0 18v-3a2 2 0 0 1 2-2h3M3 16h3a2 2 0 0 1 2 2v3"></path>
                </svg>
              )}
            </button>
            <button
              onClick={() => setIsOpen(false)}
              className="text-cyan-400/70 hover:text-cyan-300 transition"
              title="Close"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="18" y1="6" x2="6" y2="18"></line>
                <line x1="6" y1="6" x2="18" y2="18"></line>
              </svg>
            </button>
          </div>
        </div>

        {!isMinimized && (
          <>
            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4 break-words">
              {messages.length === 0 ? (
                <div className="text-center text-cyan-400/70 mt-8 font-mono text-sm">
                  <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="mx-auto mb-3 opacity-50">
                    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
                  </svg>
                  <p>Ask me anything about stocks, risk scores, market trends, or financial concepts!</p>
                  <p className="mt-2 text-xs opacity-70">Examples:</p>
                  <ul className="mt-2 text-xs space-y-1 opacity-70">
                    <li>"What is a risk score?"</li>
                    <li>"Explain volatility"</li>
                    <li>"How is AAPL performing?"</li>
                  </ul>
                </div>
              ) : (
                <>
                  {messages.map((msg, idx) => (
                    <div
                      key={idx}
                      className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                    >
                      <div
                        className={`max-w-[85%] min-w-0 rounded-lg p-3 ${
                          msg.role === 'user'
                            ? 'bg-gradient-to-r from-cyan-500 to-blue-500 text-white'
                            : 'bg-slate-800/50 text-cyan-100 border border-cyan-500/20'
                        } break-words overflow-wrap-anywhere`}
                        style={{ wordWrap: 'break-word', overflowWrap: 'anywhere' }}
                      >
                        {msg.role === 'user' ? (
                          <p className="text-sm font-mono whitespace-pre-wrap break-words">{msg.content}</p>
                        ) : (
                          <div className="text-sm font-mono break-words overflow-wrap-anywhere">
                            <MarkdownRenderer content={msg.content} />
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                  {isLoading && (
                    <div className="flex justify-start">
                      <div className="bg-slate-800/50 text-cyan-100 border border-cyan-500/20 rounded-lg p-3">
                        <div className="flex space-x-2">
                          <div className="w-2 h-2 bg-cyan-400 rounded-full animate-bounce"></div>
                          <div className="w-2 h-2 bg-cyan-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                          <div className="w-2 h-2 bg-cyan-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                        </div>
                      </div>
                    </div>
                  )}
                </>
              )}
            </div>

            {/* Input */}
            <form onSubmit={handleSendMessage} className="p-4 border-t border-cyan-500/20">
              <div className="flex gap-2">
                <input
                  ref={inputRef}
                  type="text"
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  placeholder="Ask about stocks, risk, markets..."
                  className="flex-1 px-4 py-2 bg-slate-800/50 border border-cyan-500/30 rounded-lg focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500 text-cyan-100 placeholder-cyan-400/50 font-mono text-sm"
                  disabled={isLoading}
                />
                <button
                  type="submit"
                  disabled={!inputMessage.trim() || isLoading}
                  className="px-4 py-2 bg-gradient-to-r from-cyan-500 to-blue-500 text-white rounded-lg hover:shadow-lg hover:shadow-cyan-500/50 transition disabled:opacity-50 disabled:cursor-not-allowed font-mono border border-cyan-400/30 flex items-center justify-center"
                  title="Send message"
                >
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <line x1="22" y1="2" x2="11" y2="13"></line>
                    <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
                  </svg>
                </button>
              </div>
            </form>
          </>
        )}
      </div>
    </div>
  )
}

