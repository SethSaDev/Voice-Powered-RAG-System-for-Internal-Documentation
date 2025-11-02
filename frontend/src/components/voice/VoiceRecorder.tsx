/**
 * Voice Recorder Component - Button UI with recording animation
 */

import React, { useState, useEffect } from 'react';
import { Mic, Square, Loader2 } from 'lucide-react';
import { useAudioRecorder } from '@/hooks/useAudioRecorder';

interface VoiceRecorderProps {
  onAudioComplete: (audioBlob: Blob) => void;
  disabled?: boolean;
  className?: string;
}

export const VoiceRecorder: React.FC<VoiceRecorderProps> = ({
  onAudioComplete,
  disabled = false,
  className = '',
}) => {
  const [isProcessing, setIsProcessing] = useState(false);
  
  const {
    isRecording,
    recordingDuration,
    audioLevel,
    startRecording,
    stopRecording,
    cancelRecording,
    isSupported,
  } = useAudioRecorder({
    onComplete: async (audioBlob) => {
      setIsProcessing(true);
      onAudioComplete(audioBlob);
      setTimeout(() => setIsProcessing(false), 500);
    },
  });
  
  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };
  
  if (!isSupported) {
    return (
      <div className="text-red-500 text-sm p-2 bg-red-50 rounded-md">
        Your browser doesn't support audio recording. Please use Chrome, Edge, or Safari.
      </div>
    );
  }
  
  return (
    <div className={`relative ${className}`}>
      {!isRecording ? (
        <button
          onClick={startRecording}
          disabled={disabled || isProcessing}
          className={`
            flex items-center gap-2 px-4 py-2 rounded-full font-medium transition-all
            ${disabled || isProcessing
              ? 'bg-gray-300 cursor-not-allowed'
              : 'bg-blue-500 hover:bg-blue-600 active:scale-95'
            }
            text-white shadow-lg
          `}
        >
          {isProcessing ? (
            <Loader2 className="w-5 h-5 animate-spin" />
          ) : (
            <Mic className="w-5 h-5" />
          )}
          <span>Ask with Voice</span>
        </button>
      ) : (
        <div className="flex items-center gap-3 bg-red-500 rounded-full px-4 py-2 shadow-lg animate-pulse">
          <div className="flex items-center gap-2">
            <div className="relative">
              <div
                className="w-3 h-3 bg-white rounded-full"
                style={{
                  transform: `scale(${1 + audioLevel * 2})`,
                  transition: 'transform 0.1s ease',
                }}
              />
            </div>
            <span className="text-white font-medium">
              Recording {formatDuration(recordingDuration)}
            </span>
          </div>
          
          <button
            onClick={stopRecording}
            className="bg-white text-red-500 rounded-full p-1 hover:bg-gray-100 transition-colors"
            title="Stop recording"
          >
            <Square className="w-4 h-4 fill-red-500" />
          </button>
          
          <button
            onClick={cancelRecording}
            className="text-white text-sm hover:text-gray-200 transition-colors"
          >
            Cancel
          </button>
        </div>
      )}
    </div>
  );
};