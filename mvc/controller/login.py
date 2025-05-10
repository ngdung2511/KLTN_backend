from fastapi import APIRouter, Form, HTTPException, Query, status, UploadFile, File
from pydantic import BaseModel
from ..model import answer_sheet
from ..view.answer_sheet import AnswerSheetSchema, ScoreRequest
from typing import List
from ..model import login
from ..view.login import LoginRequest, User
router = APIRouter(prefix="/authentication", tags=["Authentication"])

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(user: User):
    # 1) Basic form validation
    if not user.username.strip():
        raise HTTPException(400, "username must not be empty")
    if not user.password.strip():
        raise HTTPException(400, "password must not be empty")
    if not user.email.strip():
        raise HTTPException(400, "email must not be empty")
    if not user.role.strip():
        raise HTTPException(400, "role must not be empty")

    # 2) Validate username and password
    if login.get_user_by_username(user.username):
        raise HTTPException(status_code=400, detail="Username already exists")

    # 3) Insert user into database
    return login.insert_user(user)

@router.post("/login")
async def login_route(request: LoginRequest):
    # 1) Basic form validation
    if not request.username.strip():
        raise HTTPException(400, "username must not be empty")
    if not request.password.strip():
        raise HTTPException(400, "password must not be empty")

    # 2) Validate username and password
    user = login.authenticate_user(request.username, request.password)
    if not user:
        raise HTTPException(status_code=400, detail="Invalid username or password")

    # 3) Return user data
    return {"message": "Login successful", "user": user}
