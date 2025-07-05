// frontend/components/client-intake/ImportSummary.tsx
"use client";

import React from "react";

interface ImportSummaryProps {
  imported: number;
  merged: number;
}

export const ImportSummary = ({ imported, merged }: ImportSummaryProps) => {
  return (
    <div className="rounded-lg border border-green-300 bg-green-50 p-4 dark:border-green-800 dark:bg-green-950">
      <div className="flex">
        <div className="flex-shrink-0">
          <svg
            className="h-5 w-5 text-green-400"
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 20 20"
            fill="currentColor"
            aria-hidden="true"
          >
            <path
              fillRule="evenodd"
              d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
              clipRule="evenodd"
            />
          </svg>
        </div>
        <div className="ml-3">
          <h3 className="text-sm font-medium text-green-800 dark:text-green-300">
            Import Successful! 🚀
          </h3>
          <div className="mt-2 text-sm text-green-700 dark:text-green-400">
            <p>
              We've added <strong>{imported}</strong> new contacts and merged{" "}
              <strong>{merged}</strong> duplicates to clean up your list.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};