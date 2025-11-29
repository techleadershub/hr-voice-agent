import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import App from './App';

describe('App', () => {
  it('renders the Smart HR Recruiter header', () => {
    render(<App />);
    const headerElement = screen.getByText(/Smart HR Recruiter/i);
    expect(headerElement).toBeInTheDocument();
  });

  it('renders the upload step indicator', () => {
    render(<App />);
    const uploadStep = screen.getByText(/1. Upload/i);
    expect(uploadStep).toBeInTheDocument();
  });

  it('renders the interview step indicator', () => {
    render(<App />);
    const interviewStep = screen.getByText(/2. Interview/i);
    expect(interviewStep).toBeInTheDocument();
  });

  it('renders the results step indicator', () => {
    render(<App />);
    const resultsStep = screen.getByText(/3. Results/i);
    expect(resultsStep).toBeInTheDocument();
  });
});

