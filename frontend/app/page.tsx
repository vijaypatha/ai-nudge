import Link from 'next/link';

export default function MarketingPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-brand-primary to-gray-900 text-brand-white flex flex-col items-center justify-center p-8">
      <header className="text-center mb-12">
        <h1 className="text-5xl font-bold mb-4">Welcome to AI Nudge CRM</h1>
        <p className="text-xl text-brand-accent mb-8">
          Supercharge your real estate business with AI-powered communication.
        </p>
        <Link href="/dashboard" legacyBehavior>
          <a className="bg-brand-secondary hover:bg-brand-accent text-brand-primary font-bold py-3 px-8 rounded-lg text-lg shadow-lg transition duration-300 ease-in-out transform hover:scale-105">
            Access Dashboard
          </a>
        </Link>
      </header>

      <main className="grid md:grid-cols-3 gap-8 text-center max-w-4xl">
        <div className="bg-white/10 p-6 rounded-lg shadow-xl">
          <h2 className="text-2xl font-semibold mb-3 text-brand-secondary">Smart Responses</h2>
          <p className="text-brand-gray">Let AI draft replies to client inquiries instantly.</p>
        </div>
        <div className="bg-white/10 p-6 rounded-lg shadow-xl">
          <h2 className="text-2xl font-semibold mb-3 text-brand-secondary">Client Management</h2>
          <p className="text-brand-gray">Keep track of your clients and properties effortlessly.</p>
        </div>
        <div className="bg-white/10 p-6 rounded-lg shadow-xl">
          <h2 className="text-2xl font-semibold mb-3 text-brand-secondary">Scheduled Messaging</h2>
          <p className="text-brand-gray">Plan your follow-ups and important communications.</p>
        </div>
      </main>

      <footer className="mt-16 text-center text-brand-gray">
        <p>&copy; {new Date().getFullYear()} AI Nudge Inc. All rights reserved.</p>
      </footer>
    </div>
  );
}
