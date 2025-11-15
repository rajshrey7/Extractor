import React, { useState, useEffect } from 'react';
import './App.css';
import UploadPage from './pages/UploadPage';
import CameraCapture from './pages/CameraCapture';
import OCRResults from './pages/OCRResults';
import FormCorrection from './pages/FormCorrection';
import MosipFlow from './pages/MosipFlow';

interface TabProps {
  label: string;
  value: string;
  active: boolean;
  onClick: () => void;
}

const Tab: React.FC<TabProps> = ({ label, active, onClick }) => (
  <button
    className={`px-6 py-3 text-sm font-medium transition-colors ${
      active
        ? 'bg-blue-600 text-white border-b-2 border-blue-600'
        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
    }`}
    onClick={onClick}
  >
    {label}
  </button>
);

function App() {
  const [activeTab, setActiveTab] = useState('upload');
  const [ocrData, setOcrData] = useState<any>(null);
  const [authToken, setAuthToken] = useState<string>('');

  useEffect(() => {
    // Get auth token on mount
    fetchAuthToken();
  }, []);

  const fetchAuthToken = async () => {
    try {
      const response = await fetch(`${process.env.REACT_APP_API_URL || 'http://localhost:9000'}/api/auth/token`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: 'api_key=dev-api-key',
      });
      const data = await response.json();
      setAuthToken(data.access_token);
    } catch (error) {
      console.error('Failed to fetch auth token:', error);
    }
  };

  const handleOCRComplete = (data: any) => {
    setOcrData(data);
    setActiveTab('results');
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <h1 className="text-2xl font-bold text-gray-900">
              Extractor with MOSIP Integration
            </h1>
            <span className="text-sm text-gray-500">v2.0.0</span>
          </div>
        </div>
      </header>

      {/* Navigation Tabs */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex space-x-1">
            <Tab
              label="Upload Document"
              value="upload"
              active={activeTab === 'upload'}
              onClick={() => setActiveTab('upload')}
            />
            <Tab
              label="Camera Capture"
              value="camera"
              active={activeTab === 'camera'}
              onClick={() => setActiveTab('camera')}
            />
            <Tab
              label="OCR Results"
              value="results"
              active={activeTab === 'results'}
              onClick={() => setActiveTab('results')}
            />
            <Tab
              label="Form Correction"
              value="form"
              active={activeTab === 'form'}
              onClick={() => setActiveTab('form')}
            />
            <Tab
              label="MOSIP Registration"
              value="mosip"
              active={activeTab === 'mosip'}
              onClick={() => setActiveTab('mosip')}
            />
          </div>
        </div>
      </div>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === 'upload' && (
          <UploadPage authToken={authToken} onOCRComplete={handleOCRComplete} />
        )}
        {activeTab === 'camera' && (
          <CameraCapture authToken={authToken} onOCRComplete={handleOCRComplete} />
        )}
        {activeTab === 'results' && (
          <OCRResults ocrData={ocrData} authToken={authToken} />
        )}
        {activeTab === 'form' && (
          <FormCorrection ocrData={ocrData} authToken={authToken} />
        )}
        {activeTab === 'mosip' && (
          <MosipFlow ocrData={ocrData} authToken={authToken} />
        )}
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-auto">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <p className="text-center text-sm text-gray-500">
            Built with React, FastAPI, and MOSIP Integration
          </p>
        </div>
      </footer>
    </div>
  );
}

export default App;