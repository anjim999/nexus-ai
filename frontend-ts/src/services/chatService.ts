
import api from './api';

export interface ChatRequest {
    message: string;
    conversation_id?: string | null;
    include_sources?: boolean;
    stream?: boolean;
}

export interface ChatResponse {
    message: string;
    conversation_id: string;
    sources?: Array<{
        type: string;
        name?: string;
        page?: number;
        query?: string;
        relevance?: number;
    }>;
    confidence: number;
    agent_steps: Array<{
        agent: string;
        status: string;
        action?: string;
        result?: string;
        duration_ms?: number;
    }>;
    charts?: Array<{
        title: string;
        chart_type: 'line' | 'bar' | 'pie';
        data: any[];
        x_axis: string;
        y_axis: string;
    }>;
    actions_taken?: string[];
}

export interface ConversationItem {
    id: string;
    title: string | null;
    created_at: string;
    updated_at: string;
}

export const chatService = {
    async sendMessage(request: ChatRequest): Promise<ChatResponse> {
        const response = await api.post<ChatResponse>('/chat/', request);
        return response.data;
    },

    async getHistory(conversationId: string) {
        const response = await api.get(`/chat/history/${conversationId}`);
        return response.data;
    },

    async getConversations(): Promise<ConversationItem[]> {
        const response = await api.get<ConversationItem[]>('/chat/conversations');
        return response.data;
    },

    async deleteConversation(conversationId: string) {
        const response = await api.delete(`/chat/history/${conversationId}`);
        return response.data;
    },

    async uploadDocument(file: File) {
        const formData = new FormData();
        formData.append('file', file);
        const response = await api.post('/documents/upload', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });
        return response.data;
    }
};
