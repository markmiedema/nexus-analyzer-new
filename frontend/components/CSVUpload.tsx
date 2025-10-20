/**
 * CSV upload component with drag-and-drop functionality.
 */

'use client';

import { useCallback, useState } from 'react';

interface CSVUploadProps {
  onFileSelect: (file: File) => void;
  isUploading?: boolean;
  error?: string;
}

export function CSVUpload({ onFileSelect, isUploading = false, error }: CSVUploadProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const handleDragIn = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.dataTransfer.items && e.dataTransfer.items.length > 0) {
      setIsDragging(true);
    }
  }, []);

  const handleDragOut = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setIsDragging(false);

      if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
        const file = e.dataTransfer.files[0];
        if (file.name.endsWith('.csv')) {
          setSelectedFile(file);
          onFileSelect(file);
        } else {
          alert('Please select a CSV file');
        }
      }
    },
    [onFileSelect]
  );

  const handleFileInput = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      if (e.target.files && e.target.files.length > 0) {
        const file = e.target.files[0];
        setSelectedFile(file);
        onFileSelect(file);
      }
    },
    [onFileSelect]
  );

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  return (
    <div className="w-full">
      <div
        onDragEnter={handleDragIn}
        onDragLeave={handleDragOut}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        className={`
          relative border-2 border-dashed rounded-lg p-8 text-center transition-colors
          ${isDragging ? 'border-primary-500 bg-primary-50' : 'border-neutral-300 bg-white'}
          ${isUploading ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer hover:border-primary-400'}
        `}
      >
        <input
          type="file"
          accept=".csv"
          onChange={handleFileInput}
          disabled={isUploading}
          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer disabled:cursor-not-allowed"
        />

        <div className="space-y-4">
          {/* Upload icon */}
          <div className="text-6xl">📤</div>

          {/* Instructions */}
          <div>
            <h3 className="text-lg font-semibold text-neutral-900 mb-2">
              {selectedFile ? 'File Selected' : 'Upload Transaction Data'}
            </h3>
            {selectedFile ? (
              <div className="text-sm text-neutral-600 space-y-1">
                <p className="font-medium text-primary-700">{selectedFile.name}</p>
                <p className="text-neutral-500">{formatFileSize(selectedFile.size)}</p>
              </div>
            ) : (
              <p className="text-sm text-neutral-600">
                Drag and drop your CSV file here, or click to browse
              </p>
            )}
          </div>

          {/* File requirements */}
          <div className="text-xs text-neutral-500 bg-neutral-50 rounded-md p-4">
            <p className="font-semibold mb-2">CSV Requirements:</p>
            <ul className="text-left space-y-1 ml-4">
              <li>• Must include: transaction_date, state, amount</li>
              <li>• Optional: transaction_id, product_category, is_exempt</li>
              <li>• Maximum file size: 50 MB</li>
              <li>• Date format: YYYY-MM-DD or MM/DD/YYYY</li>
            </ul>
          </div>

          {/* Loading state */}
          {isUploading && (
            <div className="text-primary-600 font-medium">
              Uploading and processing...
            </div>
          )}

          {/* Error state */}
          {error && (
            <div className="bg-danger-50 border border-danger-200 text-danger-700 px-4 py-3 rounded-md text-sm">
              {error}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
