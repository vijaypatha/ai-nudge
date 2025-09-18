// components/ui/Textarea.tsx
import React from 'react';
import clsx from 'clsx';

interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
    variant?: 'default' | 'error';
    size?: 'sm' | 'md' | 'lg';
}

const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(
    ({ className, variant = 'default', size = 'md', ...props }, ref) => {
        const baseStyles = 'w-full rounded-md border transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-brand-accent disabled:opacity-50 disabled:pointer-events-none resize-none';

        const variantStyles = {
            default: 'bg-gray-700 border-gray-600 text-white placeholder-gray-400 focus:border-teal-500 focus:ring-1 focus:ring-teal-500',
            error: 'bg-gray-700 border-red-500 text-white placeholder-gray-400 focus:border-red-500 focus:ring-1 focus:ring-red-500',
        };

        const sizeStyles = {
            sm: 'px-3 py-2 text-sm',
            md: 'px-3 py-2 text-base',
            lg: 'px-4 py-3 text-lg',
        };

        return (
            <textarea
                className={clsx(baseStyles, variantStyles[variant], sizeStyles[size], className)}
                ref={ref}
                {...props}
            />
        );
    }
);

Textarea.displayName = 'Textarea';

export { Textarea };
