// components/ui/Button.tsx
import React from 'react';
import clsx from 'clsx';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
    variant?: 'primary' | 'secondary' | 'danger' |'ghost' | 'destructive';
    size?: 'sm' | 'md' | 'lg';
    children: React.ReactNode;
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
    ({ className, variant = 'primary', size = 'md', children, ...props }, ref) => {
        const baseStyles = 'inline-flex items-center justify-center rounded-md font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-brand-accent disabled:opacity-50 disabled:pointer-events-none';

        const variantStyles = {
            primary: 'bg-brand-accent text-white hover:bg-brand-accent/90',
            secondary: 'bg-white/10 text-brand-text-main hover:bg-white/20',
            danger: 'bg-red-600 text-white hover:bg-red-700',
            ghost: 'bg-transparent text-brand-text-main hover:bg-white/10',
            destructive: 'bg-red-100 text-red-700 hover:bg-red-200',
        };

        const sizeStyles = {
            sm: 'h-8 px-3 text-sm',
            md: 'h-10 px-4 py-2 text-base',
            lg: 'h-12 px-6 text-lg',
        };

        return (
            <button
                className={clsx(baseStyles, variantStyles[variant], sizeStyles[size], className)}
                ref={ref}
                {...props}
            >
                {children}
            </button>
        );
    }
);

Button.displayName = 'Button';

export { Button };
