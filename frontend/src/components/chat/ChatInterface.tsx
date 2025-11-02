/**
 * Main Chat Interface Component
 * Handles message display, voice input, and real-time responses
 */

'use client';

import React, { useState, useRef, useEffect } from 'react';
import { Send, Mic, Volume2, StopCircle, ThumbsUp, ThumbsDown, Loader2 } from 'lucide-react';
import { VoiceRecorder } from '@/components/voice/VoiceRecorder';
import { useWebSocket } from '@/hooks/useWebSocket';
import { MessageBubble } from './MessageBubble';
import { TypingIndicator } from './TypingIndicator';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  feedback?: number;
  processingTimeMs?: number;
}

interface ChatInterfaceProps {
  userId?: string;
  conversationId?: string;
  className?: string;
}

export const ChatInterface: React.FC<ChatInterfaceProps> = ({
  userId,
  conversationId,
  className = '',
}) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [currentResponseMessage, setCurrentResponseMessage] = useState<string>('');
  const [isPlaying, setIsPlaying] = useState(false);
  const [audioPlayer, setAudioPlayer] = useState<HTMLAudioElement | null>(null);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  
  const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'ws://localhost:8000';
  
  const { isConnected, sendMessage, sendAudio } = useWebSocket({
    url: `${backendUrl}/api/v1/voice/ws/${Math.random().toString(36).substring(7)}`,
    onMessage: (data) => {
      handleWebSocketMessage(data);
    },
    onAudioData: (audioData) => {
      playAudioResponse(audioData);
    },
    onError: (error) => {
      console.error('WebSocket error:', error);
      addSystemMessage('Connection error. Please refresh the page.');
    },
  });
  
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };
  
  useEffect(() => {
    scrollToBottom();
  }, [messages, currentResponseMessage, isTyping]);
  
  const handleWebSocketMessage = (data: any) => {
    switch (data.type) {
      case 'transcribing_started':
        setIsTyping(true);
        break;
        
      case 'transcription_complete':
        // User message is being processed
        addMessage('user', data.text);
        break;
        
      case 'retrieving_started':
        break;
        
      case 'generating_started':
        setCurrentResponseMessage('');
        break;
        
      case 'response_text':
        setCurrentResponseMessage(data.text);
        break;
        
      case 'response_complete':
        // Finalize the assistant message
        if (currentResponseMessage) {
          const messageId = addMessage('assistant', currentResponseMessage);
          setCurrentResponseMessage('');
          setIsTyping(false);
          
          // Request feedback after delay
          setTimeout(() => {
            if (messageId) {
              promptForFeedback(messageId);
            }
          }, 2000);
        }
        break;
        
      case 'synthesizing_started':
        break;
        
      case 'error':
        addSystemMessage(`Error: ${data.message}`);
        setIsTyping(false);
        setCurrentResponseMessage('');
        break;
        
      case 'pong':
        // Heartbeat received
        break;
    }
  };
  
  const addMessage = (role: 'user' | 'assistant', content: string): string => {
    const newMessage: Message = {
      id: `msg_${Date.now()}_${Math.random()}`,
      role,
      content,
      timestamp: new Date(),
    };
    
    setMessages(prev => [...prev, newMessage]);
    return newMessage.id;
  };
  
  const addSystemMessage = (content: string) => {
    setMessages(prev => [...prev, {
      id: `sys_${Date.now()}`,
      role: 'assistant',
      content: `🔔 ${content}`,
      timestamp: new Date(),
    }]);
  };
  
  const playAudioResponse = async (audioData: ArrayBuffer) => {
    try {
      // Stop any currently playing audio
      if (audioPlayer) {
        audioPlayer.pause();
        audioPlayer.currentTime = 0;
      }
      
      // Create blob and play
      const audioBlob = new Blob([audioData], { type: 'audio/mpeg' });
      const audioUrl = URL.createObjectURL(audioBlob);
      const audio = new Audio(audioUrl);
      
      setAudioPlayer(audio);
      setIsPlaying(true);
      
      audio.onended = () => {
        setIsPlaying(false);
        URL.revokeObjectURL(audioUrl);
      };
      
      audio.onerror = () => {
        setIsPlaying(false);
        URL.revokeObjectURL(audioUrl);
      };
      
      await audio.play();
    } catch (error) {
      console.error('Failed to play audio:', error);
    }
  };
  
  const handleSendMessage = () => {
    if (!inputText.trim()) return;
    if (!isConnected) {
      addSystemMessage('Not connected to server. Please wait...');
      return;
    }
    
    sendMessage({
      type: 'text_query',
      query: inputText,
      conversation_id: conversationId,
    });
    
    setInputText('');
    setIsTyping(true);
  };
  
  const handleVoiceComplete = async (audioBlob: Blob) => {
    if (!isConnected) {
      addSystemMessage('Not connected to server. Please wait...');
      return;
    }
    
    // Convert blob to array buffer
    const arrayBuffer = await audioBlob.arrayBuffer();
    sendAudio(arrayBuffer);
    setIsTyping(true);
  };
  
  const handleFeedback = async (messageId: string, feedback: number) => {
    // Update local state
    setMessages(prev => prev.map(msg =>
      msg.id === messageId ? { ...msg, feedback } : msg
    ));
    
    // Send feedback to server
    sendMessage({
      type: 'feedback',
      message_id: messageId,
      feedback: feedback,
    });
  };
  
  const promptForFeedback = (messageId: string) => {
    // Could show a toast notification
    console.log(`Requesting feedback for message ${messageId}`);
  };
  
  const stopAudio = () => {
    if (audioPlayer) {
      audioPlayer.pause();
      audioPlayer.currentTime = 0;
      setIsPlaying(false);
    }
  };
  
  return (
    <div className={`flex flex-col h-full bg-gray-50 ${className}`}>
      {/* Header */}
      <div className="bg-white border-b px-6 py-4 shadow-sm">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-semibold text-gray-900">Knowledge Base Assistant</h1>
            <p className="text-sm text-gray-500 mt-1">
              Ask questions about company policies, documentation, and procedures
            </p>
          </div>
          
          <div className="flex items-center gap-2">
            <div className={`flex items-center gap-2 text-sm ${isConnected ? 'text-green-600' : 'text-red-600'}`}>
              <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-600 animate-pulse' : 'bg-red-600'}`} />
              <span>{isConnected ? 'Connected' : 'Disconnected'}</span>
            </div>
            
            {isPlaying && (
              <button
                onClick={stopAudio}
                className="p-2 rounded-full bg-gray-100 hover:bg-gray-200 transition-colors"
                title="Stop audio"
              >
                <StopCircle className="w-5 h-5 text-gray-700" />
              </button>
            )}
          </div>
        </div>
      </div>
      
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {messages.length === 0 && (
          <div className="text-center py-12">
            <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <Mic className="w-8 h-8 text-blue-600" />
            </div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">Welcome to Voice Knowledge Base</h3>
            <p className="text-gray-500 max-w-md mx-auto">
              Ask me anything about company documents, policies, or procedures using voice or text.
            </p>
            <div className="mt-4 text-sm text-gray-400">
              Example: "How do I request time off?" or "What's the company's remote work policy?"
            </div>
          </div>
        )}
        
        {messages.map((message) => (
          <MessageBubble
            key={message.id}
            message={message}
            onFeedback={(feedback) => handleFeedback(message.id, feedback)}
          />
        ))}
        
        {currentResponseMessage && (
          <MessageBubble
            message={{
              id: 'temp',
              role: 'assistant',
              content: currentResponseMessage,
              timestamp: new Date(),
            }}
            isStreaming={true}
          />
        )}
        
        {isTyping && !currentResponseMessage && <TypingIndicator />}
        
        <div ref={messagesEndRef} />
      </div>
      
      {/* Input Area */}
      <div className="bg-white border-t p-4 shadow-lg">
        <div className="flex items-end gap-3 max-w-4xl mx-auto">
          <div className="flex-1">
            <textarea
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSendMessage();
                }
              }}
              placeholder="Type your question here..."
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
              rows={1}
              disabled={!isConnected}
            />
          </div>
          
          <VoiceRecorder
            onAudioComplete={handleVoiceComplete}
            disabled={!isConnected}
          />
          
          <button
            onClick={handleSendMessage}
            disabled={!inputText.trim() || !isConnected}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
          >
            <Send className="w-4 h-4" />
            <span>Send</span>
          </button>
        </div>
        
        <div className="text-center mt-3">
          <p className="text-xs text-gray-400">
            {isConnected ? '🔊 Voice input available • Responses will be read aloud' : '🔄 Connecting to server...'}
          </p>
        </div>
      </div>
    </div>
  );
};