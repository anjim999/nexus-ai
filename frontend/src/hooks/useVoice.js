import { useState, useEffect, useRef, useCallback } from 'react';
import api from '../services/api';

/**
 * useVoice – Custom hook for voice input (Speech-to-Text via backend Gemini) and
 * voice output (Text-to-Speech) using the Web Speech API.
 *
 * Speech-to-Text: Uses MediaRecorder API + backend Gemini 1.5 Flash
 * Text-to-Speech: Uses SpeechSynthesis (all modern browsers)
 */

// Strip markdown formatting so TTS reads clean text
const stripMarkdown = (text) => {
    if (!text) return '';
    return text
        // Remove code blocks
        .replace(/```[\s\S]*?```/g, 'code block omitted')
        // Remove inline code
        .replace(/`([^`]+)`/g, '$1')
        // Remove bold/italic markers
        .replace(/\*\*\*(.*?)\*\*\*/g, '$1')
        .replace(/\*\*(.*?)\*\*/g, '$1')
        .replace(/\*(.*?)\*/g, '$1')
        .replace(/__(.*?)__/g, '$1')
        .replace(/_(.*?)_/g, '$1')
        // Remove headers
        .replace(/^#{1,6}\s+/gm, '')
        // Remove bullet points
        .replace(/^[\s]*[-*+]\s+/gm, '')
        // Remove numbered lists
        .replace(/^[\s]*\d+\.\s+/gm, '')
        // Remove links — keep text
        .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
        // Remove images
        .replace(/!\[([^\]]*)\]\([^)]+\)/g, '$1')
        // Remove horizontal rules
        .replace(/^---+$/gm, '')
        // Remove blockquotes
        .replace(/^>\s+/gm, '')
        // Collapse multiple newlines
        .replace(/\n{3,}/g, '\n\n')
        .trim();
};

const useVoice = () => {
    // ─── Feature Detection ───
    const speechSynthesis =
        typeof window !== 'undefined' ? window.speechSynthesis : null;

    const isTTSSupported = !!speechSynthesis;
    const isSTTSupported = typeof window !== 'undefined' && !!(window.MediaRecorder && navigator.mediaDevices);
    const isSupported = isSTTSupported || isTTSSupported;

    // ─── State ───
    const [isListening, setIsListening] = useState(false);
    const [isInitializing, setIsInitializing] = useState(false);
    const [isTranscribing, setIsTranscribing] = useState(false);
    const [transcript, setTranscript] = useState('');
    const [suffix, setSuffix] = useState('');
    const [audioStream, setAudioStream] = useState(null);
    const [isSpeaking, setIsSpeaking] = useState(false);
    const [isPaused, setIsPaused] = useState(false);
    const [voiceEnabled, setVoiceEnabledState] = useState(() => {
        try {
            const stored = localStorage.getItem('nexus_voice_enabled');
            return stored !== null ? JSON.parse(stored) : true;
        } catch {
            return true;
        }
    });

    const mediaRecorderRef = useRef(null);
    const audioChunksRef = useRef([]);
    const activeUtteranceRef = useRef(null);

    // Caret tracking refs
    const previousTextRef = useRef('');
    const suffixTextRef = useRef('');

    // ─── Persist voiceEnabled ───
    const setVoiceEnabled = useCallback((val) => {
        const newVal = typeof val === 'function' ? val(voiceEnabled) : val;
        setVoiceEnabledState(newVal);
        try {
            localStorage.setItem('nexus_voice_enabled', JSON.stringify(newVal));
        } catch {
            // localStorage may be unavailable
        }
    }, [voiceEnabled]);

    // ─── Speech-to-Text ───
    const startListening = useCallback(async (beforeText = '', afterText = '') => {
        if (!isSTTSupported) return;
        if (isListening || isInitializing || isTranscribing) return;

        setIsInitializing(true);
        audioChunksRef.current = [];

        previousTextRef.current = beforeText;
        suffixTextRef.current = afterText;
        setTranscript(beforeText);
        setSuffix(afterText);

        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            setAudioStream(stream);
            
            const mediaRecorder = new MediaRecorder(stream);
            mediaRecorderRef.current = mediaRecorder;

            mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    audioChunksRef.current.push(event.data);
                }
            };

            mediaRecorder.onstop = async () => {
                setIsListening(false);
                setIsTranscribing(true);
                setAudioStream(null);
                try {
                    const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
                    const formData = new FormData();
                    formData.append('file', audioBlob, 'recording.webm');

                    // Post to Gemini speech-to-text API in the backend
                    const response = await api.post('/chat/transcribe', formData, {
                        headers: {
                            'Content-Type': 'multipart/form-data'
                        }
                    });

                    const transcribedText = response.data.text || '';
                    const prefix = previousTextRef.current;
                    const cleanTranscribed = transcribedText.trim();
                    
                    if (cleanTranscribed) {
                        const needsSpace = prefix && !prefix.endsWith(' ') && !cleanTranscribed.startsWith(' ');
                        const finalText = prefix + (needsSpace ? ' ' : '') + cleanTranscribed;
                        
                        previousTextRef.current = finalText;
                        setTranscript(finalText);
                    }
                } catch (e) {
                    console.error('Transcription backend request failed:', e);
                } finally {
                    setIsTranscribing(false);
                }
            };

            mediaRecorder.start();
            setIsListening(true);
        } catch (e) {
            console.error('Failed to start MediaRecorder:', e);
            setAudioStream(null);
        } finally {
            setIsInitializing(false);
        }
    }, [isSTTSupported, isListening, isInitializing, isTranscribing]);

    const stopListening = useCallback(() => {
        if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
            try {
                mediaRecorderRef.current.stop();
                // Shut off mic streams immediately to clear the browser tab recording indicator
                mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop());
            } catch (e) {
                console.error('Error stopping MediaRecorder:', e);
                setIsListening(false);
            }
        } else {
            setIsListening(false);
        }
        setAudioStream(null);
        setIsInitializing(false);
    }, []);

    const resetTranscript = useCallback(() => {
        setTranscript('');
        setSuffix('');
        previousTextRef.current = '';
        suffixTextRef.current = '';
        audioChunksRef.current = [];
    }, []);

    const toggleListening = useCallback((beforeText = '', afterText = '') => {
        if (isListening) {
            stopListening();
        } else {
            startListening(beforeText, afterText);
        }
    }, [isListening, startListening, stopListening]);

    const updateVoiceText = useCallback((text, cursorPosition) => {
        const pos = cursorPosition !== undefined && cursorPosition !== null ? cursorPosition : text.length;
        const before = text.slice(0, pos);
        const after = text.slice(pos);
        
        previousTextRef.current = before;
        suffixTextRef.current = after;
        
        setTranscript(before);
        setSuffix(after);
    }, []);

    // ─── Text-to-Speech ───
    const speak = useCallback((text) => {
        if (!isTTSSupported || !text) return;

        // Reset state and clear active utterance references
        if (activeUtteranceRef.current) {
            activeUtteranceRef.current.onend = null;
            activeUtteranceRef.current.onerror = null;
        }

        // Critical: Unstick Chrome SpeechSynthesis before cancel/speak
        speechSynthesis.resume();
        speechSynthesis.cancel();

        const cleanText = stripMarkdown(text);
        const utterance = new SpeechSynthesisUtterance(cleanText);
        utterance.rate = 1.0;
        utterance.pitch = 1.0;
        utterance.volume = 1.0;

        // Pick a natural voice
        const voices = speechSynthesis.getVoices();
        const preferred = voices.find(
            (v) => v.lang.startsWith('en') && v.name.toLowerCase().includes('google')
        ) || voices.find(
            (v) => v.lang.startsWith('en') && v.localService === false
        ) || voices.find(
            (v) => v.lang.startsWith('en')
        );
        if (preferred) utterance.voice = preferred;

        utterance.onend = () => {
            setIsSpeaking(false);
            setIsPaused(false);
            activeUtteranceRef.current = null;
        };

        utterance.onerror = (e) => {
            console.warn('TTS utterance error:', e.error);
            setIsSpeaking(false);
            setIsPaused(false);
            activeUtteranceRef.current = null;
        };

        activeUtteranceRef.current = utterance;
        setIsSpeaking(true);
        setIsPaused(false);
        speechSynthesis.speak(utterance);
    }, [isTTSSupported, speechSynthesis]);

    const pauseSpeaking = useCallback(() => {
        if (isTTSSupported && isSpeaking && !isPaused) {
            // Natively pause speech
            speechSynthesis.pause();
            setIsPaused(true);
        }
    }, [isTTSSupported, isSpeaking, isPaused, speechSynthesis]);

    const resumeSpeaking = useCallback(() => {
        if (isTTSSupported && isPaused) {
            // Natively resume speech
            speechSynthesis.resume();
            setIsPaused(false);
        }
    }, [isTTSSupported, isPaused, speechSynthesis]);

    const stopSpeaking = useCallback(() => {
        if (isTTSSupported) {
            if (activeUtteranceRef.current) {
                activeUtteranceRef.current.onend = null;
                activeUtteranceRef.current.onerror = null;
            }

            // Critical: Unstick Chrome SpeechSynthesis before cancel
            speechSynthesis.resume();
            speechSynthesis.cancel();
        }
        setIsSpeaking(false);
        setIsPaused(false);
        activeUtteranceRef.current = null;
    }, [isTTSSupported, speechSynthesis]);

    // ─── Cleanup on Unmount ───
    useEffect(() => {
        return () => {
            if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
                try {
                    mediaRecorderRef.current.stop();
                    mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop());
                } catch (e) {}
            }
            if (isTTSSupported) {
                speechSynthesis.cancel();
            }
        };
    }, [isTTSSupported, speechSynthesis]);

    return {
        // Speech-to-Text
        isListening,
        isInitializing,
        isTranscribing,
        audioStream,
        transcript,
        suffix,
        startListening,
        stopListening,
        toggleListening,
        resetTranscript,
        isSTTSupported,
        updateVoiceText,

        // Text-to-Speech
        isSpeaking,
        isPaused,
        speak,
        pauseSpeaking,
        resumeSpeaking,
        stopSpeaking,
        isTTSSupported,

        // General
        isSupported,
        voiceEnabled,
        setVoiceEnabled,
    };
};

export default useVoice;
