from typing import Any, Dict, List, Union
import pymongo
from ..view.login import User, LoginRequest
from datetime import datetime
from bson import ObjectId
import copy
import ast
import json
import base64
import numpy as np

db = pymongo.MongoClient("mongodb://localhost:27017/")["mcq_grading_system"]
users_collection = db["users"]

def insert_user(user: User) -> Dict[str, Any]:
    user_dict = user.model_dump()
    user_dict["created_at"] = datetime.now()
    user_dict["updated_at"] = datetime.now()
    result = users_collection.insert_one(user_dict)
    return {"_id": str(result.inserted_id)}

def get_user_by_username(username: str) -> Union[Dict[str, Any], None]:
    user = users_collection.find_one({"username": username})
    if user:
        user["_id"] = str(user["_id"])
        return user
    return None

def authenticate_user(username: str, password: str) -> Union[Dict[str, Any], None]:
    user = users_collection.find_one({"username": username, "password": password})
    if user:
        user["_id"] = str(user["_id"])
        return user
    return None