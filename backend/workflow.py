from typing import TypedDict, List, Dict, Any, Optional
from langgraph.graph import StateGraph, END
from .agents.matching_agent import matching_agent
from .agents.gap_analysis_agent import gap_analysis_agent
from .agents.question_agent import question_agent, Question
from .agents.evaluation_agent import evaluation_agent, Evaluation
from .services.database_service import database_service
from .services.guardrails import validate_evaluation

class InterviewState(TypedDict):
    interview_id: str
    job_description: str
    resume_text: str
    match_score: Optional[float]
    matched_skills: Optional[List[str]]
    missing_skills: Optional[List[str]]
    experience_gap: Optional[str]
    questions: Optional[List[Question]]
    transcript: Optional[List[Dict[str, str]]]
    evaluation: Optional[Evaluation]

def match_resume_node(state: InterviewState):
    print(f"Matching resume for interview {state['interview_id']}")
    matching_agent.process_resume(state['resume_text'], state['interview_id'])
    result = matching_agent.analyze_match(state['job_description'], state['interview_id'])
    
    # Update DB
    database_service.update_matching_results(
        int(state['interview_id']), 
        result.match_score, 
        result.matched_skills
    )
    
    return {
        "match_score": result.match_score,
        "matched_skills": result.matched_skills
    }

def gap_analysis_node(state: InterviewState):
    print(f"Analyzing gap for interview {state['interview_id']}")
    result = gap_analysis_agent.analyze_gap(state['job_description'], state['matched_skills'])
    
    # Update DB
    database_service.update_gap_analysis(
        int(state['interview_id']),
        result.missing_skills,
        result.experience_gap
    )
    
    return {
        "missing_skills": result.missing_skills,
        "experience_gap": result.experience_gap
    }

def generate_questions_node(state: InterviewState):
    print(f"Generating questions for interview {state['interview_id']}")
    gap_analysis = {
        "missing_skills": state['missing_skills'],
        "experience_gap": state['experience_gap']
    }
    questions = question_agent.generate_questions(
        state['job_description'],
        gap_analysis,
        state['match_score']
    )
    
    # Update DB
    database_service.update_questions(
        int(state['interview_id']),
        [q.model_dump() for q in questions]
    )
    
    return {"questions": questions}

def evaluate_interview_node(state: InterviewState):
    print(f"Evaluating interview {state['interview_id']}")
    result = evaluation_agent.evaluate_interview(state['job_description'], state['transcript'])

    # Hard-fail on out-of-schema output (coerced scores, unknown recommendation)
    validate_evaluation(result)

    # Update DB
    database_service.complete_interview(
        int(state['interview_id']),
        result.model_dump()
    )

    return {"evaluation": result}

# Define the graph
workflow = StateGraph(InterviewState)

# Add nodes
workflow.add_node("match_resume", match_resume_node)
workflow.add_node("gap_analysis", gap_analysis_node)
workflow.add_node("generate_questions", generate_questions_node)
workflow.add_node("evaluate_interview", evaluate_interview_node)

# Define edges
workflow.set_entry_point("match_resume")
workflow.add_edge("match_resume", "gap_analysis")
workflow.add_edge("gap_analysis", "generate_questions")
workflow.add_edge("generate_questions", END) # Preparation phase ends here

# Evaluation is a separate entry point or triggered manually
# For simplicity, we can have a separate graph or just call the node directly
# But let's keep it in the same graph but maybe disconnected? 
# Actually, LangGraph expects a connected graph. 
# We can make "evaluate_interview" accessible if we pass a state that has transcript.
# But for the "Preparation" flow, we stop at generate_questions.

app_workflow = workflow.compile()
