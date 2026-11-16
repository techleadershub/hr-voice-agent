# HR Voice Agent - Smart Recruiter Application

An AI-powered HR voice agent application that conducts intelligent interviews, analyzes resumes, and evaluates candidates using OpenAI's LLM, TTS, and Whisper technologies.

## Features

- **Resume Analysis**: Upload and analyze candidate resumes
- **Skill Matching**: Automatically match candidate skills with job requirements
- **Voice Interviews**: Conduct AI-powered voice interviews via WebSocket
- **Gap Analysis**: Identify missing skills and experience gaps
- **Automated Evaluation**: Generate comprehensive candidate evaluations

## Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.11+** - [Download Python](https://www.python.org/downloads/)
- **Node.js 18+** - [Download Node.js](https://nodejs.org/)
- **OpenAI API Key** - Get your API key from [OpenAI Platform](https://platform.openai.com/api-keys)

## Quick Start

### 1. Clone or Extract the Project

```bash
# If using git
git clone <repository-url>
cd anchorproject

# Or extract the zip file and navigate to the project directory
```

### 2. Set Up Environment Variables

Create a `.env` file in the root directory (or set environment variables):

**Option A: Create `.env` file (Recommended)**
```bash
# Create .env file in project root
OPENAI_API_KEY=sk-your-openai-api-key-here
```

**Option B: Set Environment Variable (Windows PowerShell)**
```powershell
$env:OPENAI_API_KEY="sk-your-openai-api-key-here"
```

**Option C: Set Environment Variable (Windows CMD)**
```cmd
set OPENAI_API_KEY=sk-your-openai-api-key-here
```

**Option D: Set Environment Variable (Linux/Mac)**
```bash
export OPENAI_API_KEY="sk-your-openai-api-key-here"
```

### 3. Install Backend Dependencies

Open a terminal in the project root directory:

```bash
pip install -r backend/requirements.txt
```

**Note**: It's recommended to use a virtual environment:
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Then install dependencies
pip install -r backend/requirements.txt
```

### 4. Install Frontend Dependencies

In the same or a new terminal:

```bash
cd frontend
npm install
```

### 5. Start the Backend Server

From the **project root** directory (not inside the `backend` folder):

```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

The backend will start on `http://localhost:8000`

**Verify backend is running**: Open `http://localhost:8000/docs` in your browser to see the API documentation.

### 6. Start the Frontend Development Server

Open a **new terminal** window:

```bash
cd frontend
npm run dev
```

The frontend will start on `http://localhost:5173` (or another port if 5173 is busy - check the terminal output).

### 7. Access the Application

Open your web browser and navigate to:
- **Frontend**: http://localhost:5173
- **Backend API Docs**: http://localhost:8000/docs

## Quick Start (Windows PowerShell Script)

If you're on Windows, you can use the provided PowerShell script to automatically start both services:

```powershell
.\start-services.ps1
```

This script will:
- Check if services are already running
- Start the frontend in a new window (if not running)
- Start the backend in a new window (if not running)
- Display the URLs to access the application

## Project Structure

```
anchorproject/
├── backend/              # Python FastAPI backend
│   ├── agents/          # AI agents (matching, gap analysis, interview, etc.)
│   ├── services/        # Core services (database, vector store, voice)
│   ├── tests/           # Unit tests
│   ├── main.py          # FastAPI application entry point
│   └── requirements.txt # Python dependencies
├── frontend/            # React + TypeScript frontend
│   ├── src/            # Source code
│   ├── package.json    # Node.js dependencies
│   └── vite.config.ts  # Vite configuration
├── data/               # SQLite database (created automatically)
├── qdrant_data/        # Vector database storage (created automatically)
├── Dockerfile          # Docker configuration
├── DEPLOYMENT.md       # AWS deployment guide
└── README.md           # This file
```

## Environment Variables

### Required

- `OPENAI_API_KEY` - Your OpenAI API key for LLM, TTS, and Whisper services

### Optional

- `QDRANT_URL` - External Qdrant server URL (if not provided, uses local storage)
- `QDRANT_API_KEY` - Qdrant API key (if using external Qdrant)

## Running with Docker

You can also run the entire application using Docker:

### Build the Docker Image

```bash
docker build -t hr-voice-agent:latest .
```

### Run the Container

```bash
docker run -p 8000:8000 -e OPENAI_API_KEY=your-key-here hr-voice-agent:latest
```

This will run both frontend and backend together on port 8000. Access the application at `http://localhost:8000`.

## Automatic Directory Creation

The following directories and files are created automatically on first run:

- `data/` directory and `interviews.db` - Created when the backend starts
- `qdrant_data/` directory - Created when you first upload a resume

You don't need to create these manually.

## Troubleshooting

### Backend Issues

**Port 8000 already in use:**
```bash
# Use a different port
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8001
```

**Module not found errors:**
- Ensure you're running from the project root directory
- Verify all dependencies are installed: `pip install -r backend/requirements.txt`
- Check that `PYTHONPATH` includes the project root

**OpenAI API errors:**
- Verify your `OPENAI_API_KEY` is set correctly
- Check that you have sufficient API credits
- Ensure the API key has access to GPT-4, TTS, and Whisper models

### Frontend Issues

**Port 5173 already in use:**
- Vite will automatically use the next available port
- Check the terminal output for the actual port number

**Cannot connect to backend:**
- Ensure the backend is running on port 8000
- Check that CORS is enabled (it should be by default)
- Verify the API URL in `frontend/src/config/api.ts`

**npm install fails:**
- Try deleting `node_modules` and `package-lock.json`, then run `npm install` again
- Ensure you have Node.js 18+ installed

### General Issues

**Database errors:**
- The `data/` directory should be created automatically
- Ensure the application has write permissions in the project directory

**Vector store errors:**
- The `qdrant_data/` directory should be created automatically
- For first-time setup, sentence-transformers will download models (~80MB)

## Development

### Running Tests

**Backend tests:**
```bash
# From project root
pytest backend/tests/
```

**Frontend tests:**
```bash
cd frontend
npm test
```

### API Documentation

Once the backend is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Deployment

For production deployment instructions, see [DEPLOYMENT.md](DEPLOYMENT.md).

## License

[Add your license information here]

## Support

[Add support/contact information here]

