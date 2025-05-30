import { motion } from 'framer-motion';

export default function ProcessingVisualizer({ step }) {
  const steps = [
    { id: 1, name: 'Classification', description: 'Detecting format and intent' },
    { id: 2, name: 'Agent Processing', description: 'Extracting and analyzing data' },
    { id: 3, name: 'Action Routing', description: 'Determining follow-up actions' },
    { id: 4, name: 'Completion', description: 'Finalizing results' },
  ];

  return (
    <div className="py-6">
      <div className="relative">
        {/* Progress bar */}
        <div className="absolute top-5 left-0 w-full h-1 bg-gray-700">
          <motion.div 
            className="h-full bg-primary-500"
            initial={{ width: '0%' }}
            animate={{ width: `${(step / steps.length) * 100}%` }}
            transition={{ duration: 0.5 }}
          />
        </div>

        {/* Steps */}
        <div className="flex justify-between relative">
          {steps.map((s) => (
            <div key={s.id} className="flex flex-col items-center">
              <motion.div 
                className={`w-10 h-10 rounded-full flex items-center justify-center z-10 ${
                  s.id <= step ? 'bg-primary-500' : 'bg-gray-700'
                }`}
                initial={{ scale: 0.8 }}
                animate={{ 
                  scale: s.id === step ? [1, 1.1, 1] : 1,
                  backgroundColor: s.id <= step ? '#6366f1' : '#374151'
                }}
                transition={{ 
                  duration: 0.5,
                  repeat: s.id === step ? Infinity : 0,
                  repeatType: "reverse"
                }}
              >
                {s.id < step ? (
                  <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                ) : (
                  <span className="text-white font-medium">{s.id}</span>
                )}
              </motion.div>
              <div className="mt-3 text-center">
                <p className={`font-medium ${s.id <= step ? 'text-primary-300' : 'text-gray-500'}`}>{s.name}</p>
                <p className="text-xs text-gray-500 mt-1 max-w-[120px]">{s.description}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="mt-12 text-center">
        <motion.div
          className="inline-block"
          animate={{ rotate: 360 }}
          transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
        >
          <svg className="w-12 h-12 text-primary-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
        </motion.div>
        <p className="mt-4 text-lg text-primary-300 font-medium">Processing your data...</p>
        <p className="text-gray-400 mt-2">This may take a few moments</p>
      </div>
    </div>
  );
}