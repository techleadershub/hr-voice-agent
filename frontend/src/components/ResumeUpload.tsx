import React, { useState } from 'react';
import axios from 'axios';
import { Upload, FileText, User, Briefcase } from 'lucide-react';

interface ResumeUploadProps {
  onUploadSuccess: (data: any) => void;
}

const ResumeUpload: React.FC<ResumeUploadProps> = ({ onUploadSuccess }) => {
  const [file, setFile] = useState<File | null>(null);
  const [name, setName] = useState('');
  const [jd, setJd] = useState('');
  const [loading, setLoading] = useState(false);

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    console.log('[ResumeUpload] Form submit clicked');
    
    if (!file || !name || !jd) {
      console.warn('[ResumeUpload] Validation failed:', { hasFile: !!file, hasName: !!name, hasJd: !!jd });
      return;
    }

    console.log('[ResumeUpload] Starting upload:', { 
      fileName: file.name, 
      fileSize: file.size, 
      candidateName: name,
      jobDescriptionLength: jd.length 
    });

    setLoading(true);
    const formData = new FormData();
    formData.append('file', file);
    formData.append('candidate_name', name);
    formData.append('job_description', jd);

    try {
      console.log('[ResumeUpload] Sending POST request to /upload_resume');
      const response = await axios.post('http://localhost:8000/upload_resume', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      console.log('[ResumeUpload] Upload successful:', response.data);
      onUploadSuccess(response.data);
    } catch (error: any) {
      console.error('[ResumeUpload] Upload failed:', error);
      console.error('[ResumeUpload] Error details:', {
        message: error.message,
        response: error.response?.data,
        status: error.response?.status
      });
      alert('Upload failed. Please try again.');
    } finally {
      setLoading(false);
      console.log('[ResumeUpload] Upload process completed');
    }
  };

  return (
    <div className="max-w-2xl mx-auto p-6 bg-white rounded-xl shadow-lg">
      <h2 className="text-2xl font-bold mb-6 text-gray-800 flex items-center gap-2">
        <FileText className="w-6 h-6 text-blue-600" />
        Start New Interview
      </h2>
      
      <form onSubmit={handleUpload} className="space-y-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2 flex items-center gap-2">
            <User className="w-4 h-4" /> Candidate Name
          </label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="Enter candidate name"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2 flex items-center gap-2">
            <Briefcase className="w-4 h-4" /> Job Description
          </label>
          <textarea
            value={jd}
            onChange={(e) => setJd(e.target.value)}
            className="w-full p-3 border border-gray-300 rounded-lg h-32 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="Paste job description here..."
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2 flex items-center gap-2">
            <Upload className="w-4 h-4" /> Resume (PDF/Text)
          </label>
          <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-blue-500 transition-colors">
            <input
              type="file"
              onChange={(e) => {
                const selectedFile = e.target.files?.[0] || null;
                console.log('[ResumeUpload] File selected:', selectedFile ? { name: selectedFile.name, size: selectedFile.size, type: selectedFile.type } : 'none');
                setFile(selectedFile);
              }}
              className="hidden"
              id="resume-upload"
              accept=".txt,.pdf,.docx"
            />
            <label htmlFor="resume-upload" className="cursor-pointer">
              {file ? (
                <span className="text-blue-600 font-medium">{file.name}</span>
              ) : (
                <span className="text-gray-500">Click to upload or drag and drop</span>
              )}
            </label>
          </div>
        </div>

        <button
          type="submit"
          disabled={loading}
          className={`w-full py-3 px-4 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors ${
            loading ? 'opacity-50 cursor-not-allowed' : ''
          }`}
        >
          {loading ? 'Processing...' : 'Start Interview'}
        </button>
      </form>
    </div>
  );
};

export default ResumeUpload;
