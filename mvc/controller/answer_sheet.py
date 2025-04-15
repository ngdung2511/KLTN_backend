from fastapi import APIRouter, Form, status, UploadFile, File
from ..model.upload import upload_photo
from ..model import answer_sheet
from ..view.answer_sheet import AnswerSheetSchema, ScoreRequest
from typing import List
import base64

router = APIRouter(prefix="/answer_sheet", tags=["Answer Sheet"])


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload(files: List[UploadFile] = File(...)):
    results = []
    for file in files:
        file_name = file.filename
        studentName = file_name.split(".")[0].split("_")[1]
        studentCode = file_name.split(".")[0].split("_")[0]
        
        # change image to base64
        content = await file.read()
        encoded_string = base64.b64encode(content).decode("utf-8")        

        # use LLM to get answer
        list_answer = answer_sheet.detect_answer_sheet(encoded_string)
        await file.seek(0)
        imageId = upload_photo(file)
        
        answer_sheet_data = AnswerSheetSchema(imageId=imageId['file_id'], studentName=studentName, studentCode=studentCode, detectedAnswers=list_answer)
        answer_sheet.insert_answer_sheet(answer_sheet_data)
        results.append(imageId)
    return {"message": "Answer sheets uploaded successfully", "results": results}


@router.post("/list", status_code=status.HTTP_201_CREATED)
async def list_answer_sheets():
    return answer_sheet.get_all_answer_sheets()

@router.post("/score", status_code=status.HTTP_201_CREATED)
async def score_answer_sheets(score_request: ScoreRequest):
    return answer_sheet.score_answer_sheets(score_request.answerSheetId, score_request.testId, score_request.gradedBy)

@router.post("/quick_score")
async def quick_score(answerSheet: UploadFile = File(...), correctAnswer: str = Form(...)):
    # change image to base64
    content = await answerSheet.read()
    
    encoded_string = base64.b64encode(content).decode("utf-8")
    correctAnswer_processed = [x.strip().upper() for x in correctAnswer.split(",")]

    list_answer = answer_sheet.detect_answer_sheet(encoded_string)
    return answer_sheet.quick_score(list_answer, correctAnswer_processed)