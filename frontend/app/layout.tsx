import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "AI Nudge CRM",
  description: "Your AI-powered assistant for Realtor communications",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${inter.className} antialiased`}>
        {/* Common header or navigation could go here if shared across all pages (marketing and app) */}
        {/* For this MVP, we'll keep layouts distinct for marketing vs. dashboard via nested layouts or page-specific headers */}
        {children}
      </body>
    </html>
  );
}
