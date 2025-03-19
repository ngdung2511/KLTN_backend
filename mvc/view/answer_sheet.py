from typing import Annotated, List, Optional
from pydantic import BaseModel, BeforeValidator, Field
from datetime import datetime


class DetectedAnswer(BaseModel):
    questionIndex: int
    answer: str
class AnswerSheetSchema(BaseModel):
    id: Optional[Annotated[str, BeforeValidator(str)]] = Field(alias="_id", default = None)
    imageId: str
    studentName: str
    studentCode: str
    isGraded: bool = False
    testId: Annotated[str, BeforeValidator(str)]
    dateGraded: Optional[datetime] = None
    detectedAnswers: List[DetectedAnswer]
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    status: bool = True