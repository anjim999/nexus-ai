import { useState, useEffect } from 'react';
import {
    Bot,
    Search,
    Database,
    Brain,
    Zap,
    Clock,
    RefreshCw,
    CheckCircle2,
    AlertCircle,
    Loader2,
    ChevronRight,
    Activity,
} from 'lucide-react';
import { Card, CardContent, Button, Badge, Modal } from '../components/ui';
import { clsx } from 'clsx';
import api from '../services/api';

interface Agent {
    id: string;
    name: string;
    type: string;
    description: string;
    status: 'idle' | 'thinking' | 'executing' | 'done' | 'error';
    capabilities: string[];
    tasks_completed: number;
    last_active?: string;
}

interface AgentThought {
    timestamp: string;
    agent: string;
    thought: string;
    action?: string;
    observation?: string;
    confidence?: number;
}

const agentIcons: Record<string, React.ElementType> = {
    research: Search,
    analyst: Database,
    reasoning: Brain,
    action: Zap,
    scheduler: Clock,
};

const agentGradients: Record<string, string> = {
    research: 'from-sky-500 to-cyan-500',
    analyst: 'from-violet-500 to-purple-500',
    reasoning: 'from-amber-500 to-orange-500',
    action: 'from-emerald-500 to-teal-500',
    scheduler: 'from-pink-500 to-rose-500',
};

const statusConfig = {
    idle: { variant: 'default' as const, icon: CheckCircle2, label: 'Idle' },
    thinking: { variant: 'info' as const, icon: Loader2, label: 'Thinking' },
    executing: { variant: 'warning' as const, icon: Activity, label: 'Executing' },
    done: { variant: 'success' as const, icon: CheckCircle2, label: 'Done' },
    error: { variant: 'error' as const, icon: AlertCircle, label: 'Error' },
};

