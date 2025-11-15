import React, { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import axios from 'axios';

interface UploadPageProps {
  authToken: string;
  onOCRComplete: (data: any) => void;
}

const UploadPage: React.FC<UploadPageProps> = ({ authToken, onOCRComplete }) => {
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [qualityScore, setQualityScore] = useState<any>(null);
  const [error, setError] = useState<string>('');

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    if (acceptedFiles.length === 0) return;

    setUploading(true);
    setError('');
    setUploadProgress(0);

    try {
      // Check quality first
      const qualityFormData = new FormData();
      qualityFormData.append('file', acceptedFiles[0]);
      qualityFormData.append('image_type', 'document');

      const qualityResponse = await axios.post(
        `${process.env.REACT_APP_API_URL || 'http://localhost:9000'}/api/quality`,
        qualityFormData,
        {
          headers: {
            'Authorization': `Bearer ${authToken}`,
          },
          onUploadProgress: (progressEvent) => {
            const progress = progressEvent.total
              ? Math.round((progressEvent.loaded * 50) / progressEvent.total)
              : 0;
            setUploadProgress(progress);
          },
        }
      );

      setQualityScore(qualityResponse.data);

      // Process OCR
      const ocrFormData = new FormData();
      if (acceptedFiles.length === 1) {
        ocrFormData.append('file', acceptedFiles[0]);
        
        const ocrResponse = await axios.post(
          `${process.env.REACT_APP_API_URL || 'http://localhost:9000'}/api/ocr`,
          ocrFormData,
          {
            headers: {
              'Authorization': `Bearer ${authToken}`,
            },
            onUploadProgress: (progressEvent) => {
              const progress = progressEvent.total
                ? Math.round(50 + (progressEvent.loaded * 50) / progressEvent.total)
                : 50;
              setUploadProgress(progress);
            },
          }
        );

        onOCRComplete(ocrResponse.data);
      } else {
        // Multiple files
        acceptedFiles.forEach(file => {
          ocrFormData.append('files', file);
        });

        const ocrResponse = await axios.post(
          `${process.env.REACT_APP_API_URL || 'http://localhost:9000'}/api/ocr/multi`,
          ocrFormData,
          {
            headers: {
              'Authorization': `Bearer ${authToken}`,
            },
            onUploadProgress: (progressEvent) => {
              const progress = progressEvent.total
                ? Math.round(50 + (progressEvent.loaded * 50) / progressEvent.total)
                : 50;
              setUploadProgress(progress);
            },
          }
        );

        onOCRComplete(ocrResponse.data);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Upload failed');
    } finally {
      setUploading(false);
    }
  }, [authToken, onOCRComplete]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/*': ['.png', '.jpg', '.jpeg', '.tiff', '.bmp'],
      'application/pdf': ['.pdf'],
    },
    multiple: true,
  });

  const getQualityColor = (score: number) => {
    if (score >= 90) return 'text-green-600';
    if (score >= 75) return 'text-blue-600';
    if (score >= 60) return 'text-yellow-600';
    if (score >= 40) return 'text-orange-600';
    return 'text-red-600';
  };

  return (
    <div className="space-y-6">
      <div className="bg-white shadow rounded-lg p-6">
        <h2 className="text-xl font-semibold mb-4">Upload Documents</h2>
        
        {/* Dropzone */}
        <div
          {...getRootProps()}
          className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
            isDragActive
              ? 'border-blue-500 bg-blue-50'
              : 'border-gray-300 hover:border-gray-400'
          }`}
        >
          <input {...getInputProps()} />
          <svg
            className="mx-auto h-12 w-12 text-gray-400"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
            />
          </svg>
          <p className="mt-2 text-sm text-gray-600">
            {isDragActive
              ? 'Drop the files here...'
              : 'Drag & drop files here, or click to select'}
          </p>
          <p className="text-xs text-gray-500 mt-1">
            Supports: JPG, PNG, PDF, TIFF (Multiple files supported)
          </p>
        </div>

        {/* Upload Progress */}
        {uploading && (
          <div className="mt-4">
            <div className="flex justify-between text-sm text-gray-600 mb-1">
              <span>Processing...</span>
              <span>{uploadProgress}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${uploadProgress}%` }}
              />
            </div>
          </div>
        )}

        {/* Quality Score */}
        {qualityScore && (
          <div className="mt-4 p-4 bg-gray-50 rounded-lg">
            <div className="flex items-center justify-between mb-2">
              <span className="font-medium">Quality Score:</span>
              <span className={`text-2xl font-bold ${getQualityColor(qualityScore.score)}`}>
                {qualityScore.score}/100
              </span>
            </div>
            
            {/* Quality Metrics */}
            <div className="grid grid-cols-2 gap-2 text-sm mt-3">
              {Object.entries(qualityScore.metrics).map(([key, value]: [string, any]) => (
                value !== null && (
                  <div key={key} className="flex justify-between">
                    <span className="text-gray-600">{key}:</span>
                    <span className="font-medium">{value}</span>
                  </div>
                )
              ))}
            </div>

            {/* Suggestions */}
            {qualityScore.suggestions && qualityScore.suggestions.length > 0 && (
              <div className="mt-3 pt-3 border-t border-gray-200">
                <p className="text-sm font-medium text-gray-700 mb-1">Suggestions:</p>
                <ul className="list-disc list-inside text-sm text-gray-600">
                  {qualityScore.suggestions.map((suggestion: string, index: number) => (
                    <li key={index}>{suggestion}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {/* Error Message */}
        {error && (
          <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-sm text-red-600">{error}</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default UploadPage;