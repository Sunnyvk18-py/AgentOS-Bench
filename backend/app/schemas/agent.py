from pydantic import BaseModel, Field


class AgentValidateRequest(BaseModel):
    content: str = Field(min_length=1)


class AgentValidateResponse(BaseModel):
    valid: bool
    errors: list[str] = Field(default_factory=list)
    agent_name: str | None = None
    description: str | None = None


class AgentRegisterRequest(BaseModel):
    filename: str
    content: str = Field(min_length=1)


class AgentRegisterResponse(BaseModel):
    filename: str
    agent_name: str
    message: str
