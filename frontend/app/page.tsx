// frontend/app/page.tsx
"use client";

import { useState, useEffect, useRef } from 'react';
import Image from 'next/image';
import Link from 'next/link';
import { useSearchParams, useRouter } from 'next/navigation';
import clsx from 'clsx';
// --- MODIFIED: Use the new, robust path alias ---
import { useAppContext } from '@/context/AppContext';
import type { Property, Message, Conversation, ScheduledMessage, Client, MatchedClient, CampaignBriefing } from '@/context/AppContext';
import { MessageCircleHeart, Zap, Users, MessageSquare, Paperclip, Phone, Video, Sparkles, Search, Send, Calendar, Gift, Star, X, Edit2, Info, User as UserIcon, Menu, Tag, Plus, BrainCircuit, Loader2, ArrowRight, Route, CheckSquare, MapPin } from "lucide-react";
import { motion } from "framer-motion";

const testimonials = [
  { name: "Reggie Scott", title: "Scott & Co. Realty", img: "https://images.unsplash.com/photo-1573497491208-6b1acb260507?auto=format&fit=crop&w=300&h=300&q=80", quote: "While I'm focused on closing deals for one client, AI Nudge is effortlessly connecting with all my other prospects and past clients. That's real ROI." },
  { name: "Dr. Eliza Stone", title: "CareBridge Therapy", img: "https://images.unsplash.com/photo-1517841905240-472988babdf9?auto=format&fit=crop&w=300&h=300&q=80", quote: "AI Nudge lets me stay in touch in a way that feels authentic and saves me so much time. It's a game-changer for my practice." }
];

// Animation variants for Framer Motion
const fadeInFromBottom = {
  initial: { opacity: 0, y: 30 },
  whileInView: { opacity: 1, y: 0 },
  viewport: { once: true },
  transition: { duration: 0.6, ease: "easeInOut" as const }
};

