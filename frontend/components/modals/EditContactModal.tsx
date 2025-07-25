// frontend/components/modals/EditContactModal.tsx
'use client';

import { useState, FC, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useAppContext, Client } from '@/context/AppContext';
import { Button } from '@/components/ui/Button';
import { X, Loader2, Edit, CheckCircle2, AlertTriangle, Trash2 } from 'lucide-react';

interface EditContactModalProps {
    isOpen: boolean;
    onClose: () => void;
    client: Client | CommunityMember | null;
    onContactUpdated: () => void;
    onContactDeleted: () => void;
}

// Helper type for community member
interface CommunityMember {
    client_id: string;
    full_name: string;
    user_tags: string[];
    ai_tags?: string[];
    last_interaction_days: number | null;
    health_score: number;
}

export const EditContactModal: FC<EditContactModalProps> = ({ isOpen, onClose, client, onContactUpdated, onContactDeleted }) => {
    const { api } = useAppContext();
    const [fullName, setFullName] = useState('');
    const [email, setEmail] = useState('');
    const [phone, setPhone] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [isDeleting, setIsDeleting] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState<string | null>(null);

    // Initialize form with client data when modal opens
    useEffect(() => {
        if (client) {
            setFullName(client.full_name || '');
            setEmail('email' in client ? client.email || '' : '');
            setPhone('phone' in client ? client.phone || '' : '');
        }
    }, [client]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!client || !fullName.trim()) {
            setError("Full name is required.");
            return;
        }

        setIsLoading(true);
        setError(null);
        setSuccess(null);

        try {
            const clientId = 'id' in client ? client.id : client.client_id;
            const updatedClient = await api.put(`/api/clients/${clientId}`, {
                full_name: fullName.trim(),
                email: email.trim() || undefined,
                phone: phone.trim() || undefined,
            });

            setSuccess(`Successfully updated ${updatedClient.full_name}!`);
            
            // Call the callback to refresh the community list
            onContactUpdated();

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

    const handleDelete = async () => {
        if (!client) return;
        
        if (!confirm(`Are you sure you want to delete ${client.full_name}? This action cannot be undone.`)) {
            return;
        }

        setIsDeleting(true);
        setError(null);

        try {
            const clientId = 'id' in client ? client.id : client.client_id;
            await api.del(`/api/clients/${clientId}`);
            setSuccess(`Successfully deleted ${client.full_name}!`);
            
            // Call the callback to refresh the community list
            onContactDeleted();

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
            setIsDeleting(false);
        }
    };

    const handleClose = () => {
        if (!isLoading && !isDeleting) {
            setFullName('');
            setEmail('');
            setPhone('');
            setError(null);
            setSuccess(null);
            onClose();
        }
    };

    if (!isOpen || !client) return null;

    return (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
            <motion.div 
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                className="bg-brand-primary border border-white/10 rounded-xl shadow-lg w-full max-w-md flex flex-col"
            >
                <header className="flex items-center justify-between p-4 border-b border-white/10">
                    <h2 className="font-bold text-lg text-white flex items-center gap-2">
                        <Edit className="w-5 h-5" />
                        Edit Contact
                    </h2>
                    <Button variant="ghost" size="sm" onClick={handleClose} disabled={isLoading || isDeleting}>
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
                            disabled={isLoading || isDeleting}
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
                            disabled={isLoading || isDeleting}
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
                            disabled={isLoading || isDeleting}
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
                
                <footer className="flex justify-between gap-3 p-4 bg-black/20 border-t border-white/10">
                    <Button 
                        variant="destructive" 
                        onClick={handleDelete} 
                        disabled={isLoading || isDeleting}
                    >
                        {isDeleting ? (
                            <>
                                <Loader2 className="w-4 h-4 animate-spin mr-2" />
                                Deleting...
                            </>
                        ) : (
                            <>
                                <Trash2 className="w-4 h-4 mr-2" />
                                Delete Contact
                            </>
                        )}
                    </Button>
                    
                    <div className="flex gap-3">
                        <Button variant="secondary" onClick={handleClose} disabled={isLoading || isDeleting}>
                            Cancel
                        </Button>
                        <Button onClick={handleSubmit} disabled={isLoading || isDeleting || !fullName.trim()}>
                            {isLoading ? (
                                <>
                                    <Loader2 className="w-4 h-4 animate-spin mr-2" />
                                    Saving...
                                </>
                            ) : (
                                <>
                                    <Edit className="w-4 h-4 mr-2" />
                                    Save Changes
                                </>
                            )}
                        </Button>
                    </div>
                </footer>
            </motion.div>
        </div>
    );
}; 