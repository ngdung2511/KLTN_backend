from typing import List, Union
import pymongo
from ..view.question_bank import QuestionRequest, QuestionResponse
from bson import ObjectId
from bs4 import BeautifulSoup

client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["mcq_grading_system"]
question_collection = db["questions"]
category_collection = db["categories"]

def insert_question(question: Union[QuestionRequest, List[QuestionRequest]]):
    if isinstance(question, list):
        question_collection.insert_many([q.model_dump() for q in question])
    else:
        question_collection.insert_one(question.model_dump())

def edit_question(question_id: str, question: QuestionRequest):
    dict_question = question.model_dump()
    dict_question.pop("created_at")    # delete created_at field
    question_collection.update_one({"_id": ObjectId(question_id), "status": True}, {"$set": dict_question})

def search_question(category_id: List[str] = None, difficulty: List[str] = None, page: int = 1, size: int = 10, content: str = None):
    query = {"status": True}
    if category_id:
        query["category_id"] = {"$in": [id for id in category_id]}
    if difficulty:
        query["difficulty"] = {"$in": difficulty}
    if content:
        extract_str = BeautifulSoup(content, "html.parser").get_text()
        option_conditions = [
            {"lstOptions.optionA": {"$regex": extract_str, "$options": "i"}},
            {"lstOptions.optionB": {"$regex": extract_str, "$options": "i"}},
            {"lstOptions.optionC": {"$regex": extract_str, "$options": "i"}},
            {"lstOptions.optionD": {"$regex": extract_str, "$options": "i"}}
        ]
        query["$or"] = [
            {"content": {"$regex": extract_str, "$options": "i"}},
            *option_conditions
        ]

    pipeline = [
        {
            "$match": query
        },
        {
            "$addFields": {  
                "category_id": { "$toObjectId": "$category_id" }
            }
        },
        {
            "$lookup": {
                "from": "categories",
                "localField": "category_id",
                "foreignField": "_id",
                "as": "category"
            }
        },
        {
            "$unwind": "$category"
        },
        {
            "$unset": "category_id"
        },
        {
            "$skip": (page - 1) * size
        },
        {
            "$limit": size
        }
    ]

    total = question_collection.count_documents(query)
    items = question_collection.aggregate(pipeline)
    return {"total": total, "items": [QuestionResponse(**item) for item in items]}

