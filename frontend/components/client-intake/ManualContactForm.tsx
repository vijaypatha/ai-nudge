// frontend/components/client-intake/ManualContactForm.tsx
"use client";

import React, { useState } from "react";
import { useAppContext } from "@/context/AppContext";
// Using lucide-react icons for better visual feedback
import { CheckCircle2, AlertTriangle, Loader2 } from 'lucide-react';

export const ManualContactForm = () => {
  const { api } = useAppContext();

  // State for form inputs
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  
  // State for managing the form's submission status
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
      const newClient = await api.addManualClient({
        full_name: fullName,
        email: email || undefined, // Send undefined if the string is empty
        phone: phone || undefined,
      });

      // On success, show a confirmation message and clear the form
      setSuccess(`Successfully added ${newClient.full_name}!`);
      setFullName('');
      setEmail('');
      setPhone('');

      // Hide the success message after 4 seconds
      setTimeout(() => setSuccess(null), 4000);

    } catch (err: any) {
      // On failure, display a helpful error message
      const errorMessage = err.response?.data?.detail || "An unknown error occurred.";
      setError(errorMessage);
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="rounded-lg border bg-card text-card-foreground shadow-sm p-6">
       <h3 className="text-lg font-semibold leading-none tracking-tight">Add Manually</h3>
       <p className="text-sm text-muted-foreground mt-1 mb-4">
        Add a single contact directly.
      </p>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="full_name" className="block text-sm font-medium text-gray-300">Full Name</label>
          <input 
            type="text" 
            id="full_name"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
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
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full input-field mt-1"
            placeholder="alex@example.com"
          />
        </div>
         <div>
          <label htmlFor="phone" className="block text-sm font-medium text-gray-300">Phone</label>
          <input 
            type="tel" 
            id="phone" 
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
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

        {/* Dynamic Success and Error Messages */}
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
  );
};