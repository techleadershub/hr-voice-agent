import os
from fastapi import FastAPI, UploadFile, File, Form, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import json
import asyncio
import logging
from datetime import datetime
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

from .services.database_service import database_service
from .services.voice_service import voice_service
from .services.resume_parser import parse_resume
from .services.guardrails import (
    GuardrailError,
    MAX_CANDIDATE_NAME,
    MAX_JOB_DESCRIPTION,
    MAX_RESUME_TEXT,
    sanitize_user_text,
)
from .workflow import app_workflow, evaluate_interview_node
from .agents.interview_agent import interview_agent

MAX_RESUME_BYTES = 10 * 1024 * 1024  # 10 MB

async def _read_capped(file: UploadFile, max_bytes: int) -> bytes:
    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = await file.read(64 * 1024)
        if not chunk:
            break
        total += len(chunk)
        if total > max_bytes:
            raise HTTPException(
                status_code=413,
                detail=f"Resume exceeds {max_bytes // (1024 * 1024)} MB limit",
            )
        chunks.append(chunk)
    return b"".join(chunks)

app = FastAPI(title="Smart HR Recruiter Agent")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class InterviewCreate(BaseModel):
    candidate_name: str
    job_description: str

@app.get("/health")
async def health_check():
    """Health check endpoint for Docker and AWS."""
    return {"status": "healthy", "service": "hr-voice-agent"}

@app.on_event("startup")
async def startup_event():
    logger.info("=" * 50)
    logger.info("Starting Smart HR Recruiter Agent Backend")
    logger.info("=" * 50)
    database_service.init_db()
    logger.info("Database initialized successfully")

@app.post("/upload_resume")
async def upload_resume(
    candidate_name: str = Form(...),
    job_description: str = Form(...),
    file: UploadFile = File(...)
):
    logger.info("=" * 50)
    logger.info(f"POST /upload_resume - Received request")
    logger.info(f"  Candidate: {candidate_name}")
    logger.info(f"  File: {file.filename}, Size: {file.size if hasattr(file, 'size') else 'unknown'}")
    logger.info(f"  Job description length: {len(job_description)} chars")
    
    content = b""
    try:
        # Validate text fields first — cheap, lets us reject before any I/O
        try:
            candidate_name = sanitize_user_text(
                candidate_name, MAX_CANDIDATE_NAME, field="candidate_name"
            )
            job_description = sanitize_user_text(
                job_description, MAX_JOB_DESCRIPTION, field="job_description"
            )
        except GuardrailError as e:
            raise HTTPException(status_code=400, detail=str(e))

        content = await _read_capped(file, MAX_RESUME_BYTES)
        logger.info(f"  File content read: {len(content)} bytes")

        try:
            resume_text = await asyncio.to_thread(
                parse_resume, content, file.filename, file.content_type
            )
            resume_text = sanitize_user_text(
                resume_text, MAX_RESUME_TEXT, field="resume_text"
            )
        except GuardrailError as e:
            logger.error(f"  Resume guardrail failed: {e}")
            raise HTTPException(status_code=400, detail=str(e))
        except ValueError as e:
            logger.error(f"  Resume parsing failed: {e}")
            raise HTTPException(status_code=400, detail=str(e))
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"  Unexpected error parsing resume: {e}", exc_info=True)
            raise HTTPException(status_code=400, detail=f"Failed to parse resume: {e}")
    finally:
        # Drop the upload's spooled temp file (and in-memory bytes) right away
        # so nothing accumulates on disk while the rest of the workflow runs.
        await file.close()
        content = b""
        logger.info("  Upload buffer released")

    # Create interview record
    try:
        logger.info("  Creating interview record in database...")
        interview_id = database_service.create_interview(candidate_name, resume_text, job_description)
        logger.info(f"  Interview created with ID: {interview_id}")
    except Exception as e:
        logger.error(f"  Failed to create interview: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create interview: {str(e)}")
    
    # Trigger workflow (Preparation Phase)
    initial_state = {
        "interview_id": str(interview_id),
        "job_description": job_description,
        "resume_text": resume_text,
        "match_score": None,
        "matched_skills": None,
        "missing_skills": None,
        "experience_gap": None,
        "questions": None,
        "transcript": None,
        "evaluation": None
    }
    
    # Run the graph with error handling (off the event loop — sync OpenAI calls)
    try:
        logger.info("  Starting workflow execution...")
        result = await asyncio.to_thread(app_workflow.invoke, initial_state)
        logger.info(f"  Workflow completed successfully")
        logger.info(f"  Match score: {result.get('match_score')}")
        logger.info(f"  Questions generated: {len(result.get('questions', []))}")
    except Exception as e:
        logger.error(f"  Workflow execution failed: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Workflow execution failed: {str(e)}. Interview created with ID: {interview_id}"
        )
    
    response = {
        "interview_id": interview_id,
        "status": "preparation_complete",
        "match_score": result.get("match_score"),
        "gap_analysis": {
            "missing_skills": result.get("missing_skills", []),
            "experience_gap": result.get("experience_gap")
        },
        "questions": result.get("questions", [])
    }
    logger.info(f"  Returning response with interview_id: {interview_id}")
    logger.info("=" * 50)
    return response

