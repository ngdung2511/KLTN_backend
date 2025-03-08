from typing import List, Union
import pymongo
from ..view.category import Category

client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["mcq_grading_system"]
category_collection = db["categories"]

def insert_category(category: Union[Category, List[Category]]):
    if isinstance(category, list):
        category_collection.insert_many([c.model_dump() for c in category])
    else:
        category_collection.insert_one(category.model_dump())