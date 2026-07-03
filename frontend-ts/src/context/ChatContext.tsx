import React, { createContext, useContext, useState, useEffect, ReactNode, useCallback } from 'react';
import type { ChatResponse } from '../services/chatService';
import { useChatWebSocket } from '../hooks/useChatWebSocket';
import { chatService, ConversationItem } from '../services/chatService';

export interface Message {
    id: string;
    role: 'user' | 'assistant';
    content: string;
    timestamp: Date;
    sources?: ChatResponse['sources'];
    confidence?: number;
    agentSteps?: ChatResponse['agent_steps'];
    charts?: ChatResponse['charts'];
    actionsTaken?: string[];
}

interface ChatContextType {
    messages: Message[];
    setMessages: React.Dispatch<React.SetStateAction<Message[]>>;
    input: string;
    setInput: React.Dispatch<React.SetStateAction<string>>;
    loading: boolean;
    setLoading: React.Dispatch<React.SetStateAction<boolean>>;
    conversationId: string | null;
    conversations: ConversationItem[];
    sendMessage: (message: string, onResponse: (data: any) => void) => void;
    agentStatus: string | null;
    isConnected: boolean;
    status: string;
    loadHistory: (id: string) => Promise<void>;
    loadConversations: () => Promise<void>;
    selectConversation: (id: string) => Promise<void>;
    startNewChat: () => void;
    deleteConversation: (id: string) => Promise<void>;
}

const ChatContext = createContext<ChatContextType | undefined>(undefined);

export const ChatProvider = ({ children }: { children: ReactNode }) => {
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const [conversationId, setConversationId] = useState<string | null>(null);
    const [conversations, setConversations] = useState<ConversationItem[]>([]);

    const { sendMessage: wsSendMessage, agentStatus, isConnected, status } = useChatWebSocket(conversationId);

    const loadHistory = async (id: string) => {
        try {
            const history = await chatService.getHistory(id);
            if (history && history.messages) {
                setMessages(history.messages.map((m: any) => ({
                    id: m.id || crypto.randomUUID(),
                    role: m.role,
                    content: m.content,
                    timestamp: new Date(m.created_at || m.timestamp),
                    sources: m.sources_json ? JSON.parse(m.sources_json) : undefined,
                    confidence: m.confidence,
                    agentSteps: m.agent_steps_json ? JSON.parse(m.agent_steps_json) : undefined,
                    charts: m.charts_json ? JSON.parse(m.charts_json) : undefined
                })));
            } else {
                setMessages([]);
            }
        } catch (error) {
            console.error('Failed to load chat history:', error);
            setMessages([]);
        }
    };

    const loadConversations = async () => {
        try {
            const list = await chatService.getConversations();
            setConversations(list);
        } catch (error) {
            console.error('Failed to load conversations list:', error);
        }
    };

    // Load or initialize conversation ID
    useEffect(() => {
        const initChat = async () => {
            await loadConversations();
            const storedId = localStorage.getItem('nexus_conversation_id');
            if (storedId) {
                setConversationId(storedId);
                await loadHistory(storedId);
            } else {
                const newId = crypto.randomUUID();
                setConversationId(newId);
                localStorage.setItem('nexus_conversation_id', newId);
            }
        };
        initChat();
    }, []);

    const selectConversation = async (id: string) => {
        setConversationId(id);
        localStorage.setItem('nexus_conversation_id', id);
        await loadHistory(id);
    };

    const startNewChat = () => {
        const newId = crypto.randomUUID();
        setConversationId(newId);
        localStorage.setItem('nexus_conversation_id', newId);
        setMessages([]);
    };

    const deleteConversation = async (id: string) => {
        try {
            await chatService.deleteConversation(id);
            await loadConversations();
            if (conversationId === id) {
                startNewChat();
            }
        } catch (error) {
            console.error('Failed to delete conversation:', error);
        }
    };

    const sendMessage = useCallback((message: string, onResponse: (data: any) => void) => {
        wsSendMessage(message, async (data) => {
            onResponse(data);
            // Refresh conversation list after receiving response
            await loadConversations();
        });
    }, [wsSendMessage]);

    return (
        <ChatContext.Provider
            value={{
                messages,
                setMessages,
                input,
                setInput,
                loading,
                setLoading,
                conversationId,
                conversations,
                sendMessage,
                agentStatus,
                isConnected,
                status,
                loadHistory,
                loadConversations,
                selectConversation,
                startNewChat,
                deleteConversation
            }}
        >
            {children}
        </ChatContext.Provider>
    );
};

export const useChat = () => {
    const context = useContext(ChatContext);
    if (context === undefined) {
        throw new Error('useChat must be used within a ChatProvider');
    }
    return context;
};
