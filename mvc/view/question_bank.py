from typing import Annotated, List, Optional
from pydantic import BaseModel, BeforeValidator, Field
from bson import ObjectId
from datetime import datetime

class Question(BaseModel):
    id: Optional[Annotated[str, BeforeValidator(str)]] = Field(alias="_id", default = None)
    question: str
    answers: List[str]
    correct: List[str]
    difficulty: str
    category: str
    status: bool = Field(default=True, description="True if question is active, False if question is deleted")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    model_config = {
        "json_schema_extra": {
            "example": {
                "question": "What is the capital of Nigeria?",
                "answers": ["Lagos", "Abuja", "Kano", "Ibadan"],
                "correct": ["B"],
                "difficulty": "Easy",
                "category": "Geography",
        }
    }
}
    