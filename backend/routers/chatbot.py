from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from database import get_db
from reference.chatbot import HelpBot

router = APIRouter(
    prefix="/chatbot",
    tags=["chatbot"]
)

class ChatQuery(BaseModel):
    user_name: str
    user_input: str

class FeedbackRequest(BaseModel):
    user_name: str
    question_id: int
    score: int

class QuestionResponse(BaseModel):
    id: int
    question: str
    answer: str
    article_link: str
    feedback: int

class GreetingResponse(BaseModel):
    greetings: str
    questions: List[QuestionResponse]
        

@router.get("/")
def greet_user(user_name = 'Test User'):
    bot = HelpBot()
    questions = bot.get_top_questions()
    greetings = f"Hello! {user_name}, How can I assist you?"
    return {
        "greetings": greetings,
        "questions": questions
    }

@router.get("/top-questions", response_model=List[QuestionResponse])
async def get_top_questions(limit: int = 5):
    """Get the top most common questions"""
    bot = HelpBot()
    questions = bot.get_top_questions(limit)
    return [QuestionResponse(**dict(q)) for q in questions]

@router.post("/suggest")
async def suggest_questions(query: ChatQuery):
    """
    Suggest questions or return answer if user selected a number.
    Behaves like the CLI version.
    """
    bot = HelpBot()
    user_input = query.user_input.strip().lower()
    user_name = query.user_name.strip()

    # Case 1: User entered a digit (try to interpret as top question selection)
    if user_input.isdigit():
        top_questions = bot.get_top_questions()
        num = int(user_input)
        if 1 <= num <= len(top_questions):
            selected = top_questions[num - 1]
            bot.log_query(user_name, selected["question"], selected["id"])
            return {
                "type": "answer",
                "question": selected["question"],
                "answer": bot.get_answer(selected["id"]),
                "question_id": selected["id"]
            }
        else:
            return {
                "type": "error",
                "message": f"Please select a number between 1 and {len(top_questions)}."
            }

    # Case 2: Treat input as a query
    if not user_input:
        return {
            "type": "error",
            "message": "Please enter a valid question or number."
        }

    suggestions = bot.suggest_questions(user_input)
    if not suggestions:
        return {
            "type": "no_match",
            "message": "No matches found. Try keywords like 'password', 'email', 'invite', 'billing'."
        }

    return {
        "type": suggestions['type'],
        "query": user_input,
        "message": suggestions.get('message', None) or ("Here are some suggestions" if len(suggestions['results']) > 0 else "It seems you need to contact us at contact@metricsnavigator.ai"),
        "suggestions": [] if suggestions.get('type', "query") == "greeting" else [dict(s) for s in suggestions['results'][:5]],
        "total_matches": [] if suggestions.get('type', "query") == "greeting" else len(suggestions['results'])
    }


@router.get("/answer/{question_id}")
async def get_answer(question_id: int):
    """Get answer for a specific question"""
    bot = HelpBot()
    answer = bot.get_answer(question_id)
    if answer == "No answer found.":
        raise HTTPException(status_code=404, detail="Question not found")
    return {"answer": answer}

@router.post("/feedback")
async def save_feedback(feedback: FeedbackRequest):
    """Save user feedback for a question"""
    bot = HelpBot()
    bot.save_feedback(feedback.user_name, feedback.question_id, feedback.score)
    return {"message": "Feedback saved successfully"}

@router.post("/log-query")
async def log_query(query: ChatQuery, matched_question_id: int):
    """Log a user query and its matched question"""
    bot = HelpBot()
    bot.log_query(query.user_name, query.query, matched_question_id)
    return {"message": "Query logged successfully"} 