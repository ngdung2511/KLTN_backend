
from typing import Annotated, List, Optional
from pydantic import BaseModel, BeforeValidator, Field
from datetime import datetime

class Category(BaseModel):
    id: Optional[Annotated[str, BeforeValidator(str)]] = Field(alias="_id", default = None)
    name: str
    description: str
    status: bool = True
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Geography",
                "description": "Geography is a field of science devoted to the study of the lands, features, inhabitants, and phenomena of the Earth and planets. The first person to use the word \"γεωγραφία\" was Eratosthenes (276–194 BC)."
            }
        }
    }

class CategoryCount(BaseModel):
    lstCategory: List[str] = None