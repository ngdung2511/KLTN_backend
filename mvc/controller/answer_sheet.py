from fastapi import APIRouter, status, UploadFile,File
from ..model.upload import upload_photo
from ..model import answer_sheet
from ..view.answer_sheet import AnswerSheetSchema, ScoreRequest
from typing import List
import base64
import anthropic
import ast


router = APIRouter(prefix="/answer_sheet", tags=["Answer Sheet"])
client = anthropic.Anthropic()
prompt = open("mvc/controller/prompt.txt", "r", encoding="utf-8").read()


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

        # use LLM to get answer
        message = client.messages.create(
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
        content = message.content[0].text
        list_answer = []
        try:
            list_answer = ast.literal_eval(content)
        except:
            raise ValueError("Error in processing the image. Please try again.")
        
        imageId = upload_photo(file)

        
        answer_sheet_data = AnswerSheetSchema(imageId=imageId['file_id'], studentName=studentName, studentCode=studentCode, detectedAnswers=list_answer)
        answer_sheet.insert_answer_sheet(answer_sheet_data)
        results.append(imageId)
    return {"message": "Answer sheets uploaded successfully", "results": results}


@router.post("/list", status_code=status.HTTP_201_CREATED)
async def list_answer_sheets():
    return answer_sheet.get_all_answer_sheets()

@router.post("/score")
async def score_answer_sheets(score_request: ScoreRequest):
    return answer_sheet.score_answer_sheets(score_request.answerSheetId, score_request.testId)
