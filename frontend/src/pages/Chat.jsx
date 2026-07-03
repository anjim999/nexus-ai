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
    CheckCircle2,
    MessageSquare,
    Plus,
    Trash2,
    History
} from 'lucide-react';
import {
    LineChart, Line, BarChart, Bar, PieChart, Pie, Cell,
    XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer
} from 'recharts';
import { Card, Button, Badge, Modal } from '../components/ui';
import { clsx } from 'clsx';
import ReactMarkdown from 'react-markdown';
import { useChat } from '../context/ChatContext';

const suggestedQuestions = [
    "What are the top 5 most expensive products?",
    "Show me the sales trend for the last week",
    "Which customers are at risk of churning?",
    "Schedule a sales report for next Monday",
    "Analyze the support tickets status",
];

const Chat = () => {
    const { 
        messages, setMessages, 
        input, setInput, 
        loading, setLoading, 
        conversationId, 
        conversations,
        sendMessage, 
        agentStatus, 
        isConnected, 
        status,
        selectConversation,
        startNewChat,
        deleteConversation,
        conversationsLoading,
        historyLoading,
        historySidebarOpen: sidebarOpen
    } = useChat();

    // Handle unexpected disconnections while waiting for response
    useEffect(() => {
        if ((status === 'closed' || status === 'error') && loading) {
            setLoading(false);
            setMessages((prev) => [...prev, {
                id: Date.now().toString(),
                role: 'assistant',
                content: '⚠️ Connection lost. The backend server might have restarted or crashed. Please try your request again.',
                timestamp: new Date()
            }]);
        }
    }, [status, loading]);

    const [showAgentSteps, setShowAgentSteps] = useState(null);
    const [showSources, setShowSources] = useState(null);
    const [copiedId, setCopiedId] = useState(null);
    const [deleteModalConv, setDeleteModalConv] = useState(null);
    const [isDeleting, setIsDeleting] = useState(false);
    const messagesEndRef = useRef(null);
    const inputRef = useRef(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages, agentStatus]);

    const handleSend = async () => {
        if (!input.trim() || loading || !isConnected) return;

        const userMessage = {
            id: Date.now().toString(),
            role: 'user',
            content: input.trim(),
            timestamp: new Date(),
        };

        setMessages((prev) => [...prev, userMessage]);
        setInput('');
        setLoading(true);

        sendMessage(userMessage.content, (data) => {
            const assistantMessage = {
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
            setLoading(false);
        });
    };

    const handleKeyDown = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    const handleSuggestionClick = (question) => {
        setInput(question);
        inputRef.current?.focus();
    };

    const copyToClipboard = (text, id) => {
        navigator.clipboard.writeText(text);
        setCopiedId(id);
        setTimeout(() => setCopiedId(null), 2000);
    };

    const renderChart = (chart) => {
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
                                    label={({ name, percent }) => `${name || 'Unknown'} ${percent ? (percent * 100).toFixed(0) : 0}%`}
                                    outerRadius={80}
                                    fill="#8884d8"
                                    dataKey={chart.y_axis}
                                    nameKey={chart.x_axis}
                                >
                                    {chart.data.map((_entry, index) => (
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
        <div className="flex flex-col h-[calc(100vh-64px)] -mx-4 -mb-4 -mt-3 overflow-hidden">
            {/* Chat Area */}
            <div className="flex-1 flex flex-row overflow-hidden">
                {/* Left History Sidebar */}
                {sidebarOpen && (
                    <div className="w-60 flex flex-col bg-[#0c0e17] h-full flex-shrink-0">
                        {/* New Chat Button */}
                        <div className="p-4">
                            <Button 
                                onClick={startNewChat} 
                                className="w-full flex items-center justify-center gap-2"
                                icon={<Plus className="w-4 h-4" />}
                            >
                                New Chat
                            </Button>
                        </div>
                        
                        {/* Conversation list */}
                        <div className="flex-1 overflow-y-auto p-3 space-y-1">
                            {conversationsLoading ? (
                                <div className="flex flex-col items-center justify-center h-full py-8 text-center text-xs text-muted-foreground">
                                    <Loader2 className="w-5 h-5 text-primary animate-spin mb-2" />
                                    <p>Loading history...</p>
                                </div>
                            ) : conversations.length === 0 ? (
                                <div className="flex flex-col items-center justify-center h-full py-8 text-center text-xs text-muted-foreground">
                                    <MessageSquare className="w-8 h-8 text-muted-foreground/30 mb-2 animate-bounce" />
                                    <p>No past chats</p>
                                </div>
                            ) : (
                                conversations.map((conv) => {
                                    const isActive = conv.id === conversationId;
                                    return (
                                        <div
                                            key={conv.id}
                                            onClick={() => selectConversation(conv.id)}
                                            className={clsx(
                                                "group relative flex items-center gap-3 px-3 py-2.5 rounded-lg cursor-pointer transition-all duration-200",
                                                isActive
                                                    ? "bg-primary/10 text-primary shadow-sm"
                                                    : "hover:bg-muted/60 text-muted-foreground hover:text-foreground"
                                            )}
                                        >
                                            <MessageSquare className={clsx("w-4 h-4 flex-shrink-0", isActive ? "text-primary" : "text-muted-foreground")} />
                                            <div className="flex-1 min-w-0 pr-6">
                                                <p className="text-sm font-medium truncate">
                                                    {conv.title || "New Conversation"}
                                                </p>
                                                <p className="text-[10px] text-muted-foreground/75 mt-0.5">
                                                    {new Date(conv.updated_at).toLocaleDateString([], {
                                                        month: 'short',
                                                        day: 'numeric',
                                                        hour: '2-digit',
                                                        minute: '2-digit'
                                                    })}
                                                </p>
                                            </div>
                                            <button
                                                onClick={(e) => {
                                                    e.stopPropagation();
                                                    setDeleteModalConv(conv);
                                                }}
                                                className="absolute right-2 p-1.5 rounded-lg bg-background border border-border text-muted-foreground hover:text-destructive opacity-0 group-hover:opacity-100 hover:bg-destructive/10 hover:border-destructive/20 transition-all duration-150 shadow-sm cursor-pointer"
                                            >
                                                <Trash2 className="w-3.5 h-3.5" />
                                            </button>
                                        </div>
                                    );
                                })
                            )}
                        </div>
                    </div>
                )}

                {/* Right Chat Container */}
                <div className="flex-1 flex flex-col h-full overflow-hidden bg-[#141824]">
                    {/* Messages */}
                    <div className="flex-1 overflow-y-auto p-6 space-y-6">
                        {historyLoading ? (
                            <div className="flex flex-col items-center justify-center h-full py-12 text-center text-sm text-muted-foreground">
                                <Loader2 className="w-8 h-8 text-primary animate-spin mb-3" />
                                <p>Loading conversation messages...</p>
                            </div>
                        ) : messages.length === 0 ? (
                            <div className="flex flex-col items-center justify-center h-full text-center">
                                <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center mb-6 shadow-lg shadow-violet-500/25 animate-pulse">
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
                                            className="p-4 text-left rounded-xl border border-border bg-card hover:bg-muted hover:border-primary/50 transition-all duration-200 group cursor-pointer"
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
                                            'flex-1 max-w-[85%]',
                                            message.role === 'user' ? 'ml-auto text-right' : 'text-left'
                                        )}
                                    >
                                        <div
                                            className={clsx(
                                                'inline-block rounded-2xl px-5 py-3.5 text-left shadow-sm',
                                                message.role === 'user'
                                                    ? 'bg-gradient-to-br from-violet-600 to-purple-600 text-white shadow-md'
                                                    : 'bg-[#1c2333] text-foreground'
                                            )}
                                        >
                                            <ReactMarkdown
                                                components={{
                                                    p: ({ node, ...props }) => <p className="mb-1 text-sm whitespace-pre-wrap" {...props} />,
                                                    ul: ({ node, ...props }) => <ul className="list-disc pl-4 mb-2 space-y-1 text-sm" {...props} />,
                                                    ol: ({ node, ...props }) => <ol className="list-decimal pl-4 mb-2 space-y-1 text-sm" {...props} />,
                                                    li: ({ node, ...props }) => <li className="text-sm" {...props} />,
                                                    strong: ({ node, ...props }) => <strong className="font-bold" {...props} />,
                                                    a: ({ node, ...props }) => <a className="text-violet-400 dark:text-violet-300 hover:underline font-medium" target="_blank" rel="noopener noreferrer" {...props} />,
                                                    code: ({ node, ...props }) => <code className="bg-foreground/10 px-1 py-0.5 rounded text-xs font-mono" {...props} />,
                                                    hr: ({ node, ...props }) => <hr className="my-5 border-t border-border/30" {...props} />,
                                                }}
                                            >
                                                {message.content}
                                            </ReactMarkdown>
                                        </div>

                                        {/* Assistant extras */}
                                        {message.role === 'assistant' && (
                                            <div className="mt-3 space-y-3">

                                                {/* Actions Taken */}
                                                {message.actionsTaken && message.actionsTaken.length > 0 && (
                                                    <div className="flex flex-col gap-2 p-3 bg-green-500/10 border border-green-500/20 rounded-lg text-left">
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
                                                            className="p-1.5 rounded-lg hover:bg-muted text-muted-foreground hover:text-foreground transition-colors cursor-pointer"
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
                                                    <div className="text-left">
                                                        <button
                                                            onClick={() =>
                                                                setShowSources(
                                                                    showSources === message.id ? null : message.id
                                                                )
                                                            }
                                                            className="inline-flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors cursor-pointer"
                                                        >
                                                            <ChevronDown
                                                                className={clsx(
                                                                    'w-4 h-4 transition-transform',
                                                                    showSources === message.id && 'rotate-180'
                                                                )}
                                                            />
                                                            View sources
                                                        </button>
                                                        {showSources === message.id && (
                                                            <div className="flex flex-wrap gap-2 mt-2">
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
                                                    </div>
                                                )}

                                                {/* Agent Steps */}
                                                {message.agentSteps && message.agentSteps.length > 0 && (
                                                    <div className="text-left">
                                                        <button
                                                            onClick={() =>
                                                                setShowAgentSteps(
                                                                    showAgentSteps === message.id ? null : message.id
                                                                )
                                                            }
                                                            className="inline-flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors cursor-pointer"
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
                                    <span className="text-sm">{agentStatus || "Thinking..."}</span>
                                </div>
                            </div>
                        )}

                        <div ref={messagesEndRef} />
                    </div>

                    {/* Input Area */}
                    <div className="p-4 bg-[#141824]">
                        <div className="flex items-end gap-3">
                            <div className="flex-1 relative">
                                <textarea
                                    ref={inputRef}
                                    value={input}
                                    onChange={(e) => setInput(e.target.value)}
                                    onKeyDown={handleKeyDown}
                                    placeholder="Ask anything about your business..."
                                    rows={1}
                                    className="w-full bg-[#1c2333] border border-transparent rounded-xl px-4 py-3 pr-12 text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all resize-none shadow-inner"
                                    style={{ minHeight: '48px', maxHeight: '120px' }}
                                />
                                <button className="absolute right-3 top-1/2 -translate-y-1/2 p-2 text-muted-foreground hover:text-foreground transition-colors cursor-pointer">
                                    <Mic className="w-5 h-5" />
                                </button>
                            </div>
                            <Button onClick={handleSend} loading={loading} className="h-12 px-5">
                                <Send className="w-4 h-4" />
                            </Button>
                        </div>
                    </div>
                </div>
            </div>

            {/* Delete Conversation Confirmation Modal */}
            <Modal
                isOpen={!!deleteModalConv}
                onClose={() => setDeleteModalConv(null)}
                title="Delete Conversation"
                size="sm"
            >
                <div className="space-y-4">
                    <p className="text-muted-foreground">
                        Are you sure you want to delete <strong className="text-foreground">{deleteModalConv?.title || 'this conversation'}</strong>? This will permanently erase the chat history.
                    </p>
                    <div className="flex justify-end gap-3">
                        <Button variant="outline" onClick={() => setDeleteModalConv(null)}>
                            Cancel
                        </Button>
                        <Button 
                            variant="destructive" 
                            loading={isDeleting}
                            onClick={async () => {
                                if (deleteModalConv) {
                                    setIsDeleting(true);
                                    try {
                                        await deleteConversation(deleteModalConv.id);
                                    } finally {
                                        setIsDeleting(false);
                                        setDeleteModalConv(null);
                                    }
                                }
                            }}
                        >
                            {isDeleting ? 'Deleting...' : 'Delete'}
                        </Button>
                    </div>
                </div>
            </Modal>
        </div>
    );
};

export default Chat;
