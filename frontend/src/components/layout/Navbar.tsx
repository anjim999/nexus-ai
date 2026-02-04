import { Bell, Search, Moon, Sun } from 'lucide-react';
import { useState } from 'react';

import { useTheme } from '../theme-provider';

const Navbar = () => {
    const { theme, setTheme } = useTheme();

    return (
        <header className="h-16 border-b border-border bg-card/50 backdrop-blur-sm flex items-center justify-between px-6">
            {/* Search Bar */}
            <div className="flex-1 max-w-xl">
                <div className="relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                    <input
                        type="text"
                        placeholder="Ask Nexus anything..."
                        className="w-full pl-10 pr-4 py-2 bg-muted/50 border border-border rounded-lg text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary transition-all"
                    />
                    <kbd className="absolute right-3 top-1/2 -translate-y-1/2 hidden sm:inline-flex items-center gap-1 px-2 py-0.5 text-xs font-mono text-muted-foreground bg-muted rounded">
                        ⌘K
                    </kbd>
                </div>
            </div>

            {/* Right Actions */}
            <div className="flex items-center gap-2 ml-4">
                {/* Theme Toggle */}
                <button
                    onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
                    className="p-2 rounded-lg text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
                >
                    {theme === 'dark' ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
                </button>

                {/* Notifications */}
                <button
                    onClick={() => window.location.href = '/notifications'}
                    className="relative p-2 rounded-lg text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
                >
                    <Bell className="w-5 h-5" />
                    <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-red-500 rounded-full" />
                </button>

                {/* User Avatar */}
                <button
                    onClick={() => window.location.href = '/settings'}
                    className="ml-2 flex items-center gap-3 p-1.5 rounded-lg hover:bg-muted transition-colors"
                >
                    <div className="w-8 h-8 rounded-full bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center text-white text-sm font-medium">
                        A
                    </div>
                </button>
            </div>
        </header>
    );
};

export default Navbar;
