import React, { useState, useEffect, useRef } from 'react';
import { Mic, MicOff, Volume2, MessageSquare } from 'lucide-react';

interface InterviewInterfaceProps {
    interviewId: string;
    onComplete: () => void;
}

interface Message {
    role: 'user' | 'assistant';
    content: string;
}

const InterviewInterface: React.FC<InterviewInterfaceProps> = ({ interviewId, onComplete }) => {
    const [isRecording, setIsRecording] = useState(false);
    const [messages, setMessages] = useState<Message[]>([]);
    const [status, setStatus] = useState('Connecting...');
    const wsRef = useRef<WebSocket | null>(null);
    const mediaRecorderRef = useRef<MediaRecorder | null>(null);
    const audioChunksRef = useRef<Blob[]>([]);

    useEffect(() => {
        console.log('[InterviewInterface] Initializing WebSocket for interview:', interviewId);
        const ws = new WebSocket(`ws://localhost:8000/ws/interview/${interviewId}`);
        wsRef.current = ws;

        ws.onopen = () => {
            console.log('[InterviewInterface] WebSocket connected');
            setStatus('Connected');
        };

        ws.onmessage = async (event) => {
            console.log('[InterviewInterface] Message received:', { 
                isBlob: event.data instanceof Blob,
                size: event.data instanceof Blob ? event.data.size : event.data.length 
            });
            
            // Handle different message types
            if (event.data instanceof Blob) {
                // Audio data
                console.log('[InterviewInterface] Received audio blob, size:', event.data.size);
                const audioUrl = URL.createObjectURL(event.data);
                const audio = new Audio(audioUrl);
                audio.play().catch(err => console.error('[InterviewInterface] Audio play error:', err));
            } else {
                try {
                    const data = JSON.parse(event.data);
                    console.log('[InterviewInterface] Parsed message:', data);
                    if (data.type === 'text' || data.type === 'transcription') {
                        console.log('[InterviewInterface] Adding message:', { role: data.role, content: data.content.substring(0, 50) + '...' });
                        setMessages(prev => [...prev, { role: data.role, content: data.content }]);
                    } else if (data.type === 'end') {
                        console.log('[InterviewInterface] Interview ended');
                        setStatus('Interview Completed');
                        setTimeout(onComplete, 3000);
                    } else if (data.type === 'error') {
                        console.error('[InterviewInterface] Error from server:', data.content);
                    }
                } catch (e) {
                    console.error('[InterviewInterface] Error parsing message:', e, 'Raw data:', event.data);
                }
            }
        };

        ws.onerror = (error) => {
            console.error('[InterviewInterface] WebSocket error:', error);
        };

        ws.onclose = (event) => {
            console.log('[InterviewInterface] WebSocket closed:', { code: event.code, reason: event.reason, wasClean: event.wasClean });
            setStatus('Disconnected');
        };

        return () => {
            console.log('[InterviewInterface] Cleaning up WebSocket');
            ws.close();
        };
    }, [interviewId, onComplete]);

    const startRecording = async () => {
        console.log('[InterviewInterface] Start recording clicked');
        try {
            console.log('[InterviewInterface] Requesting microphone access');
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            console.log('[InterviewInterface] Microphone access granted');
            const mediaRecorder = new MediaRecorder(stream);
            mediaRecorderRef.current = mediaRecorder;
            audioChunksRef.current = [];

            mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    console.log('[InterviewInterface] Audio chunk received:', event.data.size, 'bytes');
                    audioChunksRef.current.push(event.data);
                }
            };

            mediaRecorder.onstop = () => {
                console.log('[InterviewInterface] Recording stopped, total chunks:', audioChunksRef.current.length);
                const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
                console.log('[InterviewInterface] Audio blob created:', audioBlob.size, 'bytes');
                if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
                    console.log('[InterviewInterface] Sending audio to server');
                    wsRef.current.send(audioBlob);
                } else {
                    console.error('[InterviewInterface] WebSocket not open, readyState:', wsRef.current?.readyState);
                }
            };

            mediaRecorder.start();
            console.log('[InterviewInterface] Recording started');
            setIsRecording(true);
        } catch (error) {
            console.error('[InterviewInterface] Error accessing microphone:', error);
            alert('Could not access microphone');
        }
    };

    const stopRecording = () => {
        console.log('[InterviewInterface] Stop recording clicked');
        if (mediaRecorderRef.current && isRecording) {
            console.log('[InterviewInterface] Stopping media recorder');
            mediaRecorderRef.current.stop();
            setIsRecording(false);
            // Stop all tracks
            mediaRecorderRef.current.stream.getTracks().forEach(track => {
                console.log('[InterviewInterface] Stopping track:', track.label);
                track.stop();
            });
        } else {
            console.warn('[InterviewInterface] Cannot stop recording:', { hasRecorder: !!mediaRecorderRef.current, isRecording });
        }
    };

    return (
        <div className="max-w-4xl mx-auto p-6 bg-white rounded-xl shadow-lg h-[80vh] flex flex-col">
            <div className="flex justify-between items-center mb-6 border-b pb-4">
                <h2 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
                    <MessageSquare className="w-6 h-6 text-blue-600" />
                    Voice Interview
                </h2>
                <span className={`px-3 py-1 rounded-full text-sm font-medium ${status === 'Connected' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                    }`}>
                    {status}
                </span>
            </div>

            <div className="flex-1 overflow-y-auto mb-6 space-y-4 p-4 bg-gray-50 rounded-lg">
                {messages.map((msg, idx) => (
                    <div
                        key={idx}
                        className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                    >
                        <div
                            className={`max-w-[70%] p-4 rounded-lg ${msg.role === 'user'
                                    ? 'bg-blue-600 text-white rounded-br-none'
                                    : 'bg-white border border-gray-200 text-gray-800 rounded-bl-none shadow-sm'
                                }`}
                        >
                            <p className="text-sm font-medium mb-1 opacity-75">
                                {msg.role === 'user' ? 'You' : 'Interviewer'}
                            </p>
                            <p>{msg.content}</p>
                        </div>
                    </div>
                ))}
            </div>

            <div className="flex justify-center items-center py-6 border-t">
                <button
                    onClick={isRecording ? stopRecording : startRecording}
                    className={`p-6 rounded-full transition-all duration-300 ${isRecording
                            ? 'bg-red-500 hover:bg-red-600 animate-pulse ring-4 ring-red-200'
                            : 'bg-blue-600 hover:bg-blue-700 ring-4 ring-blue-100'
                        }`}
                >
                    {isRecording ? (
                        <MicOff className="w-8 h-8 text-white" />
                    ) : (
                        <Mic className="w-8 h-8 text-white" />
                    )}
                </button>
            </div>
            <p className="text-center text-gray-500 text-sm mt-2">
                {isRecording ? 'Recording... Click to stop and send' : 'Click microphone to answer'}
            </p>
        </div>
    );
};

export default InterviewInterface;
