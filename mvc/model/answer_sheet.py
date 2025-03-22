from typing import Any, Dict, List, Union
import pymongo
from ..view.answer_sheet import AnswerSheetSchema
from ..model.test_bank import get_test
from datetime import datetime
from bson import ObjectId

client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["mcq_grading_system"]
answer_sheet_collection = db["answer_sheet"]
test_collection = db["tests"]

def insert_answer_sheet(answer_sheet: Union[AnswerSheetSchema, List[AnswerSheetSchema]]):
    if isinstance(answer_sheet, list):
        answer_sheet_collection.insert_many([answer_sheet.model_dump() for answer_sheet in answer_sheet])
    else:
        answer_sheet_collection.insert_one(answer_sheet.model_dump())


def get_all_answer_sheets():
    total = answer_sheet_collection.count_documents({})
    items = list(answer_sheet_collection.find())
    for item in items:
        item['_id'] = str(item['_id'])
    return {"total": total, "items": items}

def grade_answers(correct_answers, student_answers) -> Dict[str, Any]:
    score = 0
    graded_answers = []

    for student_answer in student_answers:
        correct_answer = correct_answers[student_answer['questionIndex'] - 1]['correctAnswer']
        
        is_correct = False
        if correct_answer:
            if isinstance(student_answer['answer'], list):  # If student has multiple answers (e.g., B, C)
                is_correct = set(student_answer['answer']) == set(correct_answer)
            else:  # If student has only one answer (e.g., B)
                is_correct = student_answer['answer'] == correct_answer[0]

        graded_answers.append({
            "questionId": correct_answers[student_answer['questionIndex'] - 1]['questionId'],
            "studentAnswers": student_answer['answer'],
            "correctAnswer": correct_answer,
            "correct": is_correct
        })

        # Increment the score if the answer is correct
        if is_correct:
            score += 1

    # Calculate the total number of questions in the test
    total_questions = len(correct_answers)

    # Return the grading results
    return {
        "score": score,
        "totalQuestions": total_questions,
        "gradedAnswers": graded_answers,
        "percentage": (score / total_questions) * 100 if total_questions > 0 else 0
    }

def score_answer_sheets(answer_sheet_ids: List[str], test_id: str):
    testObj = get_test(test_id)
    if not testObj:
        raise ValueError("Test not found")
    
    correct_answers = [{'questionId': question.id, 'correctAnswer': question.correctOptions} for question in testObj.lstQuestions]

    for answer_sheet_id in answer_sheet_ids:
        answer_sheet = answer_sheet_collection.find_one({"_id": ObjectId(answer_sheet_id)})
        if not answer_sheet:
            raise ValueError(f"Answer sheet with ID {answer_sheet_id} not found")
        student_answers = answer_sheet['detectedAnswers']

        grading_results = grade_answers(correct_answers, student_answers)
        answer_sheet_collection.update_one({"_id": answer_sheet_id}, {"$set": {"gradingResults": grading_results, "dateGraded": datetime.now(), "isGraded": True, "testId": test_id}})
    return {"message": "Answer sheets graded successfully", "results": grading_results}
        