import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { CheckCircle, AlertTriangle, Star, BookOpen } from 'lucide-react';

interface ResultsProps {
    interviewId: string;
}

const Results: React.FC<ResultsProps> = ({ interviewId }) => {
    const [data, setData] = useState<any>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchResults = async () => {
            console.log('[Results] Fetching results for interview:', interviewId);
            try {
                // Trigger evaluation first
                console.log('[Results] Triggering evaluation...');
                await axios.post(`http://localhost:8000/interview/${interviewId}/evaluate`);
                console.log('[Results] Evaluation triggered successfully');
                
                // Then fetch full data
                console.log('[Results] Fetching interview data...');
                const response = await axios.get(`http://localhost:8000/interview/${interviewId}`);
                console.log('[Results] Data received:', {
                    hasData: !!response.data,
                    matchScore: response.data?.match_score,
                    hasEvaluation: !!response.data?.evaluation
                });
                setData(response.data);
            } catch (error: any) {
                console.error('[Results] Error fetching results:', error);
                console.error('[Results] Error details:', {
                    message: error.message,
                    response: error.response?.data,
                    status: error.response?.status
                });
            } finally {
                setLoading(false);
                console.log('[Results] Loading completed');
            }
        };

        fetchResults();
    }, [interviewId]);

    if (loading) {
        return (
            <div className="flex justify-center items-center h-64">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            </div>
        );
    }

    if (!data) return <div>No data available</div>;

    const { match_score, evaluation, gap_analysis } = data;

    return (
        <div className="max-w-4xl mx-auto p-6 space-y-6">
            <h2 className="text-3xl font-bold text-gray-800 mb-8">Interview Results</h2>

            {/* Scores Grid */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
                    <p className="text-gray-500 text-sm mb-2">Match Score</p>
                    <div className="text-3xl font-bold text-blue-600">{match_score?.toFixed(1)}%</div>
                </div>
                <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
                    <p className="text-gray-500 text-sm mb-2">Technical</p>
                    <div className="text-3xl font-bold text-green-600">{evaluation?.technical_score}/100</div>
                </div>
                <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
                    <p className="text-gray-500 text-sm mb-2">Communication</p>
                    <div className="text-3xl font-bold text-purple-600">{evaluation?.communication_score}/100</div>
                </div>
                <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
                    <p className="text-gray-500 text-sm mb-2">Overall</p>
                    <div className="text-3xl font-bold text-indigo-600">{evaluation?.overall_score}/100</div>
                </div>
            </div>

            {/* Recommendation */}
            <div className={`p-6 rounded-xl border-l-4 ${evaluation?.recommendation === 'Strong Hire' ? 'bg-green-50 border-green-500' :
                    evaluation?.recommendation === 'Hire' ? 'bg-blue-50 border-blue-500' :
                        'bg-red-50 border-red-500'
                }`}>
                <h3 className="text-lg font-semibold mb-2">Recommendation</h3>
                <p className="text-xl font-bold">{evaluation?.recommendation}</p>
            </div>

            {/* Feedback */}
            <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
                <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                    <Star className="w-5 h-5 text-yellow-500" />
                    Detailed Feedback
                </h3>
                <p className="text-gray-700 whitespace-pre-line">{evaluation?.feedback}</p>
            </div>

            {/* Gap Analysis */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
                    <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                        <AlertTriangle className="w-5 h-5 text-orange-500" />
                        Missing Skills
                    </h3>
                    <div className="flex flex-wrap gap-2">
                        {gap_analysis?.missing_skills?.map((skill: string, idx: number) => (
                            <span key={idx} className="px-3 py-1 bg-orange-100 text-orange-800 rounded-full text-sm">
                                {skill}
                            </span>
                        ))}
                    </div>
                </div>

                <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
                    <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                        <BookOpen className="w-5 h-5 text-blue-500" />
                        Experience Gap
                    </h3>
                    <p className="text-gray-700">{gap_analysis?.experience_gap}</p>
                </div>
            </div>
        </div>
    );
};

export default Results;
