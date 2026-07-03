import api from './api';

export const chatService = {
    async sendMessage(request) {
        const response = await api.post('/chat/', request);
        return response.data;
    },

    async getHistory(conversationId) {
        const response = await api.get(`/chat/history/${conversationId}`);
        return response.data;
    },

    async getConversations() {
        const response = await api.get('/chat/conversations');
        return response.data;
    },

    async deleteConversation(conversationId) {
        const response = await api.delete(`/chat/history/${conversationId}`);
        return response.data;
    },

    async uploadDocument(file) {
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