@app.get("/interview/{interview_id}")
async def get_interview(interview_id: int):
    logger.info(f"GET /interview/{interview_id} - Received request")
    
    interview = database_service.get_interview(interview_id)
    if not interview:
        logger.warning(f"  Interview {interview_id} not found")
        raise HTTPException(status_code=404, detail="Interview not found")
    
    logger.info(f"  Interview found: {interview.get('candidate_name')}, Status: {interview.get('status')}")
    
    # Parse JSON fields with error handling
    try:
        if interview.get('matched_skills'):
            interview['matched_skills'] = json.loads(interview['matched_skills'])
        if interview.get('missing_skills'):
            interview['missing_skills'] = json.loads(interview['missing_skills'])
        if interview.get('questions'):
            interview['questions'] = json.loads(interview['questions'])
            logger.info(f"  Questions parsed: {len(interview['questions'])} questions")
        if interview.get('transcript'):
            interview['transcript'] = json.loads(interview['transcript'])
            logger.info(f"  Transcript parsed: {len(interview['transcript'])} messages")
        if interview.get('evaluation'):
            interview['evaluation'] = json.loads(interview['evaluation'])
            logger.info(f"  Evaluation parsed successfully")
    except (json.JSONDecodeError, TypeError) as e:
        logger.warning(f"  Failed to parse JSON fields for interview {interview_id}: {e}")

    interview['gap_analysis'] = {
        "missing_skills": interview.get('missing_skills') or [],
        "experience_gap": interview.get('experience_gap'),
    }

    logger.info(f"  Returning interview data")
    return interview

@app.websocket("/ws/interview/{interview_id}")
async def websocket_endpoint(websocket: WebSocket, interview_id: int):
    logger.info("=" * 50)
    logger.info(f"WebSocket /ws/interview/{interview_id} - Connection attempt")
    
    await websocket.accept()
    logger.info(f"  WebSocket connection accepted for interview {interview_id}")
    
    interview = database_service.get_interview(interview_id)
    if not interview:
        logger.warning(f"  Interview {interview_id} not found, closing connection")
        await websocket.close(code=4004)
        return

    logger.info(f"  Interview found: {interview.get('candidate_name')}")

    try:
        questions = json.loads(interview['questions']) if interview.get('questions') else []
        logger.info(f"  Questions loaded: {len(questions)} questions")
    except (json.JSONDecodeError, TypeError) as e:
        logger.warning(f"  Failed to parse questions: {e}")
        questions = []
    
    try:
        transcript = json.loads(interview['transcript']) if interview.get('transcript') else []
        logger.info(f"  Transcript loaded: {len(transcript)} messages")
    except (json.JSONDecodeError, TypeError) as e:
        logger.warning(f"  Failed to parse transcript: {e}")
        transcript = []
    
    if not questions:
        logger.error(f"  No questions available for interview {interview_id}")
        await websocket.send_json({"type": "error", "content": "No questions available for this interview"})
        await websocket.close()
        return
    
    current_question_index = len([t for t in transcript if t.get('role') == 'assistant']) // 2 # Rough estimate
    if current_question_index >= len(questions):
        current_question_index = len(questions) - 1
    
    logger.info(f"  Starting at question index: {current_question_index}")

    try:
        # Send first question if not started
        if not transcript:
            logger.info("  No transcript found, sending first question")
            first_q = questions[0].get('text') if isinstance(questions[0], dict) else questions[0]
            if not first_q:
                logger.error("  Invalid question format")
                await websocket.send_json({"type": "error", "content": "Invalid question format"})
                await websocket.close()
                return
            logger.info(f"  Generating TTS for first question: {first_q[:50]}...")
            audio = await voice_service.text_to_speech(first_q)
            logger.info(f"  TTS generated: {len(audio)} bytes")
            # Send text and audio
            await websocket.send_json({"type": "text", "content": first_q, "role": "assistant"})
            await websocket.send_bytes(audio)
            logger.info("  First question sent to client")
            
            transcript.append({"role": "assistant", "content": first_q})
            database_service.update_transcript(interview_id, transcript)
            current_question_index = 0

        while True:
            # Receive audio from client
            logger.info("  Waiting for audio from client...")
            data = await websocket.receive()
            
            if "bytes" in data:
                audio_bytes = data["bytes"]
                logger.info(f"  Received audio bytes: {len(audio_bytes)} bytes")
                # Transcribe
                logger.info("  Transcribing audio...")
                user_text = await voice_service.transcribe_audio(audio_bytes)
                logger.info(f"  Transcription: {user_text}")
                
                # Send transcription back to UI
                await websocket.send_json({"type": "transcription", "content": user_text, "role": "user"})
                logger.info("  Transcription sent to client")
                
                transcript.append({"role": "user", "content": user_text})
                database_service.update_transcript(interview_id, transcript)
                
                # Decide next step
                current_question_index += 1
                logger.info(f"  Moving to question index: {current_question_index}/{len(questions)}")
                
                if current_question_index < len(questions):
                    next_q = questions[current_question_index].get('text') if isinstance(questions[current_question_index], dict) else questions[current_question_index]
                    if not next_q:
                        logger.error("  Invalid question format")
                        await websocket.send_json({"type": "error", "content": "Invalid question format"})
                        break
                    
                    logger.info(f"  Generating TTS for next question: {next_q[:50]}...")
                    audio = await voice_service.text_to_speech(next_q)
                    logger.info(f"  TTS generated: {len(audio)} bytes")
                    await websocket.send_json({"type": "text", "content": next_q, "role": "assistant"})
                    await websocket.send_bytes(audio)
                    logger.info("  Next question sent to client")
                    
                    transcript.append({"role": "assistant", "content": next_q})
                    database_service.update_transcript(interview_id, transcript)
                else:
                    # End of interview
                    logger.info("  All questions completed, ending interview")
                    end_msg = "Thank you for your time. We have finished the interview."
                    audio = await voice_service.text_to_speech(end_msg)
                    await websocket.send_json({"type": "text", "content": end_msg, "role": "assistant"})
                    await websocket.send_bytes(audio)
                    await websocket.send_json({"type": "end"})
                    logger.info("  Interview end message sent")
                    break
            
            elif "text" in data:
                logger.info(f"  Received text message: {data.get('text')}")
                # Handle text input if needed
                pass

    except WebSocketDisconnect:
        logger.info(f"  Client disconnected for interview {interview_id}")
    except Exception as e:
        logger.error(f"  WebSocket error for interview {interview_id}: {e}", exc_info=True)
        await websocket.close()

