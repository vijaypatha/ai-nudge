"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import Image from "next/image";

export default function PrivacyPolicy() {
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
            Privacy Policy
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
                <h2 className="text-2xl font-bold text-white mb-4">1. Information We Collect</h2>
                <p className="text-gray-300 leading-relaxed mb-4">
                  We collect information you provide directly to us, such as when you create an account, use our services, or contact us for support. We also collect certain information when you connect your Google account to our service.
                </p>
                <h3 className="text-xl font-semibold text-white mb-2">Personal Information:</h3>
                <ul className="list-disc list-inside text-gray-300 ml-6 space-y-1">
                  <li>Name, email address, and phone number</li>
                  <li>Business information and contact details</li>
                  <li>Client contact information you upload</li>
                  <li>Communication preferences and settings</li>
                </ul>
                <h3 className="text-xl font-semibold text-white mb-2 mt-4">Information from your Google Account:</h3>
                <p className="text-gray-300 leading-relaxed mb-4">
                  When you sign in to AI Nudge using Google, we may access certain information from your Google account with your permission, including:
                </p>
                <ul className="list-disc list-inside text-gray-300 ml-6 space-y-1">
                  <li>Your name and email address</li>
                  <li>Your Google profile picture</li>
                </ul>
                <h3 className="text-xl font-semibold text-white mb-2 mt-4">Usage Information:</h3>
                <ul className="list-disc list-inside text-gray-300 ml-6 space-y-1">
                  <li>How you interact with our platform</li>
                  <li>Message content and delivery status</li>
                  <li>Analytics and performance data</li>
                </ul>
              </div>

              <div>
                <h2 className="text-2xl font-bold text-white mb-4">2. How We Use Your Information</h2>
                <p className="text-gray-300 leading-relaxed mb-4">
                  We use the information we collect to:
                </p>
                <ul className="list-disc list-inside text-gray-300 ml-6 space-y-1">
                  <li>Provide, maintain, and improve our services</li>
                  <li>Process and deliver messages to your clients</li>
                  <li>Generate personalized AI content suggestions</li>
                  <li>Send you service-related communications</li>
                  <li>Respond to your questions and support requests</li>
                  <li>Ensure compliance with legal obligations</li>
                </ul>
              </div>

              <div>
                <h2 className="text-2xl font-bold text-white mb-4">3. Information Sharing</h2>
                <p className="text-gray-300 leading-relaxed mb-4">
                  We do not sell, trade, or otherwise transfer your personal information to third parties except in the following circumstances:
                </p>
                <ul className="list-disc list-inside text-gray-300 ml-6 space-y-1">
                  <li>With your explicit consent</li>
                  <li>To service providers who assist in operating our platform</li>
                  <li>To comply with legal requirements or protect our rights</li>
                  <li>In connection with a business transfer or merger</li>
                </ul>
              </div>

              <div>
                <h2 className="text-2xl font-bold text-white mb-4">4. Data Security</h2>
                <p className="text-gray-300 leading-relaxed">
                  We implement appropriate technical and organizational measures to protect your personal information against unauthorized access, alteration, disclosure, or destruction. However, no method of transmission over the internet is 100% secure.
                </p>
              </div>

              <div>
                <h2 className="text-2xl font-bold text-white mb-4">5. Data Retention</h2>
                <p className="text-gray-300 leading-relaxed">
                  We retain your personal information for as long as necessary to provide our services and comply with legal obligations. You may request deletion of your account and associated data at any time.
                </p>
              </div>

              <div>
                <h2 className="text-2xl font-bold text-white mb-4">6. Your Rights</h2>
                <p className="text-gray-300 leading-relaxed mb-4">
                  You have the right to:
                </p>
                <ul className="list-disc list-inside text-gray-300 ml-6 space-y-1">
                  <li>Access and review your personal information</li>
                  <li>Correct inaccurate or incomplete data</li>
                  <li>Request deletion of your personal information</li>
                  <li>Opt out of marketing communications</li>
                  <li>Export your data in a portable format</li>
                </ul>
              </div>

              <div>
                <h2 className="text-2xl font-bold text-white mb-4">7. Cookies and Tracking</h2>
                <p className="text-gray-300 leading-relaxed">
                  We use cookies and similar technologies to enhance your experience, analyze usage patterns, and improve our services. You can control cookie settings through your browser preferences.
                </p>
              </div>

              <div>
                <h2 className="text-2xl font-bold text-white mb-4">8. Third-Party Services</h2>
                <p className="text-gray-300 leading-relaxed">
                  Our service may integrate with third-party services (such as SMS providers and AI services). These services have their own privacy policies, and we encourage you to review them.
                </p>
              </div>

              <div>
                <h2 className="text-2xl font-bold text-white mb-4">9. Children's Privacy</h2>
                <p className="text-gray-300 leading-relaxed">
                  Our service is not intended for children under 13 years of age. We do not knowingly collect personal information from children under 13.
                </p>
              </div>

              <div>
                <h2 className="text-2xl font-bold text-white mb-4">10. International Transfers</h2>
                <p className="text-gray-300 leading-relaxed">
                  Your information may be transferred to and processed in countries other than your own. We ensure appropriate safeguards are in place to protect your data in accordance with this policy.
                </p>
              </div>

              <div>
                <h2 className="text-2xl font-bold text-white mb-4">11. Changes to This Policy</h2>
                <p className="text-gray-300 leading-relaxed">
                  We may update this Privacy Policy from time to time. We will notify you of any material changes by posting the new policy on our website and updating the "Last updated" date.
                </p>
              </div>

              <div>
                <h2 className="text-2xl font-bold text-white mb-4">12. Contact Us</h2>
                <p className="text-gray-300 leading-relaxed">
                  If you have any questions about this Privacy Policy or our data practices, please contact us at privacy@ainudge.com.
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