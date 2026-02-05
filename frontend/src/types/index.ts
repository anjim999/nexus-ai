// Nexus AI - TypeScript Types

// Chat Types
export interface ChatMessage {
    id?: number;
    role: 'user' | 'assistant' | 'system';
    content: string;
    timestamp?: string;
    sources?: Source[];
    confidence?: number;
    agentSteps?: AgentStep[];
}

export interface Source {
    type: 'document' | 'database';
    name: string;
    page?: number;
    relevance?: number;
    snippet?: string;
}

export interface AgentStep {
    agent: string;
    status: 'idle' | 'thinking' | 'executing' | 'done' | 'error';
    action?: string;
    result?: string;
    durationMs?: number;
}

export interface ChatResponse {
    message: string;
    conversationId: string;
    sources?: Source[];
    confidence: number;
    agentSteps: AgentStep[];
    charts?: ChartData[];
    actionsTaken?: string[];
}

// Dashboard Types
export interface MetricCard {
    id: string;
    title: string;
    value: string;
    change: number;
    trend: 'up' | 'down' | 'stable';
    period: string;
    icon?: string;
}

export interface AlertItem {
    id: string;
    title: string;
    message: string;
    severity: 'info' | 'warning' | 'critical';
    timestamp: string;
    isRead: boolean;
}

export interface AIInsight {
    id: string;
    title: string;
    summary: string;
    details: string;
    confidence: number;
    sources: string[];
    generatedAt: string;
    category: string;
    priority: number;
}

export interface ChartData {
    chartType: 'line' | 'bar' | 'pie' | 'area';
    title: string;
    data: Record<string, unknown>[];
    xAxis: string;
    yAxis: string;
}

// Document Types
export interface Document {
    id: string;
    filename: string;
    fileType: string;
    sizeBytes: number;
    uploadedAt: string;
    chunkCount: number;
    status: 'pending' | 'processing' | 'indexed' | 'failed';
}

// Agent Types
export interface AgentInfo {
    id: string;
    name: string;
    type: 'research' | 'analyst' | 'reasoning' | 'action' | 'scheduler';
    description: string;
    status: 'idle' | 'thinking' | 'executing' | 'done' | 'error';
    capabilities: string[];
    tasksCompleted: number;
}

// Report Types
export interface Report {
    id: string;
    title: string;
    reportType: string;
    format: 'pdf' | 'html' | 'markdown' | 'json';
    generatedAt: string;
    fileSizeBytes?: number;
    downloadUrl: string;
}
