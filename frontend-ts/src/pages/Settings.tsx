import { useState } from 'react';
import { Card, CardContent, Button, Input } from '../components/ui';
import { User, Lock, Bell, Globe, Palette, LogOut, Save } from 'lucide-react';
import { useTheme } from '../components/theme-provider';

const Settings = () => {
    const { setTheme, theme } = useTheme();
    const [activeTab, setActiveTab] = useState('profile');
    const [loading, setLoading] = useState(false);

    // Mock User Data
    const [user, setUser] = useState({
        name: 'Anji',
        email: 'anji@nexus.ai',
        role: 'Administrator',
        avatar: 'A'
    });

    const handleSave = async () => {
        setLoading(true);
        // Simulate API call
        await new Promise(resolve => setTimeout(resolve, 1000));
        setLoading(false);
    };

    const tabs = [
        { id: 'profile', label: 'Profile', icon: User },
        { id: 'notifications', label: 'Notifications', icon: Bell },
        { id: 'appearance', label: 'Appearance', icon: Palette },
        { id: 'security', label: 'Security', icon: Lock },
    ];

    return (
        <div className="space-y-6 max-w-5xl mx-auto">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-foreground">Settings</h1>
                    <p className="text-muted-foreground mt-1">Manage your account preferences and system settings</p>
                </div>
            </div>

            <div className="flex flex-col md:flex-row gap-6">
                {/* Sidebar Navigation */}
                <Card className="md:w-64 h-fit">
                    <CardContent className="p-2 space-y-1">
                        {tabs.map((tab) => (
                            <button
                                key={tab.id}
                                onClick={() => setActiveTab(tab.id)}
                                className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${activeTab === tab.id
                                    ? 'bg-primary/10 text-primary'
                                    : 'text-muted-foreground hover:bg-muted hover:text-foreground'
                                    }`}
                            >
                                <tab.icon className="w-4 h-4" />
                                {tab.label}
                            </button>
                        ))}
                        <div className="h-px bg-border my-2" />
                        <button className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium text-red-500 hover:bg-red-500/10 transition-colors">
                            <LogOut className="w-4 h-4" />
                            Sign Out
                        </button>
                    </CardContent>
                </Card>

                {/* Main Content Area */}
                <div className="flex-1">
                    <Card>
                        <CardContent className="p-6">
                            {activeTab === 'profile' && (
                                <div className="space-y-6">
                                    <div className="flex items-center gap-4">
                                        <div className="w-20 h-20 rounded-full bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center text-white text-3xl font-bold">
                                            {user.avatar}
                                        </div>
                                        <div>
                                            <Button variant="outline" size="sm">Change Avatar</Button>
                                        </div>
                                    </div>
                                    <div className="grid gap-4 md:grid-cols-2">
                                        <Input label="Full Name" value={user.name} onChange={(e) => setUser({ ...user, name: e.target.value })} />
                                        <Input label="Email Address" value={user.email} onChange={(e) => setUser({ ...user, email: e.target.value })} />
                                    </div>
                                    <div className="pt-4">
                                        <Button onClick={handleSave} loading={loading} icon={<Save className="w-4 h-4" />}>
                                            Save Changes
                                        </Button>
                                    </div>
                                </div>
                            )}

                            {activeTab === 'notifications' && (
                                <div className="space-y-6">
                                    <h3 className="text-lg font-medium text-foreground">Email Notifications</h3>
                                    <div className="space-y-4">
                                        {['Weekly Performance Reports', 'New Security Alerts', 'Product Updates', 'Tips & Tutorials'].map((item) => (
                                            <div key={item} className="flex items-center justify-between py-2">
                                                <span className="text-sm text-foreground">{item}</span>
                                                <input type="checkbox" defaultChecked className="toggle-checkbox" />
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {activeTab === 'appearance' && (
                                <div className="space-y-6">
                                    <h3 className="text-lg font-medium text-foreground">Theme</h3>
                                    <div className="grid grid-cols-3 gap-4">
                                        <button
                                            onClick={() => setTheme('light')}
                                            className={`p-4 rounded-xl border-2 text-center transition-all ${theme === 'light' ? 'border-primary bg-primary/5' : 'border-border hover:border-primary/50'}`}
                                        >
                                            <Sun className="w-8 h-8 mx-auto mb-2 text-foreground" />
                                            <span className="text-sm font-medium">Light</span>
                                        </button>
                                        <button
                                            onClick={() => setTheme('dark')}
                                            className={`p-4 rounded-xl border-2 text-center transition-all ${theme === 'dark' ? 'border-primary bg-primary/5' : 'border-border hover:border-primary/50'}`}
                                        >
                                            <Moon className="w-8 h-8 mx-auto mb-2 text-foreground" />
                                            <span className="text-sm font-medium">Dark</span>
                                        </button>
                                        <button
                                            onClick={() => setTheme('system')}
                                            className={`p-4 rounded-xl border-2 text-center transition-all ${theme === 'system' ? 'border-primary bg-primary/5' : 'border-border hover:border-primary/50'}`}
                                        >
                                            <Globe className="w-8 h-8 mx-auto mb-2 text-foreground" />
                                            <span className="text-sm font-medium">System</span>
                                        </button>
                                    </div>
                                </div>
                            )}

                            {activeTab === 'security' && (
                                <div className="space-y-6">
                                    <h3 className="text-lg font-medium text-foreground">Password</h3>
                                    <div className="space-y-4">
                                        <Input label="Current Password" type="password" />
                                        <Input label="New Password" type="password" />
                                        <Input label="Confirm New Password" type="password" />
                                    </div>
                                    <div className="pt-2">
                                        <Button>Update Password</Button>
                                    </div>
                                </div>
                            )}
                        </CardContent>
                    </Card>
                </div>
            </div>
        </div>
    );
};

// Helper components for the icons inside the file which are not imported
function Sun({ className }: { className?: string }) {
    return <svg className={className} xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="4" /><path d="M12 2v2" /><path d="M12 20v2" /><path d="m4.93 4.93 1.41 1.41" /><path d="m17.66 17.66 1.41 1.41" /><path d="M2 12h2" /><path d="M20 12h2" /><path d="m6.34 17.66-1.41 1.41" /><path d="m19.07 4.93-1.41 1.41" /></svg>;
}
function Moon({ className }: { className?: string }) {
    return <svg className={className} xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z" /></svg>;
}

export default Settings;
