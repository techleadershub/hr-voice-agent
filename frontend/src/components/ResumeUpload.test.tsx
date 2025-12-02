import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import ResumeUpload from './ResumeUpload';

describe('ResumeUpload', () => {
  const mockOnUploadSuccess = vi.fn();

  it('renders the upload form', () => {
    render(<ResumeUpload onUploadSuccess={mockOnUploadSuccess} />);
    expect(screen.getByText(/Start New Interview/i)).toBeInTheDocument();
  });

  it('renders candidate name input', () => {
    render(<ResumeUpload onUploadSuccess={mockOnUploadSuccess} />);
    const nameInput = screen.getByPlaceholderText(/Enter candidate name/i);
    expect(nameInput).toBeInTheDocument();
  });

  it('renders job description textarea', () => {
    render(<ResumeUpload onUploadSuccess={mockOnUploadSuccess} />);
    const jdTextarea = screen.getByPlaceholderText(/Paste job description here/i);
    expect(jdTextarea).toBeInTheDocument();
  });

  it('renders file upload input', () => {
    render(<ResumeUpload onUploadSuccess={mockOnUploadSuccess} />);
    const fileInput = document.getElementById('resume-upload');
    expect(fileInput).toBeInTheDocument();
    expect(fileInput?.getAttribute('type')).toBe('file');
  });

  it('renders submit button', () => {
    render(<ResumeUpload onUploadSuccess={mockOnUploadSuccess} />);
    const submitButton = screen.getByRole('button', { name: /Start Interview/i });
    expect(submitButton).toBeInTheDocument();
  });
});

