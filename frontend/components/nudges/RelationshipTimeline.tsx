// frontend/components/nudges/RelationshipTimeline.tsx
'use client';

import { FC, useEffect, useState } from 'react';
import { useAppContext } from '@/context/AppContext';
import { Mail, MessageCircle, ArrowUpRight, Brain } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';

interface TimelineEvent {
    type: 'message_inbound' | 'message_outbound' | 'nudge_sent';
    date: string;
    description: string;
}

const ICONS = {
    message_inbound: <MessageCircle size={16} className="text-blue-400" />,
    message_outbound: <ArrowUpRight size={16} className="text-gray-500" />,
    nudge_sent: <Brain size={16} className="text-primary-action" />,
};

const TimelineItem: FC<{ event: TimelineEvent }> = ({ event }) => (
    <div className="flex items-start gap-3">
        <div className="flex-shrink-0 mt-1 w-6 h-6 bg-white/5 rounded-full flex items-center justify-center">
            {ICONS[event.type] || <Mail size={16} />}
        </div>
        <div className="flex-1">
            <p className="text-sm text-brand-text-main">{event.description}</p>
            <p className="text-xs text-brand-text-muted">
                {formatDistanceToNow(new Date(event.date), { addSuffix: true })}
            </p>
        </div>
    </div>
);

interface RelationshipTimelineProps {
    clientId: string;
}

export const RelationshipTimeline: FC<RelationshipTimelineProps> = ({ clientId }) => {
    const { api } = useAppContext();
    const [events, setEvents] = useState<TimelineEvent[]>([]);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        const fetchTimeline = async () => {
            setIsLoading(true);
            try {
                const data = await api.get(`/api/clients/${clientId}/timeline`);
                setEvents(data || []);
            } catch (error) {
                console.error("Failed to fetch relationship timeline:", error);
                setEvents([]); // Set to empty on error
            } finally {
                setIsLoading(false);
            }
        };

        fetchTimeline();
    }, [clientId, api]);

    return (
        <div className="space-y-3">
            <h4 className="font-semibold text-sm text-brand-text-muted flex items-center gap-2">
                <Mail size={16} /> Relationship Timeline
            </h4>
            <div className="space-y-4 p-4 bg-white/[.03] border border-white/5 rounded-lg">
                {isLoading && <p className="text-xs text-brand-text-muted">Loading history...</p>}
                {!isLoading && events.length === 0 && (
                    <p className="text-xs text-brand-text-muted">No recent interactions found.</p>
                )}
                {!isLoading && events.map((event, index) => (
                    <TimelineItem key={index} event={event} />
                ))}
            </div>
        </div>
    );
};