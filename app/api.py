from fastapi import FastAPI
from .core import QAService
from .models import QARequest, QAResponse, APIResponse

app = FastAPI()
qa_service = QAService()


@app.post("/ask", response_model=APIResponse)
async def ask_question(request: QARequest):

    return qa_service.ask_question_api(request.question)


@app.get("/health")
async def health_check():
    return {"status": "OK"}
