// ---
// File Path: frontend/components/conversation/ContentSuggestionsCard.tsx
// ---

'use client';

import { useState, useEffect, FC } from 'react';
import { BookOpen, Video, FileText, ExternalLink, Send, Loader2 } from 'lucide-react';
import { InfoCard } from '@/components/ui/InfoCard';

export interface ContentResource {
  id: string;
  title: string;
  url: string;
  description?: string;
  categories: string[];
  content_type: 'article' | 'video' | 'document';
  status: 'active' | 'inactive' | 'archived';
  usage_count: number;
  created_at: string;
  updated_at: string;
}

interface ContentSuggestionsCardProps {
  clientId: string;
  api: any;
  onSendMessage: (content: string) => void;
}

export const ContentSuggestionsCard: FC<ContentSuggestionsCardProps> = ({ 
  clientId, 
  api, 
  onSendMessage 
}) => {
  const [suggestions, setSuggestions] = useState<ContentResource[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sendingResourceId, setSendingResourceId] = useState<string | null>(null);

  useEffect(() => {
    loadSuggestions();
  }, [clientId]);

  const loadSuggestions = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await api.get(`/api/content-resources/suggestions/${clientId}`);
      setSuggestions(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load content suggestions');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSendResource = async (resource: ContentResource) => {
    setSendingResourceId(resource.id);
    try {
      // Generate a personalized message for the resource
      const message = generateResourceMessage(resource);
      
      // Send the message
      await onSendMessage(message);
      
      // Increment usage count
      await api.post(`/api/content-resources/${resource.id}/increment-usage`);
      
      // Remove from suggestions after sending
      setSuggestions(prev => prev.filter(s => s.id !== resource.id));
      
    } catch (err: any) {
      setError(err.message || 'Failed to send resource');
    } finally {
      setSendingResourceId(null);
    }
  };

  const generateResourceMessage = (resource: ContentResource): string => {
    const contentType = resource.content_type;
    let baseMessage = '';
    
    switch (contentType) {
      case 'video':
        baseMessage = `I found a helpful video about ${resource.categories.join(', ')} that might be useful. It's called "${resource.title}".`;
        break;
      case 'document':
        baseMessage = `I have a helpful guide about ${resource.categories.join(', ')} that includes practical strategies. It's called "${resource.title}".`;
        break;
      default: // article
        baseMessage = `I found a helpful article about ${resource.categories.join(', ')} that might be useful. It's called "${resource.title}".`;
    }
    
    if (resource.description) {
      baseMessage += ` ${resource.description}`;
    }
    
    baseMessage += `\n\nHere's the link: ${resource.url}`;
    baseMessage += '\n\nLet me know if you find it helpful!';
    
    return baseMessage;
  };

  const getContentTypeIcon = (type: string) => {
    switch (type) {
      case 'video': return <Video size={16} />;
      case 'document': return <FileText size={16} />;
      default: return <BookOpen size={16} />;
    }
  };

  const getContentTypeColor = (type: string) => {
    switch (type) {
      case 'video': return 'text-purple-400';
      case 'document': return 'text-orange-400';
      default: return 'text-blue-400';
    }
  };

  if (isLoading) {
    return (
      <InfoCard title="Content Suggestions">
        <div className="flex items-center justify-center py-4">
          <Loader2 className="animate-spin h-5 w-5 text-teal-500" />
          <span className="ml-2 text-sm text-gray-400">Finding relevant content...</span>
        </div>
      </InfoCard>
    );
  }

  if (error) {
    return (
      <InfoCard title="Content Suggestions">
        <div className="text-red-400 text-sm py-2">{error}</div>
      </InfoCard>
    );
  }

  if (suggestions.length === 0) {
    return (
      <InfoCard title="Content Suggestions">
        <div className="text-center py-4 text-gray-400">
          <BookOpen size={24} className="mx-auto mb-2 opacity-50" />
          <p className="text-sm">No content suggestions available</p>
          <p className="text-xs">Add resources in your profile to see suggestions here</p>
        </div>
      </InfoCard>
    );
  }

  return (
    <InfoCard title="Content Suggestions">
      <div className="space-y-3">
        {suggestions.map((resource) => (
          <div
            key={resource.id}
            className="bg-gray-800/50 border border-gray-700 rounded-lg p-3 hover:border-gray-600 transition-colors"
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  <span className={`${getContentTypeColor(resource.content_type)}`}>
                    {getContentTypeIcon(resource.content_type)}
                  </span>
                  <h4 className="font-medium text-white text-sm">{resource.title}</h4>
                  <span className="text-xs text-gray-400 bg-gray-700 px-2 py-1 rounded">
                    {resource.content_type}
                  </span>
                </div>
                
                {resource.description && (
                  <p className="text-gray-300 text-xs mb-2">{resource.description}</p>
                )}
                
                <div className="flex items-center gap-2 mb-2">
                  <a
                    href={resource.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-teal-400 hover:text-teal-300 text-xs flex items-center gap-1"
                  >
                    <ExternalLink size={12} />
                    Preview
                  </a>
                  <span className="text-gray-500 text-xs">•</span>
                  <span className="text-gray-400 text-xs">
                    Used {resource.usage_count} time{resource.usage_count !== 1 ? 's' : ''}
                  </span>
                </div>

                {resource.categories.length > 0 && (
                  <div className="flex flex-wrap gap-1 mb-2">
                    {resource.categories.map((category) => (
                      <span
                        key={category}
                        className="bg-gray-700 text-gray-300 px-2 py-1 rounded text-xs"
                      >
                        {category}
                      </span>
                    ))}
                  </div>
                )}
              </div>

              <div className="ml-3">
                <button
                  onClick={() => handleSendResource(resource)}
                  disabled={sendingResourceId === resource.id}
                  className="flex items-center gap-1 px-3 py-1.5 bg-teal-600 hover:bg-teal-700 disabled:bg-gray-600 text-white rounded text-xs font-medium transition-colors"
                >
                  {sendingResourceId === resource.id ? (
                    <>
                      <Loader2 size={12} className="animate-spin" />
                      Sending...
                    </>
                  ) : (
                    <>
                      <Send size={12} />
                      Share
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </InfoCard>
  );
}; 