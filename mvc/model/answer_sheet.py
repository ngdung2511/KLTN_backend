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
import base64
import cv2
import numpy as np


client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["mcq_grading_system"]
answer_sheet_collection = db["answer_sheet"]
test_collection = db["tests"]
question_collection = db["questions"]
grading_results_collection = db["grading_results"]
grading_history_collection = db["grading_history"]
prompt = open("mvc/model/prompt.txt", "r", encoding="utf-8").read()
client_llm = anthropic.Anthropic()


def preprocess_image_simple_screen_viz(
    encoded_string: str,
    visualize: bool = True, # Set to False to disable screen visualization
    output_format: str = ".jpg" # e.g., .jpg, .png
) -> str | None:
    """
    Performs simple image preprocessing (grayscale, blur, threshold, contour)
    and optionally displays visualization steps directly on screen using cv2.imshow().

    Args:
        encoded_string: Base64 encoded string of the input image.
        visualize: If True, display intermediate images on screen. REQUIRES GUI.
        output_format: The image format for the returned base64 string.

    Returns:
        Base64 encoded string of the processed (thresholded) image, or None on failure.

    WARNING: 'visualize=True' uses cv2.imshow() which requires a GUI and blocks execution.
             Only use for local debugging, not in headless/server environments.
    """
    windows_to_destroy = [] # Keep track of opened windows if visualizing

    try:
        # 1. Decode Base64 to Bytes
        print("Step 1: Decoding Base64 string...")
        try:
            image_bytes = base64.b64decode(encoded_string)
        except (base64.binascii.Error, ValueError) as e:
            print(f"Error: Invalid Base64 string: {e}")
            return None

        # 2. Decode Bytes to OpenCV Image
        print("Step 2: Decoding image bytes to OpenCV format...")
        np_arr = np.frombuffer(image_bytes, np.uint8)
        img_color = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        if img_color is None:
            print("Error: Failed to decode image bytes into OpenCV format.")
            return None
        print(f"   - Decoded image shape: {img_color.shape}")

        # --- Visualization: Show Original ---
        if visualize:
            print("--> Visualizing: Original Image (Press any key in window to continue)")
            window_name = "1 - Original Image"
            cv2.imshow(window_name, img_color)
            windows_to_destroy.append(window_name)
            cv2.waitKey(0) # Wait indefinitely for a key press IN THE IMAGE WINDOW

        # 3. Convert to Grayscale
        print("Step 3: Converting to grayscale...")
        gray = cv2.cvtColor(img_color, cv2.COLOR_BGR2GRAY)

        # --- Visualization: Show Grayscale ---
        if visualize:
            print("--> Visualizing: Grayscale Image (Press any key in window to continue)")
            window_name = "2 - Grayscale"
            cv2.imshow(window_name, gray)
            windows_to_destroy.append(window_name)
            cv2.waitKey(0)

        # 4. Apply Gaussian Blur
        print("Step 4: Applying Gaussian Blur...")
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        # --- Visualization: Show Blurred ---
        if visualize:
            print("--> Visualizing: Blurred Image (Press any key in window to continue)")
            window_name = "3 - Blurred"
            cv2.imshow(window_name, blurred)
            windows_to_destroy.append(window_name)
            cv2.waitKey(0)

        # 5. Apply Adaptive Thresholding
        print("Step 5: Applying Adaptive Thresholding...")
        thresh = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV, 11, 2 # block_size=11, C=2
        )

        # --- Visualization: Show Thresholded ---
        if visualize:
            print("--> Visualizing: Thresholded Image (Press any key in window to continue)")
            window_name = "4 - Thresholded"
            cv2.imshow(window_name, thresh)
            windows_to_destroy.append(window_name)
            cv2.waitKey(0)

        # # 6. Find Contours
        # print("Step 6: Finding contours...")
        # contours, hierarchy = cv2.findContours(
        #     thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE # Use thresh.copy() if drawing modifies it
        # )
        # print(f"   - Found {len(contours)} contours.")

        # # --- Visualization: Draw Contours ---
        # if visualize:
        #     print("--> Visualizing: Contours on Original (Press any key in window to continue)")
        #     img_contours = img_color.copy() # Draw on a copy of the color image
        #     cv2.drawContours(img_contours, contours, -1, (0, 255, 0), 2) # Draw all in green

        #     # Optional: Highlight largest contour
        #     if contours:
        #          try:
        #              largest_contour = max(contours, key=cv2.contourArea)
        #              cv2.drawContours(img_contours, [largest_contour], -1, (0, 0, 255), 3) # Draw largest in red
        #              print("   - Highlighted largest contour in red.")
        #          except ValueError:
        #              print("   - Could not determine largest contour (no contours?).")

        #     window_name = "5 - Contours"
        #     cv2.imshow(window_name, img_contours)
        #     windows_to_destroy.append(window_name)
        #     cv2.waitKey(0)


        # 7. Prepare Output (Thresholded Image)
        print("Step 7: Encoding processed (thresholded) image to Base64...")
        success, processed_encoded_image = cv2.imencode(output_format, thresh)
        if not success:
            print(f"Error: Failed to encode processed image to {output_format}.")
            return None

        processed_base64 = base64.b64encode(processed_encoded_image.tobytes()).decode('utf-8')
        print("   - Successfully processed image.")

        return processed_base64

    except cv2.error as e:
        print(f"OpenCV Error during preprocessing: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error during preprocessing: {e}")
        return None
    finally:
        # IMPORTANT: Close any OpenCV windows that were opened
        if visualize and windows_to_destroy:
            print("-> Destroying visualization windows.")
            for window_name in windows_to_destroy:
               try:
                   cv2.destroyWindow(window_name)
               except cv2.error: # Window might already be closed manually
                   pass
            # Add a tiny waitkey to ensure windows process the close event
            cv2.waitKey(1)


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
        ids = answer_sheet_collection.insert_many([answer_sheet.model_dump() for answer_sheet in answer_sheet]).inserted_ids
        return [str(id_) for id_ in ids]
    else:
        id_ = answer_sheet_collection.insert_one(answer_sheet.model_dump()).inserted_id
        return str(id_)

