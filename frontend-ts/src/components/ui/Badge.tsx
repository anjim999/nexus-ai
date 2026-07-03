import { type ReactNode } from 'react';
import { clsx } from 'clsx';

interface BadgeProps {
    children: ReactNode;
    variant?: 'default' | 'success' | 'warning' | 'error' | 'info' | 'purple';
    size?: 'sm' | 'md';
    className?: string;
    pulse?: boolean;
}

export const Badge = ({ children, variant = 'default', size = 'md', className, pulse = false }: BadgeProps) => {
    const variants = {
        default: 'bg-muted text-muted-foreground',
        success: 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30',
        warning: 'bg-amber-500/20 text-amber-400 border border-amber-500/30',
        error: 'bg-red-500/20 text-red-400 border border-red-500/30',
        info: 'bg-sky-500/20 text-sky-400 border border-sky-500/30',
        purple: 'bg-violet-500/20 text-violet-400 border border-violet-500/30',
    };

    const sizes = {
        sm: 'px-2 py-0.5 text-xs',
        md: 'px-2.5 py-1 text-xs',
    };

    return (
        <span
            className={clsx(
                'inline-flex items-center gap-1.5 font-medium rounded-full',
                variants[variant],
                sizes[size],
                className
            )}
        >
            {pulse && (
                <span className="relative flex h-2 w-2">
                    <span className={clsx(
                        'animate-ping absolute inline-flex h-full w-full rounded-full opacity-75',
                        variant === 'success' && 'bg-emerald-400',
                        variant === 'warning' && 'bg-amber-400',
                        variant === 'error' && 'bg-red-400',
                        variant === 'info' && 'bg-sky-400',
                        variant === 'purple' && 'bg-violet-400',
                        variant === 'default' && 'bg-muted-foreground'
                    )} />
                    <span className={clsx(
                        'relative inline-flex rounded-full h-2 w-2',
                        variant === 'success' && 'bg-emerald-400',
                        variant === 'warning' && 'bg-amber-400',
                        variant === 'error' && 'bg-red-400',
                        variant === 'info' && 'bg-sky-400',
                        variant === 'purple' && 'bg-violet-400',
                        variant === 'default' && 'bg-muted-foreground'
                    )} />
                </span>
            )}
            {children}
        </span>
    );
};
