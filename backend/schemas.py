from pydantic import BaseModel

class Query(BaseModel):
    user_input: str
    user_name: str = "Anonymous"

class Feedback(BaseModel):
    user_name: str = "Anonymous"
    question_id: int
    score: int 