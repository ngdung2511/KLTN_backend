from typing import List, Union
import pymongo
from ..view.answer_sheet import AnswerSheetSchema 

client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["mcq_grading_system"]
answer_sheet_collection = db["answer_sheet"]

def insert_answer_sheet(answer_sheet: Union[AnswerSheetSchema, List[AnswerSheetSchema]]):
    if isinstance(answer_sheet, list):
        answer_sheet_collection.insert_many([answer_sheet.model_dump() for answer_sheet in answer_sheet])
    else:
        answer_sheet_collection.insert_one(answer_sheet.model_dump())