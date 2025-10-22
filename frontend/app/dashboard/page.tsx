/**
 * Dashboard home page - showing list of recent analyses.
 */

'use client';

import { useQuery } from '@tanstack/react-query';
import { analysesApi, Analysis } from '@/lib/api';
import Link from 'next/link';
import { format } from 'date-fns';

export default function DashboardPage() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['analyses'],
    queryFn: () => analysesApi.list(),
  });

  const getStatusBadgeClass = (status: Analysis['status']) => {
    switch (status) {
      case 'completed':
        return 'badge-success';
      case 'failed':
        return 'badge-danger';
      case 'processing':
      case 'pending':
        return 'badge-warning';
      default:
        return 'badge-neutral';
    }
  };

  const formatStatus = (status: Analysis['status']) => {
    return status.replace(/_/g, ' ').toUpperCase();
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-neutral-600">Loading analyses...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-danger-50 border border-danger-200 text-danger-700 px-4 py-3 rounded-md">
        Failed to load analyses. Please try again later.
      </div>
    );
  }

  const analyses = data || [];

  return (
    <div className="space-y-8">
      {/* Hero Section */}
      <div className="relative overflow-hidden bg-gradient-to-br from-primary-600 via-primary-700 to-primary-800 rounded-2xl shadow-xl">
        <div className="absolute inset-0 bg-grid-white/10"></div>
        <div className="relative px-8 py-12 md:py-16">
          <div className="max-w-3xl">
            <h1 className="text-4xl md:text-5xl font-bold text-white mb-4">
              Sales Tax Nexus Analyzer
            </h1>
            <p className="text-lg text-primary-100 mb-8">
              Analyze your sales data across all 50 states and discover your tax obligations in minutes.
            </p>
            <div className="flex flex-wrap gap-4">
              <Link
                href="/dashboard/analyses/new"
                className="inline-flex items-center px-6 py-3 bg-white text-primary-700 font-semibold rounded-lg hover:bg-primary-50 transition-all shadow-lg hover:shadow-xl transform hover:-translate-y-0.5"
              >
                <span className="text-2xl mr-2">✨</span>
                Start New Analysis
              </Link>
              {analyses.length > 0 && (
                <button className="inline-flex items-center px-6 py-3 bg-primary-500/30 text-white font-semibold rounded-lg hover:bg-primary-500/40 transition-all backdrop-blur-sm">
                  <span className="text-2xl mr-2">📊</span>
                  View All Reports
                </button>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Stats cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Total Analyses Card */}
        <div className="card hover:shadow-lg transition-all duration-300 group cursor-pointer">
          <div className="card-body">
            <div className="flex items-center justify-between mb-3">
              <div className="text-sm font-medium text-neutral-500 uppercase tracking-wide">
                Total Analyses
              </div>
              <div className="w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center group-hover:scale-110 transition-transform">
                <span className="text-2xl">📁</span>
              </div>
            </div>
            <div className="text-4xl font-bold text-primary-700">
              {analyses.length}
            </div>
            <div className="mt-2 text-xs text-neutral-500">
              {analyses.length === 0 ? 'Start your first analysis' : 'All time'}
            </div>
          </div>
        </div>

        {/* Completed Card */}
        <div className="card hover:shadow-lg transition-all duration-300 group cursor-pointer">
          <div className="card-body">
            <div className="flex items-center justify-between mb-3">
              <div className="text-sm font-medium text-neutral-500 uppercase tracking-wide">
                Completed
              </div>
              <div className="w-12 h-12 bg-success-50 rounded-lg flex items-center justify-center group-hover:scale-110 transition-transform">
                <span className="text-2xl">✅</span>
              </div>
            </div>
            <div className="text-4xl font-bold text-success-700">
              {analyses.filter((a) => a.status === 'completed').length}
            </div>
            <div className="mt-2 text-xs text-neutral-500">
              {analyses.length > 0
                ? `${Math.round((analyses.filter((a) => a.status === 'completed').length / analyses.length) * 100)}% success rate`
                : 'No completed analyses yet'
              }
            </div>
          </div>
        </div>

        {/* In Progress Card */}
        <div className="card hover:shadow-lg transition-all duration-300 group cursor-pointer">
          <div className="card-body">
            <div className="flex items-center justify-between mb-3">
              <div className="text-sm font-medium text-neutral-500 uppercase tracking-wide">
                In Progress
              </div>
              <div className="w-12 h-12 bg-warning-50 rounded-lg flex items-center justify-center group-hover:scale-110 transition-transform">
                <span className="text-2xl">⏳</span>
              </div>
            </div>
            <div className="text-4xl font-bold text-warning-700">
              {
                analyses.filter(
                  (a) =>
                    a.status === 'processing' ||
                    a.status === 'pending'
                ).length
              }
            </div>
            <div className="mt-2 text-xs text-neutral-500">
              {analyses.filter((a) => a.status === 'processing' || a.status === 'pending').length > 0
                ? 'Currently processing'
                : 'All analyses complete'
              }
            </div>
          </div>
        </div>
      </div>

      {/* Recent analyses */}
      <div className="card animate-fadeIn">
        <div className="card-header flex justify-between items-center">
          <div>
            <h2 className="text-xl font-semibold">Recent Analyses</h2>
            <p className="text-sm text-neutral-500 mt-1">View and manage your nexus analysis history</p>
          </div>
          {analyses.length > 0 && (
            <Link href="/dashboard/analyses/new" className="btn btn-primary">
              <span className="text-lg mr-1">+</span>
              New Analysis
            </Link>
          )}
        </div>

        <div className="card-body p-0">
          {analyses.length === 0 ? (
            <div className="text-center py-16 px-6">
              <div className="w-24 h-24 mx-auto mb-6 bg-gradient-to-br from-primary-100 to-primary-200 rounded-2xl flex items-center justify-center">
                <span className="text-5xl">📊</span>
              </div>
              <h3 className="text-xl font-semibold text-neutral-900 mb-2">
                Ready to get started?
              </h3>
              <p className="text-neutral-600 mb-8 max-w-md mx-auto">
                Upload your sales data and we&apos;ll analyze your nexus obligations across all 50 states automatically.
              </p>
              <Link
                href="/dashboard/analyses/new"
                className="inline-flex items-center px-8 py-4 bg-gradient-to-r from-primary-600 to-primary-700 text-white font-semibold rounded-xl hover:from-primary-700 hover:to-primary-800 transition-all shadow-lg hover:shadow-xl transform hover:-translate-y-0.5"
              >
                <span className="text-2xl mr-3">✨</span>
                Create Your First Analysis
                <span className="ml-2">→</span>
              </Link>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-neutral-200">
                <thead className="bg-neutral-50">
                  <tr>
                    <th className="px-6 py-4 text-left text-xs font-semibold text-neutral-600 uppercase tracking-wider">
                      Analysis ID
                    </th>
                    <th className="px-6 py-4 text-left text-xs font-semibold text-neutral-600 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-4 text-left text-xs font-semibold text-neutral-600 uppercase tracking-wider">
                      Created
                    </th>
                    <th className="px-6 py-4 text-left text-xs font-semibold text-neutral-600 uppercase tracking-wider">
                      Completed
                    </th>
                    <th className="px-6 py-4 text-right text-xs font-semibold text-neutral-600 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-neutral-200">
                  {analyses.map((analysis, index) => (
                    <tr
                      key={analysis.analysis_id}
                      className="hover:bg-primary-50/30 transition-colors cursor-pointer"
                      style={{ animationDelay: `${index * 50}ms` }}
                    >
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <div className="w-10 h-10 bg-primary-100 rounded-lg flex items-center justify-center mr-3">
                            <span className="text-lg">📄</span>
                          </div>
                          <div className="text-sm">
                            <div className="font-medium text-neutral-900">
                              {analysis.analysis_id.slice(0, 8)}...
                            </div>
                            <div className="text-xs text-neutral-500">
                              Analysis Report
                            </div>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`badge ${getStatusBadgeClass(analysis.status)} text-xs font-semibold px-3 py-1.5`}>
                          {formatStatus(analysis.status)}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-neutral-900">
                          {format(new Date(analysis.created_at), 'MMM d, yyyy')}
                        </div>
                        <div className="text-xs text-neutral-500">
                          {format(new Date(analysis.created_at), 'h:mm a')}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {analysis.completed_at ? (
                          <div>
                            <div className="text-sm text-neutral-900">
                              {format(new Date(analysis.completed_at), 'MMM d, yyyy')}
                            </div>
                            <div className="text-xs text-neutral-500">
                              {format(new Date(analysis.completed_at), 'h:mm a')}
                            </div>
                          </div>
                        ) : (
                          <span className="text-sm text-neutral-400">Pending</span>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        <Link
                          href={`/dashboard/analyses/${analysis.analysis_id}`}
                          className="inline-flex items-center px-4 py-2 text-primary-600 hover:text-primary-700 hover:bg-primary-50 rounded-lg transition-colors font-semibold"
                        >
                          View Details
                          <span className="ml-1">→</span>
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
