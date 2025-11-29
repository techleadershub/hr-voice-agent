## Week 3 Final Plan: Smart HR Recruiter Agent (MVP Version)

### **Product Positioning: B2B for HR**

**Target:** HR departments, recruitment agencies, hiring managers  
**Value:** Automated resume screening \+ AI-conducted interviews \+ Objective evaluation  
**Use Case:** High-volume hiring, technical role screening, initial candidate filtering

---

### **Practice Colabs (Learning Exercises)**

#### **Practice 1: Embeddings & Vector Stores**

**File:** `practice_1_embeddings.py` (150-200 lines, 4-6 concepts)

**Learning:**

1. Local embeddings generation (Sentence Transformers: all-mpnet-base-v2)  
2. Qdrant vector store setup and connection  
3. Document chunking and embedding storage  
4. Semantic search implementation  
5. Similarity matching and scoring  
6. Metadata filtering in vector search

**Technologies:**

- `sentence-transformers>=2.2.0` (all-mpnet-base-v2, 768 dims)  
- `langchain-sentence-transformers>=0.1.0`  
- `qdrant-client>=1.7.0`  
- `langchain-qdrant>=0.1.0`

**Outcome:** Build embedding-based matching with local embeddings

---

#### **Practice 2: LangChain Agents with Tools**

**File:** `practice_2_agents.py` (150-200 lines, 4-6 concepts)

**Learning:**

1. `create_tool_calling_agent()` setup  
2. Custom tool creation with `@tool` decorator  
3. Agent memory (ConversationBufferMemory)  
4. Structured outputs (Pydantic models)  
5. Tool integration and execution  
6. Agent conversation flow (maintaining context across exchanges - essential for interview agent)

**Technologies:**

- `langchain==0.3.27` (agents)  
- `langchain-openai==0.3.29`  
- `langchain-community==0.3.27`  
- `langchain-core` (no version pin - matches Week 1/2 pattern)  
- `pydantic==2.11.10` (structured output)
- `python-dotenv==1.0.1` (environment variables - used in Week 2)

**Outcome:** Build specialized agent with tools

**Why this order:** Learn agents first, then learn how to orchestrate them with LangGraph in Practice 3

---

#### **Practice 3: LangGraph Workflows**

**File:** `practice_3_langgraph.py` (150-200 lines, 4-6 concepts)

**Learning:**

1. LangGraph StateGraph creation  
2. Nodes and edges definition  
3. State management and state schema  
4. Conditional routing (if/else logic)  
5. Workflow orchestration (sequential and parallel) - orchestrating agents from Practice 2
6. State transitions and data passing between agents

**Technologies:**

- `langgraph>=0.2.0` (compatible with langchain 0.3.x)  
- `langchain-core` (no version pin - matches Week 1/2 pattern)  
- `langchain==0.3.27` (agents - from Practice 2)

**Outcome:** Build multi-step workflow orchestrating agents

**Why this order:** Now that you know agents (Practice 2), learn how to orchestrate them with LangGraph

---

#### **Practice 4: Agentic RAG, Voice & Observability**

**File:** `practice_4_advanced_agents.py` (150-200 lines, 4-6 concepts)

**Learning:**

1. Agentic retrieval (agent decides what to retrieve) - **Combines Practice 1 (Qdrant) + Practice 2 (Agents)**
2. Dynamic query formulation with agents  
3. Qdrant integration with agents (using embeddings from Practice 1)
4. Voice basics (Whisper STT, OpenAI TTS-1) - for interview agent
5. Observability setup (LangSmith tracing) - for production monitoring
6. Context-aware reasoning with retrieved data

**Technologies:**

- `langchain==0.3.27` (agents - from Practice 2)  
- `langchain-openai==0.3.29`  
- `langchain-community==0.3.27`  
- `langchain-qdrant>=0.1.0`  
- `sentence-transformers>=2.2.0` (from Practice 1)
- `openai>=1.55.0` (for Whisper STT and TTS-1)  
- `langsmith>=0.1.0`
- `python-dotenv==1.0.1` (environment variables - used in Week 2)
- `requests==2.32.4` (HTTP calls - used in Week 2)

**Outcome:** Build agentic RAG system (combining embeddings + agents) with voice and observability basics