const Agents = () => {
    const [agents, setAgents] = useState<Agent[]>([]);
    const [loading, setLoading] = useState(true);
    const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);
    const [agentLogs, setAgentLogs] = useState<AgentThought[]>([]);
    const [showLogsModal, setShowLogsModal] = useState(false);
    const [loadingLogs, setLoadingLogs] = useState(false);

    const fetchAgents = async () => {
        try {
            const response = await api.get('/agents/');
            setAgents(response.data || []);
        } catch (error) {
            console.error('Failed to fetch agents:', error);
            // Mock data for demo
            setAgents([
                {
                    id: 'research_agent',
                    name: 'Research Agent',
                    type: 'research',
                    description: 'Searches documents and retrieves relevant information using RAG',
                    status: 'idle',
                    capabilities: ['Document search', 'Semantic similarity', 'Context extraction', 'Source citation'],
                    tasks_completed: 127,
                },
                {
                    id: 'analyst_agent',
                    name: 'Analyst Agent',
                    type: 'analyst',
                    description: 'Queries databases, performs calculations, and analyzes data',
                    status: 'idle',
                    capabilities: ['SQL query generation', 'Data aggregation', 'Trend analysis', 'Anomaly detection'],
                    tasks_completed: 89,
                },
                {
                    id: 'reasoning_agent',
                    name: 'Reasoning Agent',
                    type: 'reasoning',
                    description: 'Synthesizes information from other agents and draws conclusions',
                    status: 'idle',
                    capabilities: ['Information synthesis', 'Logical reasoning', 'Confidence scoring', 'Insight generation'],
                    tasks_completed: 156,
                },
                {
                    id: 'action_agent',
                    name: 'Action Agent',
                    type: 'action',
                    description: 'Executes actions like sending emails, generating reports',
                    status: 'idle',
                    capabilities: ['Email sending', 'Report generation', 'Notification dispatch', 'API calls'],
                    tasks_completed: 45,
                },
                {
                    id: 'scheduler_agent',
                    name: 'Scheduler Agent',
                    type: 'scheduler',
                    description: 'Manages scheduled tasks and automated workflows',
                    status: 'idle',
                    capabilities: ['Task scheduling', 'Recurring reports', 'Automated monitoring', 'Triggered actions'],
                    tasks_completed: 234,
                },
            ]);
        } finally {
            setLoading(false);
        }
    };

    const fetchAgentLogs = async (agent: Agent) => {
        setSelectedAgent(agent);
        setLoadingLogs(true);
        setShowLogsModal(true);

        try {
            const response = await api.get(`/agents/thoughts/recent`);
            setAgentLogs(response.data || []);
        } catch (error) {
            console.error('Failed to fetch agent logs:', error);
            // Mock data
            setAgentLogs([
                {
                    timestamp: new Date().toISOString(),
                    agent: 'Research Agent',
                    thought: 'The user wants to know about sales performance. Let me search relevant documents.',
                    action: "search_documents('sales performance')",
                    observation: 'Found 3 documents: sales_report.pdf, quarterly_review.docx, metrics.csv',
                    confidence: 0.92,
                },
                {
                    timestamp: new Date().toISOString(),
                    agent: 'Analyst Agent',
                    thought: 'I have context from documents. Now I should query the actual sales data.',
                    action: "sql_query('SELECT SUM(amount), date FROM sales GROUP BY date')",
                    observation: 'Retrieved 30 days of sales data showing 15% decline in week 3',
                    confidence: 0.88,
                },
                {
                    timestamp: new Date().toISOString(),
                    agent: 'Reasoning Agent',
                    thought: 'Combining document insights with data analysis. The decline correlates with external factors.',
                    action: 'synthesize_insights()',
                    observation: 'Identified 3 contributing factors with high confidence',
                    confidence: 0.85,
                },
            ]);
        } finally {
            setLoadingLogs(false);
        }
    };

    const restartAgent = async (agent: Agent) => {
        try {
            await api.post(`/agents/${agent.id}/restart`);
            fetchAgents();
        } catch (error) {
            console.error('Failed to restart agent:', error);
        }
    };

    useEffect(() => {
        fetchAgents();
    }, []);

    if (loading) {
        return (
            <div className="flex items-center justify-center h-full">
                <div className="flex flex-col items-center gap-4">
                    <div className="w-12 h-12 border-4 border-primary/30 border-t-primary rounded-full animate-spin" />
                    <p className="text-muted-foreground">Loading agents...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-foreground">AI Agents</h1>
                    <p className="text-muted-foreground mt-1">Monitor and control your AI workforce</p>
                </div>
                <Button onClick={fetchAgents} icon={<RefreshCw className="w-4 h-4" />} variant="outline">
                    Refresh Status
                </Button>
            </div>

            {/* Status Summary */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <Card>
                    <CardContent className="py-4">
                        <div className="flex items-center gap-3">
                            <div className="p-2 rounded-lg bg-emerald-500/20">
                                <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                            </div>
                            <div>
                                <p className="text-2xl font-bold text-foreground">{agents.filter(a => a.status === 'idle' || a.status === 'done').length}</p>
                                <p className="text-xs text-muted-foreground">Ready</p>
                            </div>
                        </div>
                    </CardContent>
                </Card>
                <Card>
                    <CardContent className="py-4">
                        <div className="flex items-center gap-3">
                            <div className="p-2 rounded-lg bg-sky-500/20">
                                <Activity className="w-5 h-5 text-sky-400" />
                            </div>
                            <div>
                                <p className="text-2xl font-bold text-foreground">{agents.filter(a => a.status === 'thinking' || a.status === 'executing').length}</p>
                                <p className="text-xs text-muted-foreground">Active</p>
                            </div>
                        </div>
                    </CardContent>
                </Card>
                <Card>
                    <CardContent className="py-4">
                        <div className="flex items-center gap-3">
                            <div className="p-2 rounded-lg bg-violet-500/20">
                                <Bot className="w-5 h-5 text-violet-400" />
                            </div>
                            <div>
                                <p className="text-2xl font-bold text-foreground">{agents.length}</p>
                                <p className="text-xs text-muted-foreground">Total Agents</p>
                            </div>
                        </div>
                    </CardContent>
                </Card>
                <Card>
                    <CardContent className="py-4">
                        <div className="flex items-center gap-3">
                            <div className="p-2 rounded-lg bg-amber-500/20">
                                <Zap className="w-5 h-5 text-amber-400" />
                            </div>
                            <div>
                                <p className="text-2xl font-bold text-foreground">
                                    {agents.reduce((sum, a) => sum + a.tasks_completed, 0)}
                                </p>
                                <p className="text-xs text-muted-foreground">Tasks Completed</p>
                            </div>
                        </div>
                    </CardContent>
                </Card>
            </div>

            {/* Agents Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {agents.map((agent) => {
                    const Icon = agentIcons[agent.type] || Bot;
                    const gradient = agentGradients[agent.type] || 'from-gray-500 to-gray-600';
                    const status = statusConfig[agent.status];
                    const StatusIcon = status.icon;

                    return (
                        <Card key={agent.id} hover className="group">
                            <CardContent>
                                {/* Header */}
                                <div className="flex items-start justify-between mb-4">
                                    <div className={clsx('p-3 rounded-xl bg-gradient-to-br', gradient)}>
                                        <Icon className="w-6 h-6 text-white" />
                                    </div>
                                    <Badge variant={status.variant} pulse={agent.status === 'thinking' || agent.status === 'executing'}>
                                        <StatusIcon className={clsx('w-3 h-3 mr-1', (agent.status === 'thinking' || agent.status === 'executing') && 'animate-spin')} />
                                        {status.label}
                                    </Badge>
                                </div>

                                {/* Info */}
                                <h3 className="text-lg font-semibold text-foreground mb-1">{agent.name}</h3>
                                <p className="text-sm text-muted-foreground mb-4 line-clamp-2">{agent.description}</p>

                                {/* Capabilities */}
                                <div className="flex flex-wrap gap-1.5 mb-4">
                                    {agent.capabilities.slice(0, 3).map((cap, idx) => (
                                        <span
                                            key={idx}
                                            className="px-2 py-0.5 text-xs rounded-full bg-muted text-muted-foreground"
                                        >
                                            {cap}
                                        </span>
                                    ))}
                                    {agent.capabilities.length > 3 && (
                                        <span className="px-2 py-0.5 text-xs rounded-full bg-muted text-muted-foreground">
                                            +{agent.capabilities.length - 3}
                                        </span>
                                    )}
                                </div>

                                {/* Stats */}
                                <div className="flex items-center justify-between pt-4 border-t border-border">
                                    <div className="text-sm">
                                        <span className="text-foreground font-medium">{agent.tasks_completed}</span>
                                        <span className="text-muted-foreground ml-1">tasks</span>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <button
                                            onClick={() => restartAgent(agent)}
                                            className="p-2 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
                                            title="Restart agent"
                                        >
                                            <RefreshCw className="w-4 h-4" />
                                        </button>
                                        <button
                                            onClick={() => fetchAgentLogs(agent)}
                                            className="p-2 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
                                            title="View logs"
                                        >
                                            <ChevronRight className="w-4 h-4" />
                                        </button>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                    );
                })}
            </div>

            {/* Agent Logs Modal */}
            <Modal
                isOpen={showLogsModal}
                onClose={() => setShowLogsModal(false)}
                title={`${selectedAgent?.name || 'Agent'} - Recent Activity`}
                size="lg"
            >
                {loadingLogs ? (
                    <div className="flex items-center justify-center py-8">
                        <Loader2 className="w-8 h-8 animate-spin text-primary" />
                    </div>
                ) : (
                    <div className="space-y-4 max-h-[60vh] overflow-y-auto">
                        {agentLogs.map((log, idx) => (
                            <div
                                key={idx}
                                className="p-4 rounded-lg bg-muted border border-border"
                            >
                                <div className="flex items-center justify-between mb-2">
                                    <Badge variant="purple">{log.agent}</Badge>
                                    {log.confidence && (
                                        <span className="text-xs text-muted-foreground">
                                            {Math.round(log.confidence * 100)}% confidence
                                        </span>
                                    )}
                                </div>
                                <div className="space-y-2">
                                    <div>
                                        <span className="text-xs font-medium text-muted-foreground">Thought:</span>
                                        <p className="text-sm text-foreground">{log.thought}</p>
                                    </div>
                                    {log.action && (
                                        <div>
                                            <span className="text-xs font-medium text-muted-foreground">Action:</span>
                                            <p className="text-sm text-violet-400 font-mono">{log.action}</p>
                                        </div>
                                    )}
                                    {log.observation && (
                                        <div>
                                            <span className="text-xs font-medium text-muted-foreground">Observation:</span>
                                            <p className="text-sm text-emerald-400">{log.observation}</p>
                                        </div>
                                    )}
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </Modal>
        </div>
    );
};

export default Agents;
