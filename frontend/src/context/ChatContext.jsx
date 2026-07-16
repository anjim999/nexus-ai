import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { useChatWebSocket } from '../hooks/useChatWebSocket';
import { chatService } from '../services/chatService';

const ChatContext = createContext(undefined);

export const ChatProvider = ({ children }) => {
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const [conversationId, setConversationId] = useState(null);
    const [conversations, setConversations] = useState([]);
    const [conversationsLoading, setConversationsLoading] = useState(false);
    const [historyLoading, setHistoryLoading] = useState(false);
    const [historySidebarOpen, setHistorySidebarOpen] = useState(true);

    const { sendMessage: wsSendMessage, agentStatus, isConnected, status, isSocketReady } = useChatWebSocket(conversationId);

    const loadHistory = async (id) => {
        setHistoryLoading(true);
        try {
            const history = await chatService.getHistory(id);
            if (history && history.messages) {
                setMessages(history.messages.map((m) => ({
                    id: m.id || crypto.randomUUID(),
                    role: m.role ? m.role.toLowerCase() : m.role,
                    content: m.content,
                    timestamp: m.created_at || m.timestamp,
                    sources: m.sources || (m.sources_json ? JSON.parse(m.sources_json) : undefined),
                    confidence: m.confidence,
                    agentSteps: m.agent_steps || (m.agent_steps_json ? JSON.parse(m.agent_steps_json) : undefined),
                    charts: m.charts || (m.charts_json ? JSON.parse(m.charts_json) : undefined)
                })));
            } else {
                setMessages([]);
            }
        } catch (error) {
            console.error('Failed to load chat history:', error);
            setMessages([]);
        } finally {
            setHistoryLoading(false);
        }
    };

    const loadConversations = async () => {
        setConversationsLoading(true);
        try {
            const list = await chatService.getConversations();
            setConversations(list);
        } catch (error) {
            console.error('Failed to load conversations list:', error);
        } finally {
            setConversationsLoading(false);
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

    const selectConversation = async (id) => {
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

    const deleteConversation = async (id) => {
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

    const renameConversation = async (id, title) => {
        try {
            await chatService.renameConversation(id, title);
            setConversations(prev => prev.map(c => c.id === id ? { ...c, title: title } : c));
        } catch (error) {
            console.error('Failed to rename conversation:', error);
            throw error;
        }
    };

    const sendMessage = useCallback((message, onResponse) => {
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
                isSocketReady,
                status,
                loadHistory,
                loadConversations,
                selectConversation,
                startNewChat,
                deleteConversation,
                renameConversation,
                conversationsLoading,
                historyLoading,
                historySidebarOpen,
                setHistorySidebarOpen
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
