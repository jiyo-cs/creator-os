from fastapi import FastAPI

from models import AnalyzeRequest
from analytics import analyze_conversations


app = FastAPI(
    title="Creator OS API",
    description="DM Analytics & Optimization platform",
    version="0.1.0",
)


@app.get("/")
def root():
    return {
        "service": "Creator OS",
        "status": "online",
        "version": "0.1.0",
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "creator-os",
    }


@app.post("/analyze")
def analyze(payload: AnalyzeRequest):

    return analyze_conversations(
        payload.conversations
    )
