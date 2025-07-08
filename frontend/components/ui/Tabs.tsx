'use client';

import React, { useState, useRef, useEffect } from 'react';
import clsx from 'clsx';

export interface TabOption {
  id: string;
  label: string;
  icon?: React.ReactNode;
  color?: string;
  disabled?: boolean;
}

interface TabsProps {
  options: TabOption[];
  activeTab: string;
  setActiveTab: (id: string) => void;
  className?: string;
  variant?: 'default' | 'underline' | 'pill' | 'colorful';
  size?: 'sm' | 'md' | 'lg';
  centered?: boolean;
  animated?: boolean;
}

export const Tabs = ({ 
  options, 
  activeTab, 
  setActiveTab, 
  className,
  variant = 'colorful',
  size = 'md',
  centered = true,
  animated = true
}: TabsProps) => {
  const [underlineStyle, setUnderlineStyle] = useState({ width: 0, left: 0 });
  const tabsRef = useRef<HTMLDivElement>(null);
  const activeTabRef = useRef<HTMLButtonElement>(null);

  // Fixed underline position calculation
  useEffect(() => {
    if (animated && (variant === 'underline' || variant === 'colorful') && activeTabRef.current && tabsRef.current) {
      const activeTabElement = activeTabRef.current;
      const tabsContainer = tabsRef.current;
      
      const buttonRect = activeTabElement.getBoundingClientRect();
      const containerRect = tabsContainer.getBoundingClientRect();
      
      // Account for button padding based on size
      const paddingMap = { sm: 12, md: 16, lg: 24 };
      const horizontalPadding = paddingMap[size];
      
      setUnderlineStyle({
        width: buttonRect.width - (horizontalPadding * 2),
        left: (buttonRect.left - containerRect.left) + horizontalPadding
      });
    }
  }, [activeTab, animated, variant, options, size]);

  const sizeClasses = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-base',
    lg: 'px-6 py-3 text-lg'
  };

  const containerClasses = clsx(
    'relative flex gap-1',
    centered && 'justify-center w-full',
    variant === 'default' && 'bg-gray-100 dark:bg-gray-800 rounded-lg p-1',
    variant === 'pill' && 'bg-brand-dark rounded-2xl p-1 shadow-lg',
    variant === 'colorful' && 'bg-brand-dark rounded-2xl p-1 shadow-lg',
    className
  );

  const getTabClasses = (option: TabOption, isActive: boolean) => {
    const baseClasses = clsx(
      'relative font-semibold transition-all duration-300 outline-none cursor-pointer',
      'focus-visible:ring-2 focus-visible:ring-brand-accent focus-visible:z-10',
      'disabled:opacity-50 disabled:cursor-not-allowed',
      'group', // For ripple effect
      sizeClasses[size]
    );

    switch (variant) {
      case 'underline':
        return clsx(
          baseClasses,
          'rounded-none bg-transparent border-b-2 border-transparent',
          isActive 
            ? 'text-brand-accent' 
            : 'text-gray-600 dark:text-gray-400 hover:text-brand-accent'
        );
      
      case 'pill':
        return clsx(
          baseClasses,
          'rounded-full',
          isActive
            ? 'bg-brand-accent text-white shadow-md transform scale-105'
            : 'bg-transparent text-brand-light hover:bg-brand-accent/20 hover:text-white'
        );
      
      case 'colorful':
        return clsx(
          baseClasses,
          'rounded-full',
          isActive
            ? 'text-white shadow-lg transform scale-105'
            : 'bg-transparent text-brand-light hover:bg-white/10 hover:text-white'
        );
      
      default:
        return clsx(
          baseClasses,
          'rounded-md',
          isActive
            ? 'bg-white dark:bg-gray-700 text-brand-primary shadow-sm'
            : 'text-gray-600 dark:text-gray-400 hover:bg-white/50 dark:hover:bg-gray-700/50'
        );
    }
  };

  const getActiveTabStyle = (option: TabOption) => {
    if (variant === 'colorful' && option.color) {
      return {
        background: option.color,
        boxShadow: `0 4px 20px 0 ${option.color}40`
      };
    }
    return {};
  };

  return (
    <div className={clsx(centered && 'flex justify-center w-full py-4')}>
      <div className={containerClasses}>
        <div 
          ref={tabsRef}
          className="flex gap-1 relative"
          role="tablist"
          aria-orientation="horizontal"
        >
          {options.map((option) => {
            const isActive = activeTab === option.id;
            
            return (
              <button
                key={option.id}
                ref={isActive ? activeTabRef : null}
                onClick={() => !option.disabled && setActiveTab(option.id)}
                className={getTabClasses(option, isActive)}
                style={isActive ? getActiveTabStyle(option) : undefined}
                role="tab"
                aria-selected={isActive}
                aria-controls={`tabpanel-${option.id}`}
                aria-disabled={option.disabled}
                tabIndex={isActive ? 0 : -1}
                disabled={option.disabled}
              >
                {option.icon && (
                  <span className="mr-2 flex-shrink-0">
                    {option.icon}
                  </span>
                )}
                {option.label}
                
                {/* Ripple effect */}
                {animated && (
                  <span className="absolute inset-0 rounded-full bg-white/20 scale-0 transition-transform duration-200 group-active:scale-100" />
                )}
              </button>
            );
          })}
          
          {/* Fixed animated underline */}
          {animated && (variant === 'underline' || variant === 'colorful') && (
            <div
              className="absolute bottom-0 h-1 bg-brand-accent rounded-full transition-all duration-300 ease-out"
              style={{
                width: underlineStyle.width,
                left: underlineStyle.left
              }}
            />
          )}
        </div>
      </div>
    </div>
  );
};
