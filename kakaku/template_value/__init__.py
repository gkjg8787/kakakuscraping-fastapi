from pydantic import BaseModel, ConfigDict


class BaseTemplateValue(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    def get_context(self):
        return dict(self)
