from pydantic import BaseModel, Field


class ActionItem(BaseModel):
    task: str
    owner: str | None = None
    due: str | None = None


class MetaModelVersions(BaseModel):
    whisper: str | None = None
    llm: str | None = None


class Meta(BaseModel):
    duration_sec: float | None = None
    model_versions: MetaModelVersions | None = None
    cached: bool | None = None


class ProcessResponse(BaseModel):
    transcript: str
    summary: str
    participants: list[str] = Field(default_factory=list)
    decisions: list[str] = Field(default_factory=list)
    action_items: list[ActionItem] = Field(default_factory=list)
    language: str | None = None
    meta: Meta | None = None


class DocxRequest(ProcessResponse):
    pass

