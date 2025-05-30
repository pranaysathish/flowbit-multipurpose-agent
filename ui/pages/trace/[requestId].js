import { useRouter } from 'next/router';
import Head from 'next/head';
import ProcessingTrace from '../../components/ProcessingTrace';

export default function TracePage() {
  const router = useRouter();
  const { requestId } = router.query;

  return (
    <>
      <Head>
        <title>Processing Trace | FlowbitAI</title>
        <meta name="description" content="Detailed processing trace for FlowbitAI multi-agent system" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      {requestId ? (
        <ProcessingTrace requestId={requestId} />
      ) : (
        <div className="min-h-screen bg-secondary-50 p-6 flex items-center justify-center">
          <div className="bg-white rounded-lg shadow-sm border border-secondary-200 p-6 max-w-md">
            <h1 className="text-2xl font-bold text-primary-700 mb-4">Request ID Required</h1>
            <p className="text-secondary-700 mb-4">
              Please provide a valid request ID to view the processing trace.
            </p>
            <button 
              onClick={() => router.push('/')} 
              className="px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
            >
              Back to Home
            </button>
          </div>
        </div>
      )}
    </>
  );
}
