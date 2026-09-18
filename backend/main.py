from sequences import analyze_sequences
from fastapi import FastAPI, UploadFile, File, HTTPException
import json

from models import AnalyzeRequest
from analytics import analyze_conversations


app = FastAPI(
    title="Creator OS API",
    description="DM Analytics & Optimization platform",
    version="0.2.0",
)


@app.get("/")
def root():
    return {
        "service": "Creator OS",
        "status": "online",
        "version": "0.2.0",
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


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="No file provided"
        )

    if not file.filename.lower().endswith(".json"):
        raise HTTPException(
            status_code=400,
            detail="Only JSON files are supported for now"
        )

    try:

        contents = await file.read()

        data = json.loads(
            contents.decode("utf-8")
        )

        payload = AnalyzeRequest(**data)

        analytics = analyze_conversations(
            payload.conversations
        )

        return {
            "filename": file.filename,
            "status": "analyzed",
            "analytics": analytics,
        }

    except Exception as error:

        raise HTTPException(
            status_code=400,
            detail=f"Invalid JSON data: {str(error)}"
        )
@app.post("/sequences")
def sequences(payload: AnalyzeRequest):

    return {
        "sequences": analyze_sequences(
            payload.conversations
        )
    }
