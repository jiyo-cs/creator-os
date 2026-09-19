from fastapi import (
    FastAPI,
    UploadFile,
    File,
    HTTPException,
    Request,
    Response,
)

from fastapi.middleware.cors import CORSMiddleware

from auth import (
    SESSION_COOKIE,
    authenticate,
    create_session,
    verify_session,
)

from experiments import compare_variants

from experiment_store import (
    initialize_experiments,
    create_experiment,
    get_experiments,
    get_experiment,
    assign_variant,
    record_reply,
    record_conversion,
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


# ============================================================
# APP
# ============================================================

app = FastAPI(
    title="Creator OS API",
    description="DM Analytics & Optimization platform",
    version="0.3.0",
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,

    allow_origins=[
        "https://creator-os-l30s.onrender.com",
        "http://localhost:3000",
        "http://localhost:5500",
    ],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"],
)


# ============================================================
# INITIALIZATION
# ============================================================

initialize_database()
initialize_experiments()


# ============================================================
# PUBLIC ROUTES
# ============================================================

PUBLIC_PATHS = {
    "/",
    "/health",
    "/docs",
    "/openapi.json",
    "/redoc",
    "/api/auth/login",
    "/api/auth/logout",
}


# ============================================================
# AUTHENTICATION MIDDLEWARE
# ============================================================

@app.middleware("http")
async def authentication_middleware(
    request: Request,
    call_next,
):

    path = request.url.path

    # CORS preflight must always pass through.
    if request.method == "OPTIONS":
        return await call_next(request)

    # Public endpoints.
    if path in PUBLIC_PATHS:
        return await call_next(request)

    # Only protect application/API routes.
    protected = (
        path.startswith("/api/")
        or path == "/upload"
        or path == "/sequences"
        or path == "/data"
    )

    if not protected:
        return await call_next(request)

    token = request.cookies.get(
        SESSION_COOKIE
    )

    if not token:
        return Response(
            content='{"detail":"Authentication required"}',
            status_code=401,
            media_type="application/json",
        )

    try:

        session = verify_session(token)

    except Exception:

        session = None

    if not session:

        return Response(
            content='{"detail":"Authentication required"}',
            status_code=401,
            media_type="application/json",
        )

    request.state.auth = session

    return await call_next(request)


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():

    return {
        "service": "Creator OS",
        "status": "online",
        "version": "0.3.0",
    }


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
def health():

    return {
        "status": "ok",
        "service": "creator-os",
        "version": "0.3.0",
    }


# ============================================================
# AUTHENTICATION
# ============================================================

@app.post("/api/auth/login")
async def login(
    request: Request,
    response: Response,
):

    try:

        data = await request.json()

    except Exception:

        raise HTTPException(
            status_code=400,
            detail="Invalid JSON",
        )

    email = str(
        data.get("email", "")
    ).strip()

    password = str(
        data.get("password", "")
    )

    if not email or not password:

        raise HTTPException(
            status_code=400,
            detail="Email and password are required",
        )

    try:

        user = authenticate(
            email,
            password,
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=f"Authentication configuration error: {str(error)}",
        )

    if not user:

        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
        )

    try:

        token = create_session(
            user["email"]
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=f"Session configuration error: {str(error)}",
        )

    response.set_cookie(
        key=SESSION_COOKIE,
        value=token,
        max_age=60 * 60 * 12,
        httponly=True,
        secure=True,
        samesite="none",
        path="/",
    )

    return {
        "status": "authenticated",
        "user": user,
    }


@app.get("/api/auth/me")
def current_user(
    request: Request,
):

    session = getattr(
        request.state,
        "auth",
        None,
    )

    if not session:

        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
        )

    return {
        "authenticated": True,
        "user": {
            "email":
                session["email"],

            "workspace_id":
                session["workspace_id"],

            "creator_id":
                session["creator_id"],
        },
    }


@app.post("/api/auth/logout")
def logout(
    response: Response,
):

    response.delete_cookie(
        key=SESSION_COOKIE,
        path="/",
        secure=True,
        samesite="none",
    )

    return {
        "status": "logged_out",
    }


# ============================================================
# DASHBOARD
# ============================================================

@app.get("/api/dashboard")
def dashboard():

    conversations_data = get_conversations()

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

    request_data = AnalyzeRequest(
        conversations=conversations_data
    )

    analytics = analyze_conversations(
        request_data.conversations
    )

    analytics["sequences"] = (
        analyze_sequences(
            request_data.conversations
        )
    )

    return analytics


# ============================================================
# AI INSIGHTS
# ============================================================

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


# ============================================================
# EXPERIMENT ANALYTICS
# ============================================================

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


# ============================================================
# CONVERSATIONS
# ============================================================

