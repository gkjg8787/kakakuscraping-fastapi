from fastapi import Request
from pydantic import BaseModel, ConfigDict

class BaseTemplateValue(BaseModel):
    request: Request = None
    model_config = ConfigDict(arbitrary_types_allowed=True)