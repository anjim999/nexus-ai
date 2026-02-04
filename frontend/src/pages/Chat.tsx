import { useState, useRef, useEffect } from 'react';
import {
    Send,
    Mic,
    Sparkles,
    User,
    Bot,
    Loader2,
    ChevronDown,
    FileText,
    Database,
    Copy,
    Check,
    BarChart3,
    CheckCircle2
} from 'lucide-react';
import {
    LineChart, Line, BarChart, Bar, PieChart, Pie, Cell,
    XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer
} from 'recharts';
import { Card, Button, Badge } from '../components/ui';
import { clsx } from 'clsx';
import { chatService } from '../services/chatService';
import type { ChatResponse } from '../services/chatService';

interface Message {
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

const suggestedQuestions = [
    "What are the top 5 most expensive products?",
    "Show me the sales trend for the last week",
    "Which customers are at risk of churning?",
    "Schedule a sales report for next Monday",
    "Analyze the support tickets status",
];

const Chat = () => {
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const [conversationId, setConversationId] = useState<string | null>(null);
    const [showAgentSteps, setShowAgentSteps] = useState<string | null>(null);
    const [copiedId, setCopiedId] = useState<string | null>(null);
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const inputRef = useRef<HTMLTextAreaElement>(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const handleSend = async () => {
        if (!input.trim() || loading) return;

        const userMessage: Message = {
            id: Date.now().toString(),
            role: 'user',
            content: input.trim(),
            timestamp: new Date(),
        };

        setMessages((prev) => [...prev, userMessage]);
        setInput('');
        setLoading(true);

        try {
            const data = await chatService.sendMessage({
                message: userMessage.content,
                conversation_id: conversationId,
                include_sources: true,
            });

            setConversationId(data.conversation_id);

            const assistantMessage: Message = {
                id: (Date.now() + 1).toString(),
                role: 'assistant',
                content: data.message,
                timestamp: new Date(),
                sources: data.sources,
                confidence: data.confidence,
                agentSteps: data.agent_steps,
                charts: data.charts,
                actionsTaken: data.actions_taken
            };

            setMessages((prev) => [...prev, assistantMessage]);
        } catch (error) {
            console.error('Chat error:', error);
            const errorMessage: Message = {
                id: (Date.now() + 1).toString(),
                role: 'assistant',
                content: "I apologize, but I'm having trouble connecting to the server. Please ensure the backend is running and try again.",
                timestamp: new Date(),
            };
            setMessages((prev) => [...prev, errorMessage]);
        } finally {
            setLoading(false);
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    const handleSuggestionClick = (question: string) => {
        setInput(question);
        inputRef.current?.focus();
    };

    const copyToClipboard = (text: string, id: string) => {
        navigator.clipboard.writeText(text);
        setCopiedId(id);
        setTimeout(() => setCopiedId(null), 2000);
    };

    const renderChart = (chart: NonNullable<ChatResponse['charts']>[0]) => {
        const COLORS = ['#8884d8', '#82ca9d', '#ffc658', '#ff8042', '#00C49F'];

        return (
            <div className="mt-4 p-4 bg-muted/30 rounded-xl border border-border">
                <h4 className="text-sm font-medium mb-4 flex items-center gap-2">
                    <BarChart3 className="w-4 h-4 text-primary" />
                    {chart.title}
                </h4>
                <div className="h-64 w-full">
                    <ResponsiveContainer width="100%" height="100%">
                        {chart.chart_type === 'bar' ? (
                            <BarChart data={chart.data}>
                                <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
                                <XAxis dataKey={chart.x_axis} fontSize={12} />
                                <YAxis fontSize={12} />
                                <Tooltip />
                                <Bar dataKey={chart.y_axis} fill="#8884d8" radius={[4, 4, 0, 0]} />
                            </BarChart>
                        ) : chart.chart_type === 'pie' ? (
                            <PieChart>
                                <Pie
                                    data={chart.data}
                                    cx="50%"
                                    cy="50%"
                                    labelLine={false}
                                    label={({ name, percent }: { name?: string; percent?: number }) => `${name || 'Unknown'} ${percent ? (percent * 100).toFixed(0) : 0}%`}
                                    outerRadius={80}
                                    fill="#8884d8"
                                    dataKey={chart.y_axis}
                                    nameKey={chart.x_axis}
                                >
                                    {chart.data.map((_entry: any, index: number) => (
                                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                    ))}
                                </Pie>
                                <Tooltip />
                            </PieChart>
                        ) : (
                            <LineChart data={chart.data}>
                                <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
                                <XAxis dataKey={chart.x_axis} fontSize={12} />
                                <YAxis fontSize={12} />
                                <Tooltip />
                                <Line type="monotone" dataKey={chart.y_axis} stroke="#8884d8" strokeWidth={2} dot={{ r: 4 }} />
                            </LineChart>
                        )}
                    </ResponsiveContainer>
                </div>
            </div>
        );
    };

    return (
        <div className="flex flex-col h-full">
            {/* Header */}
            <div className="flex items-center justify-between mb-6">
                <div>
                    <h1 className="text-2xl font-bold text-foreground">AI Chat</h1>
                    <p className="text-muted-foreground mt-1">Ask questions about your business data</p>
                </div>
                <Badge variant="success" pulse>
                    AI Online
                </Badge>
            </div>

            {/* Chat Area */}
            <Card className="flex-1 flex flex-col overflow-hidden">
                {/* Messages */}
                <div className="flex-1 overflow-y-auto p-6 space-y-6">
                    {messages.length === 0 ? (
                        <div className="flex flex-col items-center justify-center h-full text-center">
                            <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center mb-6 shadow-lg shadow-violet-500/25">
                                <Sparkles className="w-10 h-10 text-white" />
                            </div>
                            <h2 className="text-xl font-semibold text-foreground mb-2">How can I help you today?</h2>
                            <p className="text-muted-foreground max-w-md mb-8">
                                Ask me anything about your business data. I can analyze trends, find insights, and generate reports.
                            </p>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-w-2xl w-full">
                                {suggestedQuestions.slice(0, 4).map((question, index) => (
                                    <button
                                        key={index}
                                        onClick={() => handleSuggestionClick(question)}
                                        className="p-4 text-left rounded-xl border border-border bg-card hover:bg-muted hover:border-primary/50 transition-all duration-200 group"
                                    >
                                        <p className="text-sm text-foreground font-medium group-hover:text-primary transition-colors">
                                            {question}
                                        </p>
                                    </button>
                                ))}
                            </div>
                        </div>
                    ) : (
                        messages.map((message) => (
                            <div
                                key={message.id}
                                className={clsx(
                                    'flex gap-4',
                                    message.role === 'user' ? 'flex-row-reverse' : ''
                                )}
                            >
                                {/* Avatar */}
                                <div
                                    className={clsx(
                                        'w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0',
                                        message.role === 'user'
                                            ? 'bg-gradient-to-br from-sky-500 to-cyan-500'
                                            : 'bg-gradient-to-br from-violet-500 to-purple-600'
                                    )}
                                >
                                    {message.role === 'user' ? (
                                        <User className="w-5 h-5 text-white" />
                                    ) : (
                                        <Bot className="w-5 h-5 text-white" />
                                    )}
                                </div>

                                {/* Message Content */}
                                <div
                                    className={clsx(
                                        'flex-1 max-w-[80%]',
                                        message.role === 'user' ? 'text-right' : ''
                                    )}
                                >
                                    <div
                                        className={clsx(
                                            'inline-block rounded-2xl px-4 py-3',
                                            message.role === 'user'
                                                ? 'bg-gradient-to-br from-violet-600 to-purple-600 text-white'
                                                : 'bg-muted text-foreground'
                                        )}
                                    >
                                        <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                                    </div>

                                    {/* Assistant extras */}
                                    {message.role === 'assistant' && (
                                        <div className="mt-3 space-y-3">

                                            {/* Actions Taken */}
                                            {message.actionsTaken && message.actionsTaken.length > 0 && (
                                                <div className="flex flex-col gap-2 p-3 bg-green-500/10 border border-green-500/20 rounded-lg">
                                                    <p className="text-xs font-semibold text-green-700 dark:text-green-400 mb-1">Actions Executed:</p>
                                                    {message.actionsTaken.map((action, idx) => (
                                                        <div key={idx} className="flex items-center gap-2 text-sm text-green-800 dark:text-green-300">
                                                            <CheckCircle2 className="w-4 h-4" />
                                                            <span>{action}</span>
                                                        </div>
                                                    ))}
                                                </div>
                                            )}

                                            {/* Charts */}
                                            {message.charts && message.charts.map((chart, idx) => (
                                                <div key={idx} className="w-full">
                                                    {renderChart(chart)}
                                                </div>
                                            ))}

                                            {/* Confidence */}
                                            {message.confidence && (
                                                <div className="flex items-center gap-2">
                                                    <Badge variant="purple" size="sm">
                                                        {Math.round(message.confidence * 100)}% confidence
                                                    </Badge>
                                                    <button
                                                        onClick={() => copyToClipboard(message.content, message.id)}
                                                        className="p-1.5 rounded-lg hover:bg-muted text-muted-foreground hover:text-foreground transition-colors"
                                                    >
                                                        {copiedId === message.id ? (
                                                            <Check className="w-4 h-4 text-emerald-400" />
                                                        ) : (
                                                            <Copy className="w-4 h-4" />
                                                        )}
                                                    </button>
                                                </div>
                                            )}

                                            {/* Sources */}
                                            {message.sources && message.sources.length > 0 && (
                                                <div className="flex flex-wrap gap-2">
                                                    {message.sources.map((source, idx) => (
                                                        <div
                                                            key={idx}
                                                            className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-muted text-xs text-muted-foreground"
                                                        >
                                                            {source.type === 'document' ? (
                                                                <FileText className="w-3.5 h-3.5" />
                                                            ) : (
                                                                <Database className="w-3.5 h-3.5" />
                                                            )}
                                                            <span>{source.name || "Database"}</span>
                                                        </div>
                                                    ))}
                                                </div>
                                            )}

                                            {/* Agent Steps */}
                                            {message.agentSteps && message.agentSteps.length > 0 && (
                                                <div>
                                                    <button
                                                        onClick={() =>
                                                            setShowAgentSteps(
                                                                showAgentSteps === message.id ? null : message.id
                                                            )
                                                        }
                                                        className="inline-flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors"
                                                    >
                                                        <ChevronDown
                                                            className={clsx(
                                                                'w-4 h-4 transition-transform',
                                                                showAgentSteps === message.id && 'rotate-180'
                                                            )}
                                                        />
                                                        View agent reasoning
                                                    </button>
                                                    {showAgentSteps === message.id && (
                                                        <div className="mt-2 space-y-2 p-3 rounded-lg bg-background border border-border">
                                                            {message.agentSteps.map((step, idx) => (
                                                                <div key={idx} className="flex items-center gap-3 text-xs">
                                                                    <Badge
                                                                        variant={step.status === 'done' ? 'success' : 'info'}
                                                                        size="sm"
                                                                    >
                                                                        {step.agent}
                                                                    </Badge>
                                                                    <span className="text-muted-foreground">{step.action || step.status}</span>
                                                                </div>
                                                            ))}
                                                        </div>
                                                    )}
                                                </div>
                                            )}
                                        </div>
                                    )}
                                </div>
                            </div>
                        ))
                    )}

                    {/* Loading indicator */}
                    {loading && (
                        <div className="flex gap-4">
                            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center">
                                <Bot className="w-5 h-5 text-white" />
                            </div>
                            <div className="flex items-center gap-2 text-muted-foreground">
                                <Loader2 className="w-4 h-4 animate-spin" />
                                <span className="text-sm">Thinking...</span>
                            </div>
                        </div>
                    )}

                    <div ref={messagesEndRef} />
                </div>

                {/* Input Area */}
                <div className="border-t border-border p-4">
                    <div className="flex items-end gap-3">
                        <div className="flex-1 relative">
                            <textarea
                                ref={inputRef}
                                value={input}
                                onChange={(e) => setInput(e.target.value)}
                                onKeyDown={handleKeyDown}
                                placeholder="Ask anything about your business..."
                                rows={1}
                                className="w-full bg-muted border border-border rounded-xl px-4 py-3 pr-12 text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary transition-all resize-none"
                                style={{ minHeight: '48px', maxHeight: '120px' }}
                            />
                            <button className="absolute right-3 top-1/2 -translate-y-1/2 p-2 text-muted-foreground hover:text-foreground transition-colors">
                                <Mic className="w-5 h-5" />
                            </button>
                        </div>
                        <Button onClick={handleSend} loading={loading} className="h-12 px-5">
                            <Send className="w-4 h-4" />
                        </Button>
                    </div>
                </div>
            </Card>
        </div>
    );
};

export default Chat;
