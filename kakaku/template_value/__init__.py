from fastapi import Request
from pydantic import BaseModel

class BaseTemplateValue(BaseModel):
    request: Request = None
    class Config:
        arbitrary_types_allowed = True