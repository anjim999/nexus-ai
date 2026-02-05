import { useState, useEffect, useRef, useCallback } from 'react';

export type WebSocketStatus = 'connecting' | 'open' | 'closed' | 'error';

export interface AgentStatusUpdate {
    type: 'agent_status';
    agent: string;
    status: string;
}

interface AgentStartUpdate {
    type: 'agent_start';
    agent: string;
    status: string;
}

interface AgentDoneUpdate {
    type: 'agent_done';
    agent: string;
    result: string;
}

interface StatusUpdate {
    type: 'status';
    message: string;
}

interface ResponseChunk {
    type: 'response_chunk';
    content: string;
}

export interface WebSocketResponse {
    type: 'response';
    data: any;
}

type WebSocketMessage =
    | AgentStatusUpdate
    | AgentStartUpdate
    | AgentDoneUpdate
    | StatusUpdate
    | ResponseChunk
    | WebSocketResponse;

export const useChatWebSocket = (conversationId: string | null) => {
    const [status, setStatus] = useState<WebSocketStatus>('closed');
    const [agentStatus, setAgentStatus] = useState<string | null>(null);
    const socketRef = useRef<WebSocket | null>(null);
    const onMessageRef = useRef<((data: any) => void) | null>(null);
    const onStreamRef = useRef<((chunk: string) => void) | null>(null); // For future text streaming support

    // Initialize/Update connection when conversationId changes
    useEffect(() => {
        if (!conversationId) return;

        // Close existing connection if any
        if (socketRef.current) {
            socketRef.current.close();
        }

        const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
        const wsUrl = `${apiUrl.replace('http', 'ws')}/api/v1/chat/ws/${conversationId}`;
        console.log('Connecting to WebSocket:', wsUrl);

        const ws = new WebSocket(wsUrl);
        socketRef.current = ws;
        setStatus('connecting');

        ws.onopen = () => {
            console.log('WebSocket Connected');
            setStatus('open');
        };

        ws.onmessage = (event) => {
            try {
                const data: WebSocketMessage = JSON.parse(event.data);

                if (data.type === 'agent_status') {
                    setAgentStatus(`${data.agent} is ${data.status}...`);
                } else if (data.type === 'agent_start') {
                    setAgentStatus(`${data.agent} is ${data.status}...`);
                } else if (data.type === 'agent_done') {
                    setAgentStatus(`Finished: ${data.agent}`);
                } else if (data.type === 'status') {
                    setAgentStatus(data.message);
                } else if (data.type === 'response_chunk') {
                    // Optionally handle text streaming here
                    if (onStreamRef.current) {
                        onStreamRef.current(data.content);
                    }
                } else if (data.type === 'response') {
                    setAgentStatus(null); // Clear status when done
                    if (onMessageRef.current) {
                        onMessageRef.current(data.data);
                    }
                }
            } catch (error) {
                console.error('WebSocket message parse error:', error);
            }
        };

        ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            setStatus('error');
        };

        ws.onclose = () => {
            console.log('WebSocket disconnected');
            setStatus('closed');
        };

        return () => {
            ws.close();
        };
    }, [conversationId]);

    const sendMessage = useCallback((message: string, onResponse: (data: any) => void) => {
        if (socketRef.current?.readyState === WebSocket.OPEN) {
            onMessageRef.current = onResponse;
            setAgentStatus('Processing...'); // Initial status
            socketRef.current.send(JSON.stringify({ message }));
        } else {
            console.error('WebSocket is not open');
        }
    }, []);

    return {
        status,
        agentStatus,
        sendMessage,
        isConnected: status === 'open'
    };
};
