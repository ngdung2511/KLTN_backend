from typing import List, Union
import pymongo
from ..view.question_bank import Question
from bson import ObjectId

client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["mcq_grading_system"]
question_collection = db["questions"]

def insert_question(question: Union[Question, List[Question]]):
    if isinstance(question, list):
        question_collection.insert_many([q.model_dump() for q in question])
    else:
        question_collection.insert_one(question.model_dump())

def edit_question(question_id: str, question: Question):
    dict_question = question.model_dump()
    dict_question.pop("created_at")    # delete created_at field
    question_collection.update_one({"_id": ObjectId(question_id), "status": True}, {"$set": dict_question})

def search_question(category: str = None, difficulty: str = None):
    query = {"status": True}
    if category:
        query["category"] = category
    if difficulty:
        query["difficulty"] = difficulty
    items = question_collection.find(query)
    return [Question(**item) for item in items]