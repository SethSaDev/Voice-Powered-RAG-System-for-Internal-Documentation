/**
 * Audio Recorder Hook - Captures microphone input for voice queries
 */

import { useState, useRef, useCallback } from 'react';

interface UseAudioRecorderOptions {
  onChunk?: (chunk: Blob) => void;
  onComplete?: (audioBlob: Blob) => void;
  mimeType?: string;
  sampleRate?: number;
}

export const useAudioRecorder = (options: UseAudioRecorderOptions = {}) => {
  const {
    onChunk,
    onComplete,
    mimeType = 'audio/webm',
    sampleRate = 16000,
  } = options;
  
  const [isRecording, setIsRecording] = useState(false);
  const [recordingDuration, setRecordingDuration] = useState(0);
  const [audioLevel, setAudioLevel] = useState(0);
  
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const sourceNodeRef = useRef<MediaStreamAudioSourceNode | null>(null);
  const analyserNodeRef = useRef<AnalyserNode | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const durationIntervalRef = useRef<NodeJS.Timeout>();
  const animationFrameRef = useRef<number>();
  
  const startRecording = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      
      // Create audio context for level monitoring
      audioContextRef.current = new AudioContext({ sampleRate });
      sourceNodeRef.current = audioContextRef.current.createMediaStreamSource(stream);
      analyserNodeRef.current = audioContextRef.current.createAnalyser();
      analyserNodeRef.current.fftSize = 256;
      
      sourceNodeRef.current.connect(analyserNodeRef.current);
      
      // Start level monitoring
      const dataArray = new Uint8Array(analyserNodeRef.current.frequencyBinCount);
      
      const updateLevel = () => {
        if (!analyserNodeRef.current || !isRecording) return;
        
        analyserNodeRef.current.getByteFrequencyData(dataArray);
        const average = dataArray.reduce((a, b) => a + b, 0) / dataArray.length;
        const level = average / 255; // Normalize to 0-1
        setAudioLevel(level);
        
        animationFrameRef.current = requestAnimationFrame(updateLevel);
      };
      
      updateLevel();
      
      // Set up media recorder
      mediaRecorderRef.current = new MediaRecorder(stream, { mimeType });
      chunksRef.current = [];
      
      mediaRecorderRef.current.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
          onChunk?.(event.data);
        }
      };
      
      mediaRecorderRef.current.onstop = () => {
        const audioBlob = new Blob(chunksRef.current, { type: mimeType });
        onComplete?.(audioBlob);
        
        // Clean up
        if (animationFrameRef.current) {
          cancelAnimationFrame(animationFrameRef.current);
        }
        
        // Stop all tracks
        stream.getTracks().forEach(track => track.stop());
        
        if (audioContextRef.current) {
          audioContextRef.current.close();
        }
      };
      
      mediaRecorderRef.current.start(1000); // Collect chunks every second
      setIsRecording(true);
      setRecordingDuration(0);
      
      // Track duration
      durationIntervalRef.current = setInterval(() => {
        setRecordingDuration(prev => prev + 1);
      }, 1000);
      
    } catch (error) {
      console.error('Failed to start recording:', error);
      alert('Microphone access denied. Please allow microphone permissions.');
    }
  }, [mimeType, sampleRate, onChunk, onComplete]);
  
  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      
      if (durationIntervalRef.current) {
        clearInterval(durationIntervalRef.current);
      }
      
      setAudioLevel(0);
    }
  }, [isRecording]);
  
  const cancelRecording = useCallback(() => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.onstop = null; // Prevent onComplete callback
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      chunksRef.current = [];
      
      if (durationIntervalRef.current) {
        clearInterval(durationIntervalRef.current);
      }
      
      setAudioLevel(0);
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