@app.get("/api/conversations")
def list_conversations():

    conversations = get_conversations()

    return {
        "conversations": conversations
    }


# ============================================================
# CREATE EXPERIMENT
# ============================================================

@app.post("/api/experiments")
async def create_experiment_api(
    data: dict
):

    name = data.get("name")

    variant_a = data.get(
        "variant_a"
    )

    variant_b = data.get(
        "variant_b"
    )

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


# ============================================================
# LIST EXPERIMENTS
# ============================================================

@app.get("/api/experiments/list")
def experiments_list():

    return {
        "experiments":
            get_experiments()
    }


# ============================================================
# EXPERIMENT DETAILS
# ============================================================

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


# ============================================================
# ASSIGN EXPERIMENT VARIANT
# ============================================================

@app.post(
    "/api/experiments/{experiment_id}/assign"
)
def assign_experiment_variant(
    experiment_id: int,
    data: dict,
):

    subscriber_id = data.get(
        "subscriber_id"
    )

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
        "experiment_id":
            experiment_id,

        "subscriber_id":
            subscriber_id,

        "variant":
            variant,

        "message":
            message,
    }


# ============================================================
# RECORD EXPERIMENT REPLY
# ============================================================

@app.post(
    "/api/experiments/{experiment_id}/reply"
)
def record_experiment_reply(
    experiment_id: int,
    data: dict,
):

    subscriber_id = data.get(
        "subscriber_id"
    )

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
            detail=(
                "No experiment exposure "
                "found for this subscriber"
            ),
        )

    return {
        "status": "recorded",
        "experiment_id":
            experiment_id,
        "subscriber_id":
            subscriber_id,
        "variant":
            variant,
    }


# ============================================================
# RECORD EXPERIMENT CONVERSION
# ============================================================

@app.post(
    "/api/experiments/{experiment_id}/conversion"
)
def record_experiment_conversion(
    experiment_id: int,
    data: dict,
):

    subscriber_id = data.get(
        "subscriber_id"
    )

    if not subscriber_id:

        raise HTTPException(
            status_code=400,
            detail="subscriber_id is required",
        )

    variant = record_conversion(
        experiment_id,
        str(subscriber_id),
    )

    if not variant:

        raise HTTPException(
            status_code=404,
            detail=(
                "No experiment exposure "
                "found for this subscriber"
            ),
        )

    return {
        "status": "recorded",
        "experiment_id":
            experiment_id,
        "subscriber_id":
            subscriber_id,
        "variant":
            variant,
    }


# ============================================================
# CONVERSION WEBHOOK
# ============================================================

@app.post("/api/webhooks/conversion")
def conversion_webhook(
    data: dict
):

    subscriber_id = data.get(
        "subscriber_id"
    )

    if not subscriber_id:

        raise HTTPException(
            status_code=400,
            detail="subscriber_id is required",
        )

    experiments = get_experiments()

    recorded = []

    for experiment in experiments:

        if experiment["status"] != "running":
            continue

        variant = record_conversion(
            experiment["id"],
            str(subscriber_id),
        )

        if variant:

            recorded.append(
                {
                    "experiment_id":
                        experiment["id"],

                    "variant":
                        variant,
                }
            )

    return {
        "status":
            "processed",

        "subscriber_id":
            subscriber_id,

        "conversions":
            recorded,
    }


# ============================================================
# API STATUS
# ============================================================

@app.get("/api/status")
def api_status():

    conversations = get_conversations()

    return {
        "service":
            "Creator OS",

        "status":
            "operational",

        "stored_conversations":
            len(conversations),

        "analytics":
            "available",

        "sequences":
            "available",

        "insights":
            "available",

        "experiments":
            "available",
    }


# ============================================================
# REPORTS
# ============================================================

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

    days = allowed_periods[
        period
    ]

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


# ============================================================
# UPLOAD
# ============================================================

@app.post("/upload")
async def upload_file(
    file: UploadFile = File(...)
):

    if not file.filename:

        raise HTTPException(
            status_code=400,
            detail="No file provided",
        )

    filename = file.filename.lower()

    if not filename.endswith(
        (".json", ".csv")
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "Only CSV and JSON "
                "files are supported"
            ),
        )

    try:

        contents = await file.read()

        normalized_data, skipped_rows = (
            normalize_file(
                file.filename,
                contents,
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
                detail=(
                    "No valid conversations "
                    "found in file"
                ),
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
            detail=(
                f"Invalid data: {str(error)}"
            ),
        )


# ============================================================
# SEQUENCES
# ============================================================

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


# ============================================================
# DATABASE RESET
# ============================================================

@app.delete("/data")
def delete_data():

    clear_database()

    return {
        "status": "cleared"
    }
