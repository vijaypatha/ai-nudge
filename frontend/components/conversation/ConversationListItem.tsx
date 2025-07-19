'use client';

import React from 'react';
import { Conversation } from '@/context/AppContext';
import { Avatar } from '@/components/ui/Avatar';
import { Clock, MessageCircle, Zap, Sparkles } from 'lucide-react';
import clsx from 'clsx';

interface ConversationListItemProps {
  conversation: Conversation;
  isSelected: boolean;
  onClick: () => void;
}

const formatTime = (timestamp: string) => {
  // Parse the UTC timestamp and convert to local time
  const date = new Date(timestamp);
  const now = new Date();
  const diffInHours = (now.getTime() - date.getTime()) / (1000 * 60 * 60);
  
  if (diffInHours < 24) {
    return date.toLocaleTimeString([], { 
      hour: 'numeric', 
      minute: '2-digit',
      hour12: true 
    });
  } else if (diffInHours < 48) {
    return 'Yesterday';
  } else {
    return date.toLocaleDateString([], { month: 'short', day: 'numeric' });
  }
};

const getMessageIcon = (source?: string, direction?: string) => {
  if (!source || !direction) return null;
  
  if (direction === 'outbound') {
    switch (source) {
      case 'instant_nudge':
        return <Zap className="w-3 h-3 text-cyan-400" />;
      case 'scheduled':
        return <Clock className="w-3 h-3 text-blue-400" />;
      case 'faq_auto_response':
        return <Sparkles className="w-3 h-3 text-purple-400" />;
      default:
        return <MessageCircle className="w-3 h-3 text-gray-400" />;
    }
  }
  return null;
};

export const ConversationListItem: React.FC<ConversationListItemProps> = ({
  conversation,
  isSelected,
  onClick
}) => {
  return (
    <div
      className={clsx(
        "p-4 cursor-pointer transition-all duration-200 border-l-4",
        isSelected 
          ? "bg-brand-accent/10 border-brand-accent" 
          : "border-transparent hover:bg-white/5 hover:border-white/20"
      )}
      onClick={onClick}
    >
      <div className="flex items-start gap-3">
        {/* Avatar with online indicator */}
        <div className="relative flex-shrink-0">
          <Avatar 
            name={conversation.client_name} 
            className="w-12 h-12 text-sm"
          />
          {conversation.is_online && (
            <div className="absolute -bottom-1 -right-1 w-4 h-4 bg-green-500 border-2 border-brand-dark rounded-full" />
          )}
        </div>
        
        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between mb-1">
            <h3 className="font-semibold text-brand-text-main truncate">
              {conversation.client_name}
            </h3>
            <span className="text-xs text-brand-text-muted flex-shrink-0">
              {formatTime(conversation.last_message_time)}
            </span>
          </div>
          
          <div className="flex items-center gap-2">
            {getMessageIcon(conversation.last_message_source, conversation.last_message_direction)}
            <p className={clsx(
              "text-sm truncate",
              conversation.unread_count > 0 
                ? "text-brand-text-main font-medium" 
                : "text-brand-text-muted"
            )}>
              {conversation.last_message}
            </p>
          </div>
        </div>
        
        {/* Unread indicator */}
        {conversation.unread_count > 0 && (
          <div className="flex-shrink-0">
            <div className="bg-brand-accent text-brand-dark text-xs font-bold rounded-full w-6 h-6 flex items-center justify-center">
              {conversation.unread_count > 99 ? '99+' : conversation.unread_count}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}; 