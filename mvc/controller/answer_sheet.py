from fastapi import APIRouter, status, UploadFile,File
from ..model.upload import upload_photo
from ..model.answer_sheet import AnswerSheetSchema
from typing import List, Union
from ..model import answer_sheet

router = APIRouter(prefix="/answer_sheet", tags=["Answer Sheet"])

@router.post("/upload")
async def upload(file: UploadFile = File(...)):
    file_name = file.filename
    studentName = file_name.split(".")[0].split("_")[1]
    studentCode = file_name.split(".")[0].split("_")[0]
    imageId = upload_photo(file)
    answer_sheet.insert_answer_sheet(AnswerSheetSchema(imageId=imageId['file_id'], studentName=studentName, studentCode=studentCode))
    return imageId