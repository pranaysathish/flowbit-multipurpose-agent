export default function Footer() {
    return (
      <footer className="bg-dark-300 border-t border-gray-800 py-6">
        <div className="container mx-auto px-4">
          <div className="flex flex-col md:flex-row justify-between items-center">
            <div className="mb-4 md:mb-0">
              <p className="text-gray-400 text-sm">
                &copy; {new Date().getFullYear()} FlowbitAI Technologies. All rights reserved.
              </p>
            </div>
            {/* Footer links removed as requested */}
          </div>
        </div>
      </footer>
    );
  }