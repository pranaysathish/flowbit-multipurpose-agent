import { motion } from 'framer-motion';
import Image from 'next/image';

export default function About({ onClose }) {
  return (
    <motion.div
      className="fixed inset-0 bg-primary-900 bg-opacity-50 z-50 flex items-center justify-center p-4 overflow-y-auto"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
    >
      <motion.div 
        className="bg-white rounded-xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto"
        initial={{ scale: 0.9, y: 20 }}
        animate={{ scale: 1, y: 0 }}
        transition={{ type: "spring", damping: 25 }}
      >
        <div className="p-6 md:p-8">
          <div className="flex justify-between items-center mb-6">
            <div className="flex items-center">
              <div className="relative w-12 h-12 mr-4 overflow-hidden rounded-lg">
                <Image 
                  src="/logo.jpeg" 
                  alt="FlowbitAI Logo"
                  width={48}
                  height={48}
                  className="object-cover"
                />
              </div>
              <h2 className="text-3xl font-bold bg-gradient-to-r from-primary-500 to-secondary-500 bg-clip-text text-transparent">
                FlowbitAI Multi-Agent System
              </h2>
            </div>
            <button 
              onClick={onClose}
              className="text-gray-400 hover:text-white transition-colors"
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <div className="space-y-8">
            {/* System Overview */}
            <section>
              <h3 className="text-2xl font-bold text-primary-700 mb-3">System Overview</h3>
              <p className="text-secondary-700 mb-4">
                FlowbitAI is a cutting-edge multi-agent system designed to autonomously process diverse input formats (Email, JSON, PDF), 
                intelligently classify both format and business intent, and dynamically trigger appropriate actions based on content analysis.
              </p>
              <div className="bg-secondary-50 rounded-lg p-4 border border-secondary-200">
                <h4 className="text-lg font-semibold text-primary-600 mb-2">Key Capabilities:</h4>
                <ul className="list-disc list-inside space-y-1 text-secondary-700">
                  <li>Multi-format input processing (Email, JSON, PDF)</li>
                  <li>Intelligent intent classification (RFQ, Complaint, Invoice, Regulation, Fraud Risk)</li>
                  <li>Contextual priority determination (High, Medium, Low)</li>
                  <li>Specialized agent-based processing</li>
                  <li>Dynamic action routing based on content analysis</li>
                  <li>Complete audit trail via shared memory store</li>
                </ul>
              </div>
            </section>

            {/* Architecture */}
            <section>
              <h3 className="text-2xl font-bold text-primary-700 mb-3">System Architecture</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="bg-secondary-50 rounded-lg p-4 border border-secondary-200">
                  <h4 className="text-lg font-semibold text-primary-600 mb-2">1. Classifier Agent</h4>
                  <p className="text-secondary-700">
                    The system's entry point that analyzes incoming data to determine:
                  </p>
                  <ul className="list-disc list-inside mt-2 text-secondary-700">
                    <li>Input format (Email, JSON, PDF)</li>
                    <li>Business intent using keyword matching</li>
                    <li>Priority level based on content analysis</li>
                    <li>Confidence score for classification accuracy</li>
                  </ul>
                </div>

                <div className="bg-secondary-50 rounded-lg p-4 border border-secondary-200">
                  <h4 className="text-lg font-semibold text-primary-600 mb-2">2. Specialized Processing Agents</h4>
                  <p className="text-secondary-700 mb-2">
                    Format-specific agents that extract and analyze relevant information:
                  </p>
                  <ul className="list-disc list-inside text-secondary-700">
                    <li><span className="text-primary-600">Email Agent:</span> Extracts structured fields, analyzes tone and urgency</li>
                    <li><span className="text-primary-600">JSON Agent:</span> Validates schema, detects anomalies and suspicious patterns</li>
                    <li><span className="text-primary-600">PDF Agent:</span> Extracts text and structured data from documents</li>
                  </ul>
                </div>

                <div className="bg-secondary-50 rounded-lg p-4 border border-secondary-200">
                  <h4 className="text-lg font-semibold text-primary-600 mb-2">3. Shared Memory Store</h4>
                  <p className="text-secondary-700">
                    Central repository that maintains the complete processing context:
                  </p>
                  <ul className="list-disc list-inside mt-2 text-secondary-700">
                    <li>Input metadata and raw content</li>
                    <li>Classification results and confidence scores</li>
                    <li>Agent processing results and extracted data</li>
                    <li>Chronological trace of all system actions</li>
                    <li>Final action results and timestamps</li>
                  </ul>
                </div>

                <div className="bg-secondary-50 rounded-lg p-4 border border-secondary-200">
                  <h4 className="text-lg font-semibold text-primary-600 mb-2">4. Action Router</h4>
                  <p className="text-secondary-700">
                    Decision engine that determines appropriate follow-up actions:
                  </p>
                  <ul className="list-disc list-inside mt-2 text-secondary-700">
                    <li>Evaluates classification, priority, and agent outputs</li>
                    <li>Triggers contextual actions (create ticket, alert, log)</li>
                    <li>Simulates external API calls to business systems</li>
                    <li>Records detailed action reasoning for auditability</li>
                  </ul>
                </div>
              </div>
            </section>

            {/* Processing Flow */}
            <section>
              <h3 className="text-2xl font-bold text-primary-700 mb-3">End-to-End Processing Flow</h3>
              <div className="bg-secondary-50 rounded-lg p-4 border border-secondary-200">
                <ol className="list-decimal list-inside space-y-3 text-secondary-700">
                  <li className="pb-3 border-b border-secondary-200">
                    <span className="text-primary-600 font-semibold">Input Reception:</span>
                    <p className="mt-1 ml-6 text-sm">System receives data via file upload, JSON input, or email content</p>
                  </li>
                  <li className="pb-3 border-b border-secondary-200">
                    <span className="text-primary-600 font-semibold">Classification:</span>
                    <p className="mt-1 ml-6 text-sm">Classifier Agent determines format, intent, confidence, and priority</p>
                  </li>
                  <li className="pb-3 border-b border-secondary-200">
                    <span className="text-primary-600 font-semibold">Specialized Processing:</span>
                    <p className="mt-1 ml-6 text-sm">Format-specific agent processes content to extract structured data and perform analysis</p>
                  </li>
                  <li className="pb-3 border-b border-secondary-200">
                    <span className="text-primary-600 font-semibold">Action Determination:</span>
                    <p className="mt-1 ml-6 text-sm">Action Router evaluates all data points to determine appropriate follow-up action</p>
                  </li>
                  <li>
                    <span className="text-primary-600 font-semibold">Action Execution:</span>
                    <p className="mt-1 ml-6 text-sm">System executes determined action and records complete trace in memory store</p>
                  </li>
                </ol>
              </div>
            </section>

            {/* Technical Implementation */}
            <section>
              <h3 className="text-2xl font-bold text-primary-700 mb-3">Technical Implementation</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="bg-secondary-50 rounded-lg p-4 border border-secondary-200">
                  <h4 className="text-lg font-semibold text-primary-600 mb-2">Backend Technologies</h4>
                  <ul className="list-disc list-inside space-y-1 text-secondary-700">
                    <li>Python with FastAPI for asynchronous processing</li>
                    <li>SQLite for shared memory persistence</li>
                    <li>PyPDF2 for PDF content extraction</li>
                    <li>Email parsing with Python's email module</li>
                    <li>JSON schema validation and anomaly detection</li>
                    <li>Simulated external API integrations</li>
                  </ul>
                </div>

                <div className="bg-secondary-50 rounded-lg p-4 border border-secondary-200">
                  <h4 className="text-lg font-semibold text-primary-600 mb-2">Frontend Technologies</h4>
                  <ul className="list-disc list-inside space-y-1 text-secondary-700">
                    <li>Next.js for React-based UI framework</li>
                    <li>Tailwind CSS for responsive design</li>
                    <li>Framer Motion for smooth animations</li>
                    <li>Axios for API communication</li>
                    <li>React Dropzone for file uploads</li>
                    <li>React JSON View for structured data display</li>
                  </ul>
                </div>
              </div>
            </section>

            {/* Use Cases */}
            <section>
              <h3 className="text-2xl font-bold text-primary-700 mb-3">Key Use Cases</h3>
              <div className="space-y-4">
                <div className="bg-secondary-50 rounded-lg p-4 border border-secondary-200">
                  <h4 className="text-lg font-semibold text-primary-600 mb-2">Fraud Detection</h4>
                  <p className="text-secondary-700">
                    The system identifies suspicious patterns in transactions or security alerts, 
                    flags them as high priority, and triggers immediate notifications to security teams.
                  </p>
                </div>

                <div className="bg-secondary-50 rounded-lg p-4 border border-secondary-200">
                  <h4 className="text-lg font-semibold text-primary-600 mb-2">Customer Service Automation</h4>
                  <p className="text-secondary-700">
                    Incoming customer emails are analyzed for tone and urgency, with complaints 
                    automatically routed to CRM systems and prioritized based on severity.
                  </p>
                </div>

                <div className="bg-secondary-50 rounded-lg p-4 border border-secondary-200">
                  <h4 className="text-lg font-semibold text-primary-600 mb-2">Compliance Monitoring</h4>
                  <p className="text-secondary-700">
                    PDF documents are scanned for regulatory keywords (GDPR, FDA), with compliance 
                    risks automatically flagged and escalated to legal teams.
                  </p>
                </div>
              </div>
            </section>

            {/* Future Enhancements */}
            <section>
              <h3 className="text-2xl font-bold text-primary-700 mb-3">Future Enhancements</h3>
              <div className="bg-secondary-50 rounded-lg p-4 border border-secondary-200">
                <ul className="list-disc list-inside space-y-2 text-secondary-700">
                  <li>Integration with machine learning models for improved classification accuracy</li>
                  <li>Natural language processing for deeper content understanding</li>
                  <li>Real-time monitoring dashboard for system performance</li>
                  <li>Expanded input format support (audio, images, structured data)</li>
                  <li>Containerization for scalable deployment</li>
                  <li>Advanced anomaly detection using statistical models</li>
                </ul>
              </div>
            </section>

            <div className="text-center pt-4 border-t border-secondary-200">
              <p className="text-secondary-500 text-sm">
                Developed by Pranay J Sathish for FlowbitAI • {new Date().getFullYear()}
              </p>
            </div>
          </div>
        </div>
      </motion.div>
    </motion.div>
  );
}
