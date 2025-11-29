import React, { useState } from 'react';
import ResumeUpload from './components/ResumeUpload';
import InterviewInterface from './components/InterviewInterface';
import Results from './components/Results';
import { Bot } from 'lucide-react';

function App() {
    const [view, setView] = useState<'upload' | 'interview' | 'results'>('upload');
    const [interviewId, setInterviewId] = useState<string | null>(null);

    const handleUploadSuccess = (data: any) => {
        console.log('[App] Upload success, switching to interview view:', data);
        setInterviewId(data.interview_id);
        setView('interview');
    };

    const handleInterviewComplete = () => {
        console.log('[App] Interview complete, switching to results view');
        setView('results');
    };

    return (
        <div className="min-h-screen bg-gray-50 font-sans text-gray-900">
            {/* Header */}
            <header className="bg-white shadow-sm sticky top-0 z-10">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <div className="bg-blue-600 p-2 rounded-lg">
                            <Bot className="w-6 h-6 text-white" />
                        </div>
                        <h1 className="text-xl font-bold text-gray-900">Smart HR Recruiter</h1>
                    </div>
                    <div className="flex items-center gap-4 text-sm text-gray-500">
                        <span className={view === 'upload' ? 'text-blue-600 font-medium' : ''}>1. Upload</span>
                        <span>→</span>
                        <span className={view === 'interview' ? 'text-blue-600 font-medium' : ''}>2. Interview</span>
                        <span>→</span>
                        <span className={view === 'results' ? 'text-blue-600 font-medium' : ''}>3. Results</span>
                    </div>
                </div>
            </header>

            {/* Main Content */}
            <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                {view === 'upload' && (
                    <ResumeUpload onUploadSuccess={handleUploadSuccess} />
                )}

                {view === 'interview' && interviewId && (
                    <InterviewInterface
                        interviewId={interviewId}
                        onComplete={handleInterviewComplete}
                    />
                )}

                {view === 'results' && interviewId && (
                    <Results interviewId={interviewId} />
                )}
            </main>
        </div>
    );
}

export default App;
