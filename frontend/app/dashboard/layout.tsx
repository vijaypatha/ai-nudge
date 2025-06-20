import React from 'react';
import { Home, Users, Briefcase, MessageSquare, Clock, Settings, LogOut, Zap } from 'lucide-react'; // Using lucide-react for icons
import Link from 'next/link';

const SidebarLink = ({ href, icon: Icon, children }: { href: string; icon: React.ElementType; children: React.ReactNode }) => (
  <Link href={href} legacyBehavior>
    <a className="flex items-center space-x-3 text-brand-gray hover:text-brand-white hover:bg-brand-primary/50 px-4 py-3 rounded-lg transition-colors duration-200">
      <Icon size={20} />
      <span>{children}</span>
    </a>
  </Link>
);

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex h-screen bg-gray-100">
      {/* Sidebar */}
      <aside className="w-64 bg-brand-primary text-brand-white p-6 flex flex-col justify-between shadow-2xl">
        <div>
          <div className="flex items-center space-x-2 mb-10">
            <Zap size={32} className="text-brand-secondary" />
            <h1 className="text-2xl font-bold text-brand-white">AI Nudge</h1>
          </div>
          <nav className="space-y-3">
            <SidebarLink href="/dashboard" icon={Home}>Dashboard</SidebarLink>
            <SidebarLink href="/dashboard/clients" icon={Users}>Clients</SidebarLink>
            <SidebarLink href="/dashboard/properties" icon={Briefcase}>Properties</SidebarLink>
            <SidebarLink href="/dashboard/inbox" icon={MessageSquare}>Inbox</SidebarLink>
            <SidebarLink href="/dashboard/scheduled" icon={Clock}>Scheduled</SidebarLink>
          </nav>
        </div>
        <div>
          <SidebarLink href="/dashboard/settings" icon={Settings}>Settings</SidebarLink>
          <button
            onClick={() => alert('Logout functionality to be implemented!')}
            className="w-full flex items-center space-x-3 text-brand-gray hover:text-brand-white hover:bg-brand-primary/50 px-4 py-3 rounded-lg transition-colors duration-200 mt-2"
          >
            <LogOut size={20} />
            <span>Logout</span>
          </button>
        </div>
      </aside>

      {/* Main content area */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Top header (optional, could be part of specific pages) */}
        <header className="bg-brand-white shadow-md p-4">
          <div className="flex justify-between items-center">
            <h2 className="text-xl font-semibold text-brand-primary">Dashboard Overview</h2>
            {/* Add user profile, notifications etc. here */}
            <div className="text-sm text-gray-600">Welcome, Realtor!</div>
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-x-hidden overflow-y-auto bg-gray-200 p-6">
          {children}
        </main>
      </div>
    </div>
  );
}
