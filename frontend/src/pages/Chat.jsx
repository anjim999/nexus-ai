import { useState, useRef, useEffect } from 'react';
import {
    Send,
    Mic,
    MicOff,
    Volume2,
    VolumeX,
    Play,
    Pause,
    Square,
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
    History,
    MoreVertical,
    Pencil,
    Maximize2,
    Minimize2
} from 'lucide-react';
import {
    LineChart, Line, BarChart, Bar, PieChart, Pie, Cell,
    XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer
} from 'recharts';
import { Card, Button, Badge, Modal, Input } from '../components/ui';
import { clsx } from 'clsx';
import ReactMarkdown from 'react-markdown';
import { useChat } from '../context/ChatContext';
import useVoice from '../hooks/useVoice';
import VoiceOverlay from '../components/chat/VoiceOverlay';

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
        isSocketReady,
        status,
        selectConversation,
        startNewChat,
        deleteConversation,
        renameConversation,
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
    const [activeMenuConvId, setActiveMenuConvId] = useState(null);
    const [renameModalConv, setRenameModalConv] = useState(null);
    const [renameTitle, setRenameTitle] = useState("");
    const [isRenaming, setIsRenaming] = useState(false);
    const messagesEndRef = useRef(null);
    const inputRef = useRef(null);

    // Voice Interface
    const {
        isListening,
        isInitializing,
        isTranscribing,
        audioStream,
        transcript,
        suffix,
        startListening,
        stopListening,
        toggleListening,
        isSTTSupported,
        isSpeaking,
        isPaused,
        speak,
        pauseSpeaking,
        resumeSpeaking,
        stopSpeaking,
        isTTSSupported,
        voiceEnabled,
        resetTranscript,
        updateVoiceText,
    } = useVoice();
    const [speakingMessageId, setSpeakingMessageId] = useState(null);
    const [cursorIndex, setCursorIndex] = useState(null);
    const [isInputExpanded, setIsInputExpanded] = useState(false);
    const [showExpandButton, setShowExpandButton] = useState(false);

    // Auto-grow textarea height as user types or speaks
    useEffect(() => {
        const textarea = inputRef.current;
        if (textarea) {
            textarea.style.height = 'auto';
            const maxHeight = isInputExpanded ? 350 : 120;
            const newHeight = Math.min(textarea.scrollHeight, maxHeight);
            textarea.style.height = `${newHeight}px`;

            // Only show scrollbar when the text exceeds maxHeight limits
            if (textarea.scrollHeight > maxHeight) {
                textarea.style.overflowY = 'auto';
            } else {
                textarea.style.overflowY = 'hidden';
            }

            // Check if text has reached at least 4 lines (approx >= 100px scrollHeight)
            const isLong = textarea.scrollHeight >= 100;
            setShowExpandButton(isLong);

            // Collapse if the content goes back below 4 lines
            if (!isLong && isInputExpanded) {
                setIsInputExpanded(false);
            }
        }
    }, [input, isInputExpanded]);

    // Keep cursor position aligned after text insertion
    useEffect(() => {
        if (cursorIndex !== null && inputRef.current) {
            inputRef.current.setSelectionRange(cursorIndex, cursorIndex);
            setCursorIndex(null);
        }
    }, [cursorIndex]);

    const handleStartVoice = () => {
        const textarea = inputRef.current;
        if (textarea) {
            const start = textarea.selectionStart || 0;
            const val = textarea.value || '';
            const before = val.slice(0, start);
            const after = val.slice(start);
            startListening(before, after);
        } else {
            startListening(input, '');
        }
    };

    // Sync voice transcript into input field
    useEffect(() => {
        if (transcript) {
            setInput(transcript + suffix);
            const newCursor = transcript.length;
            setCursorIndex(newCursor);
        }
    }, [transcript, suffix]);


    // Clear speakingMessageId when TTS finishes
    useEffect(() => {
        if (!isSpeaking && !isPaused) {
            setSpeakingMessageId(null);
        }
    }, [isSpeaking, isPaused]);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    const parseUTCDate = (dateStr) => {
        if (!dateStr) return new Date();
        if (dateStr instanceof Date) return dateStr;
        let parsedStr = dateStr;
        if (typeof dateStr === 'string' && !dateStr.endsWith('Z') && !dateStr.match(/[+-]\d{2}:?\d{2}$/)) {
            parsedStr = dateStr.includes('T') ? dateStr + 'Z' : dateStr.replace(' ', 'T') + 'Z';
        }
        return new Date(parsedStr);
    };

    const formatMessageTime = (date) => {
        if (!date) return "";
        const d = parseUTCDate(date);
        if (isNaN(d.getTime())) return "";
        return d.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit', hour12: true });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages, agentStatus]);

    const handleSend = async () => {
        if (!input.trim() || loading || !isSocketReady) return;

        const userMessage = {
            id: Date.now().toString(),
            role: 'user',
            content: input.trim(),
            timestamp: new Date().toISOString(),
        };

        setMessages((prev) => [...prev, userMessage]);
        setInput('');
        resetTranscript();
        setLoading(true);

        sendMessage(userMessage.content, (data) => {
            const assistantMessage = {
                id: (Date.now() + 1).toString(),
                role: 'assistant',
                content: data.message,
                timestamp: new Date().toISOString(),
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
                    <div className="w-60 flex flex-col bg-card border-r border-border h-full flex-shrink-0">
                        {/* New Chat Button */}
                        <div className="p-4 border-b border-border">
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
                            {conversationsLoading && conversations.length === 0 ? (
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
                                                    {parseUTCDate(conv.updated_at).toLocaleDateString([], {
                                                        month: 'short',
                                                        day: 'numeric',
                                                        hour: '2-digit',
                                                        minute: '2-digit'
                                                    })}
                                                </p>
                                            </div>

                                            {/* Action Menu (3 Dots) */}
                                            <div className="absolute right-2">
                                                <button
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        setActiveMenuConvId(activeMenuConvId === conv.id ? null : conv.id);
                                                    }}
                                                    className={clsx(
                                                        "p-1.5 rounded-lg bg-background border border-border text-muted-foreground hover:text-foreground shadow-sm cursor-pointer transition-all duration-150",
                                                        activeMenuConvId === conv.id ? "opacity-100" : "opacity-0 group-hover:opacity-100"
                                                    )}
                                                >
                                                    <MoreVertical className="w-3.5 h-3.5" />
                                                </button>

                                                {activeMenuConvId === conv.id && (
                                                    <>
                                                        <div
                                                            className="fixed inset-0 z-30 cursor-default"
                                                            onClick={(e) => {
                                                                e.stopPropagation();
                                                                setActiveMenuConvId(null);
                                                            }}
                                                        />
                                                        <div className="absolute right-0 mt-1 z-40 w-32 bg-card text-foreground border border-border rounded-lg shadow-lg py-1 animate-in fade-in slide-in-from-top-1 duration-100">
                                                            <button
                                                                onClick={(e) => {
                                                                    e.stopPropagation();
                                                                    setRenameModalConv(conv);
                                                                    setRenameTitle(conv.title || "New Conversation");
                                                                    setActiveMenuConvId(null);
                                                                }}
                                                                className="w-full flex items-center gap-2 px-3 py-2 text-xs hover:bg-muted text-foreground transition-colors text-left font-medium cursor-pointer"
                                                            >
                                                                <Pencil className="w-3.5 h-3.5 text-muted-foreground" />
                                                                Rename
                                                            </button>
                                                            <button
                                                                onClick={(e) => {
                                                                    e.stopPropagation();
                                                                    setDeleteModalConv(conv);
                                                                    setActiveMenuConvId(null);
                                                                }}
                                                                className="w-full flex items-center gap-2 px-3 py-2 text-xs hover:bg-destructive/10 text-destructive transition-colors text-left font-medium cursor-pointer"
                                                            >
                                                                <Trash2 className="w-3.5 h-3.5" />
                                                                Delete
                                                            </button>
                                                        </div>
                                                    </>
                                                )}
                                            </div>
                                        </div>
                                    );
                                })
                            )}
                        </div>
                    </div>
                )}

                {/* Right Chat Container */}
                <div className="flex-1 flex flex-col h-full overflow-hidden bg-slate-50 dark:bg-background">
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
                                            'w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 shadow-xs border',
                                            message.role === 'user'
                                                ? 'bg-slate-100 text-slate-700 border-slate-200/60 dark:bg-slate-800 dark:text-slate-300 dark:border-slate-700'
                                                : 'bg-slate-900 text-white border-slate-800 dark:bg-slate-100 dark:text-slate-900 dark:border-slate-200'
                                        )}
                                    >
                                        {message.role === 'user' ? (
                                            <User className="w-5 h-5" />
                                        ) : (
                                            <Bot className="w-5 h-5" />
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
                                                'inline-block rounded-2xl px-5 py-3.5 text-left shadow-sm transition-all duration-200 border',
                                                message.role === 'user'
                                                    ? 'bg-slate-900 text-slate-50 border-transparent dark:bg-slate-800 dark:text-slate-100 dark:border-slate-700'
                                                    : 'bg-card text-foreground border-border/80 shadow-xs hover:shadow-sm'
                                            )}
                                        >
                                            <ReactMarkdown
                                                components={{
                                                    p: ({ node, ...props }) => <p className="mb-1 text-sm whitespace-pre-wrap" {...props} />,
                                                    ul: ({ node, ...props }) => <ul className="list-disc pl-4 mb-2 space-y-1 text-sm" {...props} />,
                                                    ol: ({ node, ...props }) => <ol className="list-decimal pl-4 mb-2 space-y-1 text-sm" {...props} />,
                                                    li: ({ node, ...props }) => <li className="text-sm" {...props} />,
                                                    strong: ({ node, ...props }) => (
                                                        <strong
                                                            className={clsx(
                                                                message.role === 'user' ? 'text-white font-semibold' : 'text-foreground font-semibold'
                                                            )}
                                                            {...props}
                                                        />
                                                    ),
                                                    a: ({ node, ...props }) => (
                                                        <a
                                                            className={clsx(
                                                                message.role === 'user'
                                                                    ? 'text-violet-200 hover:text-white'
                                                                    : 'text-violet-600 hover:text-violet-800 dark:text-violet-400 dark:hover:text-violet-300',
                                                                'hover:underline font-medium'
                                                            )}
                                                            target="_blank"
                                                            rel="noopener noreferrer"
                                                            {...props}
                                                        />
                                                    ),
                                                    code: ({ node, ...props }) => (
                                                        <code
                                                            className={clsx(
                                                                message.role === 'user'
                                                                    ? 'bg-white/20 text-white'
                                                                    : 'bg-muted text-muted-foreground border border-border/50',
                                                                'px-1.5 py-0.5 rounded text-xs font-mono'
                                                            )}
                                                            {...props}
                                                        />
                                                    ),
                                                    hr: ({ node, ...props }) => <hr className="my-5 border-t border-border/30" {...props} />,
                                                }}
                                            >
                                                {message.content}
                                            </ReactMarkdown>
                                        </div>
                                        <div className={clsx(
                                            "mt-1 text-[10px] text-muted-foreground/60 select-none",
                                            message.role === 'user' ? 'text-right pr-2' : 'text-left pl-2'
                                        )}>
                                            {formatMessageTime(message.timestamp)}
                                        </div>

                                        {/* Assistant extras */}
                                        {message.role === 'assistant' && (
                                            <div className="mt-3 space-y-3">

                                                {/* Actions Taken */}
                                                {message.actionsTaken && message.actionsTaken.length > 0 && (
                                                    <div className="flex flex-col gap-2 p-3 bg-slate-50 border border-slate-200 rounded-lg text-left dark:bg-slate-900/40 dark:border-slate-700">
                                                        <p className="text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">Actions Executed:</p>
                                                        {message.actionsTaken.map((action, idx) => (
                                                            <div key={idx} className="flex items-center gap-2 text-sm text-slate-700 dark:text-slate-300">
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

                                                {/* Message Controls (Copy & TTS) */}
                                                <div className="flex items-center gap-2 mt-2">
                                                    {message.confidence && (
                                                        <Badge variant="purple" size="sm" className="bg-slate-100 text-slate-700 border-slate-200 dark:bg-slate-800 dark:text-slate-200 dark:border-slate-700 mr-2">
                                                            {Math.round(message.confidence * 100)}% confidence
                                                        </Badge>
                                                    )}

                                                    {/* Copy button */}
                                                    <button
                                                        onClick={() => copyToClipboard(message.content, message.id)}
                                                        className="p-1.5 rounded-lg hover:bg-muted text-muted-foreground hover:text-foreground transition-colors cursor-pointer"
                                                        title="Copy text"
                                                    >
                                                        {copiedId === message.id ? (
                                                            <Check className="w-4 h-4 text-emerald-400" />
                                                        ) : (
                                                            <Copy className="w-4 h-4" />
                                                        )}
                                                    </button>

                                                    {/* TTS Controls */}
                                                    {isTTSSupported && (
                                                        <div className="flex items-center gap-1">
                                                            {/* Play / Pause / Resume Button */}
                                                            <button
                                                                onClick={() => {
                                                                    if (speakingMessageId === message.id) {
                                                                        if (isSpeaking && !isPaused) {
                                                                            pauseSpeaking();
                                                                        } else if (isPaused) {
                                                                            resumeSpeaking();
                                                                        } else {
                                                                            speak(message.content);
                                                                        }
                                                                    } else {
                                                                        setSpeakingMessageId(message.id);
                                                                        speak(message.content);
                                                                    }
                                                                }}
                                                                className={clsx(
                                                                    "p-1.5 rounded-lg hover:bg-muted text-muted-foreground hover:text-foreground transition-colors cursor-pointer",
                                                                    speakingMessageId === message.id && isSpeaking && !isPaused && "voice-speaking"
                                                                )}
                                                                title={
                                                                    speakingMessageId === message.id && isSpeaking && !isPaused
                                                                        ? "Pause"
                                                                        : speakingMessageId === message.id && isPaused
                                                                            ? "Resume"
                                                                            : "Read aloud"
                                                                }
                                                            >
                                                                {speakingMessageId === message.id && isSpeaking && !isPaused ? (
                                                                    <Pause className="w-4.5 h-4.5" />
                                                                ) : speakingMessageId === message.id && isPaused ? (
                                                                    <Play className="w-4.5 h-4.5" />
                                                                ) : (
                                                                    <Volume2 className="w-4.5 h-4.5" />
                                                                )}
                                                            </button>

                                                            {/* Stop Button (only shown when this message is active) */}
                                                            {speakingMessageId === message.id && (isSpeaking || isPaused) && (
                                                                <button
                                                                    onClick={() => {
                                                                        stopSpeaking();
                                                                        setSpeakingMessageId(null);
                                                                    }}
                                                                    className="p-1.5 rounded-lg hover:bg-muted text-red-500 hover:text-red-600 transition-colors cursor-pointer"
                                                                    title="Stop"
                                                                >
                                                                    <Square className="w-4 h-4" />
                                                                </button>
                                                            )}
                                                        </div>
                                                    )}
                                                </div>

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
                                <div className="w-10 h-10 rounded-xl bg-slate-900 text-white flex items-center justify-center dark:bg-slate-100 dark:text-slate-900">
                                    <Bot className="w-5 h-5" />
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
                    <div className="p-4 border-t border-border bg-card">
                        <div className="flex items-end gap-3">
                            {(isListening || isInitializing || isTranscribing) ? (
                                <VoiceOverlay
                                    audioStream={audioStream}
                                    isInitializing={isInitializing}
                                    isTranscribing={isTranscribing}
                                    onCancel={() => {
                                        stopListening();
                                        resetTranscript();
                                    }}
                                    onConfirm={() => {
                                        stopListening();
                                    }}
                                />
                            ) : (
                                <>
                                    <div className="flex-1 relative">
                                        <textarea
                                            ref={inputRef}
                                            value={input}
                                            onChange={(e) => setInput(e.target.value)}
                                            onKeyDown={handleKeyDown}
                                            disabled={loading}
                                            placeholder={loading ? "AI is processing your query..." : "Ask anything about your business..."}
                                            rows={1}
                                            className="w-full bg-background border border-border rounded-xl px-4 pr-12 py-3 text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all resize-none shadow-inner disabled:opacity-60 disabled:cursor-not-allowed"
                                            style={{ minHeight: '48px', maxHeight: isInputExpanded ? '350px' : '120px' }}
                                        />
                                        
                                        {/* Expand/Collapse Toggle Button - Top Right Corner */}
                                        {showExpandButton && (
                                            <button
                                                onClick={(e) => {
                                                    e.preventDefault();
                                                    setIsInputExpanded(!isInputExpanded);
                                                }}
                                                className="absolute right-2 top-2 p-1.5 rounded-md text-muted-foreground hover:text-foreground hover:bg-muted/50 transition-all duration-200 cursor-pointer z-10"
                                                title={isInputExpanded ? "Collapse input area" : "Expand input area"}
                                            >
                                                {isInputExpanded ? (
                                                    <Minimize2 className="w-3.5 h-3.5" />
                                                ) : (
                                                    <Maximize2 className="w-3.5 h-3.5" />
                                                )}
                                            </button>
                                        )}

                                        {/* Start Voice Typing Button - Bottom Right Corner */}
                                        {isSTTSupported && (
                                            <button
                                                onClick={(e) => {
                                                    e.preventDefault();
                                                    handleStartVoice();
                                                }}
                                                disabled={loading}
                                                className="absolute right-3 bottom-2 p-1.5 rounded-full text-muted-foreground hover:text-foreground transition-all duration-200 cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed z-10"
                                                title="Start voice typing"
                                            >
                                                <Mic className="w-5 h-5" />
                                            </button>
                                        )}
                                    </div>
                                    <Button
                                        onClick={() => {
                                            handleSend();
                                            setIsInputExpanded(false);
                                        }}
                                        loading={loading}
                                        disabled={loading || !input.trim() || !isSocketReady}
                                        className="h-12 px-5"
                                    >
                                        <Send className="w-4 h-4" />
                                    </Button>
                                </>
                            )}
                        </div>
                    </div>
                </div>
            </div>

            {/* Rename Conversation Modal */}
            <Modal
                isOpen={!!renameModalConv}
                onClose={() => setRenameModalConv(null)}
                title="Rename Conversation"
                size="sm"
            >
                <div className="space-y-4">
                    <div className="space-y-1.5">
                        <label className="text-xs font-semibold text-muted-foreground">
                            Conversation Title
                        </label>
                        <Input
                            value={renameTitle}
                            onChange={(e) => setRenameTitle(e.target.value)}
                            placeholder="Enter chat name..."
                            autoFocus
                            onKeyDown={async (e) => {
                                if (e.key === 'Enter') {
                                    if (renameModalConv && renameTitle.trim()) {
                                        setIsRenaming(true);
                                        try {
                                            await renameConversation(renameModalConv.id, renameTitle.trim());
                                        } finally {
                                            setIsRenaming(false);
                                            setRenameModalConv(null);
                                        }
                                    }
                                }
                            }}
                        />
                    </div>
                    <div className="flex justify-end gap-3">
                        <Button variant="outline" onClick={() => setRenameModalConv(null)}>
                            Cancel
                        </Button>
                        <Button
                            loading={isRenaming}
                            onClick={async () => {
                                if (renameModalConv && renameTitle.trim()) {
                                    setIsRenaming(true);
                                    try {
                                        await renameConversation(renameModalConv.id, renameTitle.trim());
                                    } finally {
                                        setIsRenaming(false);
                                        setRenameModalConv(null);
                                    }
                                }
                            }}
                        >
                            Save
                        </Button>
                    </div>
                </div>
            </Modal>

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
