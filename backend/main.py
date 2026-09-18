from fastapi import (
    FastAPI,
    UploadFile,
    File,
    HTTPException,
)

import json
from experiments import compare_variants
from insights import generate_insights
from normalizer import normalize_file
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
@app.get("/api/insights")
def insights():

    conversations_data = get_conversations()

    from models import Conversation

    conversations = [
        Conversation(**conversation)
        for conversation
        in conversations_data
    ]

    if not conversations:

        return {
            "insights": [],
            "recommendations": [],
        }

    analytics = analyze_conversations(
        conversations
    )

    analytics["sequences"] = (
        analyze_sequences(
            conversations
        )
    )

    return generate_insights(
        analytics
    )
@app.get("/api/experiments")
def experiments():

    conversations_data = get_conversations()

    from models import Conversation

    conversations = [
        Conversation(**conversation)
        for conversation
        in conversations_data
    ]

    if not conversations:

        return {
            "variants": []
        }

    analytics = analyze_conversations(
        conversations
    )

    return compare_variants(
        analytics
    )
    
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
        (".json", ".csv")
    ):

        raise HTTPException(
            status_code=400,
            detail="Only CSV and JSON files are supported",
        )

    try:

        contents = await file.read()

        normalized_data, skipped_rows = (
            normalize_file(
                file.filename,
                contents
            )
        )

        from models import Conversation

        conversations = [
            Conversation(
                **conversation
            )
            for conversation
            in normalized_data
        ]

        if not conversations:

            raise HTTPException(
                status_code=400,
                detail="No valid conversations found in file",
            )

        save_conversations(
            conversations
        )

        all_conversations_data = (
            get_conversations()
        )

        all_conversations = [
            Conversation(
                **conversation
            )
            for conversation
            in all_conversations_data
        ]

        analytics = analyze_conversations(
            all_conversations
        )

        analytics["sequences"] = (
            analyze_sequences(
                all_conversations
            )
        )

        return {

            "filename":
                file.filename,

            "status":
                "analyzed",

            "normalized_conversations":
                len(conversations),

            "skipped_rows":
                skipped_rows,

            "total_stored_conversations":
                len(all_conversations),

            "analytics":
                analytics,
        }

    except HTTPException:

        raise

    except Exception as error:

        raise HTTPException(
            status_code=400,
            detail=f"Invalid data: {str(error)}",
        )
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