**Why this order:** Combines Practice 1 (embeddings/Qdrant) + Practice 2 (agents) to create Agentic RAG, plus adds voice and observability needed for the anchor project

---

#### **Practice 5: Minimal HR Recruiter Agent (Learning Version)**

**File:** `practice_5_minimal_hr_agent.py` (300 lines max)

**Purpose:** Educational learning tool - NOT the production MVP

**Learning Goal:**

- See how all concepts from Practice 1-4 combine together
- Understand the overall architecture and flow
- Practice integrating multiple components
- Preview of what the full anchor project MVP will look like
- **Note:** This is a simplified, educational version for learning. The actual production MVP is in the `anchorproject/` folder.

**Complete Features (Simplified but Functional):**

1. **Resume Processing**
   - Parse resume text (simple text input, no PDF parsing)
   - Chunk resume (500 tokens, 50 overlap)
   - Generate embeddings (all-mpnet-base-v2, local)
   - Store in Qdrant with metadata

2. **Resume Matching Agent (Agentic RAG)**
   - Agent analyzes job description
   - Agent formulates dynamic retrieval query
   - Retrieves relevant resume chunks from Qdrant
   - Agent reasons with retrieved context
   - Calculates match score
   - Returns: match_score, matched_skills, retrieved_resume_chunks

3. **Gap Analysis Agent**
   - Receives: JD, retrieved_resume_chunks, matched_skills
   - Extracts skills from JD
   - Compares with candidate skills
   - Identifies missing skills
   - Calculates experience gaps
   - Returns: missing_skills, matched_skills, experience_gap, improvement_suggestions

4. **Question Generation Agent (Dynamic)**
   - Receives: JD + Resume context + Gap analysis + Match score
   - Formulates dynamic prompt
   - Generates personalized questions:
     - Technical (missing/matched skills)
     - Behavioral (experience gaps)
     - Situational (JD requirements)
     - Personalized (resume-specific)
   - Returns: structured_questions (Pydantic model)

5. **Interview Conducting Agent**
   - Receives: generated_questions
   - Text-based interview (no voice UI - simplified)
   - Uses conversation memory
   - Asks questions in sequence
   - Conducts interview conversation

6. **Response Evaluation Agent**
   - Receives: interview_transcript, questions, responses
   - Evaluates each response
   - Scores candidate (0-100)
   - Generates feedback per question
   - Returns: scores, feedback, recommendations

7. **LangGraph Orchestrator**
   - Workflow: Match → Gap Analysis → Questions → Interview → Evaluation
   - State management
   - Agent coordination
   - Conditional routing
   - Complete end-to-end flow

**Structure:**

- Header & Setup (30-40 lines)
- Resume Processing Component (40-60 lines)
- Matching Agent Component (40-60 lines)
- Gap Analysis Component (40-60 lines)
- Question Generation Component (40-60 lines)
- Interview & Evaluation Component (40-60 lines)
- LangGraph Orchestrator & Complete Flow (50-80 lines)

**Simplifications (for learning - still has all features):**

- Text-based interview (no voice UI/WebSocket - uses simple input/output)
- Simplified error handling (basic try/except)
- Basic implementations (not production-ready, but functional)
- All in one file (for easy understanding)
- No frontend (CLI-based interaction)
- Focus on concept integration, not polish

**Technologies:**

- All technologies from Practice 1-4 with specific versions:
  - `sentence-transformers>=2.2.0` (all-mpnet-base-v2)
  - `langchain-qdrant>=0.1.0`
  - `qdrant-client>=1.7.0`
  - `langgraph>=0.2.0`
  - `langchain==0.3.27` (agents)
  - `langchain-openai==0.3.29`
  - `langchain-community==0.3.27`
  - `langchain-core` (no version pin - matches Week 1/2)
  - `pydantic==2.11.10`
  - `python-dotenv==1.0.1` (environment variables)
  - `requests==2.32.4` (HTTP calls)
  - `langsmith>=0.1.0` (basic)

**Outcome:** Educational minimal version with ALL core features, showing how all concepts work together - prepares learners for building the full anchor project MVP

---

### **Anchor Project: Smart HR Recruiter Agent (Production MVP)**

