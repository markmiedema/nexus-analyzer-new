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
      case 'processing_csv':
      case 'processing_nexus':
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

  const analyses = data?.items || [];

  return (
    <div>
      {/* Page header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-neutral-900">Dashboard</h1>
        <p className="mt-2 text-neutral-600">
          Manage your sales tax nexus analyses and reports
        </p>
      </div>

      {/* Stats cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="card">
          <div className="card-body">
            <div className="text-sm font-medium text-neutral-500 uppercase">
              Total Analyses
            </div>
            <div className="text-3xl font-bold text-primary-700 mt-2">
              {data?.total || 0}
            </div>
          </div>
        </div>

        <div className="card">
          <div className="card-body">
            <div className="text-sm font-medium text-neutral-500 uppercase">
              Completed
            </div>
            <div className="text-3xl font-bold text-success-700 mt-2">
              {analyses.filter((a) => a.status === 'completed').length}
            </div>
          </div>
        </div>

        <div className="card">
          <div className="card-body">
            <div className="text-sm font-medium text-neutral-500 uppercase">
              In Progress
            </div>
            <div className="text-3xl font-bold text-warning-700 mt-2">
              {
                analyses.filter(
                  (a) =>
                    a.status === 'processing_csv' ||
                    a.status === 'processing_nexus' ||
                    a.status === 'uploading_csv'
                ).length
              }
            </div>
          </div>
        </div>
      </div>

      {/* Recent analyses */}
      <div className="card">
        <div className="card-header flex justify-between items-center">
          <h2 className="text-xl font-semibold">Recent Analyses</h2>
          <Link href="/dashboard/analyses/new" className="btn btn-primary">
            + New Analysis
          </Link>
        </div>

        <div className="card-body p-0">
          {analyses.length === 0 ? (
            <div className="text-center py-12">
              <div className="text-neutral-400 text-5xl mb-4">📊</div>
              <h3 className="text-lg font-medium text-neutral-900 mb-2">
                No analyses yet
              </h3>
              <p className="text-neutral-600 mb-6">
                Get started by creating your first nexus analysis
              </p>
              <Link href="/dashboard/analyses/new" className="btn btn-primary">
                Create Analysis
              </Link>
            </div>
          ) : (
            <table className="min-w-full divide-y divide-neutral-200">
              <thead className="bg-neutral-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-neutral-500 uppercase tracking-wider">
                    Client
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-neutral-500 uppercase tracking-wider">
                    Period
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-neutral-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-neutral-500 uppercase tracking-wider">
                    Created
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-neutral-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-neutral-200">
                {analyses.map((analysis) => (
                  <tr key={analysis.analysis_id} className="hover:bg-neutral-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-neutral-900">
                        {analysis.client_name}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-neutral-600">
                      {format(new Date(analysis.period_start), 'MMM d, yyyy')} -{' '}
                      {format(new Date(analysis.period_end), 'MMM d, yyyy')}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`badge ${getStatusBadgeClass(analysis.status)}`}>
                        {formatStatus(analysis.status)}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-neutral-600">
                      {format(new Date(analysis.created_at), 'MMM d, yyyy')}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <Link
                        href={`/dashboard/analyses/${analysis.analysis_id}`}
                        className="text-primary-600 hover:text-primary-900"
                      >
                        View
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
}
