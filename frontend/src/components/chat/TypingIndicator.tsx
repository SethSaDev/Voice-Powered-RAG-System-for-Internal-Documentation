/**
 * Typing Indicator Component
 * Shows animated dots while assistant is processing
 */

import React from 'react';

export const TypingIndicator: React.FC = () => {
  return (
    <div className="flex justify-start animate-slide-in">
      <div className="flex gap-3 max-w-[80%]">
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gray-600 flex items-center justify-center">
          <div className="w-4 h-4 text-white">🤖</div>
        </div>
        
        <div className="bg-white rounded-lg px-4 py-3 shadow-sm border border-gray-200">
          <div className="flex gap-1">
            <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
            <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
            <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
          </div>
        </div>
      </div>
    </div>
  );
};