from fastapi import APIRouter, Form, HTTPException, Query, status, UploadFile, File
from pydantic import BaseModel
from ..model.upload import upload_photo
from ..model import answer_sheet
from ..view.answer_sheet import AnswerSheetSchema, ScoreRequest
from typing import List
import base64
from ..model.answer_sheet import preprocess_image_simple_screen_viz
router = APIRouter(prefix="/answer_sheet", tags=["Answer Sheet"])


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload(files: List[UploadFile] = File(...)):
    results = []
    for file in files:
        file_name = file.filename
        studentName = file_name.split(".")[0].split("_")[1]
        studentCode = file_name.split(".")[0].split("_")[0]
        
        # change image to base64
        content = await file.read()
        encoded_string = base64.b64encode(content).decode("utf-8")      
        processed_base64 = preprocess_image_simple_screen_viz(
                encoded_string=encoded_string,
                visualize=True # Pass the flag here
            )


        # use LLM to get answer
        list_answer = answer_sheet.detect_answer_sheet(processed_base64)
        await file.seek(0)
        imageId = upload_photo(file)
        
        answer_sheet_data = AnswerSheetSchema(imageId=imageId['file_id'], studentName=studentName, studentCode=studentCode, detectedAnswers=list_answer)
        answer_sheet.insert_answer_sheet(answer_sheet_data)
        results.append(imageId)
    return {"message": "Answer sheets uploaded successfully", "results": results}


@router.post("/list", status_code=status.HTTP_201_CREATED)
async def list_answer_sheets():
    return answer_sheet.get_all_answer_sheets()

@router.post("/score", status_code=status.HTTP_201_CREATED)
async def score_answer_sheets(score_request: ScoreRequest):
    return answer_sheet.score_answer_sheets(score_request.answerSheetId, score_request.testId, score_request.gradedBy)

@router.post("/quick_score")
async def quick_score(
    answerSheet: UploadFile = File(...),
    correctAnswer: str   = Form(...)
):
    # 1) Basic form validation
    if not correctAnswer.strip():
        raise HTTPException(400, "correctAnswer must not be empty")

    # 2) Validate filename and parse studentCode & studentName
    filename = getattr(answerSheet, "filename", None)
    if not filename:
        raise HTTPException(400, "No filename provided in upload")
    # Expecting something like "12345_JohnDoe.png"
    name_part = filename.rsplit(".", 1)[0]
    parts = name_part.split("_", 1)
    if len(parts) != 2:
        raise HTTPException(
            400,
            "Filename format invalid: expected 'studentCode_studentName.ext'"
        )
    studentCode, studentName = parts

    try:
        # 3) Read file bytes → base64
        content = await answerSheet.read()
        encoded_string = base64.b64encode(content).decode("utf-8")

        # 4) Reset stream for upload
        await answerSheet.seek(0)

        # 5) Upload to your storage and get image ID
        # image_resp = upload_photo(answerSheet)
        # if not image_resp or "file_id" not in image_resp:
        #     raise HTTPException(500, "Failed to upload answer sheet image")

        # 6) Detect answers
        detected_answers = answer_sheet.detect_answer_sheet(encoded_string)

        # 7) Build and insert your record
        sheet = AnswerSheetSchema(
            imageId        = "dummy_id",
            studentName    = studentName,
            studentCode    = studentCode,
            detectedAnswers= detected_answers
        )
        record_id = answer_sheet.insert_answer_sheet(sheet)
        if not isinstance(record_id, str):
            raise HTTPException(500, "Could not insert answer sheet record")

        # 8) Finally, compute and return the score
        correct_list = [x.strip().upper() for x in correctAnswer.split(",") if x.strip()]
        return answer_sheet.quick_score(detected_answers, correct_list, record_id)

    except HTTPException:
        # re-raise any deliberate 4xx/5xx exceptions
        raise
    except Exception as e:
        # catch-all for anything unexpected
        # (you can also log.error(e) here)
        raise HTTPException(500, "An unexpected error occurred while scoring")
    
@router.get("/grading_history/{testId}")
async def grading_history(testId: str):
    return answer_sheet.get_grading_history(testId)

@router.get("/grading_results_by_historyId/{historyId}")
async def grading_results_by_historyId(historyId: str, search: str = Query(None)):
    return answer_sheet.get_grading_results_by_historyId(historyId, search)
class UpdateDetectedAnswer(BaseModel):
    questionIndex: int
    answer: list[str]

class UpdateAnswerSheetRequest(BaseModel):
    answerSheetId: str
    answers: list[UpdateDetectedAnswer]

@router.post("/update")
async def update_answer_sheet(payload: UpdateAnswerSheetRequest):
    return answer_sheet.update_answer_sheet(payload.answerSheetId, [a.model_dump() for a in payload.answers])

