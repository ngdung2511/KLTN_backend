from typing import Annotated, List, Optional
from pydantic import BaseModel, BeforeValidator, Field
from datetime import datetime


class DetectedAnswer(BaseModel):
    questionIndex: Annotated[int, BeforeValidator(int)]
    answer: List[str]


class AnswerSheetSchema(BaseModel):
    id: Optional[Annotated[str, BeforeValidator(str)]] = Field(alias="_id", default = None)
    imageId: str
    studentName: str
    studentCode: str
    isGraded: bool = False
    testId: Annotated[str, BeforeValidator(str)] = Field(default = None)
    dateGraded: Optional[datetime] = None
    detectedAnswers: List[DetectedAnswer] = []
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    status: bool = True

    model_config = {
        "json_schema_extra": {
            "example": {
                "imageId": "1234",
                "studentName": "John Doe",
                "studentCode": "123456",
                "testId": "1234",
                "detectedAnswers": [
                    {
                        "questionIndex": 1,
                        "answer": "A"
                    },
                    {
                        "questionIndex": 2,
                        "answer": "B"
                    }
                ]
            }
        }
    }

class ScoreRequest(BaseModel):
    answerSheetId: List[Annotated[str, BeforeValidator(str)]]
    testId: Annotated[str, BeforeValidator(str)]