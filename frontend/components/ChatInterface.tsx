'use client'

import { useState, useRef, useEffect } from 'react'

interface Message {
  role: 'user' | 'assistant'
  content: string
  sources?: string[]
  timestamp: Date
}

interface ChatInterfaceProps {
  onSendMessage?: (message: string) => void
}

export default function ChatInterface({ onSendMessage }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [isConnected, setIsConnected] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  // Auto-scroll to bottom when new messages arrive
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // Check backend connection on component mount
  useEffect(() => {
    checkConnection()
  }, [])

  const checkConnection = async () => {
    try {
      const response = await fetch('/api/health')
      if (response.ok) {
        const data = await response.json()
        setIsConnected(data.status === 'healthy')
      }
    } catch (error) {
      setIsConnected(false)
    }
  }

  const sendMessage = async () => {
    if (!input.trim() || isLoading) return

    const userMessage: Message = {
      role: 'user',
      content: input.trim(),
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setIsLoading(true)

    // Call optional callback
    onSendMessage?.(input.trim())

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: input.trim() }),
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || `HTTP ${response.status}`)
      }

      const data = await response.json()
      const assistantMessage: Message = {
        role: 'assistant',
        content: data.response,
        sources: data.sources || [],
        timestamp: new Date()
      }

      setMessages(prev => [...prev, assistantMessage])
    } catch (error) {
      console.error('Chat error:', error)
      const errorMessage: Message = {
        role: 'assistant',
        content: `Sorry, I encountered an error: ${error instanceof Error ? error.message : 'Unknown error'}. Please make sure Ollama is running and the backend server is started.`,
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  const clearChat = () => {
    setMessages([])
  }

  const refreshIndex = async () => {
    try {
      setIsLoading(true)
      const response = await fetch('/api/refresh', {
        method: 'POST',
      })

      if (response.ok) {
        const data = await response.json()
        const successMessage: Message = {
          role: 'assistant',
          content: `✅ ${data.message}`,
          timestamp: new Date()
        }
        setMessages(prev => [...prev, successMessage])
      } else {
        throw new Error('Failed to refresh index')
      }
    } catch (error) {
      const errorMessage: Message = {
        role: 'assistant',
        content: `❌ Error refreshing index: ${error instanceof Error ? error.message : 'Unknown error'}`,
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const formatTimestamp = (date: Date) => {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  }

  const getFileBasename = (filepath: string) => {
    return filepath.split('/').pop() || filepath
  }

  return (
    <div className="flex flex-col h-full bg-white rounded-lg shadow-lg">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200">
        <div className="flex items-center space-x-3">
          <h2 className="text-lg font-semibold text-gray-800">ChatDBT</h2>
          <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
          <span className="text-sm text-gray-500">
            {isConnected ? 'Connected' : 'Disconnected'}
          </span>
        </div>
        
        <div className="flex space-x-2">
          <button
            onClick={refreshIndex}
            disabled={isLoading}
            className="px-3 py-1 text-sm bg-blue-100 text-blue-700 rounded hover:bg-blue-200 disabled:opacity-50"
            title="Refresh DBT index"
          >
            🔄 Refresh
          </button>
          <button
            onClick={clearChat}
            className="px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200"
            title="Clear chat history"
          >
            🗑️ Clear
          </button>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="text-center text-gray-500 mt-20">
            <div className="mb-4">
              <svg className="w-16 h-16 mx-auto text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-3.582 8-8 8a8.955 8.955 0 01-4.951-1.488A11.956 11.956 0 013 20c0-9.925 8.075-18 18-18z" />
              </svg>
            </div>
            <p className="text-lg mb-2">Welcome to ChatDBT!</p>
            <p className="text-sm mb-4">Ask me anything about your dbt project.</p>
            <div className="text-left max-w-md mx-auto space-y-2 text-sm">
              <p className="font-medium">Try asking:</p>
              <ul className="space-y-1 text-gray-600">
                <li>• "What models do I have?"</li>
                <li>• "Describe the customer table"</li>
                <li>• "How is revenue calculated?"</li>
                <li>• "What are the dependencies for user_metrics?"</li>
                <li>• "Show me all staging models"</li>
              </ul>
            </div>
          </div>
        ) : (
          messages.map((message, index) => (
            <div key={index} className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-3xl ${message.role === 'user' ? 'ml-12' : 'mr-12'}`}>
                <div className={`p-3 rounded-lg ${
                  message.role === 'user' 
                    ? 'bg-blue-500 text-white' 
                    : 'bg-gray-100 text-gray-800'
                }`}>
                  <p className="whitespace-pre-wrap">{message.content}</p>
                  
                  {/* Sources */}
                  {message.sources && message.sources.length > 0 && (
                    <div className="mt-3 pt-2 border-t border-gray-300">
                      <p className="text-xs font-semibold mb-1">📁 Sources:</p>
                      <div className="flex flex-wrap gap-1">
                        {message.sources.slice(0, 5).map((source, idx) => (
                          <span
                            key={idx}
                            className="inline-block px-2 py-1 text-xs bg-gray-200 text-gray-700 rounded"
                            title={source}
                          >
                            {getFileBasename(source)}
                          </span>
                        ))}
                        {message.sources.length > 5 && (
                          <span className="text-xs text-gray-500">
                            +{message.sources.length - 5} more
                          </span>
                        )}
                      </div>
                    </div>
                  )}
                </div>
                
                {/* Timestamp */}
                <div className={`text-xs text-gray-400 mt-1 ${
                  message.role === 'user' ? 'text-right' : 'text-left'
                }`}>
                  {formatTimestamp(message.timestamp)}
                </div>
              </div>
            </div>
          ))
        )}
        
        {/* Loading indicator */}
        {isLoading && (
          <div className="flex justify-start">
            <div className="max-w-3xl mr-12">
              <div className="bg-gray-100 text-gray-800 p-3 rounded-lg">
                <div className="flex items-center space-x-2">
                  <div className="flex space-x-1">
                    <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce"></div>
                    <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                    <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                  </div>
                  <span className="text-sm">Thinking...</span>
                </div>
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Input area */}
      <div className="p-4 border-t border-gray-200">
        <div className="flex space-x-3">
          <div className="flex-1 relative">
            <textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder={isConnected ? "Ask about your dbt project..." : "Backend disconnected. Please check the server."}
              className="w-full p-3 pr-12 border border-gray-300 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-50"
              rows={Math.min(4, Math.max(1, input.split('\n').length))}
              disabled={isLoading || !isConnected}
              style={{ minHeight: '48px', maxHeight: '120px' }}
            />
            
            {/* Character count */}
            {input.length > 500 && (
              <div className="absolute bottom-2 right-2 text-xs text-gray-400">
                {input.length}/2000
              </div>
            )}
          </div>
          
          <button
            onClick={sendMessage}
            disabled={isLoading || !input.trim() || !isConnected}
            className="px-6 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors flex items-center space-x-2"
          >
            {isLoading ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                <span>Sending</span>
              </>
            ) : (
              <>
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                </svg>
                <span>Send</span>
              </>
            )}
          </button>
        </div>
        
        {/* Connection status warning */}
        {!isConnected && (
          <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded text-sm text-red-700">
            ⚠️ Cannot connect to backend. Make sure Ollama is running and the backend server is started.
          </div>
        )}
      </div>
    </div>
  )
}