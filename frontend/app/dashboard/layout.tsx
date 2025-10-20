/**
 * Dashboard layout with navigation and tenant branding.
 */

'use client';

import { useAuth } from '@/lib/contexts/AuthContext';
import { useRouter, usePathname } from 'next/navigation';
import { useEffect } from 'react';
import Link from 'next/link';

interface NavItem {
  name: string;
  href: string;
  icon: string;
}

const navigation: NavItem[] = [
  { name: 'Dashboard', href: '/dashboard', icon: '📊' },
  { name: 'Analyses', href: '/dashboard/analyses', icon: '📈' },
  { name: 'New Analysis', href: '/dashboard/analyses/new', icon: '➕' },
];

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { user, isAuthenticated, isLoading, logout } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  // Redirect to login if not authenticated
  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/login');
    }
  }, [isLoading, isAuthenticated, router]);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-neutral-50">
        <div className="text-neutral-600">Loading...</div>
      </div>
    );
  }

  if (!isAuthenticated || !user) {
    return null; // Will redirect
  }

  return (
    <div className="min-h-screen bg-neutral-50">
      {/* Top navigation bar */}
      <nav className="bg-white shadow-sm border-b border-neutral-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            {/* Logo and brand */}
            <div className="flex items-center">
              <Link href="/dashboard" className="flex items-center">
                <span className="text-2xl font-bold text-primary-700">
                  Nexus Analyzer
                </span>
              </Link>
            </div>

            {/* User menu */}
            <div className="flex items-center space-x-4">
              <div className="text-sm text-neutral-700">
                <div className="font-medium">{user.full_name}</div>
                <div className="text-neutral-500">{user.email}</div>
              </div>

              <div className="border-l border-neutral-300 pl-4">
                <span className="badge badge-neutral uppercase">{user.role}</span>
              </div>

              <button
                onClick={logout}
                className="text-sm text-neutral-600 hover:text-neutral-900 font-medium"
              >
                Sign out
              </button>
            </div>
          </div>
        </div>
      </nav>

      <div className="flex">
        {/* Sidebar navigation */}
        <aside className="w-64 bg-white border-r border-neutral-200 min-h-[calc(100vh-64px)]">
          <nav className="px-4 py-6 space-y-1">
            {navigation.map((item) => {
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className={`
                    flex items-center px-4 py-3 text-sm font-medium rounded-md transition-colors
                    ${
                      isActive
                        ? 'bg-primary-50 text-primary-700 border-l-4 border-primary-600'
                        : 'text-neutral-700 hover:bg-neutral-50 hover:text-neutral-900'
                    }
                  `}
                >
                  <span className="mr-3 text-lg">{item.icon}</span>
                  {item.name}
                </Link>
              );
            })}
          </nav>

          {/* System status */}
          <div className="px-4 py-6 border-t border-neutral-200 mt-6">
            <div className="text-xs text-neutral-500 uppercase font-semibold mb-2">
              System Status
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-success-500 rounded-full"></div>
              <span className="text-sm text-neutral-600">All systems operational</span>
            </div>
          </div>
        </aside>

        {/* Main content */}
        <main className="flex-1 px-8 py-6">
          {children}
        </main>
      </div>
    </div>
  );
}
