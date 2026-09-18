from datetime import datetime, timedelta


def format_duration(seconds):

    if seconds is None:
        return "N/A"

    seconds = int(seconds)

    minutes = seconds // 60
    remaining = seconds % 60

    if minutes == 0:
        return f"{remaining}s"

    if remaining == 0:
        return f"{minutes}m"

    return f"{minutes}m {remaining}s"


def filter_conversations(
    conversations,
    days=None
):

    if days is None:
        return conversations

    cutoff = (
        datetime.utcnow()
        - timedelta(days=days)
    )

    filtered = []

    for conversation in conversations:

        recent_messages = []

        for message in conversation.messages:

            timestamp = message.timestamp

            if timestamp >= cutoff:
                recent_messages.append(
                    message
                )

        if recent_messages:

            from models import Conversation

            filtered.append(
                Conversation(
                    subscriber_id=
                        conversation.subscriber_id,
                    messages=recent_messages,
                )
            )

    return filtered


def generate_report(
    analytics,
    insights_data,
    experiments_data,
    period="all_time",
):

    summary = analytics.get(
        "summary",
        {}
    )

    messages = analytics.get(
        "messages",
        {}
    )

    response_time = analytics.get(
        "response_time",
        {}
    )

    message_performance = analytics.get(
        "message_performance",
        []
    )

    sequences = analytics.get(
        "sequences",
        []
    )

    top_messages = (
        message_performance[:5]
        if message_performance
        else []
    )

    biggest_dropoffs = sorted(
        sequences,
        key=lambda item:
            item.get(
                "dropoff_rate_percent",
                0
            ),
        reverse=True
    )[:5]

    experiments = (
        experiments_data
        if experiments_data
        else []
    )

    return {

        "report": {

            "generated_at":
                datetime.utcnow().isoformat(),

            "period":
                period,

            "summary": {

                "total_conversations":
                    summary.get(
                        "total_conversations",
                        0
                    ),

                "reply_rate_percent":
                    summary.get(
                        "reply_rate_percent",
                        0
                    ),

                "average_response_time":
                    format_duration(
                        response_time.get(
                            "average_seconds"
                        )
                    ),

                "creator_messages":
                    messages.get(
                        "creator_messages",
                        0
                    ),

                "subscriber_messages":
                    messages.get(
                        "subscriber_messages",
                        0
                    ),
            },

            "top_messages":
                top_messages,

            "biggest_dropoffs":
                biggest_dropoffs,

            "insights":
                insights_data.get(
                    "insights",
                    []
                ),

            "recommendations":
                insights_data.get(
                    "recommendations",
                    []
                ),

            "experiments":
                experiments,
        }
    }
