from typing import List, Union
from fastapi import APIRouter, status, UploadFile
from ..model import question_bank
from ..view.question_bank import QuestionRequest 
from datetime import datetime
import pandas as pd


router = APIRouter(prefix="/question_bank", tags=["question_bank"])

@router.post("/create", status_code=status.HTTP_201_CREATED)
async def create_question(question: Union[QuestionRequest, List[QuestionRequest]]):
    question_bank.insert_question(question)
    return {"message": "Question created successfully"}
    
@router.put("/edit/{question_id}")
async def edit_question(question_id: str, question: QuestionRequest):
    question_bank.edit_question(question_id, question)
    return {"message": "Question edited successfully"}

@router.get("/search")
async def search_question(category_id: str = None, difficulty: str = None, page: int = 1, size: int = 10):
    return question_bank.search_question(category_id, difficulty, page, size)

@router.post("/import")
async def import_file(file: UploadFile):
    if file.filename.endswith(".csv"):
        df = pd.read_csv(file.file)
    elif file.filename.endswith(".xlsx"):
        df = pd.read_excel(file.file)
    elif file.filename.endswith(".json"):
        df = pd.read_json(file.file)
    else:
        return {"message": "File format not supported"}
    
    questions = []
    for _, row in df.iterrows():
        question = QuestionRequest(
            category_id=row["category_id"],
            content=row["content"],
            lstOptions=row["lstOptions"],
            correctOptions=row["correctOptions"],
            difficulty=row["difficulty"],
            status=True,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        questions.append(question)
    question_bank.insert_question(questions)
    return {"message": "Questions imported successfully"}