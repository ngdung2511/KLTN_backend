from typing import List, Union
import pymongo
from ..view.category import Category

client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["mcq_grading_system"]
category_collection = db["categories"]
question_collection = db["questions"]

def insert_category(category: Union[Category, List[Category]]):
    if isinstance(category, list):
        category_collection.insert_many([c.model_dump() for c in category])
    else:
        category_collection.insert_one(category.model_dump())

def getLstQuestionsByCategory(category_id: List[str] = None):
    query = {"status": True}
    if category_id:
        query["category_id"] = {"$in": [id for id in category_id]}
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
            "$group": {
                "_id": {
                    "_id": { "$toString": "$category._id" },
                    "name": "$category.name",
                    "description": "$category.description"
                },
                "totalQuestionCount": {"$sum": 1}
            }
        },
        {
            "$project": {
                "_id": 0,
                "category": "$_id",
                "totalQuestionCount": 1
            }
        }
    ]
    
    return list(question_collection.aggregate(pipeline))

