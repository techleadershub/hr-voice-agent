from typing import List, Dict, Any
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

class GapAnalysisOutput(BaseModel):
    missing_skills: List[str] = Field(description="List of required skills from the JD that the candidate is missing.")
    experience_gap: str = Field(description="Analysis of any gaps in experience level or years of experience.")
    improvement_suggestions: List[str] = Field(description="Suggestions for the candidate to improve their profile for this role.")

class GapAnalysisAgent:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0)

    def analyze_gap(self, job_description: str, matched_skills: List[str]) -> GapAnalysisOutput:
        """Analyze gaps between JD and matched skills."""
        parser = PydanticOutputParser(pydantic_object=GapAnalysisOutput)
        prompt = ChatPromptTemplate.from_template(
            """
            You are an expert HR recruiter. Perform a gap analysis based on the Job Description and the skills already matched.
            
            Job Description:
            {job_description}
            
            Matched Skills (already confirmed):
            {matched_skills}
            
            Identify missing skills and experience gaps.
            Provide your output in the following format:
            {format_instructions}
            """
        )
        
        chain = prompt | self.llm | parser
        result = chain.invoke({
            "job_description": job_description,
            "matched_skills": ", ".join(matched_skills),
            "format_instructions": parser.get_format_instructions()
        })
        
        return result

gap_analysis_agent = GapAnalysisAgent()
