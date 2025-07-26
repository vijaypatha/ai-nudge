// frontend/components/client-intake/ManualContactForm.tsx
// DEFINITIVE FIX: Replaces the non-existent 'addManualClient' with the correct 'api.post' method.
"use client";

import React, { useState, useEffect } from "react";
import { motion } from 'framer-motion';
import { useAppContext } from "@/context/AppContext";
import { CheckCircle2, AlertTriangle, Loader2, UserPlus } from 'lucide-react';
import { ACTIVE_THEME } from '@/utils/theme';
import Confetti from 'react-confetti';

export const ManualContactForm = ({ onContactAdded }: { onContactAdded?: (client: any) => void }) => {
  const { api } = useAppContext();
  const [formData, setFormData] = useState({
    full_name: '',
    email: '',
    phone: '',
    company: '',
    notes: ''
  });
  const [isLoading, setIsLoading] = useState(false);
  const [success, setSuccess] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showConfetti, setShowConfetti] = useState(false);
  const [windowSize, setWindowSize] = useState({ width: 0, height: 0 });

  // Add window size tracking for confetti
  useEffect(() => {
    const handleResize = () => setWindowSize({ width: window.innerWidth, height: window.innerHeight });
    window.addEventListener('resize', handleResize);
    handleResize();
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const newClient = await api.post('/api/clients', formData);
      
      // Show confetti for every successful contact addition
      setShowConfetti(true);
      setTimeout(() => setShowConfetti(false), 7000); // Hide after 7 seconds
      
      setSuccess(`Successfully added ${newClient.full_name}!`);
      setFormData({ full_name: '', email: '', phone: '', company: '', notes: '' });
      
      if (onContactAdded) {
        onContactAdded(newClient);
      }
      
      // Auto-hide success message
      setTimeout(() => setSuccess(null), 4000);
    } catch (err: any) {
      setError(err.message || 'Failed to add contact');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <>
      {/* Confetti for successful contact additions */}
      {showConfetti && (
        <Confetti
          width={windowSize.width}
          height={windowSize.height}
          recycle={false}
          numberOfPieces={600}
          tweenDuration={7000}
          colors={[
            ACTIVE_THEME.primary.from,
            ACTIVE_THEME.primary.to,
            ACTIVE_THEME.accent,
            ACTIVE_THEME.action,
            '#ffffff'
          ]}
        />
      )}

      <div className="bg-white/5 border border-white/10 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <UserPlus className="w-5 h-5" />
          Add New Contact
        </h3>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="full_name" className="block text-sm font-medium text-gray-300">Full Name</label>
            <input 
              type="text" 
              id="full_name"
              value={formData.full_name}
              onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
              className="w-full input-field mt-1" 
              placeholder="e.g., Alex Martinez"
              required
            />
          </div>
          <div>
            <label htmlFor="email" className="block text-sm font-medium text-gray-300">Email</label>
            <input 
              type="email" 
              id="email" 
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              className="w-full input-field mt-1"
              placeholder="alex@example.com"
            />
          </div>
           <div>
            <label htmlFor="phone" className="block text-sm font-medium text-gray-300">Phone</label>
            <input 
              type="tel" 
              id="phone" 
              value={formData.phone}
              onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
              className="w-full input-field mt-1"
              placeholder="(555) 123-4567"
            />
          </div>
          <button 
              type="submit" 
              disabled={isLoading} 
              className="w-full btn-secondary flex items-center justify-center gap-2"
          >
            {isLoading ? (
              <>
                <Loader2 size={16} className="animate-spin" />
                <span>Adding...</span>
              </>
            ) : (
              'Add Contact'
            )}
          </button>
          {success && (
            <div className="mt-4 flex items-center gap-2 text-sm text-green-400 animate-in fade-in-0">
              <CheckCircle2 size={16}/> 
              <span>{success}</span>
            </div>
          )}
          {error && (
            <div className="mt-4 flex items-center gap-2 text-sm text-red-400 animate-in fade-in-0">
              <AlertTriangle size={16}/> 
              <span>{error}</span>
            </div>
          )}
        </form>
      </div>
    </>
  );
};