"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import Image from "next/image";

export default function TermsOfService() {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  return (
    <main
      className={`min-h-screen w-full flex flex-col justify-start transition-opacity duration-1000 ${
        mounted ? "opacity-100" : "opacity-0"
      } bg-gradient-to-b from-black via-gray-900 to-gray-800 text-gray-200`}
    >
      {/* Header */}
      <section className="w-full bg-animated-gradient flex flex-col items-center justify-center py-16 md:py-20 text-center px-4">
        <div className="max-w-4xl mx-auto">
          <div className="flex justify-center mb-8">
            <Link href="/">
              <Image
                src="/AI Nudge Logo.png"
                alt="AI Nudge Logo"
                width={400}
                height={80}
                priority
              />
            </Link>
          </div>
          <h1 className="text-3xl md:text-4xl lg:text-5xl font-bold text-white mb-4">
            Terms of Service
          </h1>
          <p className="text-lg text-gray-400">
            Last updated: {new Date().toLocaleDateString()}
          </p>
        </div>
      </section>

      {/* Content */}
      <section className="py-16 bg-gray-900">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8 max-w-4xl">
          <div className="prose prose-invert prose-lg max-w-none">
            <div className="space-y-8">
              <div>
                <h2 className="text-2xl font-bold text-white mb-4">1. Acceptance of Terms</h2>
                <p className="text-gray-300 leading-relaxed">
                  By accessing and using AI Nudge ("the Service"), you accept and agree to be bound by the terms and provision of this agreement. If you do not agree to abide by the above, please do not use this service.
                </p>
              </div>

              <div>
                <h2 className="text-2xl font-bold text-white mb-4">2. Description of Service</h2>
                <p className="text-gray-300 leading-relaxed">
                  AI Nudge provides an AI-powered client engagement platform that helps businesses maintain relationships with their clients through personalized messaging and automated follow-ups. The service includes SMS messaging, contact management, and AI-generated content suggestions.
                </p>
              </div>

              <div>
                <h2 className="text-2xl font-bold text-white mb-4">3. User Accounts</h2>
                <p className="text-gray-300 leading-relaxed">
                  You are responsible for maintaining the confidentiality of your account and password. You agree to accept responsibility for all activities that occur under your account or password.
                </p>
              </div>

              <div>
                <h2 className="text-2xl font-bold text-white mb-4">4. Acceptable Use</h2>
                <p className="text-gray-300 leading-relaxed">
                  You agree not to use the Service to:
                </p>
                <ul className="list-disc list-inside text-gray-300 ml-6 mt-2 space-y-1">
                  <li>Send spam, unsolicited messages, or engage in any form of harassment</li>
                  <li>Violate any applicable laws or regulations</li>
                  <li>Infringe upon the rights of others</li>
                  <li>Attempt to gain unauthorized access to the Service or other users' accounts</li>
                  <li>Use the Service for any illegal or unauthorized purpose</li>
                </ul>
              </div>

              <div>
                <h2 className="text-2xl font-bold text-white mb-4">5. Privacy and Data Protection</h2>
                <p className="text-gray-300 leading-relaxed">
                  Your privacy is important to us. Please review our Privacy Policy, which also governs your use of the Service, to understand our practices regarding the collection and use of your information.
                </p>
              </div>

              <div>
                <h2 className="text-2xl font-bold text-white mb-4">6. Payment Terms</h2>
                <p className="text-gray-300 leading-relaxed">
                  Subscription fees are billed in advance on a monthly or annual basis. All fees are non-refundable except as required by law. We reserve the right to change our pricing with 30 days' notice.
                </p>
              </div>

              <div>
                <h2 className="text-2xl font-bold text-white mb-4">7. Termination</h2>
                <p className="text-gray-300 leading-relaxed">
                  You may terminate your account at any time by contacting our support team. We may terminate or suspend your account immediately, without prior notice, for conduct that we believe violates these Terms of Service or is harmful to other users or the Service.
                </p>
              </div>

              <div>
                <h2 className="text-2xl font-bold text-white mb-4">8. Limitation of Liability</h2>
                <p className="text-gray-300 leading-relaxed">
                  In no event shall AI Nudge be liable for any indirect, incidental, special, consequential, or punitive damages, including without limitation, loss of profits, data, use, goodwill, or other intangible losses.
                </p>
              </div>

              <div>
                <h2 className="text-2xl font-bold text-white mb-4">9. Changes to Terms</h2>
                <p className="text-gray-300 leading-relaxed">
                  We reserve the right to modify these terms at any time. We will notify users of any material changes via email or through the Service. Your continued use of the Service after such changes constitutes acceptance of the new terms.
                </p>
              </div>

              <div>
                <h2 className="text-2xl font-bold text-white mb-4">10. Contact Information</h2>
                <p className="text-gray-300 leading-relaxed">
                  If you have any questions about these Terms of Service, please contact us at support@ainudge.com.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="text-base text-center space-y-8 border-t border-white/10 pt-16 pb-12 bg-black">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-center mb-6">
            <Image src="/AI Nudge Logo.png" alt="AI Nudge Footer Logo" width={220} height={44} />
          </div>
          <p className="text-gray-400">Small Nudges. Smart Guidance. Stronger Connections.</p>
          <div className="mt-10 space-x-6 font-medium">
            <Link href="/terms" className="text-gray-400 hover:text-white underline transition-colors">Terms of Service</Link>
            <Link href="/privacy" className="text-gray-400 hover:text-white underline transition-colors">Privacy Policy</Link>
          </div>
          <p className="mt-8 text-gray-400">&copy; {new Date().getFullYear()} AI Nudge. All rights reserved.</p>
        </div>
      </footer>
    </main>
  );
} 