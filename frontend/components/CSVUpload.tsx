/**
 * CSV upload component with drag-and-drop functionality.
 */

'use client';

import { useCallback, useState, useEffect } from 'react';

interface CSVUploadProps {
  onFileSelect: (file: File) => void;
  isUploading?: boolean;
  error?: string;
}

export function CSVUpload({ onFileSelect, isUploading = false, error }: CSVUploadProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [filePreview, setFilePreview] = useState<string[][]>([]);

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

  const previewFile = useCallback((file: File) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      const text = e.target?.result as string;
      const lines = text.split('\n').slice(0, 6); // Get first 6 lines (header + 5 rows)
      const preview = lines.map(line => line.split(',').slice(0, 5)); // First 5 columns
      setFilePreview(preview);
    };
    reader.readAsText(file);
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
          previewFile(file);
          onFileSelect(file);
        } else {
          alert('Please select a CSV file');
        }
      }
    },
    [onFileSelect, previewFile]
  );

  const handleFileInput = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      if (e.target.files && e.target.files.length > 0) {
        const file = e.target.files[0];
        setSelectedFile(file);
        previewFile(file);
        onFileSelect(file);
      }
    },
    [onFileSelect, previewFile]
  );

  // Simulate upload progress when uploading
  useEffect(() => {
    if (isUploading) {
      setUploadProgress(0);
      const interval = setInterval(() => {
        setUploadProgress(prev => {
          if (prev >= 90) {
            clearInterval(interval);
            return 90;
          }
          return prev + 10;
        });
      }, 200);
      return () => clearInterval(interval);
    } else {
      setUploadProgress(0);
    }
  }, [isUploading]);

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  return (
    <div className="w-full space-y-6">
      <div
        onDragEnter={handleDragIn}
        onDragLeave={handleDragOut}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        className={`
          relative border-2 border-dashed rounded-xl p-8 text-center transition-all duration-300
          ${isDragging ? 'border-primary-500 bg-primary-50 scale-105' : 'border-neutral-300 bg-white'}
          ${isUploading ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer hover:border-primary-400 hover:shadow-lg'}
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
          <div className={`text-6xl transition-transform duration-300 ${isDragging ? 'scale-125' : ''}`}>
            {selectedFile ? '✅' : '📤'}
          </div>

          {/* Instructions */}
          <div>
            <h3 className="text-lg font-semibold text-neutral-900 mb-2">
              {selectedFile ? 'File Ready!' : 'Upload Transaction Data'}
            </h3>
            {selectedFile ? (
              <div className="text-sm text-neutral-600 space-y-1">
                <p className="font-semibold text-primary-700">{selectedFile.name}</p>
                <p className="text-neutral-500">{formatFileSize(selectedFile.size)}</p>
              </div>
            ) : (
              <p className="text-sm text-neutral-600">
                Drag and drop your CSV file here, or click to browse
              </p>
            )}
          </div>

          {/* Upload Progress */}
          {isUploading && (
            <div className="space-y-2">
              <div className="text-primary-600 font-medium">
                Uploading and validating... {uploadProgress}%
              </div>
              <div className="w-full bg-neutral-200 rounded-full h-3 overflow-hidden">
                <div
                  className="bg-gradient-to-r from-primary-500 to-primary-600 h-full transition-all duration-500 ease-out"
                  style={{ width: `${uploadProgress}%` }}
                >
                  <div className="w-full h-full animate-pulse bg-white/20"></div>
                </div>
              </div>
            </div>
          )}

          {/* File requirements */}
          {!selectedFile && !isUploading && (
            <div className="text-xs text-neutral-500 bg-neutral-50 rounded-lg p-4 border border-neutral-200">
              <p className="font-semibold mb-2 text-neutral-700">CSV Requirements:</p>
              <ul className="text-left space-y-1 ml-4">
                <li>✓ Must include: transaction_date, state, amount</li>
                <li>✓ Optional: transaction_id, product_category, is_exempt</li>
                <li>✓ Maximum file size: 50 MB</li>
                <li>✓ Date format: YYYY-MM-DD or MM/DD/YYYY</li>
              </ul>
            </div>
          )}

          {/* Error state */}
          {error && (
            <div className="bg-danger-50 border border-danger-200 text-danger-700 px-4 py-3 rounded-lg text-sm animate-fadeIn">
              <div className="flex items-center">
                <span className="text-xl mr-2">⚠️</span>
                <span>{error}</span>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* File Preview */}
      {selectedFile && filePreview.length > 0 && !isUploading && (
        <div className="bg-neutral-50 rounded-xl border border-neutral-200 p-6 animate-fadeIn">
          <div className="flex items-center justify-between mb-4">
            <h4 className="text-sm font-semibold text-neutral-900 flex items-center">
              <span className="text-lg mr-2">👀</span>
              File Preview (First 5 rows)
            </h4>
            <button
              onClick={() => {
                setSelectedFile(null);
                setFilePreview([]);
              }}
              className="text-sm text-neutral-500 hover:text-danger-600 transition-colors"
            >
              Remove file
            </button>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full text-xs">
              <tbody className="divide-y divide-neutral-200">
                {filePreview.map((row, rowIndex) => (
                  <tr
                    key={rowIndex}
                    className={`${rowIndex === 0 ? 'bg-primary-50 font-semibold' : 'bg-white'}`}
                  >
                    {row.map((cell, cellIndex) => (
                      <td
                        key={cellIndex}
                        className="px-3 py-2 whitespace-nowrap text-neutral-700"
                      >
                        {cell.trim() || '(empty)'}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="mt-3 text-xs text-neutral-500">
            Showing first 5 columns and 5 rows. The full file will be processed.
          </div>
        </div>
      )}
    </div>
  );
}