**Purpose:** Full working prototype ready for production, demos, and showcasing to recruiters

**Note:** This is different from Practice 5 (minimal learning version). This is the complete, production-ready MVP.

#### **Project Structure:**

Week3/

├── practice\_1\_embeddings.py (150-200 lines, 4-6 concepts)

├── practice\_2\_agents.py (150-200 lines, 4-6 concepts)

├── practice\_3\_langgraph.py (150-200 lines, 4-6 concepts)

├── practice\_4\_advanced_agents.py (150-200 lines, 4-6 concepts)

├── practice\_5\_minimal_hr_agent.py (300 lines max - minimal anchor project)

└── anchorproject/

    ├── backend/

    │   ├── main.py (FastAPI)

    │   ├── agents/

    │   │   ├── matching\_agent.py (Agentic RAG)

    │   │   ├── gap\_analysis\_agent.py

    │   │   ├── question\_agent.py (Dynamic Question Generation)

    │   │   ├── interview\_agent.py

    │   │   └── evaluation\_agent.py

    │   ├── workflow.py (LangGraph orchestrator)

    │   ├── services/

    │   │   ├── embedding\_service.py (local: all-mpnet-base-v2)

    │   │   ├── vector\_store\_service.py (Qdrant)

    │   │   ├── voice\_service.py

    │   │   └── database\_service.py (SQLite - 8 functions: init, create, 5 updates, 2 queries)

    │   └── requirements.txt

    ├── frontend/

    │   ├── src/

    │   │   ├── components/

    │   │   ├── services/

    │   │   └── App.tsx

    │   └── package.json

    ├── Dockerfile

    ├── .dockerignore

    └── README.md

---

### **MVP Features (Complete Implementation)**

#### **Core Features (Must Have):**

**1\. Full Stack Application**

- React frontend (resume upload, results display, voice interview interface)  
- FastAPI backend (all endpoints, WebSocket support)  
- WebSocket for real-time voice communication

**2\. Resume Processing**

- Upload PDF/DOCX  
- Parse and extract text  
- Chunking (500 tokens, 50 overlap)  
- Generate embeddings (all-mpnet-base-v2, local)  
- Store in Qdrant with metadata

**3\. Agentic RAG (Core Learning)**

- Resume Matching Agent (LangChain)  
- Agent analyzes job description  
- Agent formulates dynamic retrieval query  
- Retrieves from Qdrant (semantic \+ metadata)  
- Agent reasons with retrieved context  
- Returns match score \+ matched skills \+ retrieved resume chunks

**4\. Gap Analysis Agent (LangChain)**

- Receives: JD, retrieved resume chunks, matched skills  
- Extracts skills from JD  
- Compares with candidate skills  
- Identifies missing skills  
- Calculates experience gaps  
- Returns gap analysis

**5\. Dynamic Question Generation Agent (LangChain)**

- Receives: JD \+ Resume context \+ Gap analysis \+ Match score  
- Formulates dynamic prompt  
- Generates personalized questions:  
  - Technical (missing/matched skills)  
  - Behavioral (experience gaps)  
  - Situational (JD requirements)  
  - Personalized (resume-specific)  
- Returns structured questions (Pydantic)

**6\. LangGraph Orchestrator**

- Workflow: Match → Gap Analysis → Questions → Interview → Evaluation  
- State management  
- Agent coordination  
- Conditional routing  
- Reuses compiled graph (production best practice)

**7\. Voice Interview (Core Feature)**

- Interview Conducting Agent (LangChain)  
- WebSocket endpoint (FastAPI)  
- Whisper STT integration  
- OpenAI TTS-1 integration  
- Real-time voice conversation  
- Conversation memory  
- Asks generated questions in sequence

**8\. Response Evaluation Agent (LangChain)**

- Evaluates interview responses  
- Scores candidate (technical, communication, fit)  
- Generates feedback per question  
- Returns evaluation report

**9\. Database Persistence (SQLite)**

- SQLite database for local storage  
- Single `interviews` table stores complete interview lifecycle  
- JSON storage for arrays (skills, questions)  
- Simple CRUD operations via database_service.py  
- Persists: resume text, JD, match results, gap analysis, questions, transcript, evaluation  
- Functions: createInterview(), updateMatchingResults(), updateGapAnalysis(), updateQuestions(), updateInterviewTranscript(), completeInterview(), getInterview(), listInterviews()

