import { useState, useEffect } from 'react';
import {
    TrendingUp,
    TrendingDown,
    Users,
    DollarSign,
    Ticket,
    ClipboardList,
    AlertTriangle,
    Sparkles,
    ChevronRight,
    RefreshCw,
    Minus,
} from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent, Button, Badge, LineChartComponent } from '../components/ui';
import { clsx } from 'clsx';
import api from '../services/api';

interface MetricCard {
    id: string;
    title: string;
    value: string;
    change: number;
    trend: 'up' | 'down' | 'stable';
    period: string;
    icon: string;
}

interface AlertItem {
    id: string;
    title: string;
    message: string;
    severity: 'info' | 'warning' | 'critical';
    timestamp: string;
    is_read: boolean;
}

interface AIInsight {
    id: string;
    title: string;
    summary: string;
    confidence: number;
    category: string;
    priority: number;
}

interface ChartData {
    chart_type: string;
    title: string;
    data: Record<string, unknown>[];
    x_axis: string;
    y_axis: string;
}

const iconMap: Record<string, React.ElementType> = {
    'trending-up': TrendingUp,
    users: Users,
    ticket: Ticket,
    clipboard: ClipboardList,
};

const Dashboard = () => {
    const [metrics, setMetrics] = useState<MetricCard[]>([]);
    const [alerts, setAlerts] = useState<AlertItem[]>([]);
    const [insights, setInsights] = useState<AIInsight[]>([]);
    const [chartData, setChartData] = useState<ChartData[]>([]);
    const [loading, setLoading] = useState(true);
    const [refreshing, setRefreshing] = useState(false);

    const fetchDashboardData = async () => {
        try {
            const response = await api.get('/insights/dashboard');
            const data = response.data;
            setMetrics(data.metrics || []);
            setAlerts(data.alerts || []);
            setInsights(data.insights || []);
            setChartData(data.charts || []);
        } catch (error) {
            console.error('Failed to fetch dashboard data:', error);
            // Set mock data for demo
            setMetrics([
                { id: 'revenue', title: 'Revenue', value: '₹12.4L', change: 12.5, trend: 'up', period: 'vs last week', icon: 'trending-up' },
                { id: 'customers', title: 'Active Customers', value: '1,247', change: 8.3, trend: 'up', period: 'vs last week', icon: 'users' },
                { id: 'tickets', title: 'Open Tickets', value: '47', change: -15.2, trend: 'down', period: 'vs last week', icon: 'ticket' },
                { id: 'tasks', title: 'Pending Tasks', value: '23', change: 0, trend: 'stable', period: 'vs last week', icon: 'clipboard' },
            ]);
            setAlerts([
                { id: 'alert_1', title: 'Revenue Anomaly Detected', message: 'Revenue dropped 25% on Tuesday compared to average', severity: 'warning', timestamp: new Date().toISOString(), is_read: false },
                { id: 'alert_2', title: 'Customer Churn Risk', message: '3 high-value customers showing disengagement patterns', severity: 'critical', timestamp: new Date().toISOString(), is_read: false },
            ]);
            setInsights([
                { id: 'insight_1', title: 'Marketing Campaign Impact', summary: 'Recent email campaign drove 35% increase in website traffic', confidence: 0.89, category: 'marketing', priority: 2 },
                { id: 'insight_2', title: 'Product Performance', summary: 'Product A outperforming others by 40% this quarter', confidence: 0.92, category: 'products', priority: 1 },
            ]);
            setChartData([
                {
                    chart_type: 'line', title: 'Revenue Trend', data: [
                        { date: 'Mon', value: 12000 },
                        { date: 'Tue', value: 9000 },
                        { date: 'Wed', value: 15000 },
                        { date: 'Thu', value: 14000 },
                        { date: 'Fri', value: 18000 },
                        { date: 'Sat', value: 16000 },
                        { date: 'Sun', value: 11000 },
                    ], x_axis: 'date', y_axis: 'value'
                },
            ]);
        } finally {
            setLoading(false);
            setRefreshing(false);
        }
    };

    useEffect(() => {
        fetchDashboardData();
    }, []);

    const handleRefresh = () => {
        setRefreshing(true);
        fetchDashboardData();
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center h-full">
                <div className="flex flex-col items-center gap-4">
                    <div className="w-12 h-12 border-4 border-primary/30 border-t-primary rounded-full animate-spin" />
                    <p className="text-muted-foreground">Loading dashboard...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-foreground">Dashboard</h1>
                    <p className="text-muted-foreground mt-1">Your business intelligence at a glance</p>
                </div>
                <Button onClick={handleRefresh} loading={refreshing} icon={<RefreshCw className="w-4 h-4" />}>
                    Refresh
                </Button>
            </div>

            {/* Metrics Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {metrics.map((metric) => {
                    const Icon = iconMap[metric.icon] || DollarSign;
                    return (
                        <Card key={metric.id} hover className="cursor-pointer">
                            <CardContent>
                                <div className="flex items-start justify-between">
                                    <div className="p-2.5 rounded-xl bg-gradient-to-br from-violet-500/20 to-purple-500/20">
                                        <Icon className="w-5 h-5 text-violet-400" />
                                    </div>
                                    <span
                                        className={clsx(
                                            'inline-flex items-center gap-1 text-sm font-medium',
                                            metric.trend === 'up' && 'text-emerald-400',
                                            metric.trend === 'down' && 'text-red-400',
                                            metric.trend === 'stable' && 'text-amber-400'
                                        )}
                                    >
                                        {metric.trend === 'up' && <TrendingUp className="w-4 h-4" />}
                                        {metric.trend === 'down' && <TrendingDown className="w-4 h-4" />}
                                        {metric.trend === 'stable' && <Minus className="w-4 h-4" />}
                                        {Math.abs(metric.change)}%
                                    </span>
                                </div>
                                <div className="mt-4">
                                    <p className="text-2xl font-bold text-foreground">{metric.value}</p>
                                    <p className="text-sm text-muted-foreground mt-1">{metric.title}</p>
                                    <p className="text-xs text-muted-foreground/60 mt-0.5">{metric.period}</p>
                                </div>
                            </CardContent>
                        </Card>
                    );
                })}
            </div>

            {/* Main Content Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Chart Section */}
                <Card className="lg:col-span-2">
                    <CardHeader>
                        <CardTitle>Revenue Trend</CardTitle>
                        <Badge variant="success">Live</Badge>
                    </CardHeader>
                    <CardContent>
                        {chartData.length > 0 ? (
                            <LineChartComponent
                                data={chartData[0].data}
                                xKey={chartData[0].x_axis}
                                yKey={chartData[0].y_axis}
                                height={280}
                            />
                        ) : (
                            <div className="h-[280px] flex items-center justify-center text-muted-foreground">
                                No chart data available
                            </div>
                        )}
                    </CardContent>
                </Card>

                {/* Alerts Section */}
                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <AlertTriangle className="w-5 h-5 text-amber-400" />
                            Alerts
                        </CardTitle>
                        <Badge variant="error">{alerts.filter(a => !a.is_read).length} new</Badge>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-3">
                            {alerts.length === 0 ? (
                                <p className="text-muted-foreground text-center py-4">No alerts</p>
                            ) : (
                                alerts.map((alert) => (
                                    <div
                                        key={alert.id}
                                        className={clsx(
                                            'p-3 rounded-lg border cursor-pointer transition-colors hover:bg-muted/50',
                                            alert.severity === 'critical' && 'bg-red-500/10 border-red-500/30',
                                            alert.severity === 'warning' && 'bg-amber-500/10 border-amber-500/30',
                                            alert.severity === 'info' && 'bg-sky-500/10 border-sky-500/30'
                                        )}
                                    >
                                        <div className="flex items-center gap-2 mb-1">
                                            <Badge
                                                variant={
                                                    alert.severity === 'critical'
                                                        ? 'error'
                                                        : alert.severity === 'warning'
                                                            ? 'warning'
                                                            : 'info'
                                                }
                                                size="sm"
                                            >
                                                {alert.severity}
                                            </Badge>
                                        </div>
                                        <h4 className="text-sm font-medium text-foreground">{alert.title}</h4>
                                        <p className="text-xs text-muted-foreground mt-1 line-clamp-2">
                                            {alert.message}
                                        </p>
                                    </div>
                                ))
                            )}
                        </div>
                    </CardContent>
                </Card>
            </div>

            {/* AI Insights Section */}
            <Card glow>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <Sparkles className="w-5 h-5 text-violet-400" />
                        AI Insights
                    </CardTitle>
                    <Button variant="ghost" size="sm">
                        View All <ChevronRight className="w-4 h-4" />
                    </Button>
                </CardHeader>
                <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {insights.map((insight) => (
                            <div
                                key={insight.id}
                                className="p-4 rounded-xl bg-gradient-to-br from-violet-500/10 to-purple-500/10 border border-violet-500/20 hover:border-violet-500/40 transition-colors cursor-pointer"
                            >
                                <div className="flex items-center justify-between mb-2">
                                    <Badge variant="purple">{insight.category}</Badge>
                                    <span className="text-xs text-muted-foreground">
                                        {Math.round(insight.confidence * 100)}% confidence
                                    </span>
                                </div>
                                <h4 className="font-medium text-foreground mb-1">{insight.title}</h4>
                                <p className="text-sm text-muted-foreground">{insight.summary}</p>
                            </div>
                        ))}
                    </div>
                </CardContent>
            </Card>
        </div>
    );
};

export default Dashboard;
