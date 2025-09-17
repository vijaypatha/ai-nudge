// FILE: frontend/components/settings/RoleManager.tsx (NEW FILE)

'use client';

import { useState, useEffect } from 'react';
import { useAppContext } from '@/context/AppContext';
import { Button } from '@/components/ui/Button';
import { X, Plus, Loader2, CheckCircle, AlertTriangle } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export const RoleManager = () => {
    const { api, clientRoles, refreshClientRoles } = useAppContext();
    const [roles, setRoles] = useState<string[]>([]);
    const [newRole, setNewRole] = useState('');
    const [status, setStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle');
    const [error, setError] = useState('');

    useEffect(() => {
        setRoles(clientRoles);
    }, [clientRoles]);

    const handleAddRole = () => {
        if (newRole && !roles.includes(newRole)) {
            setRoles([...roles, newRole]);
            setNewRole('');
        }
    };

    const handleRemoveRole = (roleToRemove: string) => {
        if (roles.length <= 1) {
            setError("You must have at least one client role.");
            setTimeout(() => setError(''), 3000);
            return;
        }
        setRoles(roles.filter(role => role !== roleToRemove));
    };

    const handleSave = async () => {
        setStatus('loading');
        setError('');
        try {
            await api.put('/api/settings/roles', { roles });
            setStatus('success');
            if (refreshClientRoles) {
                refreshClientRoles();
            }
            setTimeout(() => setStatus('idle'), 2000);
        } catch (err: any) {
            setStatus('error');
            setError(err.message || "Failed to save roles.");
        }
    };

    return (
        <div className="bg-brand-primary border border-white/10 rounded-lg shadow-md w-full max-w-2xl">
            <div className="p-6 border-b border-white/10">
                <h2 className="text-xl font-bold text-white">Manage Client Roles</h2>
                <p className="text-sm text-gray-400 mt-1">Customize the client roles available when adding a new contact.</p>
            </div>
            <div className="p-6 space-y-4">
                <div className="space-y-2">
                    {roles.map((role, index) => (
                        <motion.div
                            key={index}
                            layout
                            initial={{ opacity: 0, y: -10 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, x: -20 }}
                            transition={{ duration: 0.2 }}
                            className="flex items-center justify-between bg-black/20 p-2 rounded-md"
                        >
                            <span className="text-white ml-2">{role}</span>
                            <Button variant="ghost" size="sm" onClick={() => handleRemoveRole(role)}>
                                <X className="w-4 h-4" />
                            </Button>
                        </motion.div>
                    ))}
                </div>
                <div className="flex gap-2">
                    <input
                        type="text"
                        value={newRole}
                        onChange={(e) => setNewRole(e.target.value)}
                        placeholder="Add a new role..."
                        onKeyDown={(e) => e.key === 'Enter' && handleAddRole()}
                        className="flex-1 p-3 bg-black/20 border border-white/20 rounded-lg text-white placeholder-gray-400 focus:ring-2 focus:ring-primary-action focus:border-transparent"
                    />
                    <Button onClick={handleAddRole} variant="secondary">
                        <Plus className="w-4 h-4 mr-2" />
                        Add
                    </Button>
                </div>
            </div>
            <div className="flex justify-between items-center p-4 bg-black/20 border-t border-white/10 rounded-b-lg">
                <div className="text-sm h-5">
                    <AnimatePresence>
                        {status === 'success' && (
                            <motion.div initial={{ opacity: 0}} animate={{ opacity: 1}} exit={{ opacity: 0}} className="flex items-center gap-2 text-green-400">
                                <CheckCircle size={16} /> Roles saved successfully!
                            </motion.div>
                        )}
                        {status === 'error' && (
                             <motion.div initial={{ opacity: 0}} animate={{ opacity: 1}} exit={{ opacity: 0}} className="flex items-center gap-2 text-red-400">
                                <AlertTriangle size={16} /> {error}
                            </motion.div>
                        )}
                    </AnimatePresence>
                </div>
                <Button onClick={handleSave} disabled={status === 'loading'}>
                    {status === 'loading' ? (
                        <>
                            <Loader2 className="w-4 h-4 animate-spin mr-2" />
                            Saving...
                        </>
                    ) : (
                        'Save Changes'
                    )}
                </Button>
            </div>
        </div>
    );
};
