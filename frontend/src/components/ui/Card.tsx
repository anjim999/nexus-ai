import { ReactNode } from 'react';
import { clsx } from 'clsx';

interface CardProps {
    children: ReactNode;
    className?: string;
    hover?: boolean;
    glow?: boolean;
}

export const Card = ({ children, className, hover = false, glow = false }: CardProps) => {
    return (
        <div
            className={clsx(
                'bg-card rounded-xl border border-border p-6',
                hover && 'transition-all duration-300 hover:border-primary/50 hover:shadow-lg hover:shadow-primary/5',
                glow && 'shadow-lg shadow-primary/10',
                className
            )}
        >
            {children}
        </div>
    );
};

interface CardHeaderProps {
    children: ReactNode;
    className?: string;
}

export const CardHeader = ({ children, className }: CardHeaderProps) => {
    return (
        <div className={clsx('flex items-center justify-between mb-4', className)}>
            {children}
        </div>
    );
};

interface CardTitleProps {
    children: ReactNode;
    className?: string;
}

export const CardTitle = ({ children, className }: CardTitleProps) => {
    return (
        <h3 className={clsx('text-lg font-semibold text-foreground', className)}>
            {children}
        </h3>
    );
};

interface CardContentProps {
    children: ReactNode;
    className?: string;
}

export const CardContent = ({ children, className }: CardContentProps) => {
    return <div className={clsx(className)}>{children}</div>;
};
