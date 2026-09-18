from fastapi import (
    FastAPI,
    UploadFile,
    File,
    HTTPException,
)

from fastapi.middleware.cors import CORSMiddleware

import json

from experiments import compare_variants

from experiment_store import (
    initialize_experiments,
    create_experiment,
    get_experiments,
    get_experiment,
    assign_variant,
    record_reply,
    sync_experiment_results,
)

from insights import generate_insights
from normalizer import normalize_file
from reports import generate_report
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

app.add_middleware(

    CORSMiddleware,

    allow_origins=["*"],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"],

)

initialize_database()

initialize_experiments()


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
@app.get("/api/conversations")
def list_conversations():
    conversations = get_conversations()

    return {
        "conversations": conversations
    }
@app.post("/api/experiments")
async def create_experiment_api(data: dict):

    name = data.get("name")
    variant_a = data.get("variant_a")
    variant_b = data.get("variant_b")

    if not name:
        raise HTTPException(
            status_code=400,
            detail="Experiment name is required",
        )

    if not variant_a or not variant_b:
        raise HTTPException(
            status_code=400,
            detail="Both variants are required",
        )

    experiment_id = create_experiment(
        name,
        variant_a,
        variant_b,
    )

    return {
        "id": experiment_id,
        "status": "created",
    }    
@app.get("/api/experiments/list")
def experiments_list():

    return {
        "experiments":
            get_experiments()
    }
@app.get("/api/experiments/{experiment_id}")
def experiment_details(
    experiment_id: int
):

    experiment = get_experiment(
        experiment_id
    )

    if not experiment:

        raise HTTPException(
            status_code=404,
            detail="Experiment not found",
        )

    return experiment
@app.post("/api/experiments/{experiment_id}/assign")
def assign_experiment_variant(
    experiment_id: int,
    data: dict
):

    subscriber_id = data.get("subscriber_id")

    if not subscriber_id:
        raise HTTPException(
            status_code=400,
            detail="subscriber_id is required",
        )

    variant = assign_variant(
        experiment_id,
        str(subscriber_id),
    )

    if not variant:
        raise HTTPException(
            status_code=404,
            detail="Experiment not found",
        )

    experiment = get_experiment(
        experiment_id
    )

    message = (
        experiment["variant_a"]
        if variant == "A"
        else experiment["variant_b"]
    )

    return {
        "experiment_id": experiment_id,
        "subscriber_id": subscriber_id,
        "variant": variant,
        "message": message,
    }


@app.post("/api/experiments/{experiment_id}/reply")
def record_experiment_reply(
    experiment_id: int,
    data: dict
):

    subscriber_id = data.get("subscriber_id")

    if not subscriber_id:
        raise HTTPException(
            status_code=400,
            detail="subscriber_id is required",
        )

    variant = record_reply(
        experiment_id,
        str(subscriber_id),
    )

    if not variant:
        raise HTTPException(
            status_code=404,
            detail="No experiment exposure found for this subscriber",
        )

    return {
        "status": "recorded",
        "experiment_id": experiment_id,
        "subscriber_id": subscriber_id,
        "variant": variant,
    }
    
@app.get("/api/status")
def api_status():

    conversations = get_conversations()

    return {
        "service": "Creator OS",
        "status": "operational",
        "stored_conversations":
            len(conversations),
        "analytics": "available",
        "sequences": "available",
        "insights": "available",
        "experiments": "available",
    }
@app.get("/api/reports/latest")
def latest_report(
    period: str = "all_time"
):

    allowed_periods = {
        "7d": 7,
        "30d": 30,
        "all_time": None,
    }

    if period not in allowed_periods:

        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid period. "
                "Use 7d, 30d, or all_time."
            ),
        )

    conversations_data = (
        get_conversations()
    )

    from models import Conversation

    conversations = [
        Conversation(**conversation)
        for conversation
        in conversations_data
    ]

    days = allowed_periods[period]

    from reports import filter_conversations

    conversations = filter_conversations(
        conversations,
        days,
    )

    if not conversations:

        return {
            "report": None,
            "period": period,
        }

    analytics = analyze_conversations(
        conversations
    )

    analytics["sequences"] = (
        analyze_sequences(
            conversations
        )
    )

    insights_data = generate_insights(
        analytics
    )

    experiments_data = (
        get_experiments()
    )

    return generate_report(
        analytics,
        insights_data,
        experiments_data,
        period,
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

        save_conversations(
            conversations
        )
        sync_experiment_results(
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
