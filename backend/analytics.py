from statistics import mean


def analyze_conversations(conversations):

    total_conversations = len(conversations)

    replied_conversations = 0

    creator_messages = 0
    subscriber_messages = 0

    response_times = []

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

            elif sender == "subscriber":
                subscriber_messages += 1

            if (
                sender == "creator"
                and i + 1 < len(messages)
            ):

                next_message = messages[i + 1]

                if next_message.sender.lower().strip() == "subscriber":

                    subscriber_replied = True

                    response_time = (
                        next_message.timestamp
                        - message.timestamp
                    ).total_seconds()

                    if response_time >= 0:
                        response_times.append(response_time)

        if subscriber_replied:
            replied_conversations += 1

    reply_rate = (
        replied_conversations / total_conversations * 100
        if total_conversations
        else 0
    )

    average_response_time = (
        mean(response_times)
        if response_times
        else None
    )

    return {
        "summary": {
            "total_conversations": total_conversations,
            "conversations_with_reply": replied_conversations,
            "reply_rate_percent": round(reply_rate, 2),
        },

        "messages": {
            "creator_messages": creator_messages,
            "subscriber_messages": subscriber_messages,
            "total_messages": (
                creator_messages + subscriber_messages
            ),
        },

        "response_time": {
            "average_seconds": (
                round(average_response_time, 2)
                if average_response_time is not None
                else None
            ),
        },
    }
