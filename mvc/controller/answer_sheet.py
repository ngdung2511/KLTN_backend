

from fastapi import APIRouter, status, UploadFile,File
from ..model.upload import upload_photo

router = APIRouter(prefix="/answer_sheet", tags=["Answer Sheet"])

@router.post("/create", status_code=status.HTTP_201_CREATED)
# async def create_category(category: Union[Category, List[Category]]):
#     category_model.insert_category(category)
#     return {"message": "category created successfully"}


@router.post("/upload")
async def upload(file: UploadFile = File(...)):
    result = upload_photo(file)
    return result
