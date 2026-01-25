import { useState, useEffect } from 'react';
import {
    FileText,
    Download,
    Plus,
    Calendar,
    Clock,
    Trash2,
    Mail,
    FileBarChart,
    Play,
    Pause,
} from 'lucide-react';
import { Card, CardContent, Button, Badge, Input, Modal } from '../components/ui';
import { clsx } from 'clsx';
import api from '../services/api';

interface Report {
    id: string;
    title: string;
    report_type: string;
    format: string;
    generated_at: string;
    file_size_bytes?: number;
    download_url: string;
    expires_at: string;
}

interface ScheduledReport {
    id: string;
    title: string;
    report_type: string;
    frequency: string;
    next_run: string;
    recipients: string[];
    is_active: boolean;
}

const reportTypes = [
    { value: 'daily_summary', label: 'Daily Summary' },
    { value: 'weekly_analysis', label: 'Weekly Analysis' },
    { value: 'monthly_report', label: 'Monthly Report' },
    { value: 'custom', label: 'Custom Report' },
];

const formatFileSize = (bytes?: number) => {
    if (!bytes) return '-';
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
};

const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-IN', {
        day: 'numeric',
        month: 'short',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
    });
};

const Reports = () => {
    const [reports, setReports] = useState<Report[]>([]);
    const [scheduledReports, setScheduledReports] = useState<ScheduledReport[]>([]);
    const [loading, setLoading] = useState(true);
    const [generating, setGenerating] = useState(false);
    const [showGenerateModal, setShowGenerateModal] = useState(false);
    const [showScheduleModal, setShowScheduleModal] = useState(false);
    const [activeTab, setActiveTab] = useState<'generated' | 'scheduled'>('generated');

    // Form states
    const [reportTitle, setReportTitle] = useState('');
    const [reportType, setReportType] = useState('weekly_analysis');
    const [reportFormat, setReportFormat] = useState('pdf');
    const [timeRangeDays, setTimeRangeDays] = useState(7);
    const [includeAI, setIncludeAI] = useState(true);
    const [scheduleFrequency, setScheduleFrequency] = useState('weekly');
    const [scheduleRecipients, setScheduleRecipients] = useState('');

    const fetchReports = async () => {
        try {
            const [reportsRes, scheduledRes] = await Promise.all([
                api.get('/reports/'),
                api.get('/reports/schedule'),
            ]);
            setReports(reportsRes.data || []);
            setScheduledReports(scheduledRes.data || []);
        } catch (error) {
            console.error('Failed to fetch reports:', error);
            // Mock data
            setReports([
                {
                    id: 'report_1',
                    title: 'Weekly Performance Report',
                    report_type: 'weekly_analysis',
                    format: 'pdf',
                    generated_at: new Date().toISOString(),
                    file_size_bytes: 245000,
                    download_url: '/api/v1/reports/report_1/download',
                    expires_at: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
                },
                {
                    id: 'report_2',
                    title: 'Daily Summary - Jan 25',
                    report_type: 'daily_summary',
                    format: 'pdf',
                    generated_at: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
                    file_size_bytes: 125000,
                    download_url: '/api/v1/reports/report_2/download',
                    expires_at: new Date(Date.now() + 6 * 24 * 60 * 60 * 1000).toISOString(),
                },
            ]);
            setScheduledReports([
                {
                    id: 'sched_1',
                    title: 'Daily Morning Briefing',
                    report_type: 'daily_summary',
                    frequency: 'daily',
                    next_run: new Date(Date.now() + 12 * 60 * 60 * 1000).toISOString(),
                    recipients: ['team@company.com'],
                    is_active: true,
                },
            ]);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchReports();
    }, []);

    const handleGenerateReport = async () => {
        if (!reportTitle.trim()) return;
        setGenerating(true);

        try {
            await api.post('/reports/generate', {
                title: reportTitle,
                report_type: reportType,
                format: reportFormat,
                time_range_days: timeRangeDays,
                include_ai_analysis: includeAI,
            });

            await fetchReports();
            setShowGenerateModal(false);
            resetForm();
        } catch (error) {
            console.error('Failed to generate report:', error);
        } finally {
            setGenerating(false);
        }
    };

    const handleScheduleReport = async () => {
        if (!reportTitle.trim() || !scheduleRecipients.trim()) return;

        try {
            await api.post('/reports/schedule', {
                title: reportTitle,
                report_type: reportType,
                frequency: scheduleFrequency,
                recipients: scheduleRecipients.split(',').map((r) => r.trim()),
            });

            await fetchReports();
            setShowScheduleModal(false);
            resetForm();
        } catch (error) {
            console.error('Failed to schedule report:', error);
        }
    };

    const handleDownload = async (report: Report) => {
        try {
            window.open(`${api.defaults.baseURL}${report.download_url}`, '_blank');
        } catch (error) {
            console.error('Download failed:', error);
        }
    };

    const handleToggleSchedule = async (schedule: ScheduledReport) => {
        try {
            await api.put(`/reports/schedule/${schedule.id}/toggle`);
            fetchReports();
        } catch (error) {
            console.error('Failed to toggle schedule:', error);
        }
    };

    const handleDeleteReport = async (reportId: string) => {
        try {
            await api.delete(`/reports/${reportId}`);
            setReports((prev) => prev.filter((r) => r.id !== reportId));
        } catch (error) {
            console.error('Failed to delete report:', error);
        }
    };

    const resetForm = () => {
        setReportTitle('');
        setReportType('weekly_analysis');
        setReportFormat('pdf');
        setTimeRangeDays(7);
        setIncludeAI(true);
        setScheduleFrequency('weekly');
        setScheduleRecipients('');
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center h-full">
                <div className="flex flex-col items-center gap-4">
                    <div className="w-12 h-12 border-4 border-primary/30 border-t-primary rounded-full animate-spin" />
                    <p className="text-muted-foreground">Loading reports...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-foreground">Reports</h1>
                    <p className="text-muted-foreground mt-1">Generate and schedule AI-powered reports</p>
                </div>
                <div className="flex items-center gap-3">
                    <Button variant="outline" onClick={() => setShowScheduleModal(true)} icon={<Calendar className="w-4 h-4" />}>
                        Schedule
                    </Button>
                    <Button onClick={() => setShowGenerateModal(true)} icon={<Plus className="w-4 h-4" />}>
                        Generate Report
                    </Button>
                </div>
            </div>

            {/* Tabs */}
            <div className="flex items-center gap-1 p-1 bg-muted rounded-lg w-fit">
                <button
                    onClick={() => setActiveTab('generated')}
                    className={clsx(
                        'px-4 py-2 rounded-md text-sm font-medium transition-colors',
                        activeTab === 'generated'
                            ? 'bg-background text-foreground shadow-sm'
                            : 'text-muted-foreground hover:text-foreground'
                    )}
                >
                    Generated ({reports.length})
                </button>
                <button
                    onClick={() => setActiveTab('scheduled')}
                    className={clsx(
                        'px-4 py-2 rounded-md text-sm font-medium transition-colors',
                        activeTab === 'scheduled'
                            ? 'bg-background text-foreground shadow-sm'
                            : 'text-muted-foreground hover:text-foreground'
                    )}
                >
                    Scheduled ({scheduledReports.length})
                </button>
            </div>

            {/* Generated Reports */}
            {activeTab === 'generated' && (
                <div className="space-y-4">
                    {reports.length === 0 ? (
                        <Card>
                            <CardContent className="py-12 text-center">
                                <FileBarChart className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
                                <h3 className="text-lg font-medium text-foreground mb-2">No reports yet</h3>
                                <p className="text-muted-foreground mb-4">Generate your first AI-powered report</p>
                                <Button onClick={() => setShowGenerateModal(true)}>Generate Report</Button>
                            </CardContent>
                        </Card>
                    ) : (
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                            {reports.map((report) => (
                                <Card key={report.id} hover className="group">
                                    <CardContent>
                                        <div className="flex items-start justify-between mb-4">
                                            <div className="p-3 rounded-xl bg-gradient-to-br from-violet-500/20 to-purple-500/20">
                                                <FileText className="w-6 h-6 text-violet-400" />
                                            </div>
                                            <Badge variant="purple">{report.format.toUpperCase()}</Badge>
                                        </div>
                                        <h4 className="font-medium text-foreground mb-1 line-clamp-1">{report.title}</h4>
                                        <p className="text-sm text-muted-foreground mb-4">
                                            {formatDate(report.generated_at)}
                                        </p>
                                        <div className="flex items-center justify-between text-sm">
                                            <span className="text-muted-foreground">
                                                {formatFileSize(report.file_size_bytes)}
                                            </span>
                                            <div className="flex items-center gap-2">
                                                <button
                                                    onClick={() => handleDeleteReport(report.id)}
                                                    className="p-2 rounded-lg text-muted-foreground hover:text-red-400 hover:bg-red-500/10 opacity-0 group-hover:opacity-100 transition-all"
                                                >
                                                    <Trash2 className="w-4 h-4" />
                                                </button>
                                                <button
                                                    onClick={() => handleDownload(report)}
                                                    className="p-2 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
                                                >
                                                    <Download className="w-4 h-4" />
                                                </button>
                                            </div>
                                        </div>
                                    </CardContent>
                                </Card>
                            ))}
                        </div>
                    )}
                </div>
            )}

            {/* Scheduled Reports */}
            {activeTab === 'scheduled' && (
                <div className="space-y-4">
                    {scheduledReports.length === 0 ? (
                        <Card>
                            <CardContent className="py-12 text-center">
                                <Calendar className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
                                <h3 className="text-lg font-medium text-foreground mb-2">No scheduled reports</h3>
                                <p className="text-muted-foreground mb-4">Set up automated report generation</p>
                                <Button onClick={() => setShowScheduleModal(true)}>Schedule Report</Button>
                            </CardContent>
                        </Card>
                    ) : (
                        <Card>
                            <div className="divide-y divide-border">
                                {scheduledReports.map((schedule) => (
                                    <div
                                        key={schedule.id}
                                        className="flex items-center gap-4 p-4 hover:bg-muted/50 transition-colors"
                                    >
                                        <div className="p-2.5 rounded-xl bg-gradient-to-br from-amber-500/20 to-orange-500/20">
                                            <Clock className="w-5 h-5 text-amber-400" />
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <h4 className="font-medium text-foreground truncate">{schedule.title}</h4>
                                            <p className="text-sm text-muted-foreground">
                                                {schedule.frequency.charAt(0).toUpperCase() + schedule.frequency.slice(1)} • Next: {formatDate(schedule.next_run)}
                                            </p>
                                            <div className="flex items-center gap-1 mt-1">
                                                <Mail className="w-3.5 h-3.5 text-muted-foreground" />
                                                <span className="text-xs text-muted-foreground">
                                                    {schedule.recipients.join(', ')}
                                                </span>
                                            </div>
                                        </div>
                                        <Badge variant={schedule.is_active ? 'success' : 'default'}>
                                            {schedule.is_active ? 'Active' : 'Paused'}
                                        </Badge>
                                        <button
                                            onClick={() => handleToggleSchedule(schedule)}
                                            className="p-2 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
                                        >
                                            {schedule.is_active ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                                        </button>
                                    </div>
                                ))}
                            </div>
                        </Card>
                    )}
                </div>
            )}

            {/* Generate Report Modal */}
            <Modal
                isOpen={showGenerateModal}
                onClose={() => {
                    setShowGenerateModal(false);
                    resetForm();
                }}
                title="Generate Report"
                size="md"
            >
                <div className="space-y-4">
                    <Input
                        label="Report Title"
                        placeholder="e.g., Weekly Performance Report"
                        value={reportTitle}
                        onChange={(e) => setReportTitle(e.target.value)}
                    />

                    <div>
                        <label className="block text-sm font-medium text-foreground mb-1.5">Report Type</label>
                        <select
                            value={reportType}
                            onChange={(e) => setReportType(e.target.value)}
                            className="w-full bg-input border border-border rounded-lg px-4 py-2.5 text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
                        >
                            {reportTypes.map((type) => (
                                <option key={type.value} value={type.value}>
                                    {type.label}
                                </option>
                            ))}
                        </select>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="block text-sm font-medium text-foreground mb-1.5">Format</label>
                            <select
                                value={reportFormat}
                                onChange={(e) => setReportFormat(e.target.value)}
                                className="w-full bg-input border border-border rounded-lg px-4 py-2.5 text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
                            >
                                <option value="pdf">PDF</option>
                                <option value="html">HTML</option>
                                <option value="markdown">Markdown</option>
                            </select>
                        </div>
                        <Input
                            label="Time Range (days)"
                            type="number"
                            value={timeRangeDays}
                            onChange={(e) => setTimeRangeDays(Number(e.target.value))}
                            min={1}
                            max={365}
                        />
                    </div>

                    <div className="flex items-center gap-3">
                        <input
                            type="checkbox"
                            id="include-ai"
                            checked={includeAI}
                            onChange={(e) => setIncludeAI(e.target.checked)}
                            className="w-4 h-4 rounded border-border bg-input text-primary focus:ring-primary/50"
                        />
                        <label htmlFor="include-ai" className="text-sm text-foreground">
                            Include AI-generated analysis and recommendations
                        </label>
                    </div>

                    <div className="flex justify-end gap-3 pt-4">
                        <Button variant="outline" onClick={() => setShowGenerateModal(false)}>
                            Cancel
                        </Button>
                        <Button onClick={handleGenerateReport} loading={generating}>
                            Generate
                        </Button>
                    </div>
                </div>
            </Modal>

            {/* Schedule Report Modal */}
            <Modal
                isOpen={showScheduleModal}
                onClose={() => {
                    setShowScheduleModal(false);
                    resetForm();
                }}
                title="Schedule Report"
                size="md"
            >
                <div className="space-y-4">
                    <Input
                        label="Report Title"
                        placeholder="e.g., Daily Morning Briefing"
                        value={reportTitle}
                        onChange={(e) => setReportTitle(e.target.value)}
                    />

                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="block text-sm font-medium text-foreground mb-1.5">Report Type</label>
                            <select
                                value={reportType}
                                onChange={(e) => setReportType(e.target.value)}
                                className="w-full bg-input border border-border rounded-lg px-4 py-2.5 text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
                            >
                                {reportTypes.map((type) => (
                                    <option key={type.value} value={type.value}>
                                        {type.label}
                                    </option>
                                ))}
                            </select>
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-foreground mb-1.5">Frequency</label>
                            <select
                                value={scheduleFrequency}
                                onChange={(e) => setScheduleFrequency(e.target.value)}
                                className="w-full bg-input border border-border rounded-lg px-4 py-2.5 text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
                            >
                                <option value="daily">Daily</option>
                                <option value="weekly">Weekly</option>
                                <option value="monthly">Monthly</option>
                            </select>
                        </div>
                    </div>

                    <Input
                        label="Recipients (comma-separated emails)"
                        placeholder="e.g., team@company.com, manager@company.com"
                        value={scheduleRecipients}
                        onChange={(e) => setScheduleRecipients(e.target.value)}
                        icon={<Mail className="w-4 h-4" />}
                    />

                    <div className="flex justify-end gap-3 pt-4">
                        <Button variant="outline" onClick={() => setShowScheduleModal(false)}>
                            Cancel
                        </Button>
                        <Button onClick={handleScheduleReport}>
                            Schedule
                        </Button>
                    </div>
                </div>
            </Modal>
        </div>
    );
};

export default Reports;
