import { clsx } from 'clsx';

export const Card = ({ children, className, hover = false, glow = false }) => {
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

export const CardHeader = ({ children, className }) => {
    return (
        <div className={clsx('flex items-center justify-between mb-4', className)}>
            {children}
        </div>
    );
};

export const CardTitle = ({ children, className }) => {
    return (
        <h3 className={clsx('text-lg font-semibold text-foreground', className)}>
            {children}
        </h3>
    );
};

export const CardContent = ({ children, className }) => {
    return <div className={clsx(className)}>{children}</div>;
};
