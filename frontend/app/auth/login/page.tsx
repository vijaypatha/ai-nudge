import { Suspense } from 'react';
import LoginForm from './login-form';
import { Sparkles } from 'lucide-react';

// This is a simple server component that wraps our client component in a Suspense boundary.
export default function LoginPage() {
  return (
    <Suspense fallback={<LoadingSpinner />}>
      <LoginForm />
    </Suspense>
  );
}

// A fallback component to show while the main form is loading.
const LoadingSpinner = () => (
    <div className="min-h-screen w-full flex items-center justify-center bg-gray-900">
        <Sparkles className="w-12 h-12 text-teal-500 animate-spin" />
    </div>
);