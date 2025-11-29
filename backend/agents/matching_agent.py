from typing import List, Dict, Any
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain.text_splitter import RecursiveCharacterTextSplitter
from ..services.embedding_service import embedding_service
from ..services.vector_store_service import vector_store_service, PointStruct
import uuid
import os

class MatchingOutput(BaseModel):
    match_score: float = Field(description="A score between 0 and 100 indicating how well the candidate matches the job description.")
    matched_skills: List[str] = Field(description="List of skills from the job description that the candidate possesses.")
    reasoning: str = Field(description="Brief explanation of the match score.")

class MatchingAgent:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0)
        self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)

    def process_resume(self, resume_text: str, interview_id: str):
        """Chunk resume, embed, and store in Qdrant."""
        chunks = self.text_splitter.split_text(resume_text)
        embeddings = embedding_service.embed_documents(chunks)
        
        points = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            points.append(PointStruct(
                id=str(uuid.uuid4()),
                vector=embedding,
                payload={"text": chunk, "interview_id": interview_id, "chunk_index": i}
            ))
        
        vector_store_service.create_collection("resumes")
        vector_store_service.upsert_vectors("resumes", points)

    def analyze_match(self, job_description: str, interview_id: str) -> MatchingOutput:
        """Analyze match between JD and resume."""
        # 1. Retrieve relevant resume chunks
        jd_embedding = embedding_service.embed_text(job_description)
        search_results = vector_store_service.search(
            collection_name="resumes",
            query_vector=jd_embedding,
            limit=5
        )
        
        retrieved_context = "\n\n".join([res.payload['text'] for res in search_results])
        
        # 2. LLM Analysis
        parser = PydanticOutputParser(pydantic_object=MatchingOutput)
        prompt = ChatPromptTemplate.from_template(
            """
            You are an expert HR recruiter. Analyze the following candidate resume context against the job description.
            
            Job Description:
            {job_description}
            
            Resume Context (Retrieved Chunks):
            {context}
            
            Determine the match score (0-100) and identify matched skills.
            Provide your output in the following format:
            {format_instructions}
            """
        )
        
        chain = prompt | self.llm | parser
        result = chain.invoke({
            "job_description": job_description,
            "context": retrieved_context,
            "format_instructions": parser.get_format_instructions()
        })
        
        return result

matching_agent = MatchingAgent()
