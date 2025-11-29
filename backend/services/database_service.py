import sqlite3
import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "interviews.db")

class DatabaseService:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.init_db()

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS interviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                candidate_name TEXT,
                resume_text TEXT,
                job_description TEXT,
                status TEXT DEFAULT 'pending',
                match_score REAL,
                matched_skills TEXT, -- JSON
                missing_skills TEXT, -- JSON
                experience_gap TEXT,
                questions TEXT, -- JSON
                transcript TEXT, -- JSON
                evaluation TEXT, -- JSON
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        conn.close()

    def create_interview(self, candidate_name: str, resume_text: str, job_description: str) -> int:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO interviews (candidate_name, resume_text, job_description, status)
            VALUES (?, ?, ?, 'pending')
        """, (candidate_name, resume_text, job_description))
        interview_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return interview_id

    def update_matching_results(self, interview_id: int, match_score: float, matched_skills: List[str]):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE interviews
            SET match_score = ?, matched_skills = ?
            WHERE id = ?
        """, (match_score, json.dumps(matched_skills), interview_id))
        conn.commit()
        conn.close()

    def update_gap_analysis(self, interview_id: int, missing_skills: List[str], experience_gap: str):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE interviews
            SET missing_skills = ?, experience_gap = ?
            WHERE id = ?
        """, (json.dumps(missing_skills), experience_gap, interview_id))
        conn.commit()
        conn.close()

    def update_questions(self, interview_id: int, questions: List[Dict[str, Any]]):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE interviews
            SET questions = ?
            WHERE id = ?
        """, (json.dumps(questions), interview_id))
        conn.commit()
        conn.close()

    def update_transcript(self, interview_id: int, transcript: List[Dict[str, str]]):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE interviews
            SET transcript = ?, status = 'in_progress'
            WHERE id = ?
        """, (json.dumps(transcript), interview_id))
        conn.commit()
        conn.close()

    def complete_interview(self, interview_id: int, evaluation: Dict[str, Any]):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE interviews
            SET evaluation = ?, status = 'completed'
            WHERE id = ?
        """, (json.dumps(evaluation), interview_id))
        conn.commit()
        conn.close()

    def get_interview(self, interview_id: int) -> Optional[Dict[str, Any]]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM interviews WHERE id = ?", (interview_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return dict(row)
        return None

    def list_interviews(self) -> List[Dict[str, Any]]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM interviews ORDER BY created_at DESC")
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

# Singleton instance
database_service = DatabaseService()
