from collections import defaultdict
from statistics import mean


def analyze_conversations(conversations):

    total_conversations = len(conversations)

    replied_conversations = 0

    creator_messages = 0
    subscriber_messages = 0

    response_times = []

    message_stats = defaultdict(
        lambda: {
            "sent": 0,
            "replies": 0,
            "response_times": [],
        }
    )

    for conversation in conversations:

        messages = sorted(
            conversation.messages,
            key=lambda message: message.timestamp
        )

        subscriber_replied = False

        for i, message in enumerate(messages):

            sender = message.sender.lower().strip()

            if sender == "creator":

                creator_messages += 1

                message_text = message.text.strip()

                message_stats[message_text]["sent"] += 1

                if i + 1 < len(messages):

                    next_message = messages[i + 1]

                    if (
                        next_message.sender.lower().strip()
                        == "subscriber"
                    ):

                        subscriber_replied = True

                        message_stats[
                            message_text
                        ]["replies"] += 1

                        response_time = (
                            next_message.timestamp
                            - message.timestamp
                        ).total_seconds()

                        if response_time >= 0:

                            response_times.append(
                                response_time
                            )

                            message_stats[
                                message_text
                            ]["response_times"].append(
                                response_time
                            )

            elif sender == "subscriber":

                subscriber_messages += 1

        if subscriber_replied:
            replied_conversations += 1


    reply_rate = (
        replied_conversations
        / total_conversations
        * 100
        if total_conversations
        else 0
    )


    average_response_time = (
        mean(response_times)
        if response_times
        else None
    )


    # =========================
    # MESSAGE PERFORMANCE
    # =========================

    message_performance = []

    for text, stats in message_stats.items():

        sent = stats["sent"]
        replies = stats["replies"]

        reply_rate_for_message = (
            replies / sent * 100
            if sent
            else 0
        )

        avg_response = (
            mean(stats["response_times"])
            if stats["response_times"]
            else None
        )

        message_performance.append(
            {
                "message": text,
                "times_sent": sent,
                "replies": replies,
                "reply_rate_percent": round(
                    reply_rate_for_message,
                    2
                ),
                "average_response_seconds": (
                    round(avg_response, 2)
                    if avg_response is not None
                    else None
                ),
            }
        )


    # Highest performing messages first

    message_performance.sort(
        key=lambda item:
            item["reply_rate_percent"],
        reverse=True
    )


    return {

        "summary": {

            "total_conversations":
                total_conversations,

            "conversations_with_reply":
                replied_conversations,

            "reply_rate_percent":
                round(reply_rate, 2),
        },


        "messages": {

            "creator_messages":
                creator_messages,

            "subscriber_messages":
                subscriber_messages,

            "total_messages":
                creator_messages
                + subscriber_messages,
        },


        "response_time": {

            "average_seconds":
                (
                    round(
                        average_response_time,
                        2
                    )
                    if average_response_time
                    is not None
                    else None
                ),
        },


        "message_performance":
            message_performance,
    }
