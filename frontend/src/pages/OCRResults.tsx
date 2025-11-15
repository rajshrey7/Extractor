import React from 'react';

interface OCRResultsProps {
  ocrData: any;
  authToken: string;
}

const OCRResults: React.FC<OCRResultsProps> = ({ ocrData, authToken }) => {
  if (!ocrData) {
    return (
      <div className="bg-white shadow rounded-lg p-6">
        <p className="text-gray-500 text-center">No OCR data available. Please upload a document first.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="bg-white shadow rounded-lg p-6">
        <h2 className="text-xl font-semibold mb-4">OCR Results</h2>
        
        {/* Document Info */}
        <div className="mb-6">
          <h3 className="text-lg font-medium mb-2">Document Information</h3>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <span className="text-gray-600">Document ID:</span>
              <span className="ml-2 font-medium">{ocrData.document_id}</span>
            </div>
            <div>
              <span className="text-gray-600">Pages:</span>
              <span className="ml-2 font-medium">{ocrData.total_pages}</span>
            </div>
            <div>
              <span className="text-gray-600">Quality Score:</span>
              <span className="ml-2 font-medium">{ocrData.quality?.score || 'N/A'}</span>
            </div>
            <div>
              <span className="text-gray-600">Engines Used:</span>
              <span className="ml-2 font-medium">{ocrData.engines_used?.join(', ') || 'N/A'}</span>
            </div>
          </div>
        </div>

        {/* Extracted Fields */}
        <div className="mb-6">
          <h3 className="text-lg font-medium mb-2">Extracted Fields</h3>
          <div className="bg-gray-50 rounded-lg p-4">
            {Object.entries(ocrData.merged_fields || {}).map(([key, value]: [string, any]) => (
              <div key={key} className="flex justify-between py-2 border-b border-gray-200 last:border-0">
                <span className="font-medium capitalize">{key.replace('_', ' ')}:</span>
                <div className="text-right">
                  <span>{value.value || value}</span>
                  {value.confidence && (
                    <span className="ml-2 text-sm text-gray-500">
                      ({Math.round(value.confidence * 100)}% confidence)
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Raw Text */}
        <div>
          <h3 className="text-lg font-medium mb-2">Raw Text</h3>
          <div className="bg-gray-50 rounded-lg p-4 max-h-60 overflow-y-auto">
            <pre className="whitespace-pre-wrap text-sm">{ocrData.raw_text}</pre>
          </div>
        </div>

        {/* Heatmap Preview */}
        {ocrData.pages?.[0]?.heatmap && (
          <div className="mt-6">
            <h3 className="text-lg font-medium mb-2">Confidence Heatmap</h3>
            <img
              src={ocrData.pages[0].heatmap}
              alt="Confidence Heatmap"
              className="w-full rounded-lg"
            />
          </div>
        )}
      </div>
    </div>
  );
};

export default OCRResults;