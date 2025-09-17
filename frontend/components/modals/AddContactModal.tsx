// frontend/components/modals/AddContactModal.tsx
'use client';

import { useState, FC, useEffect, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useAppContext } from '@/context/AppContext';
import { Button } from '@/components/ui/Button';
import { X, Loader2, UserPlus, CheckCircle2, AlertTriangle, Copy, PartyPopper } from 'lucide-react';

interface AddContactModalProps {
    isOpen: boolean;
    onClose: () => void;
    onContactAdded: () => void;
    onShowConfetti?: () => void;
}

type ModalView = 'form' | 'loading' | 'success';

export const AddContactModal: FC<AddContactModalProps> = ({ isOpen, onClose, onContactAdded, onShowConfetti }) => {
    // --- MODIFICATION: Get user and clientRoles from context ---
    const { api, user, clientRoles } = useAppContext();
    const [view, setView] = useState<ModalView>('form');
    
    // Form state
    const [fullName, setFullName] = useState('');
    const [email, setEmail] = useState('');
    const [phone, setPhone] = useState('');
    // --- MODIFICATION: Default role comes from the dynamic list ---
    const [role, setRole] = useState(clientRoles[0] || '');
    const [createHub, setCreateHub] = useState(true);

    // Outcome state
    const [error, setError] = useState<string | null>(null);
    const [successData, setSuccessData] = useState<{ name: string; hubUrl: string | null } | null>(null);
    const [isCopied, setIsCopied] = useState(false);

    const resetState = () => {
        setFullName('');
        setEmail('');
        setPhone('');
        setRole(clientRoles[0] || ''); // Reset to the first available role
        setCreateHub(true);
        setError(null);
        setSuccessData(null);
        setView('form');
        setIsCopied(false);
    };

    const handleClose = () => {
        if (view === 'loading') return;
        resetState();
        onClose();
    };
    
    useEffect(() => {
        // Reset form when modal is re-opened
        if (isOpen) {
            resetState();
        }
    }, [isOpen, clientRoles]); // Reset if roles change while modal is closed

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!fullName) {
            setError("Full name is required.");
            return;
        }

        setView('loading');
        setError(null);

        try {
            const response = await api.post('/api/clients/manual', {
                full_name: fullName,
                email: email || undefined,
                phone: phone || undefined,
                client_role: role.toLowerCase(),
                create_hub: createHub,
            });

            setSuccessData({ name: response.client.full_name, hubUrl: response.hub_url });
            setView('success');
            onContactAdded();
            if (onShowConfetti) onShowConfetti();

        } catch (err: any) {
            const errorMessage = err.message || "An unknown error occurred.";
            setError(errorMessage);
            setView('form'); // Go back to form on error
        }
    };
    
    const handleCopy = () => {
        if (successData?.hubUrl) {
            navigator.clipboard.writeText(successData.hubUrl);
            setIsCopied(true);
            setTimeout(() => setIsCopied(false), 2000);
        }
    };


    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
            <motion.div 
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                className="bg-brand-primary border border-white/10 rounded-xl shadow-lg w-full max-w-md flex flex-col"
            >
                <header className="flex items-center justify-between p-4 border-b border-white/10">
                    <h2 className="font-bold text-lg text-white flex items-center gap-2">
                        <UserPlus className="w-5 h-5" />
                        Add New Contact
                    </h2>
                    <Button variant="ghost" size="sm" onClick={handleClose} disabled={view === 'loading'}>
                        <X className="w-5 h-5" />
                    </Button>
                </header>
                
                <AnimatePresence mode="wait">
                    {view === 'loading' && (
                        <motion.div key="loading" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="p-12 flex flex-col items-center justify-center gap-4 text-white">
                            <Loader2 className="w-10 h-10 animate-spin text-primary-action" />
                            <p>Creating contact...</p>
                        </motion.div>
                    )}

                    {view === 'success' && successData && (
                        <motion.div key="success" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="p-6 text-center">
                            <PartyPopper className="w-16 h-16 text-green-400 mx-auto mb-4" />
                            <h3 className="text-xl font-bold text-white">Contact Added!</h3>
                            <p className="text-gray-300 mt-1">
                                {successData.name} is now in your community.
                            </p>
                            
                            {successData.hubUrl && (
                                <div className="mt-6">
                                    <label className="text-sm font-medium text-gray-300">Client Hub Link</label>
                                    <div className="flex items-center gap-2 mt-2">
                                        <input 
                                            type="text"
                                            readOnly
                                            value={successData.hubUrl}
                                            className="w-full truncate p-2 bg-black/20 border border-white/20 rounded-lg text-gray-400 text-sm"
                                        />
                                        <Button variant="secondary" onClick={handleCopy}>
                                            {isCopied ? <CheckCircle2 size={16} /> : <Copy size={16} />}
                                        </Button>
                                    </div>
                                    <p className="text-xs text-gray-400 mt-2">Share this permanent link with your client.</p>
                                </div>
                            )}
                            <Button onClick={handleClose} className="mt-6 w-full">Done</Button>
                        </motion.div>
                    )}

                    {view === 'form' && (
                         <motion.div key="form" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                            <form onSubmit={handleSubmit} className="p-6 space-y-4">
                                <div>
                                    <label htmlFor="full_name" className="block text-sm font-medium text-gray-300 mb-2">Full Name *</label>
                                    <input type="text" id="full_name" value={fullName} onChange={(e) => setFullName(e.target.value)}
                                        className="w-full p-3 bg-black/20 border border-white/20 rounded-lg text-white placeholder-gray-400 focus:ring-2 focus:ring-primary-action focus:border-transparent" 
                                        placeholder="e.g., Alex Martinez" required />
                                </div>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    <div>
                                        <label htmlFor="email" className="block text-sm font-medium text-gray-300 mb-2">Email</label>
                                        <input type="email" id="email" value={email} onChange={(e) => setEmail(e.target.value)}
                                            className="w-full p-3 bg-black/20 border border-white/20 rounded-lg text-white placeholder-gray-400 focus:ring-2 focus:ring-primary-action focus:border-transparent"
                                            placeholder="alex@example.com" />
                                    </div>
                                    <div>
                                        <label htmlFor="phone" className="block text-sm font-medium text-gray-300 mb-2">Phone</label>
                                        <input type="tel" id="phone" value={phone} onChange={(e) => setPhone(e.target.value)}
                                            className="w-full p-3 bg-black/20 border border-white/20 rounded-lg text-white placeholder-gray-400 focus:ring-2 focus:ring-primary-action focus:border-transparent"
                                            placeholder="(555) 123-4567" />
                                    </div>
                                </div>
                                <div>
                                    <label htmlFor="role" className="block text-sm font-medium text-gray-300 mb-2">Client Role</label>
                                    {/* --- MODIFICATION: Dynamic role dropdown --- */}
                                    <select id="role" value={role} onChange={(e) => setRole(e.target.value)}
                                        className="w-full p-3 bg-black/20 border border-white/20 rounded-lg text-white focus:ring-2 focus:ring-primary-action focus:border-transparent">
                                        {clientRoles.map(r => (
                                            <option key={r} value={r}>{r}</option>
                                        ))}
                                    </select>
                                </div>
                                <div className="flex items-center gap-3 mt-4">
                                    <input type="checkbox" id="create-hub" checked={createHub} onChange={(e) => setCreateHub(e.target.checked)} 
                                        className="h-4 w-4 rounded bg-black/20 border-white/30 text-primary-action focus:ring-primary-action" />
                                    <label htmlFor="create-hub" className="text-sm text-gray-300">Create Client Hub</label>
                                </div>

                                {error && (
                                    <div className="flex items-center gap-2 text-sm text-red-400 animate-in fade-in-0 p-3 bg-red-500/10 rounded-lg">
                                        <AlertTriangle size={16}/> <span>{error}</span>
                                    </div>
                                )}
                            </form>
                            <footer className="flex justify-end gap-3 p-4 bg-black/20 border-t border-white/10">
                                <Button variant="secondary" onClick={handleClose}>Cancel</Button>
                                <Button onClick={handleSubmit} disabled={!fullName.trim()}>
                                    <UserPlus className="w-4 h-4 mr-2" /> Add Contact
                                </Button>
                            </footer>
                        </motion.div>
                    )}
                </AnimatePresence>
            </motion.div>
        </div>
    );
};