export default function LandingPage() {
  return (
    <main className="min-h-screen w-full flex flex-col justify-start bg-gray-900 text-gray-200 bg-subtle-pattern">
      <header className="fixed top-0 left-0 right-0 z-50 bg-gray-900/80 backdrop-blur-lg border-b border-white/10">
        <div className="container mx-auto px-6 py-4 flex justify-between items-center">
          <Image src="/AI Nudge Logo.png" alt="AI Nudge Logo" width={150} height={30} />
          <div className="flex items-center gap-4">
            <Link href="/auth/login" className="text-gray-300 hover:text-white transition-colors text-sm font-semibold">Log In</Link>
            <Link href="/auth/login?action=signup" className="btn-primary flex items-center gap-2 group text-sm">
              <span>Try It Free</span> <ArrowRight className="w-4 h-4 transition-transform group-hover:translate-x-1" />
            </Link>
          </div>
        </div>
      </header>

      <section className="w-full flex flex-col items-center justify-center pt-40 pb-24 md:pt-48 md:pb-32 text-center px-4 relative">
        <div className="absolute inset-0 bg-gradient-to-b from-gray-900 via-gray-900/80 to-transparent z-0"></div>
        <motion.div {...fadeInFromBottom} transition={{...fadeInFromBottom.transition, delay: 0.2}} className="relative z-10">
          <h1 className="text-4xl sm:text-5xl md:text-6xl lg:text-7xl font-extrabold text-white mb-6 leading-tight">
            Client Engagement, <br /> Back to Basics.
          </h1>
          <h2 className="text-2xl md:text-3xl lg:text-4xl text-gray-100 mb-8 leading-tight max-w-3xl mx-auto font-semibold">
            <span className="text-gradient-animated">Powered by AI.</span>
          </h2>
        </motion.div>
        <motion.p {...fadeInFromBottom} transition={{...fadeInFromBottom.transition, delay: 0.4}} className="text-lg md:text-xl text-gray-400 mb-12 leading-relaxed max-w-2xl mx-auto relative z-10">
          We help your customers remember you with timely, personal messages, automatically and in your authentic style.
        </motion.p>
        <motion.div {...fadeInFromBottom} transition={{...fadeInFromBottom.transition, delay: 0.6}}>
          <Link href="/auth/login?action=signup" passHref>
            <button className="btn-primary btn-lg font-semibold">Start Your Free Trial</button>
          </Link>
        </motion.div>
      </section>

      <section id="how-it-works" className="py-20 md:py-28 bg-gray-900/50">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div {...fadeInFromBottom} className="text-center mb-14 md:mb-20">
            <h2 className="text-3xl md:text-4xl lg:text-5xl font-bold tracking-tight text-white">
              Your GPS for <span className="text-gradient-animated">Staying Top-of-Mind</span>
            </h2>
            <p className="mt-5 text-lg md:text-xl text-gray-400 max-w-2xl mx-auto">
              Navigate client engagement effortlessly. We guide you every step of the way.
            </p>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 lg:gap-10">
            <motion.div {...fadeInFromBottom} transition={{...fadeInFromBottom.transition, delay: 0.2}} className="card p-6 md:p-8 rounded-xl text-center flex flex-col items-center">
                <div className="p-4 bg-gradient-to-br from-blue-500/10 to-teal-500/10 rounded-full mb-6"><MapPin className="w-10 h-10 text-blue-400" /></div>
                <h3 className="text-xl font-semibold text-white mb-3">1. Set Destination</h3>
                <p className="text-base text-gray-400 flex-grow leading-relaxed">Define your goals, teach AI Nudge your style, and add your contacts.</p>
            </motion.div>
            <motion.div {...fadeInFromBottom} transition={{...fadeInFromBottom.transition, delay: 0.4}} className="card p-6 md:p-8 rounded-xl text-center flex flex-col items-center">
              <div className="p-4 bg-gradient-to-br from-teal-500/10 to-emerald-500/10 rounded-full mb-6"><Route className="w-10 h-10 text-teal-400" /></div>
              <h3 className="text-xl font-semibold text-white mb-3">2. See The Route</h3>
              <p className="text-base text-gray-400 flex-grow leading-relaxed">Our AI drafts personalized nudges in your voice, mapped to your goals.</p>
            </motion.div>
            <motion.div {...fadeInFromBottom} transition={{...fadeInFromBottom.transition, delay: 0.6}} className="card p-6 md:p-8 rounded-xl text-center flex flex-col items-center">
                <div className="p-4 bg-gradient-to-br from-emerald-500/10 to-green-500/10 rounded-full mb-6"><CheckSquare className="w-10 h-10 text-emerald-400" /></div>
                <h3 className="text-xl font-semibold text-white mb-3">3. Follow or Adjust</h3>
                <p className="text-base text-gray-400 flex-grow leading-relaxed">Review the plan. Let it run automatically, or make adjustments as needed.</p>
            </motion.div>
          </div>
        </div>
      </section>
      
      <section className="py-20 md:py-28">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8">
            <motion.div {...fadeInFromBottom} className="text-center mb-14 md:mb-20">
                <h2 className="text-3xl md:text-4xl lg:text-5xl font-bold mb-4 text-white">Trusted by Professionals Like You</h2>
            </motion.div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8 lg:gap-10">
                {testimonials.map((person, i) => (
                    <motion.div {...fadeInFromBottom} transition={{...fadeInFromBottom.transition, delay: i * 0.2 + 0.2}} key={i} className="card p-6 md:p-8 text-center group flex flex-col items-center rounded-xl">
                        <Image src={person.img} alt={person.name} width={100} height={100} className="rounded-full mx-auto mb-6 object-cover border-4 border-white/20 shadow-lg" />
                        <h3 className="font-semibold text-xl text-white mb-1">{person.name}</h3>
                        <p className="text-sm text-gray-400 mb-5">{person.title}</p>
                        <p className="text-md italic text-gray-300 leading-relaxed">"{person.quote}"</p>
                    </motion.div>
                ))}
            </div>
        </div>
      </section>

      <footer className="text-base text-center space-y-8 border-t border-white/10 pt-16 pb-12 bg-black">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8">
            <motion.p {...fadeInFromBottom} className="text-gray-400 max-w-lg mx-auto">Ready to build stronger connections and grow your business? Start your free trial today.</motion.p>
            <motion.div {...fadeInFromBottom} transition={{...fadeInFromBottom.transition, delay: 0.2}} className="mt-8">
                <Link href="/auth/login?action=signup" passHref><button className="btn-primary text-lg px-8 py-3 font-semibold">Get Started</button></Link>
            </motion.div>
        </div>
      </footer>
    </main>
  );
}