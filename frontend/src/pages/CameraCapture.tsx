import React, { useRef, useState, useEffect } from 'react';
import axios from 'axios';

interface CameraCaptureProps {
  authToken: string;
  onOCRComplete: (data: any) => void;
}

const CameraCapture: React.FC<CameraCaptureProps> = ({ authToken, onOCRComplete }) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [capturing, setCapturing] = useState(false);
  const [qualityScore, setQualityScore] = useState<any>(null);
  const [stream, setStream] = useState<MediaStream | null>(null);

  useEffect(() => {
    startCamera();
    return () => {
      if (stream) {
        stream.getTracks().forEach(track => track.stop());
      }
    };
  }, []);

  const startCamera = async () => {
    try {
      const mediaStream = await navigator.mediaDevices.getUserMedia({
        video: { width: 1280, height: 720 }
      });
      if (videoRef.current) {
        videoRef.current.srcObject = mediaStream;
      }
      setStream(mediaStream);
    } catch (err) {
      console.error('Failed to start camera:', err);
    }
  };

  const captureFrame = async () => {
    if (!videoRef.current || !canvasRef.current) return;

    const video = videoRef.current;
    const canvas = canvasRef.current;
    const context = canvas.getContext('2d');

    if (!context) return;

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    context.drawImage(video, 0, 0);

    canvas.toBlob(async (blob) => {
      if (!blob) return;

      setCapturing(true);
      
      try {
        // Check quality
        const formData = new FormData();
        formData.append('file', blob, 'capture.jpg');
        formData.append('image_type', 'document');

        const qualityResponse = await axios.post(
          `${process.env.REACT_APP_API_URL || 'http://localhost:9000'}/api/quality`,
          formData,
          {
            headers: {
              'Authorization': `Bearer ${authToken}`,
            },
          }
        );

        setQualityScore(qualityResponse.data);

        // If quality is good, process OCR
        if (qualityResponse.data.score > 70) {
          const ocrResponse = await axios.post(
            `${process.env.REACT_APP_API_URL || 'http://localhost:9000'}/api/ocr`,
            formData,
            {
              headers: {
                'Authorization': `Bearer ${authToken}`,
              },
            }
          );

          onOCRComplete(ocrResponse.data);
        }
      } catch (err) {
        console.error('Capture error:', err);
      } finally {
        setCapturing(false);
      }
    }, 'image/jpeg');
  };

  return (
    <div className="space-y-6">
      <div className="bg-white shadow rounded-lg p-6">
        <h2 className="text-xl font-semibold mb-4">Camera Capture</h2>
        
        <div className="relative">
          <video
            ref={videoRef}
            autoPlay
            playsInline
            className="w-full rounded-lg"
          />
          <canvas ref={canvasRef} className="hidden" />
          
          {qualityScore && (
            <div className="absolute top-4 right-4 bg-white p-3 rounded-lg shadow">
              <div className="text-sm font-medium">Quality Score</div>
              <div className={`text-2xl font-bold ${
                qualityScore.score >= 70 ? 'text-green-600' : 'text-orange-600'
              }`}>
                {qualityScore.score}/100
              </div>
              {qualityScore.suggestions && qualityScore.suggestions[0] && (
                <div className="text-xs text-gray-600 mt-1">
                  {qualityScore.suggestions[0]}
                </div>
              )}
            </div>
          )}
        </div>

        <div className="mt-4 flex justify-center">
          <button
            onClick={captureFrame}
            disabled={capturing}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400"
          >
            {capturing ? 'Processing...' : 'Capture Document'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default CameraCapture;