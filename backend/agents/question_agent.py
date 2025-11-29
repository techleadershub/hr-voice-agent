from typing import List, Dict, Any
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
import uuid

class Question(BaseModel):
    id: str = Field(description="Unique identifier for the question.")
    text: str = Field(description="The question text.")
    type: str = Field(description="Type of question: Technical, Behavioral, Situational, or Personalized.")
    context: str = Field(description="Context or reason for asking this question.")

class QuestionList(BaseModel):
    questions: List[Question] = Field(description="List of generated questions.")

class QuestionAgent:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0.7)

    def generate_questions(self, job_description: str, gap_analysis: Dict[str, Any], match_score: float) -> List[Question]:
        """Generate personalized interview questions: 1 intro + 2 technical + 1 behavioral."""
        parser = PydanticOutputParser(pydantic_object=QuestionList)
        
        # Start with "Tell me about yourself" question
        intro_question = Question(
            id=str(uuid.uuid4()),
            text="Tell me about yourself.",
            type="Personalized",
            context="Standard opening question to get to know the candidate"
        )
        
        # Generate questions with specific requirements
        prompt = ChatPromptTemplate.from_template(
            """
            You are an expert HR recruiter. Generate interview questions for a candidate.
            
            Job Description:
            {job_description}
            
            Match Score: {match_score}
            
            Gap Analysis:
            {gap_analysis}
            
            Generate questions with these EXACT requirements:
            - Generate at least 3 Technical questions (type must be "Technical")
            - Generate at least 2 Behavioral questions (type must be "Behavioral")
            
            Technical questions should:
            1. Focus on key technical skills required for the role
            2. Address any missing skills or gaps identified
            3. Be specific and relevant to the job description
            
            Behavioral questions should:
            1. Assess soft skills, teamwork, or problem-solving
            2. Be relevant to the role and company culture
            3. Help understand the candidate's experience and approach
            
            Provide your output in the following format:
            {format_instructions}
            """
        )
        
        chain = prompt | self.llm | parser
        result = chain.invoke({
            "job_description": job_description,
            "match_score": match_score,
            "gap_analysis": str(gap_analysis),
            "format_instructions": parser.get_format_instructions()
        })
        
        # Filter and select questions
        technical_questions = [q for q in result.questions if q.type.lower() in ['technical', 'tech']][:2]
        behavioral_questions = [q for q in result.questions if q.type.lower() in ['behavioral', 'behavioural']][:1]
        
        # Fallback if we don't have enough questions
        if len(technical_questions) < 2:
            # Add default technical questions if needed
            default_tech = [
                Question(
                    id=str(uuid.uuid4()),
                    text="What technical skills do you have that are most relevant to this role?",
                    type="Technical",
                    context="Assess technical competency"
                ),
                Question(
                    id=str(uuid.uuid4()),
                    text="Can you walk me through a technical project you've worked on?",
                    type="Technical",
                    context="Assess technical experience"
                )
            ]
            technical_questions = (technical_questions + default_tech)[:2]
        
        if not behavioral_questions:
            behavioral_question = Question(
                id=str(uuid.uuid4()),
                text="Can you describe a challenging situation you faced at work and how you handled it?",
                type="Behavioral",
                context="Assess problem-solving and communication skills"
            )
            behavioral_questions = [behavioral_question]
        
        # Combine: intro + 2 technical + 1 behavioral (total: 4 questions)
        all_questions = [intro_question] + technical_questions + behavioral_questions
        
        return all_questions

question_agent = QuestionAgent()
