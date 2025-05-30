import { motion } from 'framer-motion';
import Image from 'next/image';
import { useState } from 'react';
import About from './About';

export default function Header() {
  const [showAbout, setShowAbout] = useState(false);
  
  return (
    <>
      <motion.header 
        className="bg-white border-b border-secondary-200 shadow-sm"
        initial={{ y: -100 }}
        animate={{ y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <div className="container mx-auto px-4 py-6 flex justify-between items-center">
          <div className="flex items-center">
            <div className="relative w-10 h-10 mr-3 overflow-hidden rounded-lg">
              <Image 
                src="/logo.jpeg" 
                alt="FlowbitAI Logo"
                width={40}
                height={40}
                className="object-cover"
              />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-primary-600">FlowbitAI</h1>
              <p className="text-sm text-secondary-500">Multi-Agent Processing System</p>
            </div>
          </div>
          
          <div className="hidden md:flex items-center space-x-6">
            <button 
              onClick={() => setShowAbout(true)} 
              className="text-secondary-600 hover:text-primary-600 transition-colors font-medium"
            >
              About
            </button>
            <a 
              href="https://github.com/yourusername/flowbit-ai-multi-agent" 
              target="_blank" 
              rel="noopener noreferrer" 
              className="text-secondary-600 hover:text-primary-600 transition-colors font-medium"
            >
              GitHub
            </a>
          </div>
        </div>
      </motion.header>
      
      {showAbout && <About onClose={() => setShowAbout(false)} />}
    </>
  );
}