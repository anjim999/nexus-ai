import { useState, useEffect } from 'react';
import { Card, CardContent, Button } from '../components/ui';
import { Bell, Check, Trash2, AlertTriangle, Info, CheckCircle } from 'lucide-react';
import api from '../services/api';
import { clsx } from 'clsx';
import { formatDistanceToNow } from 'date-fns';

interface Notification {
    id: string;
    title: string;
    message: string;
    severity: 'info' | 'warning' | 'critical' | 'success';
    timestamp: string;
    is_read: boolean;
    action_url?: string;
}

const Notifications = () => {
    const [notifications, setNotifications] = useState<Notification[]>([]);
    const [loading, setLoading] = useState(true);
    const [filter, setFilter] = useState<'all' | 'unread'>('all');

    const fetchNotifications = async () => {
        try {
            const response = await api.get('/insights/alerts');
            setNotifications(response.data || []);
        } catch (error) {
            console.error('Failed to fetch notifications:', error);
            // Mock fallback
            setNotifications([
                {
                    id: '1',
                    title: 'System Update',
                    message: 'Nexus AI has been updated to version 1.2.0',
                    severity: 'info',
                    timestamp: new Date().toISOString(),
                    is_read: false
                }
            ]);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchNotifications();
        // Poll for notifications every 30 seconds
        const interval = setInterval(fetchNotifications, 30000);
        return () => clearInterval(interval);
    }, []);

    const markAsRead = async (id: string) => {
        try {
            await api.post(`/insights/alerts/${id}/read`);
            setNotifications(prev =>
                prev.map(n => n.id === id ? { ...n, is_read: true } : n)
            );
        } catch (error) {
            console.error('Failed to mark as read:', error);
        }
    };

    const markAllAsRead = async () => {
        try {
            const unreadIds = notifications.filter(n => !n.is_read).map(n => n.id);
            await Promise.all(unreadIds.map(id => api.post(`/insights/alerts/${id}/read`)));
            setNotifications(prev => prev.map(n => ({ ...n, is_read: true })));
        } catch (error) {
            console.error('Failed to mark all as read:', error);
        }
    };

    const deleteNotification = async (id: string) => {
        // In real app, call delete API if exists. Assuming just local hide for now or toggle logic
        setNotifications(prev => prev.filter(n => n.id !== id));
    };

    const getIcon = (severity: string) => {
        switch (severity) {
            case 'critical': return <AlertTriangle className="w-5 h-5 text-red-500" />;
            case 'warning': return <AlertTriangle className="w-5 h-5 text-amber-500" />;
            case 'success': return <CheckCircle className="w-5 h-5 text-green-500" />;
            default: return <Info className="w-5 h-5 text-blue-500" />;
        }
    };

    const filteredNotifications = filter === 'all'
        ? notifications
        : notifications.filter(n => !n.is_read);

    if (loading) {
        return (
            <div className="flex items-center justify-center h-full">
                <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
            </div>
        );
    }

    return (
        <div className="space-y-6 max-w-4xl mx-auto">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-foreground">Notifications</h1>
                    <p className="text-muted-foreground mt-1">Stay updated with system alerts and insights</p>
                </div>
                <div className="flex gap-2">
                    <Button variant="outline" onClick={markAllAsRead} disabled={!notifications.some(n => !n.is_read)}>
                        <Check className="w-4 h-4 mr-2" />
                        Mark all as read
                    </Button>
                </div>
            </div>

            <div className="flex gap-2 p-1 bg-muted rounded-lg w-fit">
                <button
                    onClick={() => setFilter('all')}
                    className={clsx(
                        'px-4 py-1.5 rounded-md text-sm font-medium transition-all',
                        filter === 'all' ? 'bg-background text-foreground shadow-sm' : 'text-muted-foreground hover:text-foreground'
                    )}
                >
                    All
                </button>
                <button
                    onClick={() => setFilter('unread')}
                    className={clsx(
                        'px-4 py-1.5 rounded-md text-sm font-medium transition-all',
                        filter === 'unread' ? 'bg-background text-foreground shadow-sm' : 'text-muted-foreground hover:text-foreground'
                    )}
                >
                    Unread
                </button>
            </div>

            <div className="space-y-3">
                {filteredNotifications.length === 0 ? (
                    <Card>
                        <CardContent className="py-12 text-center text-muted-foreground">
                            <Bell className="w-12 h-12 mx-auto mb-4 opacity-50" />
                            <p>No notifications to show</p>
                        </CardContent>
                    </Card>
                ) : (
                    filteredNotifications.map((notification) => (
                        <Card key={notification.id} className={clsx('transition-all', !notification.is_read && 'bg-primary/5 border-primary/20')}>
                            <CardContent className="p-4 flex gap-4 items-start">
                                <div className={clsx('p-2 rounded-full bg-muted', !notification.is_read && 'bg-background')}>
                                    {getIcon(notification.severity)}
                                </div>
                                <div className="flex-1 min-w-0">
                                    <div className="flex justify-between items-start">
                                        <h4 className={clsx('font-medium mb-1', !notification.is_read && 'text-primary')}>
                                            {notification.title}
                                        </h4>
                                        <span className="text-xs text-muted-foreground whitespace-nowrap ml-4">
                                            {formatDistanceToNow(new Date(notification.timestamp), { addSuffix: true })}
                                        </span>
                                    </div>
                                    <p className="text-sm text-muted-foreground leading-relaxed">
                                        {notification.message}
                                    </p>
                                    {notification.action_url && (
                                        <a href={notification.action_url} className="text-xs text-primary hover:underline mt-2 inline-block">
                                            View details →
                                        </a>
                                    )}
                                </div>
                                <div className="flex flex-col gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                    {!notification.is_read && (
                                        <button
                                            onClick={() => markAsRead(notification.id)}
                                            className="p-1.5 rounded-md hover:bg-muted text-muted-foreground hover:text-primary"
                                            title="Mark as read"
                                        >
                                            <div className="w-2 h-2 rounded-full bg-primary" />
                                        </button>
                                    )}
                                    <button
                                        onClick={() => deleteNotification(notification.id)}
                                        className="p-1.5 rounded-md hover:bg-muted text-muted-foreground hover:text-red-500"
                                        title="Dismiss"
                                    >
                                        <Trash2 className="w-4 h-4" />
                                    </button>
                                </div>
                            </CardContent>
                        </Card>
                    ))
                )}
            </div>
        </div>
    );
};

export default Notifications;
