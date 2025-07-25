// frontend/components/modals/AddContactModal.tsx
'use client';

import { useState, FC } from 'react';
import { motion } from 'framer-motion';
import { useAppContext } from '@/context/AppContext';
import { Button } from '@/components/ui/Button';
import { X, Loader2, UserPlus, CheckCircle2, AlertTriangle } from 'lucide-react';

interface AddContactModalProps {
    isOpen: boolean;
    onClose: () => void;
    onContactAdded: () => void;
}

export const AddContactModal: FC<AddContactModalProps> = ({ isOpen, onClose, onContactAdded }) => {
    const { api } = useAppContext();
    const [fullName, setFullName] = useState('');
    const [email, setEmail] = useState('');
    const [phone, setPhone] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState<string | null>(null);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!fullName) {
            setError("Full name is required.");
            return;
        }

        setIsLoading(true);
        setError(null);
        setSuccess(null);

        try {
            const newClient = await api.post('/api/clients/manual', {
                full_name: fullName,
                email: email || undefined,
                phone_number: phone || undefined,
            });

            setSuccess(`Successfully added ${newClient.full_name}!`);
            setFullName('');
            setEmail('');
            setPhone('');

            // Call the callback to refresh the community list
            onContactAdded();

            // Close modal after a short delay
            setTimeout(() => {
                setSuccess(null);
                onClose();
            }, 2000);

        } catch (err: any) {
            const errorMessage = err.message || "An unknown error occurred.";
            setError(errorMessage);
            console.error(err);
        } finally {
            setIsLoading(false);
        }
    };

    const handleClose = () => {
        if (!isLoading) {
            setFullName('');
            setEmail('');
            setPhone('');
            setError(null);
            setSuccess(null);
            onClose();
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
                    <Button variant="ghost" size="sm" onClick={handleClose} disabled={isLoading}>
                        <X className="w-5 h-5" />
                    </Button>
                </header>
                
                <form onSubmit={handleSubmit} className="p-6 space-y-4">
                    <div>
                        <label htmlFor="full_name" className="block text-sm font-medium text-gray-300 mb-2">
                            Full Name *
                        </label>
                        <input 
                            type="text" 
                            id="full_name"
                            value={fullName}
                            onChange={(e) => setFullName(e.target.value)}
                            className="w-full p-3 bg-black/20 border border-white/20 rounded-lg text-white placeholder-gray-400 focus:ring-2 focus:ring-primary-action focus:border-transparent" 
                            placeholder="e.g., Alex Martinez"
                            required
                            disabled={isLoading}
                        />
                    </div>
                    
                    <div>
                        <label htmlFor="email" className="block text-sm font-medium text-gray-300 mb-2">
                            Email
                        </label>
                        <input 
                            type="email" 
                            id="email" 
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            className="w-full p-3 bg-black/20 border border-white/20 rounded-lg text-white placeholder-gray-400 focus:ring-2 focus:ring-primary-action focus:border-transparent"
                            placeholder="alex@example.com"
                            disabled={isLoading}
                        />
                    </div>
                    
                    <div>
                        <label htmlFor="phone" className="block text-sm font-medium text-gray-300 mb-2">
                            Phone
                        </label>
                        <input 
                            type="tel" 
                            id="phone" 
                            value={phone}
                            onChange={(e) => setPhone(e.target.value)}
                            className="w-full p-3 bg-black/20 border border-white/20 rounded-lg text-white placeholder-gray-400 focus:ring-2 focus:ring-primary-action focus:border-transparent"
                            placeholder="(555) 123-4567"
                            disabled={isLoading}
                        />
                    </div>

                    {success && (
                        <div className="flex items-center gap-2 text-sm text-green-400 animate-in fade-in-0 p-3 bg-green-500/10 rounded-lg">
                            <CheckCircle2 size={16}/> 
                            <span>{success}</span>
                        </div>
                    )}
                    
                    {error && (
                        <div className="flex items-center gap-2 text-sm text-red-400 animate-in fade-in-0 p-3 bg-red-500/10 rounded-lg">
                            <AlertTriangle size={16}/> 
                            <span>{error}</span>
                        </div>
                    )}
                </form>
                
                <footer className="flex justify-end gap-3 p-4 bg-black/20 border-t border-white/10">
                    <Button variant="secondary" onClick={handleClose} disabled={isLoading}>
                        Cancel
                    </Button>
                    <Button onClick={handleSubmit} disabled={isLoading || !fullName.trim()}>
                        {isLoading ? (
                            <>
                                <Loader2 className="w-4 h-4 animate-spin mr-2" />
                                Adding...
                            </>
                        ) : (
                            <>
                                <UserPlus className="w-4 h-4 mr-2" />
                                Add Contact
                            </>
                        )}
                    </Button>
                </footer>
            </motion.div>
        </div>
    );
}; 