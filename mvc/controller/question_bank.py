from typing import List, Union
from fastapi import APIRouter, status, UploadFile
from ..model import question_bank
from ..view.question_bank import QuestionRequest, SearchQuestionRequest, ChatQuestionRequest
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

@router.post("/search")
async def search_question(search_question_request: SearchQuestionRequest):
    return question_bank.search_question(search_question_request.category_id, search_question_request.difficulty, search_question_request.page, search_question_request.size, search_question_request.content)

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

@router.post("/chat")
async def chat_question(chat_question_request: ChatQuestionRequest):
    return question_bank.chat_question(chat_question_request.question_id, chat_question_request.messages)

@router.post("/difficulty_count")
async def difficulty_count(category_ids: List[str] = None):
    return question_bank.difficulty_count(category_ids)