@app.post("/interview/{interview_id}/evaluate")
async def evaluate_interview(interview_id: int):
    logger.info("=" * 50)
    logger.info(f"POST /interview/{interview_id}/evaluate - Received request")
    
    interview = database_service.get_interview(interview_id)
    if not interview:
        logger.warning(f"  Interview {interview_id} not found")
        raise HTTPException(status_code=404, detail="Interview not found")
    
    logger.info(f"  Interview found: {interview.get('candidate_name')}")
        
    try:
        transcript = json.loads(interview['transcript']) if interview.get('transcript') else []
        logger.info(f"  Transcript loaded: {len(transcript)} messages")
    except (json.JSONDecodeError, TypeError) as e:
        logger.warning(f"  Failed to parse transcript: {e}")
        transcript = []
    
    state = {
        "interview_id": str(interview_id),
        "job_description": interview.get('job_description', ''),
        "transcript": transcript
    }
    
    try:
        logger.info("  Starting evaluation...")
        result = await asyncio.to_thread(evaluate_interview_node, state)
        evaluation = result.get('evaluation')
        
        # evaluation is a Pydantic model, not a dict - access attributes directly
        if evaluation:
            logger.info(f"  Evaluation completed: {evaluation.recommendation}")
            logger.info("=" * 50)
            # Convert Pydantic model to dict for JSON response
            return evaluation.model_dump()
        else:
            logger.warning("  No evaluation returned")
            logger.info("=" * 50)
            raise HTTPException(status_code=500, detail="Evaluation returned no results")
    except Exception as e:
        logger.error(f"  Evaluation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")

# Serve static files (Frontend)
# This is for production where frontend is built to /app/frontend/dist
if os.path.exists("frontend/dist"):
    app.mount("/assets", StaticFiles(directory="frontend/dist/assets"), name="assets")

    @app.get("/{full_path:path}")
    async def serve_app(full_path: str):
        # Check if file exists in dist (e.g. favicon.ico)
        if os.path.exists(f"frontend/dist/{full_path}") and full_path != "":
            return FileResponse(f"frontend/dist/{full_path}")
        # Otherwise serve index.html for SPA routing
        return FileResponse("frontend/dist/index.html")
