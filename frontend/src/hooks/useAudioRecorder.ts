import { useState, useRef, useCallback } from 'react';

interface UseAudioRecorderOptions {
  onComplete?: (audioBlob: Blob) => void;
  onChunk?: (chunk: Blob) => void;
  mimeType?: string;
}

export const useAudioRecorder = (options: UseAudioRecorderOptions = {}) => {
  const [isRecording, setIsRecording] = useState(false);
  const [recordingDuration, setRecordingDuration] = useState(0);
  const [audioLevel, setAudioLevel] = useState(0);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const durationIntervalRef = useRef<NodeJS.Timeout>();
  
  const startRecording = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream, { mimeType: options.mimeType || 'audio/webm' });
      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];
      
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
          options.onChunk?.(event.data);
        }
      };
      
      mediaRecorder.onstop = () => {
        const audioBlob = new Blob(chunksRef.current, { type: 'audio/webm' });
        options.onComplete?.(audioBlob);
        stream.getTracks().forEach(track => track.stop());
      };
      
      mediaRecorder.start(1000);
      setIsRecording(true);
      
      durationIntervalRef.current = setInterval(() => {
        setRecordingDuration(prev => prev + 1);
      }, 1000);
      
      // Simulate audio level
      const levelInterval = setInterval(() => {
        setAudioLevel(Math.random());
      }, 100);
      
      return () => {
        clearInterval(levelInterval);
        if (durationIntervalRef.current) clearInterval(durationIntervalRef.current);
      };
    } catch (error) {
      console.error('Failed to start recording:', error);
    }
  }, [options]);
  
  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      setRecordingDuration(0);
      setAudioLevel(0);
      if (durationIntervalRef.current) clearInterval(durationIntervalRef.current);
    }
  }, [isRecording]);
  
  const cancelRecording = useCallback(() => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.onstop = null;
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      setRecordingDuration(0);
      setAudioLevel(0);
      chunksRef.current = [];
      if (durationIntervalRef.current) clearInterval(durationIntervalRef.current);
    }
  }, [isRecording]);
  
  return {
    isRecording,
    recordingDuration,
    audioLevel,
    startRecording,
    stopRecording,
    cancelRecording,
    isSupported: !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia),
  };
};
