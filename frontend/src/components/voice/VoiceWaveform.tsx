import React, { useEffect, useRef } from 'react';

interface VoiceWaveformProps {
  audioLevel: number;
  isRecording: boolean;
}

export const VoiceWaveform: React.FC<VoiceWaveformProps> = ({ audioLevel, isRecording }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  
  useEffect(() => {
    if (!canvasRef.current || !isRecording) return;
    
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    
    const width = canvas.width;
    const height = canvas.height;
    
    ctx.clearRect(0, 0, width, height);
    ctx.fillStyle = '#3b82f6';
    
    const barHeight = audioLevel * height;
    ctx.fillRect(0, height - barHeight, width, barHeight);
  }, [audioLevel, isRecording]);
  
  return (
    <canvas
      ref={canvasRef}
      width={100}
      height={40}
      className="border rounded"
      style={{ width: '100px', height: '40px' }}
    />
  );
};
