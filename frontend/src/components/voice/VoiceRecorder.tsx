import React, { useState } from 'react';
import { useAudioRecorder } from '@/hooks/useAudioRecorder';

interface VoiceRecorderProps {
  onAudioComplete: (audioBlob: Blob) => void;
  disabled?: boolean;
}

export const VoiceRecorder: React.FC<VoiceRecorderProps> = ({ onAudioComplete, disabled = false }) => {
  const [isProcessing, setIsProcessing] = useState(false);
  
  const { isRecording, recordingDuration, audioLevel, startRecording, stopRecording, isSupported } = useAudioRecorder({
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
    return <div className="text-red-500">Microphone not supported</div>;
  }
  
  if (!isRecording) {
    return (
      <button
        onClick={startRecording}
        disabled={disabled || isProcessing}
        className="px-4 py-2 bg-blue-500 text-white rounded-full hover:bg-blue-600"
      >
        🎤 Record
      </button>
    );
  }
  
  return (
    <div className="flex items-center gap-2 px-4 py-2 bg-red-500 text-white rounded-full">
      <span>Recording {formatDuration(recordingDuration)}</span>
      <button onClick={stopRecording} className="ml-2">⏹️</button>
    </div>
  );
};
