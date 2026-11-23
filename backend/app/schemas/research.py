from datetime import datetime

from pydantic import BaseModel, Field


class BriefResponse(BaseModel):
    ticker: str
    company_name: str
    brief_text: str
    generated_at: datetime
    fetched_at: str
    disclaimer: str

class ChatMessage(BaseModel):
    role: str = Field(pattern="^(user|assistant)$")
    content: str = Field(min_length=1, max_length=4000)

class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(default_factory=list, max_length=20)
    user_message: str = Field(min_length=1, max_length=4000)

class ChatResponse(BaseModel):
    reply: str
    messages: list[ChatMessage]
    generated_at: datetime
    disclaimer: str

class ExplainResponse(BaseModel):
    ticker: str
    text: str
    generated_at: datetime
    disclaimer: str
