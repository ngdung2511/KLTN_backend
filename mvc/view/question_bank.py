from typing import Annotated, Dict, List, Optional
from pydantic import BaseModel, BeforeValidator, Field
from bson import ObjectId
from datetime import datetime

class Question(BaseModel):
    id: Optional[Annotated[str, BeforeValidator(str)]] = Field(alias="_id", default = None)
    content: str
    lstOptions: Dict[str, str]
    correctOptions: List[str]
    difficulty: str
    category: str
    status: bool = Field(default=True, description="True if question is active, False if question is deleted")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    model_config = {
    "json_schema_extra": {
        "example": {
            "content": "<p>What is the capital of France?</p>",
            "lstOptions": {
                "optionA": "<p>Paris</p>",
                "optionB": "<p>London</p>",
                "optionC": "<p>Berlin</p>",
                "optionD": "<p>Madrid</p>"
            },
            "correctOptions": ["A"],
            "category": "Geography",
            "difficulty": "Easy"
        }
    }
}
    