# FlowbitAI Multi-Agent System UI

This directory contains the frontend UI for the FlowbitAI Multi-Agent Processing System.

## Technology Stack

- **React** - Frontend library
- **Next.js** - React framework
- **Tailwind CSS** - Utility-first CSS framework
- **Axios** - HTTP client for API requests

## Features

- Dashboard overview with system status
- File upload interface for Email, JSON, and PDF files
- Real-time processing visualization
- Results display with formatted output
- Processing history and audit logs

## Setup and Installation

1. Install dependencies:
```bash
cd ui
npm install
```

2. Run the development server:
```bash
npm run dev
```

3. Build for production:
```bash
npm run build
```

## Development

The UI communicates with the FastAPI backend running on `http://localhost:8000`.
