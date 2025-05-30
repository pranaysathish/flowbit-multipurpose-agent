import { motion } from 'framer-motion';

export default function ResultCard({ result }) {
  if (!result) return null;

  const getStatusColor = (status) => {
    if (status === 'completed') return 'text-green-500';
    if (status === 'error') return 'text-red-500';
    return 'text-yellow-500';
  };

  const getPriorityColor = (priority) => {
    if (priority === 'HIGH') return 'text-red-500';
    if (priority === 'MEDIUM') return 'text-yellow-500';
    return 'text-green-500';
  };

  return (
    <motion.div 
      className="card hover:shadow-lg transition-shadow"
      whileHover={{ y: -5 }}
      transition={{ duration: 0.2 }}
    >
      <div className="flex justify-between items-start mb-4">
        <div>
          <h3 className="font-bold text-lg text-primary-300">{result.classification.format}</h3>
          <p className="text-gray-400 text-sm">Intent: {result.classification.intent}</p>
        </div>
        <span className={`px-2 py-1 rounded text-xs font-medium ${getPriorityColor(result.classification.priority)}`}>
          {result.classification.priority}
        </span>
      </div>

      <div className="space-y-2 mb-4">
        <div className="flex justify-between">
          <span className="text-gray-400 text-sm">Action:</span>
          <span className="text-sm">{result.action_result.action_type}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-400 text-sm">Status:</span>
          <span className={`text-sm ${getStatusColor(result.action_result.status)}`}>
            {result.action_result.status}
          </span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-400 text-sm">Request ID:</span>
          <span className="text-sm font-mono text-xs">{result.request_id.substring(0, 8)}...</span>
        </div>
      </div>

      <button 
        className="w-full py-2 text-sm bg-dark-200 hover:bg-dark-100 rounded transition-colors text-primary-300"
        onClick={() => window.open(`http://localhost:8000/status/${result.request_id}`, '_blank')}
      >
        View Details
      </button>
    </motion.div>
  );
}