def update_answer_sheet(answer_sheet_id: str, answers: list[dict]):
    """
    Update the detectedAnswers field for the answer sheet with the given ID.
    Args:
        answer_sheet_id (str): The ID of the answer sheet to update.
        answers (list[dict]): List of answers with questionIndex and answer fields.
    Returns:
        dict: Result of the update operation.
    """

    result = answer_sheet_collection.update_one(
        {"_id": ObjectId(answer_sheet_id)},
        {"$set": {"detectedAnswers": answers, "updated_at": datetime.now()}}
    )
    if result.matched_count == 0:
        return {"success": False, "message": f"Answer sheet with ID {answer_sheet_id} not found."}
    return {"success": True, "message": "Answer sheet updated successfully."}

def get_all_answer_sheets():
    total = answer_sheet_collection.count_documents({})
    items = list(answer_sheet_collection.find())
    return {"total": total, "items": convert_objectids(items)}

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
                is_correct = set(student_answer['answer']) == set(correct_answer)
            else:  # If student has only one answer (e.g., B)
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
# Convert any ObjectId fields in grading_results to strings before returning
def convert_objectids(obj):
    if isinstance(obj, list):
        return [convert_objectids(i) for i in obj]
    elif isinstance(obj, dict):
        return {k: convert_objectids(v) for k, v in obj.items()}
    elif isinstance(obj, ObjectId):
        return str(obj)
    else:
        return obj
def score_answer_sheets(answer_sheet_ids: List[str], test_id: str, graded_by: str = "system"):
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
        grading_result['testId'] = test_id
        grading_result['isQuickScore'] = False
        grading_results.append(copy.deepcopy(grading_result))


    grading_history = {
        "testId": test_id,
        "gradingResults": grading_results,
        "gradedBy": graded_by,
        "gradedAt": datetime.now(),
        "isQuickScore": False,
    }
    grading_history_insert_result = grading_history_collection.insert_one(grading_history)
    grading_history_id_str = str(grading_history_insert_result.inserted_id)

    # Add gradingId to each grading result and update DB
    for grading_result in grading_results:
        grading_result["gradingId"] = grading_history_id_str
        grading_results_collection.insert_one(grading_result)

        answer_sheet_collection.update_one(
            {"_id": ObjectId(grading_result.get("answer_sheet_id"))},
            {"$set": {"gradingResults": grading_results, "dateGraded": datetime.now(), "isGraded": True, "testId": test_id}}
        )

    # Optionally, remove fields from grading_result before returning if you don't want to expose them
    # for grading_result in grading_results:
    #     grading_result.pop("testId", None)
    #     grading_result.pop("isQuickScore", None)
    #     grading_result.pop("answer_sheet_id", None)
    #     grading_result.pop("gradedAnswers", None)



    return {"message": "Answer sheets graded successfully", "results": convert_objectids(grading_results)}


