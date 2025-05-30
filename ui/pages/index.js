import { useState, useEffect } from 'react';
import Head from 'next/head';
import { motion } from 'framer-motion';
import { useDropzone } from 'react-dropzone';
import axios from 'axios';
import { toast } from 'react-toastify';
import dynamic from 'next/dynamic';

// Dynamically import ReactJson to avoid SSR issues
const ReactJson = dynamic(() => import('react-json-view'), { ssr: false });

// Components
import Header from '../components/Header';
import ProcessingVisualizer from '../components/ProcessingVisualizer';
import ResultCard from '../components/ResultCard';
import Footer from '../components/Footer';

export default function Home() {
  const [file, setFile] = useState(null);
  const [jsonData, setJsonData] = useState('');
  const [emailData, setEmailData] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [processingStep, setProcessingStep] = useState(0);
  const [result, setResult] = useState(null);
  const [requestId, setRequestId] = useState(null);
  const [processingHistory, setProcessingHistory] = useState([]);

  // File dropzone setup
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop: acceptedFiles => {
      if (acceptedFiles.length > 0) {
        setFile(acceptedFiles[0]);
        setJsonData('');
        setEmailData('');
        toast.info(`File selected: ${acceptedFiles[0].name}`);
      }
    }
  });

  // Process the input data
  const processData = async () => {
    if (!file && !jsonData && !emailData) {
      toast.error('Please provide input data (file, JSON, or email)');
      return;
    }

    setIsProcessing(true);
    setProcessingStep(1);
    setResult(null);

    try {
      const formData = new FormData();
      
      if (file) {
        formData.append('file', file);
      } else if (jsonData) {
        formData.append('json_data', jsonData);
      } else if (emailData) {
        formData.append('email_data', emailData);
      }

      // Simulate processing steps with delays
      setTimeout(() => setProcessingStep(2), 1000); // Classification
      setTimeout(() => setProcessingStep(3), 2000); // Agent processing
      setTimeout(() => setProcessingStep(4), 3000); // Action routing

      const response = await axios.post('http://localhost:8000/process', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });

      setResult(response.data);
      setRequestId(response.data.request_id);
      
      // Add to processing history
      setProcessingHistory(prev => [response.data, ...prev].slice(0, 5));
      
      toast.success('Processing completed successfully!');
    } catch (error) {
      console.error('Error processing data:', error);
      toast.error(error.response?.data?.detail || 'Error processing data');
    } finally {
      setIsProcessing(false);
      setProcessingStep(0);
    }
  };

  // Clear the form
  const clearForm = () => {
    setFile(null);
    setJsonData('');
    setEmailData('');
    setResult(null);
  };

  return (
    <div className="min-h-screen flex flex-col">
      <Head>
        <title>FlowbitAI Multi-Agent System</title>
        <meta name="description" content="Process diverse input formats with AI agents" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <Header />

      <main className="flex-grow container mx-auto px-4 py-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="grid grid-cols-1 lg:grid-cols-2 gap-8"
        >
          {/* Input Section */}
          <div className="card">
            <h2 className="text-2xl font-bold mb-6 text-primary-700">Input Data</h2>
            
            <div className="space-y-6">
              {/* File Upload */}
              <div>
                <h3 className="text-lg font-medium mb-2">Upload File</h3>
                <div 
                  {...getRootProps()} 
                  className={`border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors ${
                    isDragActive ? 'border-primary-400 bg-primary-900/20' : 'border-gray-600 hover:border-primary-500'
                  }`}
                >
                  <input {...getInputProps()} />
                  {file ? (
                    <p className="text-primary-300">{file.name} ({(file.size / 1024).toFixed(2)} KB)</p>
                  ) : (
                    <p>Drag & drop a file here, or click to select</p>
                  )}
                  <p className="text-sm text-gray-400 mt-2">Supported formats: .json, .pdf, .eml, .txt</p>
                </div>
              </div>

              {/* JSON Input */}
              <div>
                <h3 className="text-lg font-medium mb-2">JSON Data</h3>
                <textarea 
                  className="input-field h-32 font-mono"
                  placeholder="Paste JSON data here..."
                  value={jsonData}
                  onChange={(e) => {
                    setJsonData(e.target.value);
                    setFile(null);
                    setEmailData('');
                  }}
                />
              </div>

              {/* Email Input */}
              <div>
                <h3 className="text-lg font-medium mb-2">Email Data</h3>
                <textarea 
                  className="input-field h-32 font-mono"
                  placeholder="Paste email content here..."
                  value={emailData}
                  onChange={(e) => {
                    setEmailData(e.target.value);
                    setFile(null);
                    setJsonData('');
                  }}
                />
              </div>

              {/* Action Buttons */}
              <div className="flex space-x-4">
                <button 
                  className="btn-primary flex-1"
                  onClick={processData}
                  disabled={isProcessing}
                >
                  {isProcessing ? 'Processing...' : 'Process Data'}
                </button>
                <button 
                  className="btn-secondary flex-1"
                  onClick={clearForm}
                  disabled={isProcessing}
                >
                  Clear
                </button>
              </div>
            </div>
          </div>

          {/* Results Section */}
          <div className="card">
            <h2 className="text-2xl font-bold mb-6 text-primary-700">Processing Results</h2>
            
            {isProcessing ? (
              <ProcessingVisualizer step={processingStep} />
            ) : result ? (
              <div className="space-y-6">
                <div>
                  <h3 className="text-lg font-medium mb-2">Classification</h3>
                  <div className="glass p-4 rounded-lg">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <p className="text-gray-400">Format</p>
                        <p className="text-lg font-medium">{result.classification.format}</p>
                      </div>
                      <div>
                        <p className="text-gray-400">Intent</p>
                        <p className="text-lg font-medium">{result.classification.intent}</p>
                      </div>
                      <div>
                        <p className="text-gray-400">Confidence</p>
                        <p className="text-lg font-medium">{(result.classification.confidence * 100).toFixed(1)}%</p>
                      </div>
                      <div>
                        <p className="text-gray-400">Priority</p>
                        <p className={`text-lg font-medium ${
                          result.classification.priority === 'HIGH' ? 'text-red-500' :
                          result.classification.priority === 'MEDIUM' ? 'text-yellow-500' :
                          'text-green-500'
                        }`}>
                          {result.classification.priority}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>

                <div>
                  <h3 className="text-lg font-medium mb-2">Processing Result</h3>
                  <div className="glass p-4 rounded-lg overflow-auto max-h-60">
                    <ReactJson 
                      src={result.processing_result} 
                      theme="monokai"
                      displayDataTypes={false}
                      collapsed={1}
                    />
                  </div>
                </div>

                <div>
                  <h3 className="text-lg font-medium mb-2">Action Result</h3>
                  <div className="glass p-4 rounded-lg">
                    <div className="mb-2">
                      <span className="text-gray-400">Action Type:</span>
                      <span className="ml-2 font-medium">{result.action_result.action_type}</span>
                    </div>
                    <div className="mb-2">
                      <span className="text-gray-400">Status:</span>
                      <span className={`ml-2 font-medium ${
                        result.action_result.status === 'completed' ? 'text-green-500' : 'text-red-500'
                      }`}>
                        {result.action_result.status}
                      </span>
                    </div>
                    <div>
                      <span className="text-gray-400">Message:</span>
                      <span className="ml-2">{result.action_result.message}</span>
                    </div>
                  </div>
                </div>

                <div>
                  <button 
                    className="btn-secondary w-full"
                    onClick={() => window.open(`/trace/${result.request_id}`, '_blank')}
                  >
                    View Full Processing Trace
                  </button>
                </div>
              </div>
            ) : (
              <div className="text-center py-12">
                <p className="text-gray-400">No results to display. Submit data for processing.</p>
              </div>
            )}
          </div>
        </motion.div>

        {/* Processing History */}
        {processingHistory.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
            className="mt-8"
          >
            <h2 className="text-2xl font-bold mb-6 text-primary-700">Processing History</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {processingHistory.map((item, index) => (
                <ResultCard key={index} result={item} />
              ))}
            </div>
          </motion.div>
        )}
      </main>

      <Footer />
    </div>
  );
}
