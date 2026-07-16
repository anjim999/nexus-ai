import { useRef, useEffect } from 'react';
import { X, Check, Loader2 } from 'lucide-react';

/**
 * VoiceOverlay – ChatGPT style full-width voice dictation overlay widget
 * with a high-performance Web Audio API canvas visualizer.
 */
const VoiceOverlay = ({
    audioStream,
    isInitializing,
    isTranscribing,
    onCancel,
    onConfirm
}) => {
    const canvasRef = useRef(null);

    useEffect(() => {
        if (!audioStream) return;

        let audioCtx;
        let analyser;
        let source;
        let animationFrameId;

        try {
            audioCtx = new (window.AudioContext || window.webkitAudioContext)();
            analyser = audioCtx.createAnalyser();
            source = audioCtx.createMediaStreamSource(audioStream);
            
            source.connect(analyser);
            analyser.fftSize = 64; // Gives 32 frequency bins
            
            const bufferLength = analyser.frequencyBinCount;
            const dataArray = new Uint8Array(bufferLength);
            
            const canvas = canvasRef.current;
            if (canvas) {
                const dpr = window.devicePixelRatio || 1;
                canvas.width = canvas.clientWidth * dpr;
                canvas.height = canvas.clientHeight * dpr;
                
                const ctx = canvas.getContext('2d');
                ctx.scale(dpr, dpr);

                const draw = () => {
                    const width = canvas.clientWidth;
                    const height = canvas.clientHeight;
                    
                    analyser.getByteFrequencyData(dataArray);
                    
                    ctx.clearRect(0, 0, width, height);
                    
                    const barWidth = 3;
                    const gap = 3;
                    const totalBars = Math.floor(width / (barWidth + gap));
                    
                    ctx.fillStyle = '#94a3b8'; // Slate-400 color
                    
                    for (let i = 0; i < totalBars; i++) {
                        // Map visual bar index to frequency data array
                        const binIndex = Math.floor((i / totalBars) * bufferLength);
                        const amplitude = dataArray[binIndex] || 0;
                        
                        // Map amplitude to vertical bar scaling
                        const percent = amplitude / 255;
                        const barHeight = Math.max(3, percent * height * 0.85);
                        
                        const x = i * (barWidth + gap);
                        const y = (height - barHeight) / 2;
                        
                        ctx.beginPath();
                        if (ctx.roundRect) {
                            ctx.roundRect(x, y, barWidth, barHeight, 1.5);
                        } else {
                            ctx.rect(x, y, barWidth, barHeight);
                        }
                        ctx.fill();
                    }
                    
                    animationFrameId = requestAnimationFrame(draw);
                };
                
                draw();
            }
        } catch (e) {
            console.error("Failed to initialize audio visualizer:", e);
        }

        return () => {
            if (animationFrameId) {
                cancelAnimationFrame(animationFrameId);
            }
            if (audioCtx && audioCtx.state !== 'closed') {
                audioCtx.close().catch(() => {});
            }
        };
    }, [audioStream]);

    return (
        <div className="flex items-center gap-3 w-full bg-muted/60 border border-border/80 rounded-xl px-4 py-3 shadow-inner h-12 transition-all duration-300">
            {/* Middle Live Waveform Canvas */}
            <div className="flex-1 h-full flex items-center relative overflow-hidden">
                {isInitializing ? (
                    <div className="text-xs text-muted-foreground animate-pulse pl-1 flex items-center gap-1.5">
                        <Loader2 className="w-3.5 h-3.5 animate-spin text-primary" />
                        Initializing microphone...
                    </div>
                ) : (
                    <canvas 
                        ref={canvasRef} 
                        className="w-full h-6 opacity-75"
                        style={{ display: 'block', width: '100%', height: '24px' }}
                    />
                )}
            </div>

            {/* Right Control Buttons */}
            <div className="flex items-center gap-2">
                {/* Close/Discard button */}
                <button
                    onClick={onCancel}
                    className="p-1.5 rounded-full hover:bg-muted-foreground/15 text-muted-foreground hover:text-foreground transition-all duration-200 cursor-pointer"
                    title="Cancel dictation"
                >
                    <X className="w-4 h-4" />
                </button>

                {/* Confirm/Done button */}
                <button
                    onClick={onConfirm}
                    disabled={isTranscribing}
                    className="p-1.5 rounded-full bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-500 transition-all duration-200 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
                    title={isTranscribing ? "Transcribing speech..." : "Done dictating"}
                >
                    {isTranscribing ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                        <Check className="w-4 h-4" />
                    )}
                </button>
            </div>
        </div>
    );
};

export default VoiceOverlay;
