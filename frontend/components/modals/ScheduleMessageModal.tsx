// frontend/components/modals/ScheduleMessageModal.tsx
'use client';

import { useState, FC, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useAppContext } from '@/context/AppContext';
import { Button } from '@/components/ui/Button';
import { X, Loader2, CalendarClock, Users, Send } from 'lucide-react';
import { ACTIVE_THEME } from '@/utils/theme';
import Confetti from 'react-confetti';

interface ScheduleMessageModalProps {
    isOpen: boolean;
    onClose: () => void;
    onScheduleSuccess: () => void;
    clientId: string;
    initialContent?: string;
}

export const ScheduleMessageModal: FC<ScheduleMessageModalProps> = ({ 
    isOpen, 
    onClose, 
    onScheduleSuccess, 
    clientId, 
    initialContent = ''
}) => {
    const { api, user } = useAppContext();
    const [content, setContent] = useState('');
    const [date, setDate] = useState('');
    const [isSaving, setIsSaving] = useState(false);
    const [showConfetti, setShowConfetti] = useState(false);
    const [windowSize, setWindowSize] = useState({ width: 0, height: 0 });

    // Add window size tracking for confetti
    useEffect(() => {
        const handleResize = () => setWindowSize({ width: window.innerWidth, height: window.innerHeight });
        window.addEventListener('resize', handleResize);
        handleResize();
        return () => window.removeEventListener('resize', handleResize);
    }, []);

    useEffect(() => {
        if (isOpen) {
            // Set default time to 30 mins in the future
            const futureDate = new Date(Date.now() + 30 * 60 * 1000);
            const year = futureDate.getFullYear();
            const month = (futureDate.getMonth() + 1).toString().padStart(2, '0');
            const day = futureDate.getDate().toString().padStart(2, '0');
            const hours = futureDate.getHours().toString().padStart(2, '0');
            const minutes = futureDate.getMinutes().toString().padStart(2, '0');
            setDate(`${year}-${month}-${day}T${hours}:${minutes}`);
            setContent(initialContent);
        }
    }, [isOpen, initialContent]);

    const handleSchedule = async () => {
        if (!content || !date || !clientId) {
            alert("Please fill out all fields.");
            return;
        }
        setIsSaving(true);
        try {
            // Get user's timezone automatically
            const userTimezone = user?.timezone || Intl.DateTimeFormat().resolvedOptions().timeZone;
            
            await api.post(`/api/scheduled-messages`, {
                client_id: clientId,
                content: content,
                scheduled_at_local: date,
                timezone: userTimezone,
            });
            
            // Show confetti for successful scheduling
            setShowConfetti(true);
            setTimeout(() => setShowConfetti(false), 4000); // Hide after 4 seconds

            onScheduleSuccess();
        } catch (error) {
            console.error("Failed to schedule message:", error);
            alert("Could not schedule the message. Please try again.");
        } finally {
            setIsSaving(false);
        }
    };

    if (!isOpen) return null;

    return (
        <>
            {/* Confetti for successful message scheduling */}
            {showConfetti && (
                <Confetti
                    width={windowSize.width}
                    height={windowSize.height}
                    recycle={false}
                    numberOfPieces={100} // Adjust as needed
                    tweenDuration={4000}
                    colors={[
                        ACTIVE_THEME.primary.from,
                        ACTIVE_THEME.primary.to,
                        ACTIVE_THEME.accent,
                        ACTIVE_THEME.action,
                        '#ffffff'
                    ]}
                />
            )}

            <motion.div 
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4"
            >
                <motion.div 
                    initial={{ opacity: 0, y: 30 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="bg-brand-primary border border-white/10 rounded-xl shadow-lg w-full max-w-lg flex flex-col"
                >
                    <header className="flex items-center justify-between p-4 border-b border-white/10">
                        <h2 className="font-bold text-lg text-white">Schedule a Message</h2>
                        <Button variant="ghost" size="sm" onClick={onClose}><X className="w-5 h-5" /></Button>
                    </header>
                    <main className="p-6 space-y-4">
                        <div>
                            <label className="text-sm font-semibold text-gray-300 mb-2 block">Message</label>
                            <textarea
                                value={content}
                                onChange={(e) => setContent(e.target.value)}
                                className="w-full h-32 p-3 bg-black/20 border border-white/20 rounded-lg text-white focus:ring-2 focus:ring-primary-action"
                                placeholder="Write your message here..."
                            />
                        </div>
                        <div>
                            <label className="text-sm font-semibold text-gray-300 mb-2 block">Date & Time</label>
                            <input
                                type="datetime-local"
                                value={date}
                                onChange={(e) => setDate(e.target.value)}
                                className="w-full p-3 bg-black/20 border border-white/20 rounded-lg text-white focus:ring-2 focus:ring-primary-action"
                            />
                        </div>
                    </main>
                    <footer className="flex justify-end gap-3 p-4 bg-black/20 border-t border-white/10">
                        <Button variant="secondary" onClick={onClose} disabled={isSaving}>Cancel</Button>
                        <Button onClick={handleSchedule} disabled={isSaving || !content || !date}>
                            {isSaving ? <Loader2 className="w-4 h-4 animate-spin" /> : <CalendarClock className="w-4 h-4 mr-2" />}
                            Schedule Message
                        </Button>
                    </footer>
                </motion.div>
            </motion.div>
        </>
    );
};