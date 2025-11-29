from typing import List, Dict, Any
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

class Evaluation(BaseModel):
    technical_score: float = Field(description="Score for technical skills (0-100).")
    communication_score: float = Field(description="Score for communication skills (0-100).")
    cultural_fit_score: float = Field(description="Score for cultural fit (0-100).")
    overall_score: float = Field(description="Overall score (0-100).")
    feedback: str = Field(description="Detailed feedback on the candidate's performance.")
    recommendation: str = Field(description="Hire, No Hire, or Strong Hire.")

class EvaluationAgent:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0)

    def evaluate_interview(self, job_description: str, transcript: List[Dict[str, str]]) -> Evaluation:
        """Evaluate the interview based on the transcript."""
        parser = PydanticOutputParser(pydantic_object=Evaluation)
        prompt = ChatPromptTemplate.from_template(
            """
            You are an expert HR recruiter. Evaluate the following interview transcript against the job description.
            
            Job Description:
            {job_description}
            
            Interview Transcript:
            {transcript}
            
            Assess the candidate on Technical Skills, Communication, and Cultural Fit.
            Provide detailed feedback and a final recommendation.
            
            Provide your output in the following format:
            {format_instructions}
            """
        )
        
        # Format transcript
        transcript_text = "\n".join([f"{entry['role']}: {entry['content']}" for entry in transcript])
        
        chain = prompt | self.llm | parser
        result = chain.invoke({
            "job_description": job_description,
            "transcript": transcript_text,
            "format_instructions": parser.get_format_instructions()
        })
        
        return result

evaluation_agent = EvaluationAgent()
