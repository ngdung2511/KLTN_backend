from typing import Annotated, Dict, List, Optional
from pydantic import BaseModel, BeforeValidator, Field
from datetime import datetime

class User(BaseModel):
    id: Optional[Annotated[str, BeforeValidator(str)]] = Field(alias="_id", default=None)
    username: str
    password: str
    email: str
    role: str
    status: bool = Field(default=True, description="True if user is active, False if user is deleted")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    model_config = {
        "json_schema_extra": {
            "example": {
                "username": "johndoe",
                "password": "password123",
                "email": "dung123@gmail.com",
                "role": "admin"
            }
        }
    }

class LoginRequest(BaseModel):
    username: str
    password: str

    model_config = {
        "json_schema_extra": {
            "example": {
                "username": "johndoe",
                "password": "password123"
            }
        }
    }