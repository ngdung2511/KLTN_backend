from typing import Annotated, List, Optional, Union
from pydantic import BaseModel, BeforeValidator, Field
from datetime import datetime
from .question_bank import QuestionResponse


class TestAutoResquest(BaseModel):
    title: str = "Test"
    description: str = "Test"
    category_id: List[str]
    hardQuestionCount: int
    mediumQuestionCount: int
    easyQuestionCount: int

    model_config = {
        "json_schema_extra": {
            "example": {
                "category_id": ["67cc1cf12c007149d45165cf","67cc1cf12c007149d45165c9"],
                "hardQuestionCount": "2",
                "easyQuestionCount": "2",
                "mediumQuestionCount": "2"
            }
        }
    } 


class TestRequest(BaseModel):
    id: Optional[Annotated[str, BeforeValidator(str)]] = Field(alias="_id", default = None)
    title: str
    description: str
    lstQuestions_id: List[str]
    status: bool = True
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "title": "Test on Geography",
                "description": "Test on Geography for SS1 students",
                "category_id": "67c86fd31c35282cca94fbad",
                "questions_id": ["60f9b2b3b2e9b1c5f9a2d0f3", "60f9b2b3b2e9b1c5f9a2d0f4", "60f9b2b3b2e9b1c5f9a2d0f5"]
            }
        }
    }

class TestResponse(BaseModel):
    id: Optional[Annotated[str, BeforeValidator(str)]] = Field(alias="_id", default = None)
    title: str
    description: str
    lstQuestions: List[QuestionResponse]
    status: bool
    created_at: datetime
    updated_at: datetime