def quick_score(student_answers: List[str], correct_answers: List[str], id_: str = None):
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
            "answer_sheet_id": id_
        })

        if is_correct:
            score += 1
    results = {
        "studentAnswers": student_answers,
        "correctAnswers": correct_answers,
        "score": score,
        "studentName": answer_sheet_collection.find_one({"_id": ObjectId(id_)})['studentName'],
        "studentCode": answer_sheet_collection.find_one({"_id": ObjectId(id_)})['studentCode'],
        "totalQuestions": total_questions,
        "gradedAnswers": graded_answers,
        "percentage": (score / total_questions) * 100 if total_questions > 0 else 0,
        "isQuickScore": True,
        "answer_sheet_id": id_
    }
    found_grading_result = grading_results_collection.find_one({"answer_sheet_id": id_, "isQuickScore": True})
    if found_grading_result:
        grading_results_collection.update_one({"answer_sheet_id": id_, "isQuickScore": True}, {"$set": results})
    else:
        grading_results_collection.insert_one(results)

    grading_history_collection.insert_one({
        "gradingResults": [results],
        "testId": None,
        "gradedBy": "system",
        "gradedAt": datetime.now(),
        "isQuickScore": True,
    })
        

    return {
        "score": score,
        "totalQuestions": total_questions,
        "gradedAnswers": graded_answers,
        "percentage": (score / total_questions) * 100 if total_questions > 0 else 0
    }

def get_grading_history(test_id: str):
    grading_history = grading_history_collection.find({"testId": test_id})
    grading_history_list = []
    for item in grading_history:
        item['_id'] = str(item['_id'])
        item['testName'] = test_collection.find_one({"_id": ObjectId(test_id)})['title']
        item['sheetCount'] = len(item['gradingResults'])

        grading_history_list.append(item)
    return grading_history_list

def get_grading_results_by_historyId(grading_history_id: str, search: str = None):
    grading_results = list(grading_results_collection.find({"gradingId": grading_history_id}))
    if grading_results:
        for result in grading_results:
            result['_id'] = str(result['_id'])
    print('search', search)
    if search:
        search_lower = search.lower()
        grading_results = [
            result for result in grading_results
            if search_lower in result.get('studentName', '').lower()
            or search_lower in result.get('studentCode', '').lower()
        ]

    # --- Calculate statistics ---
    scores = [result['score'] for result in grading_results]
    average_score = sum(scores) / len(scores) if scores else 0
    highest_score = max(scores) if scores else 0
    lowest_score = min(scores) if scores else 0

    # Count incorrect answers per question
    question_incorrect_counts = {}
    for result in grading_results:
        for answer in result.get('gradedAnswers', []):
            if not answer.get('correct', False):
                qid = answer.get('questionId')
                question_incorrect_counts[qid] = question_incorrect_counts.get(qid, 0) + 1

    # Find the question with the most incorrect answers
    most_incorrect_question_id = None
    most_incorrect_count = 0
    for qid, count in question_incorrect_counts.items():
        if count > most_incorrect_count:
            most_incorrect_question_id = qid
            most_incorrect_count = count

    # Find the question content with the most incorrect answers
    most_incorrect_question_content = None
    if most_incorrect_question_id:
        for result in grading_results:
            for idx, answer in enumerate(result.get('gradedAnswers', [])):
                if answer.get('questionId') == most_incorrect_question_id:
                    most_incorrect_question_content = answer.get('questionContent')
                    most_incorrect_qindex = idx + 1
                    break
                if most_incorrect_question_content is not None:
                    break

    stats = {
        "average_score": average_score,
        "highest_score": highest_score,
        "lowest_score": lowest_score,
        "most_incorrect_question": {
            "qIndex": most_incorrect_qindex,
            "questionId": most_incorrect_question_id,
            "incorrect_count": most_incorrect_count,
            "questionContent": most_incorrect_question_content,
            } if most_incorrect_question_id else None
        }

    return convert_objectids({
        "results": grading_results,
        "stats": stats
    })     


if __name__ == "__main__":
    student_answers = [{'questionIndex': 1, 'answer': ['A']}, {'questionIndex': 2, 'answer': ['B']}, {'questionIndex': 3, 'answer': ['C']}]
    correct_answers = ['A', 'B']
    print(quick_score(student_answers, correct_answers))