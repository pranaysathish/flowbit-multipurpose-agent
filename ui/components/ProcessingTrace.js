import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';

export default function ProcessingTrace({ requestId }) {
  const [traceData, setTraceData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchTraceData = async () => {
      try {
        setLoading(true);
        const response = await fetch(`http://localhost:8000/status/${requestId}`);
        if (!response.ok) {
          throw new Error('Failed to fetch trace data');
        }
        const data = await response.json();
        setTraceData(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    if (requestId) {
      fetchTraceData();
    }
  }, [requestId]);

  if (loading) {
    return (
      <div className="min-h-screen bg-secondary-50 p-6">
        <div className="max-w-6xl mx-auto">
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-600"></div>
            <span className="ml-3 text-primary-600">Loading processing trace...</span>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-secondary-50 p-6">
        <div className="max-w-6xl mx-auto">
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
            <h2 className="text-xl font-bold mb-2">Error</h2>
            <p>{error}</p>
          </div>
        </div>
      </div>
    );
  }

  if (!traceData) {
    return (
      <div className="min-h-screen bg-secondary-50 p-6">
        <div className="max-w-6xl mx-auto">
          <div className="bg-secondary-100 border border-secondary-200 rounded-lg p-4">
            <p className="text-secondary-700">No trace data available for this request.</p>
          </div>
        </div>
      </div>
    );
  }

  // Helper function to render nested objects
  const renderObject = (obj, level = 0) => {
    return (
      <div className={`ml-${level * 4}`}>
        {Object.entries(obj).map(([key, value], index) => {
          // Skip rendering timestamps for cleaner view
          if (key === 'timestamp') return null;
          
          const isObject = value !== null && typeof value === 'object';
          
          return (
            <div key={index} className="mb-2">
              <div className="flex items-start">
                <span className="font-semibold text-primary-700 mr-2">{key}:</span>
                {isObject ? (
                  <div className="flex-1">
                    {Array.isArray(value) ? (
                      <div className="pl-4">
                        {value.map((item, i) => (
                          <div key={i} className="mb-2 border-l-2 border-secondary-200 pl-2">
                            {typeof item === 'object' && item !== null ? (
                              renderObject(item, level + 1)
                            ) : (
                              <span className="text-secondary-700">{String(item)}</span>
                            )}
                          </div>
                        ))}
                      </div>
                    ) : (
                      renderObject(value, level + 1)
                    )}
                  </div>
                ) : (
                  <span className="text-secondary-700">{String(value)}</span>
                )}
              </div>
            </div>
          );
        })}
      </div>
    );
  };

  // Format the trace data into sections
  const formatTraceData = () => {
    const sections = [
      { title: 'Input Information', data: { 
        'Input Type': traceData.data?.input_source || 'Unknown',
        'Request ID': traceData.request_id,
        'Timestamp': new Date(traceData.timestamp).toLocaleString(),
      }},
      { title: 'Classification Results', data: traceData.data?.classification_details || {} },
      { title: 'Processing Details', data: traceData.data?.extraction_details || {} },
      { title: 'Compliance Analysis', data: traceData.data?.compliance_data || {} },
      { title: 'Action Results', data: traceData.action_result || {} },
    ];

    return sections.filter(section => Object.keys(section.data).length > 0);
  };

  const sections = formatTraceData();

  return (
    <div className="min-h-screen bg-secondary-50 p-6">
      <div className="max-w-6xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <header className="mb-8">
            <h1 className="text-3xl font-bold text-primary-700">Processing Trace</h1>
            <p className="text-secondary-600">
              Request ID: <span className="font-mono bg-secondary-100 px-2 py-1 rounded">{requestId}</span>
            </p>
          </header>

          <div className="space-y-6">
            {sections.map((section, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: index * 0.1 }}
                className="bg-white rounded-lg shadow-sm border border-secondary-200 overflow-hidden"
              >
                <div className="bg-secondary-100 px-6 py-3 border-b border-secondary-200">
                  <h2 className="text-xl font-bold text-primary-700">{section.title}</h2>
                </div>
                <div className="p-6">
                  {renderObject(section.data)}
                </div>
              </motion.div>
            ))}
          </div>
          
          <div className="mt-8 text-center">
            <button 
              onClick={() => window.history.back()} 
              className="px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
            >
              Back to Results
            </button>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
