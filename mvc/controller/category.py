from typing import List, Union
from fastapi import APIRouter, status
from ..model import category as category_model
from ..view.category import Category


router = APIRouter(prefix="/category", tags=["Category"])

@router.post("/create", status_code=status.HTTP_201_CREATED)
async def create_category(category: Union[Category, List[Category]]):
    category_model.insert_category(category)
    return {"message": "category created successfully"}