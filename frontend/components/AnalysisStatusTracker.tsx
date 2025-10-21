/**
 * Analysis status tracker component showing progress.
 */

'use client';

import { Analysis } from '@/lib/api';

type AnalysisStatus = Analysis['status'];

interface AnalysisStatusTrackerProps {
  status: AnalysisStatus;
  errorMessage?: string;
}

interface StatusStep {
  id: AnalysisStatus;
  label: string;
  description: string;
}

const STATUS_STEPS: StatusStep[] = [
  {
    id: 'pending',
    label: 'Pending',
    description: 'Analysis queued for processing',
  },
  {
    id: 'processing',
    label: 'Processing',
    description: 'Analyzing transactions and determining nexus',
  },
  {
    id: 'completed',
    label: 'Completed',
    description: 'Analysis complete',
  },
  {
    id: 'failed',
    label: 'Failed',
    description: 'Analysis encountered an error',
  },
];

export function AnalysisStatusTracker({ status, errorMessage }: AnalysisStatusTrackerProps) {
  const currentStepIndex = STATUS_STEPS.findIndex((step) => step.id === status);
  const isFailed = status === 'failed';

  const getStepStatus = (stepIndex: number): 'completed' | 'current' | 'upcoming' | 'failed' => {
    if (isFailed && stepIndex === currentStepIndex) return 'failed';
    if (stepIndex < currentStepIndex) return 'completed';
    if (stepIndex === currentStepIndex) return 'current';
    return 'upcoming';
  };

  return (
    <div className="card">
      <div className="card-header">
        <h3 className="text-lg font-semibold">Analysis Progress</h3>
      </div>
      <div className="card-body">
        {/* Status message */}
        {isFailed ? (
          <div className="mb-6 bg-danger-50 border border-danger-200 text-danger-700 px-4 py-3 rounded-md">
            <div className="font-semibold mb-1">Analysis Failed</div>
            <div className="text-sm">{errorMessage || 'An error occurred during processing'}</div>
          </div>
        ) : status === 'completed' ? (
          <div className="mb-6 bg-success-50 border border-success-200 text-success-700 px-4 py-3 rounded-md">
            <div className="font-semibold">Analysis Complete</div>
            <div className="text-sm">Your nexus analysis has been completed successfully</div>
          </div>
        ) : (
          <div className="mb-6 bg-primary-50 border border-primary-200 text-primary-700 px-4 py-3 rounded-md">
            <div className="font-semibold">Processing...</div>
            <div className="text-sm">Your analysis is currently being processed</div>
          </div>
        )}

        {/* Progress steps */}
        <nav aria-label="Progress">
          <ol className="space-y-4">
            {STATUS_STEPS.map((step, stepIdx) => {
              const stepStatus = getStepStatus(stepIdx);

              return (
                <li key={step.id} className="relative">
                  <div className="flex items-start">
                    {/* Step indicator */}
                    <div className="relative flex h-10 w-10 flex-shrink-0 items-center justify-center">
                      {stepStatus === 'completed' ? (
                        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary-600">
                          <span className="text-white font-bold">✓</span>
                        </div>
                      ) : stepStatus === 'failed' ? (
                        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-danger-600">
                          <span className="text-white font-bold">✕</span>
                        </div>
                      ) : stepStatus === 'current' ? (
                        <div className="flex h-10 w-10 items-center justify-center rounded-full border-2 border-primary-600 bg-white">
                          <div className="h-3 w-3 rounded-full bg-primary-600 animate-pulse"></div>
                        </div>
                      ) : (
                        <div className="flex h-10 w-10 items-center justify-center rounded-full border-2 border-neutral-300 bg-white">
                          <span className="text-neutral-400 font-semibold">{stepIdx + 1}</span>
                        </div>
                      )}

                      {/* Connecting line */}
                      {stepIdx !== STATUS_STEPS.length - 1 && (
                        <div className="absolute top-10 left-5 -ml-px h-full w-0.5 bg-neutral-200">
                          <div
                            className={`
                              h-full transition-all
                              ${stepStatus === 'completed' ? 'bg-primary-600' : ''}
                            `}
                          />
                        </div>
                      )}
                    </div>

                    {/* Step content */}
                    <div className="ml-4 flex-1">
                      <div
                        className={`
                          text-sm font-medium
                          ${
                            stepStatus === 'completed' || stepStatus === 'current'
                              ? 'text-primary-600'
                              : stepStatus === 'failed'
                              ? 'text-danger-600'
                              : 'text-neutral-500'
                          }
                        `}
                      >
                        {step.label}
                      </div>
                      <div className="text-sm text-neutral-600 mt-1">{step.description}</div>

                      {/* Current step spinner */}
                      {stepStatus === 'current' && !isFailed && (
                        <div className="mt-2 flex items-center text-xs text-primary-600">
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary-600 mr-2"></div>
                          In progress...
                        </div>
                      )}
                    </div>
                  </div>
                </li>
              );
            })}
          </ol>
        </nav>

        {/* Retry button for failed analyses */}
        {isFailed && (
          <div className="mt-6 pt-6 border-t border-neutral-200">
            <button className="btn btn-primary w-full">
              Retry Analysis
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
