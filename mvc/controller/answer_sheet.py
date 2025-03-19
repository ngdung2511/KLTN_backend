from fastapi import APIRouter, status, UploadFile,File
from ..model.upload import upload_photo
from ..model.answer_sheet import AnswerSheetSchema
from typing import List, Union
from ..model import answer_sheet

router = APIRouter(prefix="/answer_sheet", tags=["Answer Sheet"])

@router.post("/create", status_code=status.HTTP_201_CREATED)
# async def create_category(category: Union[Category, List[Category]]):
#     category_model.insert_category(category)
#     return {"message": "category created successfully"}


@router.post("/upload")
async def upload(file: UploadFile = File(...)):
    result = upload_photo(file)
    return result

@router.post("/upload_schema")
async def upload_schema(schema: AnswerSheetSchema):
    answer_sheet.insert_answer_sheet(schema)
    return {"message": "answer sheet created successfully"}