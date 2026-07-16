import { useState, useEffect, useRef, useCallback } from 'react';

export const useChatWebSocket = (conversationId) => {
    const [status, setStatus] = useState('closed');
    const [agentStatus, setAgentStatus] = useState(null);
    const socketRef = useRef(null);
    const onMessageRef = useRef(null);
    const onStreamRef = useRef(null); // For future text streaming support

    const reconnectTimeoutRef = useRef(null);

    // Initialize/Update connection when conversationId changes
    useEffect(() => {
        if (!conversationId) return;

        let isMounted = true;

        const connect = () => {
            // Close existing connection if any
            if (socketRef.current) {
                try {
                    socketRef.current.close();
                } catch (e) {
                    console.error('Error closing socket:', e);
                }
            }

            const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
            const cleanApiUrl = apiUrl.endsWith('/') ? apiUrl.slice(0, -1) : apiUrl;
            const wsUrl = `${cleanApiUrl.replace('http', 'ws')}/api/v1/chat/ws/${conversationId}`;
            console.log('Connecting to WebSocket:', wsUrl);

            const ws = new WebSocket(wsUrl);
            socketRef.current = ws;
            setStatus('connecting');

            ws.onopen = () => {
                if (!isMounted) return;
                console.log('WebSocket Connected');
                setStatus('open');
            };

            ws.onmessage = (event) => {
                if (!isMounted) return;
                try {
                    const data = JSON.parse(event.data);

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
                if (!isMounted) return;
                console.error('WebSocket error:', error);
                setStatus('error');
            };

            ws.onclose = () => {
                if (!isMounted) return;
                console.log('WebSocket disconnected');
                setStatus('closed');

                // Attempt auto-reconnect after 3 seconds
                reconnectTimeoutRef.current = setTimeout(() => {
                    if (isMounted) {
                        console.log('Attempting to reconnect WebSocket...');
                        connect();
                    }
                }, 3000);
            };
        };

        connect();

        return () => {
            isMounted = false;
            if (socketRef.current) {
                socketRef.current.close();
            }
            if (reconnectTimeoutRef.current) {
                clearTimeout(reconnectTimeoutRef.current);
            }
        };
    }, [conversationId]);

    const isSocketReady = status === 'open' && (socketRef.current?.url || '').includes(conversationId);

    const sendMessage = useCallback((message, onResponse) => {
        const wsUrl = socketRef.current?.url || '';
        if (socketRef.current?.readyState === WebSocket.OPEN && wsUrl.includes(conversationId)) {
            onMessageRef.current = onResponse;
            setAgentStatus('Processing...'); // Initial status
            socketRef.current.send(JSON.stringify({ message }));
        } else {
            console.error('WebSocket is not open or not ready for this conversation');
        }
    }, [conversationId]);

    return {
        status,
        agentStatus,
        sendMessage,
        isSocketReady,
        isConnected: status === 'open'
    };
};
