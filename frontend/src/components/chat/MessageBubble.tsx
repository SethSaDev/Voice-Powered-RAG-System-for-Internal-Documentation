/**
 * Individual Message Bubble Component
 * Displays user or assistant messages with feedback buttons
 */

import React, { useState } from 'react';
import { ThumbsUp, ThumbsDown, Copy, Check, User, Bot, Clock } from 'lucide-react';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  feedback?: number;
  processingTimeMs?: number;
}

interface MessageBubbleProps {
  message: Message;
  onFeedback?: (feedback: number) => void;
  isStreaming?: boolean;
}

export const MessageBubble: React.FC<MessageBubbleProps> = ({
  message,
  onFeedback,
  isStreaming = false,
}) => {
  const [copied, setCopied] = useState(false);
  const isUser = message.role === 'user';
  
  const handleCopy = async () => {
    await navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };
  
  const formatTime = (date: Date) => {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };
  
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} animate-slide-in`}>
      <div className={`flex gap-3 max-w-[80%] ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
        {/* Avatar */}
        <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
          isUser ? 'bg-blue-600' : 'bg-gray-600'
        }`}>
          {isUser ? (
            <User className="w-4 h-4 text-white" />
          ) : (
            <Bot className="w-4 h-4 text-white" />
          )}
        </div>
        
        {/* Message Content */}
        <div className={`relative group`}>
          <div className={`rounded-lg px-4 py-2 shadow-sm ${
            isUser
              ? 'bg-blue-600 text-white'
              : 'bg-white text-gray-900 border border-gray-200'
          }`}>
            {/* Processing time indicator (assistant only) */}
            {!isUser && message.processingTimeMs && (
              <div className="text-xs opacity-70 mb-1 flex items-center gap-1">
                <Clock className="w-3 h-3" />
                <span>{message.processingTimeMs}ms</span>
              </div>
            )}
            
            {/* Message text */}
            <div className={`whitespace-pre-wrap break-words ${isStreaming ? 'border-l-4 border-blue-500 pl-3' : ''}`}>
              {message.content}
              {isStreaming && (
                <span className="inline-block w-2 h-4 ml-1 bg-blue-500 animate-blink" />
              )}
            </div>
          </div>
          
          {/* Action Buttons (assistant only) */}
          {!isUser && !isStreaming && (
            <div className="absolute -bottom-8 right-0 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
              <button
                onClick={handleCopy}
                className="p-1 rounded hover:bg-gray-100 transition-colors"
                title="Copy to clipboard"
              >
                {copied ? (
                  <Check className="w-3 h-3 text-green-600" />
                ) : (
                  <Copy className="w-3 h-3 text-gray-500" />
                )}
              </button>
              
              {onFeedback && message.feedback === undefined && (
                <>
                  <button
                    onClick={() => onFeedback(1)}
                    className="p-1 rounded hover:bg-gray-100 transition-colors"
                    title="Helpful"
                  >
                    <ThumbsUp className="w-3 h-3 text-gray-500 hover:text-green-600" />
                  </button>
                  <button
                    onClick={() => onFeedback(-1)}
                    className="p-1 rounded hover:bg-gray-100 transition-colors"
                    title="Not helpful"
                  >
                    <ThumbsDown className="w-3 h-3 text-gray-500 hover:text-red-600" />
                  </button>
                </>
              )}
              
              {message.feedback === 1 && (
                <span className="text-xs text-green-600">✓ Helpful</span>
              )}
              {message.feedback === -1 && (
                <span className="text-xs text-red-600">✗ Not helpful</span>
              )}
            </div>
          )}
          
          {/* Timestamp */}
          <div className={`text-xs text-gray-400 mt-1 ${isUser ? 'text-right' : 'text-left'}`}>
            {formatTime(message.timestamp)}
          </div>
        </div>
      </div>
    </div>
  );
};