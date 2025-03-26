from typing import Annotated, Dict, List, Optional
from pydantic import BaseModel, BeforeValidator, Field
from datetime import datetime
from .category import Category

class SearchQuestionRequest(BaseModel):
    category_id: List[str] = Field(alias="category_id", default=None)
    difficulty: List[str] = Field(alias="difficulty", default=None)
    content: str = None
    page: int = 1
    size: int = 10

    model_config = {
        "json_schema_extra": {
            "example": {
                "category_id": ["67c86fd31c35282cca94fbad"],
                "difficulty": ["Easy"],
                "page": 1,
                "size": 10
            }
        }
    }

class QuestionRequest(BaseModel):
    id: Optional[Annotated[str, BeforeValidator(str)]] = Field(alias="_id", default = None)
    content: str
    lstOptions: Dict[str, str]
    correctOptions: List[str]
    difficulty: str
    category_id: str
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
            "category_id": "67c86fd31c35282cca94fbad",
            "difficulty": "Easy"
        }
    }
}

class QuestionResponse(BaseModel):
    id: Optional[Annotated[str, BeforeValidator(str)]] = Field(alias="_id", default = None)
    content: str
    lstOptions: Dict[str, str]
    correctOptions: List[str]
    difficulty: str
    category: Category
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
            "category": {
                "id": "67c86fd31c35282cca94fbad",
                "name": "Geoography",
                "description": "Questions related to geography"
            },
            "difficulty": "Easy"
        }
    }
}
    
class ChatQuestionRequest(BaseModel):
    question_id: str
    messages: List[dict]

    model_config = {
        "json_schema_extra": {
            "example": {
                "question_id": "67c86fd31c35282cca94fbad",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Why is the ocean salty?"
                            }
                        ]
                    }
                ]
            }
        }
    }