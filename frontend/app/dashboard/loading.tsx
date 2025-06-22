// frontend/app/dashboard/loading.tsx
//Purpose: To provide an automatic Suspense boundary and loading UI for the dashboard page, resolving the Next.js production build error.


'use client';

import { Sparkles } from "lucide-react";

export default function Loading() {
  // You can add any UI you want here, like a skeleton screen or a spinner.
  // We'll reuse the spinner from our main page's initial load state.
  return (
    <div className="flex flex-col justify-center items-center h-screen text-brand-text-muted bg-brand-dark">
      <Sparkles className="w-10 h-10 text-brand-accent animate-spin mb-4" />
      <p className="text-xl font-medium">Loading Dashboard...</p>
    </div>
  );
}