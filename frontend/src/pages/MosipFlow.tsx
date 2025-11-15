import React, { useState } from 'react';
import axios from 'axios';

interface MosipFlowProps {
  ocrData: any;
  authToken: string;
}

const MosipFlow: React.FC<MosipFlowProps> = ({ ocrData, authToken }) => {
  const [registrationStatus, setRegistrationStatus] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [registrationId, setRegistrationId] = useState<string>('');

  const handlePreRegistration = async () => {
    if (!ocrData?.merged_fields) return;

    setLoading(true);
    try {
      const response = await axios.post(
        `${process.env.REACT_APP_API_URL || 'http://localhost:9000'}/api/form/submit`,
        {
          form_data: ocrData.merged_fields,
          pre_registration: true,
          registration: false
        },
        {
          headers: {
            'Authorization': `Bearer ${authToken}`,
            'Content-Type': 'application/json'
          }
        }
      );

      setRegistrationStatus(response.data);
      if (response.data.pre_registration?.preRegId) {
        setRegistrationId(response.data.pre_registration.preRegId);
      }
    } catch (error) {
      console.error('Pre-registration error:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleFullRegistration = async () => {
    if (!ocrData?.merged_fields) return;

    setLoading(true);
    try {
      const response = await axios.post(
        `${process.env.REACT_APP_API_URL || 'http://localhost:9000'}/api/form/submit`,
        {
          form_data: ocrData.merged_fields,
          pre_registration: false,
          registration: true
        },
        {
          headers: {
            'Authorization': `Bearer ${authToken}`,
            'Content-Type': 'application/json'
          }
        }
      );

      setRegistrationStatus(response.data);
      if (response.data.registration?.registrationId) {
        setRegistrationId(response.data.registration.registrationId);
      }
    } catch (error) {
      console.error('Registration error:', error);
    } finally {
      setLoading(false);
    }
  };

  const checkStatus = async () => {
    if (!registrationId) return;

    setLoading(true);
    try {
      const response = await axios.get(
        `${process.env.REACT_APP_API_URL || 'http://localhost:9000'}/api/mosip/status/${registrationId}`,
        {
          headers: {
            'Authorization': `Bearer ${authToken}`
          }
        }
      );

      setRegistrationStatus(response.data);
    } catch (error) {
      console.error('Status check error:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="bg-white shadow rounded-lg p-6">
        <h2 className="text-xl font-semibold mb-4">MOSIP Registration Flow</h2>
        
        {!ocrData ? (
          <p className="text-gray-500 text-center">No data available. Please process a document first.</p>
        ) : (
          <>
            <div className="grid grid-cols-2 gap-4 mb-6">
              <button
                onClick={handlePreRegistration}
                disabled={loading}
                className="px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400"
              >
                Start Pre-Registration
              </button>
              <button
                onClick={handleFullRegistration}
                disabled={loading}
                className="px-4 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-400"
              >
                Full Registration
              </button>
            </div>

            {registrationId && (
              <div className="mb-4">
                <p className="text-sm text-gray-600">Registration ID:</p>
                <p className="font-mono text-lg">{registrationId}</p>
                <button
                  onClick={checkStatus}
                  disabled={loading}
                  className="mt-2 px-3 py-1 text-sm bg-gray-200 rounded hover:bg-gray-300"
                >
                  Check Status
                </button>
              </div>
            )}

            {registrationStatus && (
              <div className="bg-gray-50 rounded-lg p-4">
                <h3 className="font-medium mb-2">Registration Status</h3>
                <pre className="text-sm overflow-x-auto">
                  {JSON.stringify(registrationStatus, null, 2)}
                </pre>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default MosipFlow;