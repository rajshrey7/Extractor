import React, { useState, useEffect } from 'react';
import axios from 'axios';

interface FormCorrectionProps {
  ocrData: any;
  authToken: string;
}

const FormCorrection: React.FC<FormCorrectionProps> = ({ ocrData, authToken }) => {
  const [formFields, setFormFields] = useState<any>({});
  const [editing, setEditing] = useState<string>('');
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (ocrData?.merged_fields) {
      const fields: any = {};
      Object.entries(ocrData.merged_fields).forEach(([key, value]: [string, any]) => {
        fields[key] = value.value || value;
      });
      setFormFields(fields);
    }
  }, [ocrData]);

  const handleFieldChange = (fieldName: string, value: string) => {
    setFormFields({
      ...formFields,
      [fieldName]: value
    });
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      // Save corrected data (implement actual save logic)
      console.log('Saving corrected data:', formFields);
      // You can send this to backend or store locally
    } catch (error) {
      console.error('Save error:', error);
    } finally {
      setSaving(false);
    }
  };

  if (!ocrData) {
    return (
      <div className="bg-white shadow rounded-lg p-6">
        <p className="text-gray-500 text-center">No data available for correction. Please process a document first.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="bg-white shadow rounded-lg p-6">
        <h2 className="text-xl font-semibold mb-4">Form Correction & Verification</h2>
        
        <div className="space-y-4">
          {Object.entries(formFields).map(([key, value]) => (
            <div key={key} className="border rounded-lg p-4">
              <label className="block text-sm font-medium text-gray-700 mb-1 capitalize">
                {key.replace(/_/g, ' ')}
              </label>
              <div className="flex items-center space-x-2">
                <input
                  type="text"
                  value={value || ''}
                  onChange={(e) => handleFieldChange(key, e.target.value)}
                  onFocus={() => setEditing(key)}
                  onBlur={() => setEditing('')}
                  className={`flex-1 px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                    editing === key ? 'border-blue-500' : 'border-gray-300'
                  }`}
                />
                {ocrData.merged_fields[key]?.confidence && (
                  <span className="text-sm text-gray-500">
                    {Math.round(ocrData.merged_fields[key].confidence * 100)}% confidence
                  </span>
                )}
              </div>
              {editing === key && (
                <p className="text-xs text-gray-500 mt-1">
                  Original: {ocrData.merged_fields[key]?.value || ocrData.merged_fields[key]}
                </p>
              )}
            </div>
          ))}
        </div>

        <div className="mt-6 flex justify-end space-x-4">
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
          >
            Reset
          </button>
          <button
            onClick={handleSave}
            disabled={saving}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400"
          >
            {saving ? 'Saving...' : 'Save Corrections'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default FormCorrection;