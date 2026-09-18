from collections import defaultdict


def compare_variants(analytics):

    messages = analytics.get(
        "message_performance",
        []
    )

    variants = []

    for index, message in enumerate(messages):

        variants.append({
            "variant": chr(65 + index),
            "message": message["message"],
            "sent": message["times_sent"],
            "replies": message["replies"],
            "reply_rate_percent":
                message["reply_rate_percent"],
            "average_response_seconds":
                message["average_response_seconds"],
        })

    variants.sort(
        key=lambda item:
            item["reply_rate_percent"],
        reverse=True
    )

    return {
        "variants": variants
    }
