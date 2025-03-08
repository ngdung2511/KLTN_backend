from typing import List, Union
import pymongo
from ..view.question_bank import QuestionRequest, QuestionResponse
from bson import ObjectId

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

def search_question(category_id: str = None, difficulty: str = None):
    query = {"status": True}
    if category_id:
        query["category_id"] = category_id
    if difficulty:
        query["difficulty"] = difficulty
    print(query)
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
        }
    ]

    items = question_collection.aggregate(pipeline)
    return [QuestionResponse(**item) for item in items]
