from typing import List, Union
import pymongo
from mvc.view.test_bank import TestRequest, TestResponse
from bson import ObjectId
from mvc.view.question_bank import Question
import datetime

client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["mcq_grading_system"]
test_collection = db["tests"]
question_collection = db["questions"]

def insert_test(test: Union[TestRequest, List[TestRequest]]):
    result = None
    if isinstance(test, list):
        result = test_collection.insert_many([t.model_dump() for t in test])
    else:
        result = test_collection.insert_one(test.model_dump())
    return result
    

def auto_create_test(category: str, hardQuestionCount: int, easyQuestionCount: int, mediumQuestionCount: int):
    hard_questions = list(question_collection.aggregate([{"$match": {"category": category, "difficulty": "Hard", "status": True}}, {"$sample": {"size": hardQuestionCount}}]))
    if len(hard_questions) < hardQuestionCount:
        return {"message": f"Not enough hard questions in {category}"}
    easy_questions = list(question_collection.aggregate([{"$match": {"category": category, "difficulty": "Easy", "status": True}}, {"$sample": {"size": easyQuestionCount}}]))
    if len(easy_questions) < easyQuestionCount:
        return {"message": f"Not enough easy questions in {category}"}
    medium_questions = list(question_collection.aggregate([{"$match": {"category": category, "difficulty": "Medium", "status": True}}, {"$sample": {"size": mediumQuestionCount}}]))
    if len(medium_questions) < mediumQuestionCount:
        return {"message": f"Not enough medium questions in {category}"}
    questions = hard_questions + easy_questions + medium_questions
    custom_order = ["Easy", "Medium", "Hard"]
    questions = sorted(questions, key=lambda x: custom_order.index(x["difficulty"]))
    questions = [Question(**q) for q in questions]
    
    test_response = TestResponse(title=f"Test on {category}", description=f"Test on {category} for SS1 students", subject=category, questions =questions, status=True, created_at=datetime.datetime.now(), updated_at=datetime.datetime.now())
    test_request = TestRequest(title=f"Test on {category}", description=f"Test on {category} for SS1 students", subject=category, questions_id=[str(q.id) for q in questions], status=True, created_at=datetime.datetime.now(), updated_at=datetime.datetime.now())

    result = insert_test(test_request)
    test_response.id = str(result.inserted_id)
    return test_response

def edit_test(test_id: str, test: TestRequest):
    dict_test = test.model_dump()
    dict_test.pop("created_at")    # delete created_at field
    test_collection.update_one({"_id": ObjectId(test_id), "status": True}, {"$set": dict_test})

def search_by_name(name: str):
    pipeline = [
        {
            "$match": {
                "title": {"$regex": name, "$options": "i"},
                "status": True
            }
        },
        {
            "$addFields": {  
                "questions_id": {
                    "$map": {
                        "input": "$questions_id",
                        "as": "id",
                        "in": { "$toObjectId": "$$id" } 
                    }
                }
            }
        },
        {
            "$lookup": {
                "from": "questions",
                "localField": "questions_id",
                "foreignField": "_id",
                "as": "questions"
            }
        },
        {
            "$unset": "questions_id"
        }
    ]
    items = list(test_collection.aggregate(pipeline))
    items = [TestResponse(**item) for item in items]

    return items