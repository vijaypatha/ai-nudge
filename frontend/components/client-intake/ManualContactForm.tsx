// frontend/components/client-intake/ManualContactForm.tsx
"use client";

import React from "react";

export const ManualContactForm = () => {
  // We'll add full form handling with react-hook-form later.
  // For now, this is a visual placeholder consistent with the design.
  return (
    <div className="rounded-lg border bg-card text-card-foreground shadow-sm p-6">
       <h3 className="text-lg font-semibold leading-none tracking-tight">Add Manually</h3>
       <p className="text-sm text-muted-foreground mt-1 mb-4">
        Add a single contact directly.
      </p>
      <form className="space-y-4">
        <div>
          <label htmlFor="full_name" className="block text-sm font-medium text-gray-700">Full Name</label>
          <input type="text" id="full_name" disabled className="mt-1 block w-full rounded-md border-gray-300 shadow-sm sm:text-sm p-2 bg-gray-100" />
        </div>
        <div>
          <label htmlFor="email" className="block text-sm font-medium text-gray-700">Email</label>
          <input type="email" id="email" disabled className="mt-1 block w-full rounded-md border-gray-300 shadow-sm sm:text-sm p-2 bg-gray-100" />
        </div>
         <div>
          <label htmlFor="phone" className="block text-sm font-medium text-gray-700">Phone</label>
          <input type="tel" id="phone" disabled className="mt-1 block w-full rounded-md border-gray-300 shadow-sm sm:text-sm p-2 bg-gray-100" />
        </div>
        <button type="submit" disabled className="inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 bg-secondary text-secondary-foreground hover:bg-secondary/80 h-10 px-4 py-2 w-full">
            Add Contact (Coming Soon)
        </button>
      </form>
    </div>
  );
};