from typing import List
from fastapi import APIRouter, HTTPException
from ..view.test_bank import AnswerKeyRequest, TestRequest, TestAutoResquest
from ..model import test_bank

router = APIRouter(prefix="/test_bank", tags=["test_bank"])

@router.post("/create")
async def create_test(test: TestRequest):
    test_bank.insert_test(test)
    return {"message": "Test created successfully"}

@router.post("/create-auto")
async def create_test_auto(test: TestAutoResquest):
    results = test_bank.auto_create_test(test.category_id, test.hardQuestionCount, test.easyQuestionCount, test.mediumQuestionCount, test.title, test.description)
    if isinstance(results, dict):
        raise HTTPException(status_code=400, detail=results["message"])
    return results

@router.put("/edit/{test_id}")
async def edit_test(test: TestRequest, test_id: str):
    test_bank.edit_test(test_id, test)

    return {"message": "Edit test"}

@router.get("/search")
async def search_by_name(name: str):
    items = test_bank.search_by_name(name)
    if not items:
        raise HTTPException(status_code=404, detail="Item not found")
    return items

@router.get("/get/{test_id}")
async def get_test(test_id: str):
    item = test_bank.get_test(test_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@router.post("/answer_key/create")
async def create_answer_key(answer_key: AnswerKeyRequest):
    test_bank.insert_answer_key(answer_key)
    return {"message": "Answer key created successfully"}

    # View detail
@router.get("/answer_key/{answer_key_id}")
async def get_answer_key(answer_key_id: str):
    doc = test_bank.get_answer_key(answer_key_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Answer key not found")
    return doc

# Get list
@router.get("/answer_key")
async def list_answer_keys():
    return test_bank.list_answer_keys()

# Edit/update
@router.put("/answer_key/{answer_key_id}")
async def update_answer_key(answer_key_id: str, answer_key_update: AnswerKeyRequest):
    success = test_bank.update_answer_key(answer_key_id, answer_key_update)
    if not success:
        raise HTTPException(status_code=404, detail="Answer key not found or not updated")
    return {"message": "Answer key updated successfully"}

# Delete
@router.delete("/answer_key/{answer_key_id}")
async def delete_answer_key(answer_key_id: str):
    success = test_bank.delete_answer_key(answer_key_id)
    if not success:
        raise HTTPException(status_code=404, detail="Answer key not found or already deleted")
    return {"message": "Answer key deleted successfully"}