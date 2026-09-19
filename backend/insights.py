from statistics import mean


def format_duration(seconds):

    if seconds is None:
        return None

    seconds = int(seconds)

    minutes = seconds // 60
    remaining = seconds % 60

    if minutes == 0:
        return f"{remaining}s"

    if remaining == 0:
        return f"{minutes}m"

    return f"{minutes}m {remaining}s"


def generate_insights(analytics):

    summary = analytics.get(
        "summary",
        {}
    )

    messages = analytics.get(
        "message_performance",
        []
    )

    sequences = analytics.get(
        "sequences",
        []
    )

    response_time = analytics.get(
        "response_time",
        {}
    )

    total_conversations = summary.get(
        "total_conversations",
        0
    )

    reply_rate = summary.get(
        "reply_rate_percent",
        0
    )

    average_response = response_time.get(
        "average_seconds"
    )

    insights = []
    recommendations = []

    # ==================================================
    # 1. OVERALL ENGAGEMENT
    # ==================================================

    if total_conversations == 0:

        return {
            "overview": {
                "status": "no_data",
                "total_conversations": 0,
                "reply_rate_percent": 0,
            },
            "insights": [],
            "recommendations": [],
        }

    if reply_rate >= 70:

        insights.append({
            "type": "positive",
            "title": "Strong conversation engagement",
            "description": (
                f"{reply_rate}% of conversations "
                "received a subscriber reply."
            ),
        })

    elif reply_rate >= 40:

        insights.append({
            "type": "neutral",
            "title": "Moderate conversation engagement",
            "description": (
                f"The current conversation reply rate "
                f"is {reply_rate}%."
            ),
        })

        recommendations.append({
            "priority": "high",
            "title": "Improve the opening message",
            "description": (
                "Review the first creator message in "
                "conversations that receive no reply. "
                "Test shorter, more specific openings."
            ),
        })

    else:

        insights.append({
            "type": "warning",
            "title": "Low conversation engagement",
            "description": (
                f"Only {reply_rate}% of conversations "
                "received a subscriber reply."
            ),
        })

        recommendations.append({
            "priority": "high",
            "title": "Review the first-touch message",
            "description": (
                "A large proportion of conversations "
                "stop before the subscriber replies. "
                "Prioritize the opening message and "
                "the first follow-up."
            ),
        })

    # ==================================================
    # 2. RESPONSE TIME
    # ==================================================

    if average_response is not None:

        formatted_time = format_duration(
            average_response
        )

        insights.append({
            "type": "neutral",
            "title": "Average subscriber response time",
            "description": (
                f"Subscribers respond after an average "
                f"of {formatted_time}."
            ),
        })

        if average_response > 3600:

            recommendations.append({
                "priority": "medium",
                "title": "Review delayed conversations",
                "description": (
                    "Average response time is above one "
                    "hour. Review whether follow-ups are "
                    "being sent too late."
                ),
            })

    # ==================================================
    # 3. MESSAGE PERFORMANCE
    # ==================================================

    reliable_messages = [
        message
        for message in messages
        if message.get("times_sent", 0) >= 2
    ]

    if reliable_messages:

        best_message = max(
            reliable_messages,
            key=lambda item:
                item.get(
                    "reply_rate_percent",
                    0
                )
        )

        worst_message = min(
            reliable_messages,
            key=lambda item:
                item.get(
                    "reply_rate_percent",
                    0
                )
        )

        insights.append({
            "type": "positive",
            "title": "Best-performing message",
            "description": (
                f'"{best_message["message"]}" has a '
                f'{best_message["reply_rate_percent"]}% '
                f'reply rate across '
                f'{best_message["times_sent"]} sends.'
            ),
            "data": best_message,
        })

        if (
            worst_message["message"]
            != best_message["message"]
        ):

            insights.append({
                "type": "warning",
                "title": "Lowest-performing message",
                "description": (
                    f'"{worst_message["message"]}" has a '
                    f'{worst_message["reply_rate_percent"]}% '
                    f'reply rate across '
                    f'{worst_message["times_sent"]} sends.'
                ),
                "data": worst_message,
            })

            recommendations.append({
                "priority": "high",
                "title": "Review the weakest message",
                "description": (
                    "Inspect the message with the lowest "
                    "reply rate and compare its wording, "
                    "length and position in the conversation "
                    "with higher-performing messages."
                ),
                "data": worst_message,
            })

    # ==================================================
    # 4. SEQUENCE DROP-OFF
    # ==================================================

    reliable_sequences = [
        sequence
        for sequence in sequences
        if sequence.get("entered", 0) >= 2
    ]

    if reliable_sequences:

        biggest_drop = max(
            reliable_sequences,
            key=lambda sequence:
                sequence.get(
                    "dropoff_rate_percent",
                    0
                )
        )

        if biggest_drop.get(
            "dropoff_rate_percent",
            0
        ) >= 50:

            insights.append({
                "type": "warning",
                "title": "Major conversation drop-off",
                "description": (
                    f'{biggest_drop["step"]} has a '
                    f'{biggest_drop["dropoff_rate_percent"]}% '
                    "drop-off rate."
                ),
                "data": biggest_drop,
            })

            recommendations.append({
                "priority": "high",
                "title": "Review the drop-off point",
                "description": (
                    f'Inspect {biggest_drop["step"]}. '
                    "Messages immediately before this "
                    "point should be reviewed for relevance, "
                    "timing and clarity."
                ),
                "data": biggest_drop,
            })

    # ==================================================
    # 5. DATA QUALITY
    # ==================================================

    if total_conversations < 20:

        insights.append({
            "type": "neutral",
            "title": "Small dataset",
            "description": (
                f"The current dataset contains "
                f"{total_conversations} conversations. "
                "Performance patterns may change as "
                "more conversations are imported."
            ),
        })

    elif total_conversations < 50:

        insights.append({
            "type": "neutral",
            "title": "Growing dataset",
            "description": (
                f"The system currently has "
                f"{total_conversations} conversations. "
                "Additional data will make message-level "
                "patterns more reliable."
            ),
        })

    else:

        insights.append({
            "type": "positive",
            "title": "Useful analysis sample",
            "description": (
                f"The system has {total_conversations} "
                "conversations available for analysis."
            ),
        })

    # ==================================================
    # 6. GENERAL ACTION PLAN
    # ==================================================

    if not recommendations:

        recommendations.append({
            "priority": "medium",
            "title": "Continue monitoring performance",
            "description": (
                "No major performance issue was detected "
                "from the current dataset. Continue "
                "collecting conversations and monitor "
                "message-level changes."
            ),
        })

    return {
        "overview": {
            "status": "ready",
            "total_conversations":
                total_conversations,
            "reply_rate_percent":
                reply_rate,
            "average_response_time":
                format_duration(
                    average_response
                )
                if average_response is not None
                else None,
        },

        "insights":
            insights,

        "recommendations":
            recommendations,
    }
