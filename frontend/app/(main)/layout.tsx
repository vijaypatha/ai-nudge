// frontend/app/dashboard/layout.tsx
// Using a dedicated layout for the /dashboard route is the standard, most reliable way to enforce rules across an entire section of a Next.js application.
import AuthGuard from '@/components/AuthGuard';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <AuthGuard>{children}</AuthGuard>;
}