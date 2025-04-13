from typing import Any, Dict, List, Union
import pymongo
from ..view.answer_sheet import AnswerSheetSchema
from ..model.test_bank import get_test
from datetime import datetime
from bson import ObjectId
import copy
from bs4 import BeautifulSoup
import anthropic
import ast
import json

client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["mcq_grading_system"]
answer_sheet_collection = db["answer_sheet"]
test_collection = db["tests"]
question_collection = db["questions"]
prompt = open("mvc/model/prompt.txt", "r", encoding="utf-8").read()
client_llm = anthropic.Anthropic()

def detect_answer_sheet(encoded_string):
    message = client_llm.messages.create(
        model="claude-3-7-sonnet-20250219",
        max_tokens=2048,
        system=[
            {
                "type": "text",
                "text": prompt,
                "cache_control": {"type": "ephemeral"}
            }
        ],
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": encoded_string
                        }
                    },
                    {
                        "type": "text",
                        "text": "Identify which options have been filled."
                    }
                ]
            }
        ]
    )
    content = json.dumps([item for item in json.loads(message.content[0].text) if item['answer']])
    list_answer = []
    try:
        list_answer = ast.literal_eval(content)
    except:
        raise ValueError("Error in processing the image. Please try again.")
    
    return list_answer


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

def grade_answers(correct_answers, student_answers, answer_sheet_id) -> Dict[str, Any]:
    score = 0
    graded_answers = []
    total_questions = len(correct_answers)

    # Filter student answers to only include those with questionIndex within the test range
    valid_student_answers = [
        answer for answer in student_answers 
        if 1 <= answer['questionIndex'] <= total_questions 
    ]

    for student_answer in valid_student_answers:
        question_idx = student_answer['questionIndex'] - 1
        correct_answer = correct_answers[question_idx]['correctAnswer']
        
        is_correct = False
        if correct_answer:
            if isinstance(student_answer['answer'], list):  # If student has multiple answers (e.g., B, C)
                print('list')
                is_correct = set(student_answer['answer']) == set(correct_answer)
            else:  # If student has only one answer (e.g., B)
                print('single', student_answer['answer'] == correct_answer[0])
                is_correct = student_answer['answer'] == correct_answer[0]

        graded_answers.append({
            "questionId": correct_answers[question_idx]['questionId'],
            "studentAnswers": student_answer['answer'],
            "correctAnswer": correct_answer,
            "correct": is_correct,
            "questionContent": question_collection.find_one({"_id": ObjectId(correct_answers[question_idx]['questionId'])})['content'],
            "correctAnswerContent": BeautifulSoup(question_collection.find_one({"_id": ObjectId(correct_answers[question_idx]['questionId'])})['lstOptions']['option' + correct_answer[0]], 'html.parser').get_text()
        })

        # Increment the score if the answer is correct
        if is_correct:
            score += 1

    # Return the grading results
    return {
        "answer_sheet_id": answer_sheet_id,
        "studentName": answer_sheet_collection.find_one({"_id": ObjectId(answer_sheet_id)})['studentName'],
        "studentCode": answer_sheet_collection.find_one({"_id": ObjectId(answer_sheet_id)})['studentCode'],
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
    
    grading_results = []
    for answer_sheet_id in answer_sheet_ids:
        answer_sheet = answer_sheet_collection.find_one({"_id": ObjectId(answer_sheet_id)})
        if not answer_sheet:
            raise ValueError(f"Answer sheet with ID {answer_sheet_id} not found")
        student_answers = answer_sheet['detectedAnswers']

        grading_result = grade_answers(correct_answers, student_answers, answer_sheet_id)
        grading_results.append(copy.deepcopy(grading_result))
        grading_result.pop("answer_sheet_id")
        grading_result.pop("gradedAnswers")

        answer_sheet_collection.update_one({"_id": ObjectId(answer_sheet_id)}, {"$set": {"gradingResults": grading_results, "dateGraded": datetime.now(), "isGraded": True, "testId": test_id}})
    return {"message": "Answer sheets graded successfully", "results": grading_results}


def quick_score(student_answers: List[str], correct_answers: List[str]):
    score = 0
    graded_answers = []
    total_questions = len(correct_answers)

    for i in range(len(correct_answers)):
        question_idx = i + 1
        correct_answer = [correct_answers[i]]
        student_answer = next((answer['answer'] for answer in student_answers if answer['questionIndex'] == question_idx), None)
        is_correct = False
        if correct_answer:
            if isinstance(student_answer, list):
                is_correct = set(student_answer) == set(correct_answer)
            else:
                is_correct = student_answer == correct_answer[0]

        graded_answers.append({
            "questionIndex": question_idx,
            "studentAnswers": student_answer,
            "correctAnswer": correct_answer,
            "correct": is_correct,
        })

        if is_correct:
            score += 1
    return {
        "score": score,
        "totalQuestions": total_questions,
        "gradedAnswers": graded_answers,
        "percentage": (score / total_questions) * 100 if total_questions > 0 else 0
    }

if __name__ == "__main__":
    student_answers = [{'questionIndex': 1, 'answer': ['A']}, {'questionIndex': 2, 'answer': ['B']}, {'questionIndex': 3, 'answer': ['C']}]
    correct_answers = ['A', 'B']
    print(quick_score(student_answers, correct_answers))