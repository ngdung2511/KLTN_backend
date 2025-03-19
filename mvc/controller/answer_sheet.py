from fastapi import APIRouter, status, UploadFile,File
from ..model.upload import upload_photo
from ..model.answer_sheet import AnswerSheetSchema
from typing import List, Union
from ..model import answer_sheet

router = APIRouter(prefix="/answer_sheet", tags=["Answer Sheet"])

@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload(files: List[UploadFile] = File(...)):
    results = []
    for file in files:
        file_name = file.filename
        studentName = file_name.split(".")[0].split("_")[1]
        studentCode = file_name.split(".")[0].split("_")[0]
        imageId = upload_photo(file)
        answer_sheet_data = AnswerSheetSchema(imageId=imageId['file_id'], studentName=studentName, studentCode=studentCode)
        answer_sheet.insert_answer_sheet(answer_sheet_data)
        results.append(imageId)
    return {"message": "Answer sheets uploaded successfully", "results": results}


@router.post("/list", status_code=status.HTTP_201_CREATED)
async def list_answer_sheets():
    return answer_sheet.get_all_answer_sheets()


