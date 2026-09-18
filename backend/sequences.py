from collections import defaultdict


def analyze_sequences(conversations):

    sequence_stats = defaultdict(
        lambda: {
            "entered": 0,
            "continued": 0,
            "dropped": 0,
        }
    )

    for conversation in conversations:

        messages = sorted(
            conversation.messages,
            key=lambda message: message.timestamp
        )

        creator_messages = [
            message
            for message in messages
            if message.sender.lower().strip() == "creator"
        ]

        for index, message in enumerate(creator_messages):

            sequence_name = f"Step {index + 1}"

            sequence_stats[
                sequence_name
            ]["entered"] += 1

            # Check whether the subscriber
            # replied after this creator message

            original_index = messages.index(message)

            continued = False

            if original_index + 1 < len(messages):

                next_message = messages[
                    original_index + 1
                ]

                if (
                    next_message.sender.lower().strip()
                    == "subscriber"
                ):
                    continued = True

            if continued:

                sequence_stats[
                    sequence_name
                ]["continued"] += 1

            else:

                sequence_stats[
                    sequence_name
                ]["dropped"] += 1


    results = []

    for step, stats in sequence_stats.items():

        entered = stats["entered"]
        continued = stats["continued"]
        dropped = stats["dropped"]

        continuation_rate = (
            continued / entered * 100
            if entered
            else 0
        )

        dropoff_rate = (
            dropped / entered * 100
            if entered
            else 0
        )

        results.append(
            {
                "step": step,
                "entered": entered,
                "continued": continued,
                "dropped": dropped,
                "continuation_rate_percent":
                    round(
                        continuation_rate,
                        2
                    ),
                "dropoff_rate_percent":
                    round(
                        dropoff_rate,
                        2
                    ),
            }
        )

    return results
