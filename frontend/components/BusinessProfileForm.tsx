/**
 * Business profile form component with location management.
 */

'use client';

import { useForm, useFieldArray } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

const locationSchema = z.object({
  state_code: z.string().min(2, 'State is required').max(2),
  location_type: z.enum(['office', 'warehouse', 'retail', 'remote_employee', 'other']),
  employee_count: z.number().min(0).optional(),
});

const businessProfileSchema = z.object({
  legal_business_name: z.string().min(1, 'Legal business name is required'),
  doing_business_as: z.string().optional(),
  business_structure: z.string().optional(),
  has_employees: z.boolean(),
  employee_count: z.number().min(0).optional(),
  has_inventory: z.boolean(),
  uses_marketplace_facilitators: z.boolean(),
  marketplace_names: z.array(z.string()).optional(),
  locations: z.array(locationSchema).min(0),
});

export type BusinessProfileFormData = z.infer<typeof businessProfileSchema>;

interface BusinessProfileFormProps {
  onSubmit: (data: BusinessProfileFormData) => void;
  initialData?: Partial<BusinessProfileFormData>;
  isSubmitting?: boolean;
}

const US_STATES = [
  'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
  'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
  'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
  'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
  'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY', 'DC'
];

export function BusinessProfileForm({
  onSubmit,
  initialData,
  isSubmitting = false,
}: BusinessProfileFormProps) {
  const {
    register,
    handleSubmit,
    watch,
    control,
    formState: { errors },
  } = useForm<BusinessProfileFormData>({
    resolver: zodResolver(businessProfileSchema),
    defaultValues: initialData || {
      has_employees: false,
      has_inventory: false,
      uses_marketplace_facilitators: false,
      locations: [],
    },
  });

  const { fields, append, remove } = useFieldArray({
    control,
    name: 'locations',
  });

  const hasEmployees = watch('has_employees');
  const usesMarketplaceFacilitators = watch('uses_marketplace_facilitators');

  const handleAddLocation = () => {
    append({
      state_code: '',
      location_type: 'office',
      employee_count: 0,
    });
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      {/* Business Information */}
      <div className="card">
        <div className="card-header">
          <h3 className="text-lg font-semibold">Business Information</h3>
        </div>
        <div className="card-body space-y-4">
          <div>
            <label htmlFor="legal_business_name" className="block text-sm font-medium text-neutral-700">
              Legal Business Name *
            </label>
            <input
              id="legal_business_name"
              type="text"
              {...register('legal_business_name')}
              className={`mt-1 input ${errors.legal_business_name ? 'input-error' : ''}`}
              placeholder="Acme Corporation"
            />
            {errors.legal_business_name && (
              <p className="mt-1 text-sm text-danger-600">{errors.legal_business_name.message}</p>
            )}
          </div>

          <div>
            <label htmlFor="doing_business_as" className="block text-sm font-medium text-neutral-700">
              Doing Business As (DBA)
            </label>
            <input
              id="doing_business_as"
              type="text"
              {...register('doing_business_as')}
              className="mt-1 input"
              placeholder="Optional"
            />
          </div>

          <div>
            <label htmlFor="business_structure" className="block text-sm font-medium text-neutral-700">
              Business Structure
            </label>
            <select
              id="business_structure"
              {...register('business_structure')}
              className="mt-1 input"
            >
              <option value="">Select structure</option>
              <option value="Sole Proprietorship">Sole Proprietorship</option>
              <option value="LLC">LLC</option>
              <option value="S-Corp">S Corporation</option>
              <option value="C-Corp">C Corporation</option>
              <option value="Partnership">Partnership</option>
              <option value="Non-Profit">Non-Profit</option>
              <option value="Other">Other</option>
            </select>
          </div>
        </div>
      </div>

      {/* Employee Information */}
      <div className="card">
        <div className="card-header">
          <h3 className="text-lg font-semibold">Employee Information</h3>
        </div>
        <div className="card-body space-y-4">
          <div className="flex items-center">
            <input
              id="has_employees"
              type="checkbox"
              {...register('has_employees')}
              className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-neutral-300 rounded"
            />
            <label htmlFor="has_employees" className="ml-2 block text-sm text-neutral-700">
              Business has employees
            </label>
          </div>

          {hasEmployees && (
            <div>
              <label htmlFor="employee_count" className="block text-sm font-medium text-neutral-700">
                Total Employee Count
              </label>
              <input
                id="employee_count"
                type="number"
                {...register('employee_count', { valueAsNumber: true })}
                className="mt-1 input"
                placeholder="0"
              />
            </div>
          )}
        </div>
      </div>

      {/* Inventory */}
      <div className="card">
        <div className="card-header">
          <h3 className="text-lg font-semibold">Inventory</h3>
        </div>
        <div className="card-body">
          <div className="flex items-center">
            <input
              id="has_inventory"
              type="checkbox"
              {...register('has_inventory')}
              className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-neutral-300 rounded"
            />
            <label htmlFor="has_inventory" className="ml-2 block text-sm text-neutral-700">
              Business maintains physical inventory
            </label>
          </div>
        </div>
      </div>

      {/* Marketplace Facilitators */}
      <div className="card">
        <div className="card-header">
          <h3 className="text-lg font-semibold">Marketplace Facilitators</h3>
        </div>
        <div className="card-body space-y-4">
          <div className="flex items-center">
            <input
              id="uses_marketplace_facilitators"
              type="checkbox"
              {...register('uses_marketplace_facilitators')}
              className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-neutral-300 rounded"
            />
            <label htmlFor="uses_marketplace_facilitators" className="ml-2 block text-sm text-neutral-700">
              Sells through marketplace facilitators (Amazon, eBay, etc.)
            </label>
          </div>

          {usesMarketplaceFacilitators && (
            <div>
              <label htmlFor="marketplace_names" className="block text-sm font-medium text-neutral-700">
                Marketplace Names (comma-separated)
              </label>
              <input
                id="marketplace_names"
                type="text"
                {...register('marketplace_names')}
                className="mt-1 input"
                placeholder="Amazon, eBay, Etsy"
              />
              <p className="mt-1 text-xs text-neutral-500">
                Enter marketplace names separated by commas
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Physical Locations */}
      <div className="card">
        <div className="card-header flex justify-between items-center">
          <h3 className="text-lg font-semibold">Physical Locations</h3>
          <button
            type="button"
            onClick={handleAddLocation}
            className="btn btn-secondary text-sm"
          >
            + Add Location
          </button>
        </div>
        <div className="card-body space-y-4">
          {fields.length === 0 ? (
            <p className="text-sm text-neutral-500 text-center py-4">
              No locations added yet. Click &quot;Add Location&quot; to begin.
            </p>
          ) : (
            fields.map((field, index) => (
              <div key={field.id} className="border border-neutral-200 rounded-md p-4 space-y-3">
                <div className="flex justify-between items-center mb-2">
                  <h4 className="font-medium text-neutral-900">Location {index + 1}</h4>
                  <button
                    type="button"
                    onClick={() => remove(index)}
                    className="text-danger-600 hover:text-danger-700 text-sm font-medium"
                  >
                    Remove
                  </button>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-neutral-700">
                      State *
                    </label>
                    <select
                      {...register(`locations.${index}.state_code`)}
                      className={`mt-1 input ${errors.locations?.[index]?.state_code ? 'input-error' : ''}`}
                    >
                      <option value="">Select state</option>
                      {US_STATES.map((state) => (
                        <option key={state} value={state}>
                          {state}
                        </option>
                      ))}
                    </select>
                    {errors.locations?.[index]?.state_code && (
                      <p className="mt-1 text-sm text-danger-600">
                        {errors.locations[index]?.state_code?.message}
                      </p>
                    )}
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-neutral-700">
                      Location Type *
                    </label>
                    <select
                      {...register(`locations.${index}.location_type`)}
                      className="mt-1 input"
                    >
                      <option value="office">Office</option>
                      <option value="warehouse">Warehouse</option>
                      <option value="retail">Retail Store</option>
                      <option value="remote_employee">Remote Employee</option>
                      <option value="other">Other</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-neutral-700">
                      Employee Count
                    </label>
                    <input
                      type="number"
                      {...register(`locations.${index}.employee_count`, { valueAsNumber: true })}
                      className="mt-1 input"
                      placeholder="0"
                    />
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Submit Button */}
      <div className="flex justify-end space-x-4">
        <button
          type="submit"
          disabled={isSubmitting}
          className="btn btn-primary"
        >
          {isSubmitting ? 'Saving...' : 'Continue'}
        </button>
      </div>
    </form>
  );
}
