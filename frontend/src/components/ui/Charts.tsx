import {
    AreaChart,
    Area,
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    PieChart,
    Pie,
    Cell,
} from 'recharts';
import { clsx } from 'clsx';

interface ChartProps {
    data: Record<string, unknown>[];
    xKey: string;
    yKey: string;
    height?: number;
    className?: string;
    color?: string;
    gradientId?: string;
}

// Gradient colors for charts
const CHART_COLORS = {
    primary: '#8b5cf6',
    secondary: '#06b6d4',
    tertiary: '#f59e0b',
    success: '#10b981',
    danger: '#ef4444',
};

const PIE_COLORS = ['#8b5cf6', '#06b6d4', '#f59e0b', '#10b981', '#ef4444', '#6366f1'];

// Custom Tooltip
const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
        return (
            <div className="bg-card border border-border rounded-lg px-3 py-2 shadow-xl">
                <p className="text-sm text-muted-foreground">{label}</p>
                <p className="text-lg font-semibold text-foreground">
                    {typeof payload[0].value === 'number'
                        ? payload[0].value.toLocaleString()
                        : payload[0].value}
                </p>
            </div>
        );
    }
    return null;
};

export const LineChartComponent = ({
    data,
    xKey,
    yKey,
    height = 300,
    className,
    color = CHART_COLORS.primary,
    gradientId = 'lineGradient',
}: ChartProps) => {
    return (
        <div className={clsx('w-full', className)} style={{ height }}>
            <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                    <defs>
                        <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
                            <stop offset="0%" stopColor={color} stopOpacity={0.3} />
                            <stop offset="100%" stopColor={color} stopOpacity={0} />
                        </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="hsl(217.2 32.6% 17.5%)" vertical={false} />
                    <XAxis
                        dataKey={xKey}
                        axisLine={false}
                        tickLine={false}
                        tick={{ fill: 'hsl(215 20.2% 65.1%)', fontSize: 12 }}
                    />
                    <YAxis
                        axisLine={false}
                        tickLine={false}
                        tick={{ fill: 'hsl(215 20.2% 65.1%)', fontSize: 12 }}
                    />
                    <Tooltip content={<CustomTooltip />} />
                    <Area
                        type="monotone"
                        dataKey={yKey}
                        stroke={color}
                        strokeWidth={2}
                        fill={`url(#${gradientId})`}
                    />
                </AreaChart>
            </ResponsiveContainer>
        </div>
    );
};

export const BarChartComponent = ({
    data,
    xKey,
    yKey,
    height = 300,
    className,
    color = CHART_COLORS.primary,
}: ChartProps) => {
    return (
        <div className={clsx('w-full', className)} style={{ height }}>
            <ResponsiveContainer width="100%" height="100%">
                <BarChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="hsl(217.2 32.6% 17.5%)" vertical={false} />
                    <XAxis
                        dataKey={xKey}
                        axisLine={false}
                        tickLine={false}
                        tick={{ fill: 'hsl(215 20.2% 65.1%)', fontSize: 12 }}
                    />
                    <YAxis
                        axisLine={false}
                        tickLine={false}
                        tick={{ fill: 'hsl(215 20.2% 65.1%)', fontSize: 12 }}
                    />
                    <Tooltip content={<CustomTooltip />} />
                    <Bar dataKey={yKey} fill={color} radius={[4, 4, 0, 0]} />
                </BarChart>
            </ResponsiveContainer>
        </div>
    );
};

interface PieChartProps {
    data: { name: string; value: number }[];
    height?: number;
    className?: string;
}

export const PieChartComponent = ({ data, height = 300, className }: PieChartProps) => {
    return (
        <div className={clsx('w-full', className)} style={{ height }}>
            <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                    <Pie
                        data={data}
                        cx="50%"
                        cy="50%"
                        innerRadius={60}
                        outerRadius={90}
                        paddingAngle={4}
                        dataKey="value"
                    >
                        {data.map((_, index) => (
                            <Cell key={`cell-${index}`} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                        ))}
                    </Pie>
                    <Tooltip content={<CustomTooltip />} />
                </PieChart>
            </ResponsiveContainer>
        </div>
    );
};
