import { useState } from 'react';
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
            {/* Skip to content - Hidden by default, visible on focus for accessibility */}
            <a 
                href="#main" 
                className="absolute left-[-9999px] focus:left-4 focus:top-4 focus:z-[100] focus:px-4 focus:py-2 focus:bg-blue-600 focus:text-white focus:rounded-lg focus:shadow-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
                Skip to content
            </a>

            {/* Header with Navigation */}
            <header className="bg-white border-b border-gray-200 fixed top-0 left-0 z-50 w-full shadow-sm">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="flex items-center justify-between h-16">
                        <a href="/" className="focus-visible:focus-visible inline-flex" aria-label="Homepage">
                            <div className="bg-blue-600 p-2 rounded-lg">
                                <Bot className="w-6 h-6 text-white" />
                            </div>
                        </a>
                        <div className="flex items-center gap-4 text-sm">
                            <span className={view === 'upload' ? 'text-blue-600 font-medium' : 'text-gray-500'}>1. Upload</span>
                            <span className="text-gray-400">→</span>
                            <span className={view === 'interview' ? 'text-blue-600 font-medium' : 'text-gray-500'}>2. Interview</span>
                            <span className="text-gray-400">→</span>
                            <span className={view === 'results' ? 'text-blue-600 font-medium' : 'text-gray-500'}>3. Results</span>
                        </div>
                    </div>
                </div>
            </header>

            {/* Main Content */}
            <main id="main" className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 pt-24">
                <section className="container">
                    <article className="grid-cursor border-theme-border-02 mb-v3 gap-y-0">
                        <div className="col-span-full grid grid-cols-subgrid *:col-span-full md:col-start-1 md:col-end-19 lg:col-start-1 lg:col-end-17 xl:col-start-7 xl:col-end-19">
                            <div className="prose prose--block prose--blog col-span-full">
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
                            </div>
                        </div>
                    </article>
                </section>
            </main>
        </div>
    );
}

export default App;
