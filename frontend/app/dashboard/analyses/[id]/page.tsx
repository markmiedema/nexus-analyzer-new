/**
 * Analysis detail page displaying nexus results, liability estimates, and reports.
 */

'use client';

import { useQuery } from '@tanstack/react-query';
import { analysesApi, nexusApi, liabilityApi } from '@/lib/api';
import { AnalysisStatusTracker } from '@/components/AnalysisStatusTracker';
import { ReportViewer } from '@/components/ReportViewer';
import { useState } from 'react';
import Link from 'next/link';

interface PageProps {
  params: Promise<{ id: string }>;
}

export default function AnalysisDetailPage({ params }: PageProps) {
  const [activeTab, setActiveTab] = useState<'overview' | 'nexus' | 'liability' | 'reports'>('overview');
  const [resolvedParams, setResolvedParams] = useState<{ id: string } | null>(null);

  // Resolve params Promise
  params.then(setResolvedParams);

  const analysisId = resolvedParams?.id || '';

  // Fetch analysis
  const { data: analysis, isLoading: analysisLoading } = useQuery({
    queryKey: ['analysis', analysisId],
    queryFn: () => analysesApi.get(analysisId),
    enabled: !!analysisId,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      // Refetch every 5 seconds if processing
      return status && ['uploading_csv', 'processing_csv', 'processing_nexus'].includes(status)
        ? 5000
        : false;
    },
  });

  // Fetch nexus results
  const { data: nexusResults } = useQuery({
    queryKey: ['nexus-results', analysisId],
    queryFn: () => nexusApi.getResults(analysisId),
    enabled: !!analysisId && analysis?.status === 'completed',
  });

  // Fetch liability estimates
  const { data: liabilityEstimates } = useQuery({
    queryKey: ['liability-estimates', analysisId],
    queryFn: () => liabilityApi.getEstimates(analysisId),
    enabled: !!analysisId && analysis?.status === 'completed',
  });

  // Compute nexus summary from results
  const nexusSummary = nexusResults ? {
    total_nexus_states: nexusResults.length,
    physical_nexus_count: nexusResults.filter(r => r.has_physical_nexus).length,
    economic_nexus_count: nexusResults.filter(r => r.has_economic_nexus).length,
  } : null;

  // Compute liability summary from estimates
  const liabilitySummary = liabilityEstimates ? {
    total_liability_mid: liabilityEstimates.reduce((sum, est) => sum + (est.estimated_liability || 0), 0),
    high_risk_count: liabilityEstimates.filter(est => est.estimated_liability > 10000).length,
    top_5_states: liabilityEstimates
      .sort((a, b) => (b.estimated_liability || 0) - (a.estimated_liability || 0))
      .slice(0, 5)
      .map(est => ({ state: est.state, liability: est.estimated_liability || 0 })),
  } : null;

  if (!analysisId) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-neutral-600">Loading...</div>
      </div>
    );
  }

  if (analysisLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-neutral-600">Loading analysis...</div>
      </div>
    );
  }

  if (!analysis) {
    return (
      <div className="text-center py-12">
        <h2 className="text-2xl font-bold text-neutral-900 mb-4">Analysis Not Found</h2>
        <Link href="/dashboard" className="btn btn-primary">
          Back to Dashboard
        </Link>
      </div>
    );
  }

  const isCompleted = analysis.status === 'completed';

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  const getStatusBadgeClass = (status: string) => {
    if (status.includes('nexus')) return 'badge-success';
    if (status === 'close_to_threshold') return 'badge-warning';
    return 'badge-neutral';
  };

  const getRiskBadgeClass = (risk: string) => {
    if (risk === 'high') return 'badge-danger';
    if (risk === 'medium') return 'badge-warning';
    return 'badge-neutral';
  };

  return (
    <div>
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-neutral-900">Sales Tax Nexus Analysis</h1>
            <p className="mt-1 text-neutral-600">
              Created: {new Date(analysis.created_at).toLocaleDateString()}
              {analysis.completed_at && ` • Completed: ${new Date(analysis.completed_at).toLocaleDateString()}`}
            </p>
          </div>
          <Link href="/dashboard" className="btn btn-secondary">
            ← Back to Dashboard
          </Link>
        </div>
      </div>

      {/* Status Tracker */}
      {!isCompleted && (
        <div className="mb-6">
          <AnalysisStatusTracker status={analysis.status} />
        </div>
      )}

      {/* Tabs */}
      {isCompleted && (
        <>
          <div className="border-b border-neutral-200 mb-6">
            <nav className="-mb-px flex space-x-8">
              {[
                { id: 'overview', label: 'Overview' },
                { id: 'nexus', label: 'Nexus Results' },
                { id: 'liability', label: 'Liability Estimates' },
                { id: 'reports', label: 'Reports' },
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as typeof activeTab)}
                  className={`
                    py-4 px-1 border-b-2 font-medium text-sm transition-colors
                    ${
                      activeTab === tab.id
                        ? 'border-primary-500 text-primary-600'
                        : 'border-transparent text-neutral-500 hover:text-neutral-700 hover:border-neutral-300'
                    }
                  `}
                >
                  {tab.label}
                </button>
              ))}
            </nav>
          </div>

          {/* Tab Content */}
          <div className="space-y-6">
            {activeTab === 'overview' && (
              <>
                {/* Summary Cards */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div className="card">
                    <div className="card-body">
                      <div className="text-sm font-medium text-neutral-500 uppercase mb-2">
                        States with Nexus
                      </div>
                      <div className="text-3xl font-bold text-primary-700">
                        {nexusSummary?.total_nexus_states || 0}
                      </div>
                      {nexusSummary && (
                        <div className="text-sm text-neutral-600 mt-2">
                          {nexusSummary.physical_nexus_count} Physical • {nexusSummary.economic_nexus_count} Economic
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="card">
                    <div className="card-body">
                      <div className="text-sm font-medium text-neutral-500 uppercase mb-2">
                        Estimated Liability
                      </div>
                      <div className="text-3xl font-bold text-warning-700">
                        {liabilitySummary ? formatCurrency(liabilitySummary.total_liability_mid) : '$0'}
                      </div>
                      <div className="text-sm text-neutral-600 mt-2">Mid-range estimate</div>
                    </div>
                  </div>

                  <div className="card">
                    <div className="card-body">
                      <div className="text-sm font-medium text-neutral-500 uppercase mb-2">
                        High Risk States
                      </div>
                      <div className="text-3xl font-bold text-danger-700">
                        {liabilitySummary?.high_risk_count || 0}
                      </div>
                      <div className="text-sm text-neutral-600 mt-2">Require immediate attention</div>
                    </div>
                  </div>
                </div>

                {/* Top States */}
                {liabilitySummary && liabilitySummary.top_5_states.length > 0 && (
                  <div className="card">
                    <div className="card-header">
                      <h3 className="text-lg font-semibold">Top States by Liability</h3>
                    </div>
                    <div className="card-body p-0">
                      <table className="min-w-full">
                        <thead className="bg-neutral-50">
                          <tr>
                            <th className="px-6 py-3 text-left text-xs font-medium text-neutral-500 uppercase">
                              State
                            </th>
                            <th className="px-6 py-3 text-right text-xs font-medium text-neutral-500 uppercase">
                              Estimated Liability
                            </th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-neutral-200">
                          {liabilitySummary.top_5_states.map((state) => (
                            <tr key={state.state}>
                              <td className="px-6 py-4 whitespace-nowrap font-medium">{state.state}</td>
                              <td className="px-6 py-4 whitespace-nowrap text-right font-semibold text-primary-700">
                                {formatCurrency(state.liability)}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}
              </>
            )}

            {activeTab === 'nexus' && (
              <div className="card">
                <div className="card-header">
                  <h3 className="text-lg font-semibold">Nexus Determination Results</h3>
                </div>
                <div className="card-body p-0">
                  {!nexusResults || nexusResults.length === 0 ? (
                    <div className="text-center py-12">
                      <p className="text-neutral-600">No nexus results available</p>
                    </div>
                  ) : (
                    <table className="min-w-full">
                      <thead className="bg-neutral-50">
                        <tr>
                          <th className="px-6 py-3 text-left text-xs font-medium text-neutral-500 uppercase">
                            State
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-neutral-500 uppercase">
                            Status
                          </th>
                          <th className="px-6 py-3 text-right text-xs font-medium text-neutral-500 uppercase">
                            Sales
                          </th>
                          <th className="px-6 py-3 text-right text-xs font-medium text-neutral-500 uppercase">
                            Transactions
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-neutral-500 uppercase">
                            Recommendation
                          </th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-neutral-200">
                        {nexusResults.map((result) => (
                          <tr key={result.result_id} className="hover:bg-neutral-50">
                            <td className="px-6 py-4 whitespace-nowrap font-medium">{result.state}</td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <span className={`badge ${getStatusBadgeClass(result.nexus_status)}`}>
                                {result.nexus_status.replace(/_/g, ' ').toUpperCase()}
                              </span>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-right">
                              {formatCurrency(result.total_sales)}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-right">
                              {result.transaction_count.toLocaleString()}
                            </td>
                            <td className="px-6 py-4 text-sm text-neutral-600">{result.recommendation}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  )}
                </div>
              </div>
            )}

            {activeTab === 'liability' && (
              <div className="card">
                <div className="card-header">
                  <h3 className="text-lg font-semibold">Liability Estimates by State</h3>
                </div>
                <div className="card-body p-0">
                  {!liabilityEstimates || liabilityEstimates.length === 0 ? (
                    <div className="text-center py-12">
                      <p className="text-neutral-600">No liability estimates available</p>
                    </div>
                  ) : (
                    <table className="min-w-full">
                      <thead className="bg-neutral-50">
                        <tr>
                          <th className="px-6 py-3 text-left text-xs font-medium text-neutral-500 uppercase">
                            State
                          </th>
                          <th className="px-6 py-3 text-right text-xs font-medium text-neutral-500 uppercase">
                            Low
                          </th>
                          <th className="px-6 py-3 text-right text-xs font-medium text-neutral-500 uppercase">
                            Mid
                          </th>
                          <th className="px-6 py-3 text-right text-xs font-medium text-neutral-500 uppercase">
                            High
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-neutral-500 uppercase">
                            Risk
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-neutral-500 uppercase">
                            Recommendation
                          </th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-neutral-200">
                        {liabilityEstimates.map((estimate) => (
                          <tr key={estimate.estimate_id} className="hover:bg-neutral-50">
                            <td className="px-6 py-4 whitespace-nowrap font-medium">{estimate.state}</td>
                            <td className="px-6 py-4 whitespace-nowrap text-right text-sm">
                              {formatCurrency(estimate.estimated_liability_low)}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-right font-semibold text-primary-700">
                              {formatCurrency(estimate.estimated_liability_mid)}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-right text-sm">
                              {formatCurrency(estimate.estimated_liability_high)}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <span className={`badge ${getRiskBadgeClass(estimate.risk_level)}`}>
                                {estimate.risk_level.toUpperCase()}
                              </span>
                            </td>
                            <td className="px-6 py-4 text-sm text-neutral-600">{estimate.recommendation}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  )}
                </div>
              </div>
            )}

            {activeTab === 'reports' && <ReportViewer analysisId={analysisId} />}
          </div>
        </>
      )}
    </div>
  );
}
