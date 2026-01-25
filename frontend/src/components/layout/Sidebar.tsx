import { NavLink } from 'react-router-dom';
import {
    LayoutDashboard,
    MessageSquare,
    FileText,
    Bot,
    FileBarChart,
    Settings,
    Brain
} from 'lucide-react';
import { clsx } from 'clsx';

const navigation = [
    { name: 'Dashboard', href: '/', icon: LayoutDashboard },
    { name: 'Chat', href: '/chat', icon: MessageSquare },
    { name: 'Documents', href: '/documents', icon: FileText },
    { name: 'Agents', href: '/agents', icon: Bot },
    { name: 'Reports', href: '/reports', icon: FileBarChart },
];

const Sidebar = () => {
    return (
        <aside className="w-64 bg-card border-r border-border flex flex-col">
            {/* Logo */}
            <div className="h-16 flex items-center gap-3 px-6 border-b border-border">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center">
                    <Brain className="w-6 h-6 text-white" />
                </div>
                <div>
                    <h1 className="text-lg font-bold text-foreground">Nexus</h1>
                    <p className="text-xs text-muted-foreground">AI Intelligence</p>
                </div>
            </div>

            {/* Navigation */}
            <nav className="flex-1 px-3 py-4 space-y-1">
                {navigation.map((item) => (
                    <NavLink
                        key={item.name}
                        to={item.href}
                        className={({ isActive }) =>
                            clsx(
                                'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200',
                                isActive
                                    ? 'bg-primary/10 text-primary'
                                    : 'text-muted-foreground hover:bg-muted hover:text-foreground'
                            )
                        }
                    >
                        <item.icon className="w-5 h-5" />
                        {item.name}
                    </NavLink>
                ))}
            </nav>

            {/* Footer */}
            <div className="p-3 border-t border-border">
                <NavLink
                    to="/settings"
                    className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
                >
                    <Settings className="w-5 h-5" />
                    Settings
                </NavLink>
            </div>
        </aside>
    );
};

export default Sidebar;