**10\. Frontend Features**

- Resume upload interface  
- Match score visualization  
- Gap analysis display  
- Voice interview interface (WebSocket client)  
- Evaluation report display

**11\. Basic Deployment**

- Docker containerization (with SQLite volume persistence)  
- AWS App Runner deployment (via GitHub)  
- Environment variables setup

---

### **Docker Strategy & SQLite Persistence**

#### **Dockerfile Structure:**

```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create data directory for SQLite (persistent volume)
RUN mkdir -p /app/data

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### **Local Docker (Development/Testing):**

**Volume Mount for SQLite Persistence:**

```bash
# Build
docker build -t smart-hr-recruiter .

# Run with volume mount (SQLite file persists on host)
docker run -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  -e OPENAI_API_KEY=your_key \
  -e QDRANT_URL=your_qdrant_url \
  -e QDRANT_API_KEY=your_qdrant_key \
  smart-hr-recruiter
```

**Key Points:**
- **Volume Mount:** `-v $(pwd)/data:/app/data` maps host directory to container
- **SQLite File Location:** `/app/data/interviews.db` (persists across container restarts)
- **Data Persistence:** Interview data survives container restarts and rebuilds
- **Backup:** Simply copy `data/interviews.db` file for backups

#### **AWS App Runner Deployment:**

**SQLite Considerations:**
- **Ephemeral Storage:** AWS App Runner uses ephemeral storage (data lost on restart)
- **MVP Acceptable:** For demo/prototype, this is acceptable (interviews can be re-run)
- **Production Limitation:** For production, consider migrating to RDS/PostgreSQL later

**Deployment Steps:**
1. Push code to GitHub (with Dockerfile)
2. AWS Console → App Runner → Create service
3. Source: GitHub repository + branch
4. Build: Auto-detect Dockerfile
5. Port: 8000
6. Environment Variables:
   ```
   OPENAI_API_KEY
   QDRANT_URL (if using Qdrant Cloud)
   QDRANT_API_KEY (if using Qdrant Cloud)
   LANGCHAIN_API_KEY (LangSmith)
   ```
7. Deploy

**Note:** SQLite file is created in `/app/data/` inside container. Data persists during container lifetime but is lost on service restart/redeploy. For MVP/demo purposes, this is acceptable.

#### **Future Production Upgrade Path:**

When scaling to production:
1. **Option 1:** Migrate SQLite → PostgreSQL (RDS)
   - Same schema, just change database_service.py
   - Use AWS RDS for managed PostgreSQL
2. **Option 2:** Use AWS EFS (Elastic File System)
   - Mount EFS volume to App Runner
   - SQLite file persists across restarts
   - More complex setup, but keeps SQLite simplicity

**For MVP:** SQLite with ephemeral storage is fine - demonstrates persistence concept, simple setup, no external database needed.

---

#### **Basic Implementation (Can Be Simplified):**

**Observability:**

- Basic LangSmith setup (tracing enabled)  
- Essential metrics only

**Error Handling:**

- Essential error handling (API failures, validation)  
- Basic retry logic  
- User-friendly error messages  
- Advanced error recovery (can be added later)

**UI/UX:**

- Functional UI (works correctly)  
- Basic styling (Tailwind CSS)  
- Not heavily polished (can be enhanced later)

**Performance:**

- Works correctly  
- Basic optimization  
- Advanced caching/optimization (can be added later)

---

### **Complete Full Stack Workflow (MVP)**

#### **End-to-End Flow:**

1\. HR uploads candidate resume (React Frontend)

   ↓

2\. FastAPI receives file → Parse resume (PDF/DOCX)

   ↓

2a. SQLite: createInterview() - Create interview record (candidate_name, resume_text, job_description, status='pending')

   ↓

3\. LangGraph Orchestrator starts workflow

   ↓

4\. Resume Matching Agent (LangChain \+ Agentic RAG)

   ├─ Chunks resume (500 tokens, 50 overlap)

   ├─ Generates embeddings (all-mpnet-base-v2, local)

   ├─ Stores in Qdrant with metadata

   ├─ Agent analyzes job description

   ├─ Agent formulates retrieval query (dynamic)

   ├─ Retrieves relevant resume chunks from Qdrant

   ├─ Agent reasons with retrieved context

   ├─ Calculates match score

   └─ Returns: match\_score, matched\_skills, retrieved\_resume\_chunks

   ↓

4a. SQLite: updateMatchingResults() - Save match score and matched skills (JSON)

   ↓

5\. Gap Analysis Agent (LangChain)

   ├─ Receives: JD, retrieved\_resume\_chunks, matched\_skills

   ├─ Extracts skills from JD

   ├─ Compares with candidate skills

   ├─ Identifies missing skills

   ├─ Calculates experience gaps

   └─ Returns: missing\_skills, matched\_skills, experience\_gap, improvement\_suggestions

   ↓

5a. SQLite: updateGapAnalysis() - Save missing skills (JSON) and experience gap

   ↓

6\. Question Generation Agent (LangChain \- Dynamic)

   ├─ Receives: JD \+ Resume context \+ Gap analysis \+ Match score

   ├─ Formulates dynamic prompt

   ├─ Generates personalized questions

   └─ Returns: structured\_questions (Pydantic model)

   ↓

6a. SQLite: updateQuestions() - Save generated questions (JSON array)

   ↓

7\. Interview Conducting Agent (LangChain)

   ├─ Receives: generated\_questions

   ├─ WebSocket connection (React ↔ FastAPI)

   ├─ Real-time voice: Whisper STT → Agent → OpenAI TTS-1

   ├─ Uses conversation memory

   ├─ Asks questions in sequence

   └─ Conducts interview

   ↓

7a. SQLite: updateInterviewTranscript() - Update transcript as interview progresses (real-time), set status='in_progress'

   ↓

8\. Response Evaluation Agent (LangChain)

   ├─ Receives: interview\_transcript, questions, responses

   ├─ Evaluates each response

   ├─ Scores candidate (0-100)

   ├─ Generates feedback

   └─ Returns: scores, feedback, recommendations

   ↓

8a. SQLite: completeInterview() - Save evaluation (scores, feedback, recommendations), set status='completed'

   ↓

9\. LangGraph completes workflow

   ↓

10\. FastAPI returns report (from SQLite via getInterview()) → React displays results

---

### **Technology Stack (Version-Specific for Compatibility)**

#### **Backend:**

- **Python:** 3.11+ (required for all dependencies)
- **FastAPI:** >=0.115.0  
- **LangChain:** ==0.3.27 (stable, compatible with ConversationBufferMemory and create_tool_calling_agent)
- **LangChain OpenAI:** ==0.3.29  
- **LangChain Community:** ==0.3.27  
- **LangChain Core:** No version pin (matches Week 1/2 pattern - installs latest compatible)
- **LangGraph:** >=0.2.0 (compatible with langchain 0.3.x)
- **Pydantic:** ==2.11.10 (compatible with langchain 0.3.x, used in Week 2)
- **Python-dotenv:** ==1.0.1 (environment variables - used in Week 2)
- **Requests:** ==2.32.4 (HTTP calls - used in Week 2)
- **WebSocket support:** FastAPI native

#### **AI/ML:**

- **OpenAI:** >=1.55.0 (for GPT-4o chat and Whisper STT)
- **Sentence Transformers:** >=2.2.0  
- **Model:** `all-mpnet-base-v2` (768 dims, local embeddings)
- **LangChain Sentence Transformers:** >=0.1.0  
- **OpenAI TTS-1:** Included with OpenAI API (TTS)

#### **Vector Store:**

- **Qdrant:** Local or cloud
- **qdrant-client:** >=1.7.0  
- **langchain-qdrant:** >=0.1.0

#### **Database:**

- **SQLite:** Local file-based database (simple, no setup)
- **sqlite3:** Python standard library (built-in)
- **Purpose:** Store interview data (resume, JD, questions, responses, evaluations)
- **Schema:** Single `interviews` table with JSON fields for arrays

#### **Frontend:**

- **React:** 18.2+  
- **TypeScript:** Latest stable
- **Tailwind CSS:** Latest stable
- **WebSocket client:** Native browser API or socket.io-client

#### **Observability:**

- **LangSmith:** >=0.1.0 (basic setup)

#### **Deployment:**

- **Docker:** Latest stable
  - **SQLite Persistence:** Volume mount for local Docker (`-v $(pwd)/data:/app/data`)
  - **Data Location:** `/app/data/interviews.db` inside container
- **AWS App Runner:** Via GitHub integration
  - **SQLite Note:** Ephemeral storage (data lost on restart - acceptable for MVP/demo)
  - **Future:** Can migrate to RDS PostgreSQL or AWS EFS for production
- **GitHub:** Source code repository

#### **Compatibility Notes:**

- **LangChain 0.3.27** is used (not 1.0) to maintain compatibility with:
  - `ConversationBufferMemory` (stable API in 0.3.x)
  - `create_tool_calling_agent()` (stable API in 0.3.x)
  - Existing Week 1 & Week 2 codebase
- **Pydantic 2.11.10** ensures compatibility with LangChain 0.3.x
- **LangGraph >=0.2.0** works with LangChain 0.3.x (avoid 1.0 for now due to breaking changes)
- All versions tested for backward compatibility

---

### **Agent Architecture**

**5 LangChain Agents:**

1. **Resume Matching Agent** (Agentic RAG with Qdrant)  
2. **Gap Analysis Agent**  
3. **Question Generation Agent** (Dynamic)  
4. **Interview Conducting Agent**  
5. **Response Evaluation Agent**

**1 LangGraph Orchestrator:**

- Manages workflow  
- State transitions  
- Agent coordination  
- Reuses compiled graph

---

### **MVP Deliverable**

**Working System:**

- Upload resume → Get match score  
- See gap analysis  
- Get personalized questions  
- Conduct voice interview (real-time)  
- Get evaluation report  
- Deployed to AWS App Runner

**Technologies Demonstrated:**

- LangChain \+ LangGraph  
- Agentic RAG \+ Qdrant  
- Voice (Whisper STT \+ OpenAI TTS-1)  
- Full stack (React \+ FastAPI)  
- AWS deployment

---

### **Learning Outcomes**

**Agentic AI:**

- Agentic RAG (local embeddings \+ Qdrant \+ agentic retrieval)  
- Dynamic question generation (personalized per candidate)  
- LangGraph workflow orchestration  
- Multi-agent systems (5 agents \+ orchestrator)  
- Agent memory  
- Voice agents  
- Observability (basic)  
- Production patterns

**Technical:**

- Full-stack development  
- Real-time systems (WebSocket)  
- Vector databases (Qdrant)  
- Local embeddings (cost optimization)  
- Database persistence (SQLite)  
- Production deployment  
- System design

---

### **Summary**

**Practice Colabs:** 5 files (4 concept files + 1 minimal learning version)

- **Files 1-4:** Individual concepts (150-200 lines each, 4-6 concepts per file)
- **File 5:** Minimal HR Recruiter Agent (300 lines max) - **Educational learning tool** showing how all concepts combine

**Anchor Project MVP:** Complete HR Recruiter Agent (Production-ready)

- **Purpose:** Full working prototype for production, demos, and showcasing to recruiters
- **Different from Practice 5:** Production-ready with full features, deployment, polished UI
- **Location:** `anchorproject/` folder with full stack (React + FastAPI + all services)

**Key Features:**

- Agentic RAG: Local embeddings (all-mpnet-base-v2) \+ Qdrant \+ dynamic retrieval  
- Dynamic Questions: Personalized based on JD \+ Resume \+ Gap Analysis  
- Voice Interview: Real-time voice conversation  
- Full Workflow: LangGraph orchestrates 5 agents  
- Full Stack: React \+ FastAPI  
- Deployment: Docker (with SQLite volume persistence) → AWS App Runner (via GitHub)

**MVP Scope:**

- Complete: All core features implemented  
- Basic: Observability, error handling, UI polish (functional, not perfect)

**Technologies:** LangChain, LangGraph, FastAPI, React, Qdrant, Sentence Transformers, Whisper, OpenAI TTS-1, SQLite, AWS App Runner

**Final MVP Plan: Week 3 with complete core features, basic implementation for non-core aspects.**  
