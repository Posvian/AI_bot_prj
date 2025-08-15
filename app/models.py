from typing import Any, Union

from pydantic import BaseModel


class AIMessage(BaseModel):
    content: str


class QARequest(BaseModel):
    question: str


class QAResponse(BaseModel):
    answer: Union[str, AIMessage]
    sources: list[str]


class APIResponse(BaseModel):
    response: QAResponse
