/**
 * Report viewer/download component.
 */

'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { reportsApi, getErrorMessage } from '@/lib/api';
import { useState } from 'react';

interface ReportViewerProps {
  analysisId: string;
}

export function ReportViewer({ analysisId }: ReportViewerProps) {
  const queryClient = useQueryClient();
  const [error, setError] = useState<string>('');
  const [downloadingReportId, setDownloadingReportId] = useState<string>('');

  // Fetch reports
  const { data: reports, isLoading } = useQuery({
    queryKey: ['reports', analysisId],
    queryFn: () => reportsApi.list(analysisId),
  });

  // Generate summary report
  const generateSummaryMutation = useMutation({
    mutationFn: () => reportsApi.generate(analysisId, 'summary'),
    onSuccess: () => {
      setError('');
      // Refetch reports after a delay to allow generation to complete
      setTimeout(() => {
        queryClient.invalidateQueries({ queryKey: ['reports', analysisId] });
      }, 5000);
    },
    onError: (err) => {
      setError(getErrorMessage(err));
    },
  });

  // Generate detailed report
  const generateDetailedMutation = useMutation({
    mutationFn: () => reportsApi.generate(analysisId, 'detailed'),
    onSuccess: () => {
      setError('');
      // Refetch reports after a delay to allow generation to complete
      setTimeout(() => {
        queryClient.invalidateQueries({ queryKey: ['reports', analysisId] });
      }, 5000);
    },
    onError: (err) => {
      setError(getErrorMessage(err));
    },
  });

  // Download report
  const handleDownload = async (reportId: string, reportType: string) => {
    setDownloadingReportId(reportId);
    try {
      const blob = await reportsApi.download(reportId);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `nexus_analysis_${reportType}_${new Date().toISOString().split('T')[0]}.pdf`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setDownloadingReportId('');
    }
  };


  const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  if (isLoading) {
    return (
      <div className="card">
        <div className="card-body text-center py-8">
          <div className="text-neutral-600">Loading reports...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="card">
      <div className="card-header flex justify-between items-center">
        <h3 className="text-lg font-semibold">Reports</h3>
        <div className="space-x-2">
          <button
            onClick={() => generateSummaryMutation.mutate()}
            disabled={generateSummaryMutation.isPending}
            className="btn btn-secondary text-sm"
          >
            {generateSummaryMutation.isPending ? 'Generating...' : '📄 Generate Summary'}
          </button>
          <button
            onClick={() => generateDetailedMutation.mutate()}
            disabled={generateDetailedMutation.isPending}
            className="btn btn-secondary text-sm"
          >
            {generateDetailedMutation.isPending ? 'Generating...' : '📊 Generate Detailed'}
          </button>
        </div>
      </div>

      <div className="card-body">
        {/* Error display */}
        {error && (
          <div className="mb-4 bg-danger-50 border border-danger-200 text-danger-700 px-4 py-3 rounded-md text-sm">
            {error}
          </div>
        )}

        {/* Generation in progress message */}
        {(generateSummaryMutation.isPending || generateDetailedMutation.isPending) && (
          <div className="mb-4 bg-primary-50 border border-primary-200 text-primary-700 px-4 py-3 rounded-md text-sm">
            <div className="flex items-center">
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary-600 mr-2"></div>
              Report generation in progress. This may take a few moments...
            </div>
          </div>
        )}

        {/* Reports list */}
        {!reports || reports.length === 0 ? (
          <div className="text-center py-8">
            <div className="text-neutral-400 text-5xl mb-4">📄</div>
            <h4 className="text-lg font-medium text-neutral-900 mb-2">No reports generated yet</h4>
            <p className="text-neutral-600 mb-6">
              Generate a summary or detailed report to get started
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {reports.map((report) => (
              <div
                key={report.report_id}
                className="border border-neutral-200 rounded-md p-4 hover:bg-neutral-50 transition-colors"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    <div className="text-3xl">
                      {report.report_type === 'summary' ? '📄' : '📊'}
                    </div>
                    <div>
                      <div className="font-medium text-neutral-900">
                        {report.report_type === 'summary'
                          ? 'Executive Summary Report'
                          : 'Detailed Analysis Report'}
                      </div>
                      <div className="text-sm text-neutral-600 mt-1">
                        Generated: {formatDate(report.created_at)}
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => handleDownload(report.report_id, report.report_type)}
                      disabled={downloadingReportId === report.report_id}
                      className="btn btn-primary text-sm"
                    >
                      {downloadingReportId === report.report_id ? (
                        <>
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                          Downloading...
                        </>
                      ) : (
                        <>⬇️ Download</>
                      )}
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
