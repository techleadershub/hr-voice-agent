# HR Voice Agent - Smart Recruiter Application

An AI-powered HR voice agent application that conducts intelligent interviews, analyzes resumes, and evaluates candidates using OpenAI's LLM, TTS, and Whisper technologies.

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![Node.js](https://img.shields.io/badge/Node.js-18+-green.svg)](https://nodejs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18+-61DAFB.svg)](https://reactjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-3178C6.svg)](https://www.typescriptlang.org/)

## ✨ Features

- **📄 Resume Analysis**: Upload and analyze candidate resumes with intelligent parsing
- **🎯 Skill Matching**: Automatically match candidate skills with job requirements using vector similarity
- **🎤 Voice Interviews**: Conduct AI-powered voice interviews via WebSocket with real-time transcription
- **📊 Gap Analysis**: Identify missing skills and experience gaps between candidates and job requirements
- **✅ Automated Evaluation**: Generate comprehensive candidate evaluations with detailed scoring
- **🔍 Vector Search**: Semantic search capabilities using Qdrant vector database
- **🌐 Modern UI**: Beautiful, responsive React frontend with Tailwind CSS

## Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.11+** - [Download Python](https://www.python.org/downloads/)
- **Node.js 18+** - [Download Node.js](https://nodejs.org/)
- **OpenAI API Key** - Get your API key from [OpenAI Platform](https://platform.openai.com/api-keys)

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/techleadershub/hr-voice-agent.git
cd hr-voice-agent
```

### 2. Set Up Environment Variables

Create a `.env` file in the root directory:

```bash
# Copy the example file
cp .env.example .env

# Edit .env and add your OpenAI API key
nano .env  # or use your preferred editor
```

Add your OpenAI API key:
```env
OPENAI_API_KEY=sk-your-openai-api-key-here
```

**Get your API key**: Visit [OpenAI Platform](https://platform.openai.com/api-keys) to create an API key.

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

## 🏗️ Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **LangChain** - LLM application framework
- **LangGraph** - Multi-agent workflow orchestration
- **OpenAI** - GPT-4, Whisper, and TTS APIs
- **Qdrant** - Vector database for semantic search
- **SQLite** - Lightweight database for interview data
- **Sentence Transformers** - Embedding models

### Frontend
- **React 18** - UI library
- **TypeScript** - Type-safe JavaScript
- **Vite** - Fast build tool
- **Tailwind CSS** - Utility-first CSS framework
- **Lucide React** - Icon library

## 📁 Project Structure

```
hr-voice-agent/
├── backend/                    # Python FastAPI backend
│   ├── agents/                # AI agents
│   │   ├── matching_agent.py      # Resume-job matching
│   │   ├── gap_analysis_agent.py  # Skill gap analysis
│   │   ├── question_agent.py      # Interview question generation
│   │   ├── interview_agent.py     # Voice interview orchestration
│   │   └── evaluation_agent.py    # Candidate evaluation
│   ├── services/              # Core services
│   │   ├── database_service.py    # SQLite operations
│   │   ├── vector_store_service.py # Qdrant operations
│   │   ├── embedding_service.py   # Text embeddings
│   │   └── voice_service.py       # OpenAI TTS/Whisper
│   ├── tests/                 # Unit tests
│   ├── main.py               # FastAPI application
│   ├── workflow.py            # LangGraph workflow
│   └── requirements.txt      # Python dependencies
├── frontend/                  # React + TypeScript frontend
│   ├── src/
│   │   ├── components/       # React components
│   │   ├── config/           # Configuration
│   │   └── main.tsx          # Entry point
│   ├── package.json          # Node.js dependencies
│   └── vite.config.ts        # Vite configuration
├── data/                     # SQLite database (auto-created)
├── qdrant_data/              # Vector database (auto-created)
├── Dockerfile                 # Docker configuration
├── EC2_DEPLOYMENT.md         # EC2 deployment guide
├── DOMAIN_SETUP.md           # Domain configuration guide
├── .env.example              # Environment variables template
└── README.md                 # This file
```

## Environment Variables

### Required

- `OPENAI_API_KEY` - Your OpenAI API key for LLM, TTS, and Whisper services

### Optional

- `QDRANT_URL` - External Qdrant server URL (if not provided, uses local storage)
- `QDRANT_API_KEY` - Qdrant API key (if using external Qdrant)

## 🐳 Running with Docker

You can run the entire application using Docker for a simplified setup:

### Build the Docker Image

```bash
docker build -t hr-voice-agent:latest .
```

### Run the Container

```bash
docker run -p 8000:8000 \
  --env-file .env \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/qdrant_data:/app/qdrant_data \
  hr-voice-agent:latest
```

This will run both frontend and backend together on port 8000. Access the application at `http://localhost:8000`.

**Note**: The `-v` flags mount volumes to persist your data between container restarts.

## 📝 How It Works

1. **Resume Upload**: Candidate uploads their resume and job description
2. **Matching Analysis**: AI analyzes resume and matches skills with job requirements
3. **Gap Analysis**: Identifies missing skills and experience gaps
4. **Question Generation**: Creates personalized interview questions
5. **Voice Interview**: Conducts real-time voice interview via WebSocket
6. **Evaluation**: Generates comprehensive candidate evaluation report

## 🔧 Automatic Directory Creation

The following directories and files are created automatically on first run:

- `data/` directory and `interviews.db` - Created when the backend starts
- `qdrant_data/` directory - Created when you first upload a resume

You don't need to create these manually.

## 🐛 Troubleshooting

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

## 💻 Development

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

## 🚀 Deployment

For production deployment instructions, see:
- [EC2_DEPLOYMENT.md](EC2_DEPLOYMENT.md) - Deploy to AWS EC2
- [DOMAIN_SETUP.md](DOMAIN_SETUP.md) - Configure custom domain

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License.

Copyright (c) 2025 Ascend IT Career OPC Private Limited

See the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [OpenAI](https://openai.com/) for GPT-4, Whisper, and TTS APIs
- [LangChain](https://www.langchain.com/) for LLM orchestration
- [Qdrant](https://qdrant.tech/) for vector search capabilities
- [FastAPI](https://fastapi.tiangolo.com/) for the excellent web framework
- [React](https://reactjs.org/) and [Vite](https://vitejs.dev/) for the frontend

## 📧 Contact

For questions or support, please open an issue on GitHub.

---

⭐ If you find this project helpful, please consider giving it a star!

