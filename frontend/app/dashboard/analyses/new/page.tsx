/**
 * New Analysis wizard page with multi-step form.
 */

'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useMutation } from '@tanstack/react-query';
import { analysesApi, businessProfileApi, getErrorMessage } from '@/lib/api';
import { CSVUpload } from '@/components/CSVUpload';
import { BusinessProfileForm, BusinessProfileFormData } from '@/components/BusinessProfileForm';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

type Step = 'basic' | 'csv' | 'profile' | 'processing';

const basicInfoSchema = z.object({
  client_name: z.string().min(1, 'Client name is required'),
  period_start: z.string().min(1, 'Start date is required'),
  period_end: z.string().min(1, 'End date is required'),
});

type BasicInfoFormData = z.infer<typeof basicInfoSchema>;

export default function NewAnalysisPage() {
  const router = useRouter();
  const [currentStep, setCurrentStep] = useState<Step>('basic');
  const [analysisId, setAnalysisId] = useState<string>('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [error, setError] = useState<string>('');

  // Step 1: Basic info form
  const {
    register,
    handleSubmit: handleBasicSubmit,
    formState: { errors: basicErrors },
  } = useForm<BasicInfoFormData>({
    resolver: zodResolver(basicInfoSchema),
  });

  // Create analysis mutation
  const createAnalysisMutation = useMutation({
    mutationFn: analysesApi.create,
    onSuccess: (data) => {
      setAnalysisId(data.analysis_id);
      setCurrentStep('csv');
      setError('');
    },
    onError: (err) => {
      setError(getErrorMessage(err));
    },
  });

  // Upload CSV mutation
  const uploadCsvMutation = useMutation({
    mutationFn: ({ analysisId, file }: { analysisId: string; file: File }) =>
      analysesApi.uploadCsv(analysisId, file),
    onSuccess: () => {
      setCurrentStep('profile');
      setError('');
    },
    onError: (err) => {
      setError(getErrorMessage(err));
    },
  });

  // Create business profile mutation
  const createProfileMutation = useMutation({
    mutationFn: ({ analysisId, data }: { analysisId: string; data: BusinessProfileFormData }) =>
      businessProfileApi.createOrUpdate(analysisId, {
        ...data,
        marketplace_names: data.marketplace_names?.[0]
          ? (data.marketplace_names[0] as string).split(',').map((s) => s.trim())
          : undefined,
      }),
    onSuccess: () => {
      setCurrentStep('processing');
      // Redirect to analysis detail page after a short delay
      setTimeout(() => {
        router.push(`/dashboard/analyses/${analysisId}`);
      }, 2000);
    },
    onError: (err) => {
      setError(getErrorMessage(err));
    },
  });

  // Step handlers
  const onBasicInfoSubmit = (data: BasicInfoFormData) => {
    createAnalysisMutation.mutate(data);
  };

  const onFileSelect = (file: File) => {
    setSelectedFile(file);
  };

  const onCsvContinue = () => {
    if (!selectedFile) {
      setError('Please select a CSV file');
      return;
    }
    uploadCsvMutation.mutate({ analysisId, file: selectedFile });
  };

  const onProfileSubmit = (data: BusinessProfileFormData) => {
    createProfileMutation.mutate({ analysisId, data });
  };

  const steps = [
    { id: 'basic', name: 'Basic Info', completed: currentStep !== 'basic' },
    { id: 'csv', name: 'Upload CSV', completed: ['profile', 'processing'].includes(currentStep) },
    { id: 'profile', name: 'Business Profile', completed: currentStep === 'processing' },
  ];

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-neutral-900">Create New Analysis</h1>
        <p className="mt-2 text-neutral-600">
          Follow the steps below to set up your sales tax nexus analysis
        </p>
      </div>

      {/* Progress Steps */}
      <div className="mb-8">
        <nav aria-label="Progress">
          <ol className="flex items-center">
            {steps.map((step, stepIdx) => (
              <li
                key={step.id}
                className={`relative ${
                  stepIdx !== steps.length - 1 ? 'pr-8 sm:pr-20 flex-1' : ''
                }`}
              >
                <div className="flex items-center">
                  <div
                    className={`
                      relative flex h-8 w-8 items-center justify-center rounded-full
                      ${
                        step.completed
                          ? 'bg-primary-600'
                          : step.id === currentStep
                          ? 'border-2 border-primary-600 bg-white'
                          : 'border-2 border-neutral-300 bg-white'
                      }
                    `}
                  >
                    {step.completed ? (
                      <span className="text-white font-bold">✓</span>
                    ) : (
                      <span
                        className={`
                          ${step.id === currentStep ? 'text-primary-600' : 'text-neutral-500'}
                          font-semibold
                        `}
                      >
                        {stepIdx + 1}
                      </span>
                    )}
                  </div>
                  <span
                    className={`
                      ml-3 text-sm font-medium
                      ${
                        step.completed || step.id === currentStep
                          ? 'text-primary-600'
                          : 'text-neutral-500'
                      }
                    `}
                  >
                    {step.name}
                  </span>
                </div>

                {stepIdx !== steps.length - 1 && (
                  <div className="absolute top-4 left-4 -ml-px mt-0.5 h-0.5 w-full bg-neutral-300">
                    <div
                      className={`h-full ${step.completed ? 'bg-primary-600' : ''}`}
                      style={{ width: step.completed ? '100%' : '0%' }}
                    />
                  </div>
                )}
              </li>
            ))}
          </ol>
        </nav>
      </div>

      {/* Error Display */}
      {error && (
        <div className="mb-6 bg-danger-50 border border-danger-200 text-danger-700 px-4 py-3 rounded-md">
          {error}
        </div>
      )}

      {/* Step Content */}
      {currentStep === 'basic' && (
        <div className="card">
          <div className="card-header">
            <h2 className="text-xl font-semibold">Analysis Information</h2>
          </div>
          <div className="card-body">
            <form onSubmit={handleBasicSubmit(onBasicInfoSubmit)} className="space-y-4">
              <div>
                <label htmlFor="client_name" className="block text-sm font-medium text-neutral-700">
                  Client Name *
                </label>
                <input
                  id="client_name"
                  type="text"
                  {...register('client_name')}
                  className={`mt-1 input ${basicErrors.client_name ? 'input-error' : ''}`}
                  placeholder="Company Name"
                />
                {basicErrors.client_name && (
                  <p className="mt-1 text-sm text-danger-600">{basicErrors.client_name.message}</p>
                )}
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label htmlFor="period_start" className="block text-sm font-medium text-neutral-700">
                    Period Start Date *
                  </label>
                  <input
                    id="period_start"
                    type="date"
                    {...register('period_start')}
                    className={`mt-1 input ${basicErrors.period_start ? 'input-error' : ''}`}
                  />
                  {basicErrors.period_start && (
                    <p className="mt-1 text-sm text-danger-600">{basicErrors.period_start.message}</p>
                  )}
                </div>

                <div>
                  <label htmlFor="period_end" className="block text-sm font-medium text-neutral-700">
                    Period End Date *
                  </label>
                  <input
                    id="period_end"
                    type="date"
                    {...register('period_end')}
                    className={`mt-1 input ${basicErrors.period_end ? 'input-error' : ''}`}
                  />
                  {basicErrors.period_end && (
                    <p className="mt-1 text-sm text-danger-600">{basicErrors.period_end.message}</p>
                  )}
                </div>
              </div>

              <div className="flex justify-end pt-4">
                <button
                  type="submit"
                  disabled={createAnalysisMutation.isPending}
                  className="btn btn-primary"
                >
                  {createAnalysisMutation.isPending ? 'Creating...' : 'Continue'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {currentStep === 'csv' && (
        <div className="card">
          <div className="card-header">
            <h2 className="text-xl font-semibold">Upload Transaction Data</h2>
          </div>
          <div className="card-body">
            <CSVUpload
              onFileSelect={onFileSelect}
              isUploading={uploadCsvMutation.isPending}
              error={error}
            />

            <div className="flex justify-between mt-6">
              <button
                type="button"
                onClick={() => setCurrentStep('basic')}
                className="btn btn-secondary"
              >
                Back
              </button>
              <button
                type="button"
                onClick={onCsvContinue}
                disabled={!selectedFile || uploadCsvMutation.isPending}
                className="btn btn-primary"
              >
                {uploadCsvMutation.isPending ? 'Uploading...' : 'Continue'}
              </button>
            </div>
          </div>
        </div>
      )}

      {currentStep === 'profile' && (
        <BusinessProfileForm
          onSubmit={onProfileSubmit}
          isSubmitting={createProfileMutation.isPending}
        />
      )}

      {currentStep === 'processing' && (
        <div className="card">
          <div className="card-body text-center py-12">
            <div className="text-6xl mb-4">✅</div>
            <h2 className="text-2xl font-bold text-neutral-900 mb-2">Analysis Created!</h2>
            <p className="text-neutral-600 mb-6">
              Your analysis is being processed. Redirecting to the analysis page...
            </p>
            <div className="inline-block">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
