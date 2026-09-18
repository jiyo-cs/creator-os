def generate_insights(analytics):

    insights = []

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

    reply_rate = summary.get(
        "reply_rate_percent",
        0
    )

    total_conversations = summary.get(
        "total_conversations",
        0
    )


    # Overall engagement

    if reply_rate >= 70:

        insights.append({
            "type": "positive",
            "title": "Strong reply rate",
            "description":
                f"Subscribers replied in "
                f"{reply_rate}% of conversations.",
        })

    elif reply_rate >= 40:

        insights.append({
            "type": "neutral",
            "title": "Moderate reply rate",
            "description":
                f"The current reply rate is "
                f"{reply_rate}%. There is room "
                f"to improve initial engagement.",
        })

    else:

        insights.append({
            "type": "warning",
            "title": "Low reply rate",
            "description":
                f"Only {reply_rate}% of conversations "
                f"received a subscriber reply. "
                f"The opening message and early "
                f"follow-ups should be reviewed.",
        })


    # Best messages

    if messages:

        best = messages[0]

        insights.append({
            "type": "positive",
            "title": "Top performing message",
            "description":
                f'"{best["message"]}" generated '
                f'{best["reply_rate_percent"]}% reply rate '
                f'across {best["times_sent"]} sends.',
        })


    # Worst messages

    if len(messages) >= 2:

        worst = messages[-1]

        insights.append({
            "type": "warning",
            "title": "Message requiring review",
            "description":
                f'"{worst["message"]}" generated '
                f'{worst["reply_rate_percent"]}% reply rate '
                f'across {worst["times_sent"]} sends.',
        })


    # Sequence drop-off

    if sequences:

        biggest_drop = max(
            sequences,
            key=lambda sequence:
                sequence["dropoff_rate_percent"]
        )

        if biggest_drop[
            "dropoff_rate_percent"
        ] > 50:

            insights.append({
                "type": "warning",
                "title": "Major sequence drop-off",
                "description":
                    f'{biggest_drop["step"]} has a '
                    f'{biggest_drop["dropoff_rate_percent"]}% '
                    f'drop-off rate.',
            })


    # Dataset size

    if total_conversations < 50:

        insights.append({
            "type": "neutral",
            "title": "More data needed",
            "description":
                "The dataset contains fewer than "
                "50 conversations. Insights may "
                "become more reliable with a larger "
                "sample.",
        })


    # Recommendations

    recommendations = [

        {
            "priority": "high",
            "title":
                "Test the opening message",
            "description":
                "Create an alternative version of "
                "the first automated message and "
                "compare reply rates."
        },

        {
            "priority": "medium",
            "title":
                "Review high-dropoff steps",
            "description":
                "Inspect messages immediately before "
                "large conversation drop-offs."
        },

        {
            "priority": "medium",
            "title":
                "Build message experiments",
            "description":
                "Track message variants separately "
                "so performance can be compared "
                "over time."
        }

    ]


    return {

        "insights":
            insights,

        "recommendations":
            recommendations,

    }
