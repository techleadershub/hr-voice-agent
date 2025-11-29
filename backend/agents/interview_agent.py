from typing import List, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

class InterviewAgent:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0.7)

    def generate_response(self, transcript: List[Dict[str, str]], current_question: str) -> str:
        """Generate a conversational response to the candidate's answer."""
        prompt = ChatPromptTemplate.from_template(
            """
            You are an AI interviewer conducting a voice interview.
            
            Current Question: {current_question}
            
            Transcript so far:
            {transcript}
            
            The candidate has just finished speaking. 
            Acknowledge their answer briefly and professionally. 
            Do NOT ask the next question yet. Just provide a transition or acknowledgement.
            Keep it short (1-2 sentences) as this is a voice conversation.
            """
        )
        
        chain = prompt | self.llm | StrOutputParser()
        
        # Format transcript for prompt
        transcript_text = "\n".join([f"{entry['role']}: {entry['content']}" for entry in transcript[-3:]]) # Last 3 turns
        
        result = chain.invoke({
            "current_question": current_question,
            "transcript": transcript_text
        })
        
        return result

interview_agent = InterviewAgent()
