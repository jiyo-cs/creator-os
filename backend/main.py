from fastapi import (
    FastAPI,
    UploadFile,
    File,
    HTTPException,
)

import json

from models import AnalyzeRequest
from analytics import analyze_conversations
from sequences import analyze_sequences

from database import (
    initialize_database,
    save_conversations,
    get_conversations,
    clear_database,
)


app = FastAPI(
    title="Creator OS API",
    description="DM Analytics & Optimization platform",
    version="0.3.0",
)


# =========================
# DATABASE
# =========================

initialize_database()


# =========================
# ROOT
# =========================

@app.get("/")
def root():

    return {
        "service": "Creator OS",
        "status": "online",
        "version": "0.3.0",
    }


@app.get("/health")
def health():

    return {
        "status": "ok",
        "service": "creator-os",
    }


# =========================
# ANALYTICS
# =========================

@app.get("/api/dashboard")
def dashboard():

    conversations_data = get_conversations()

    payload = [
        AnalyzeRequest(
            conversations=[]
        )
    ]

    if not conversations_data:

        return {
            "summary": {
                "total_conversations": 0,
                "conversations_with_reply": 0,
                "reply_rate_percent": 0,
            },

            "messages": {
                "creator_messages": 0,
                "subscriber_messages": 0,
                "total_messages": 0,
            },

            "response_time": {
                "average_seconds": None,
            },

            "message_performance": [],

            "sequences": [],
        }


    request = AnalyzeRequest(
        conversations=conversations_data
    )


    analytics = analyze_conversations(
        request.conversations
    )


    analytics["sequences"] = (
        analyze_sequences(
            request.conversations
        )
    )


    return analytics


# =========================
# UPLOAD
# =========================

@app.post("/upload")
async def upload_file(
    file: UploadFile = File(...)
):

    if not file.filename:

        raise HTTPException(
            status_code=400,
            detail="No file provided",
        )


    if not file.filename.lower().endswith(
        ".json"
    ):

        raise HTTPException(
            status_code=400,
            detail="Only JSON files are supported",
        )


    try:

        contents = await file.read()

        data = json.loads(
            contents.decode("utf-8")
        )

        payload = AnalyzeRequest(
            **data
        )


        # Store imported conversations

        save_conversations(
            payload.conversations
        )


        # Analyze everything currently stored

        all_conversations_data = (
            get_conversations()
        )


        all_conversations = []

        for conversation in all_conversations_data:

            from models import Conversation

            all_conversations.append(
                Conversation(
                    **conversation
                )
            )


        analytics = analyze_conversations(
            all_conversations
        )


        return {

            "filename":
                file.filename,

            "status":
                "analyzed",

            "stored_conversations":
                len(
                    all_conversations
                ),

            "analytics":
                analytics,
        }


    except Exception as error:

        raise HTTPException(
            status_code=400,
            detail=f"Invalid data: {str(error)}",
        )


# =========================
# SEQUENCES
# =========================

@app.get("/sequences")
def sequences():

    conversations_data = (
        get_conversations()
    )


    from models import Conversation

    conversations = [
        Conversation(**conversation)
        for conversation
        in conversations_data
    ]


    return {
        "sequences":
            analyze_sequences(
                conversations
            )
    }


# =========================
# DATABASE RESET
# =========================

@app.delete("/data")
def delete_data():

    clear_database()

    return {
        "status": "cleared"
    }
