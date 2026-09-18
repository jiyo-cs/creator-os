import csv
import io
import json
from collections import defaultdict
from datetime import datetime


FIELD_ALIASES = {
    "subscriber_id": [
        "subscriber_id",
        "user_id",
        "user",
        "username",
        "subscriber",
        "customer_id",
        "fan_id",
    ],

    "sender": [
        "sender",
        "from",
        "author",
        "role",
        "type",
    ],

    "text": [
        "text",
        "message",
        "content",
        "body",
    ],

    "timestamp": [
        "timestamp",
        "created_at",
        "date",
        "datetime",
        "time",
    ],
}


def find_field(row, field_name):

    aliases = FIELD_ALIASES[field_name]

    normalized_row = {
        str(key).strip().lower():
        value
        for key, value in row.items()
    }

    for alias in aliases:

        if alias in normalized_row:

            value = normalized_row[alias]

            if value is not None and str(value).strip():

                return str(value).strip()

    return None


def normalize_sender(value):

    if not value:
        return None

    value = value.lower().strip()

    creator_values = {
        "creator",
        "owner",
        "admin",
        "me",
        "self",
        "model",
        "account",
    }

    subscriber_values = {
        "subscriber",
        "user",
        "fan",
        "customer",
        "member",
        "client",
    }

    if value in creator_values:
        return "creator"

    if value in subscriber_values:
        return "subscriber"

    return value


def normalize_timestamp(value):

    if not value:
        return None

    value = value.strip()

    formats = [
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%d/%m/%Y %H:%M:%S",
        "%d/%m/%Y %H:%M",
    ]

    for date_format in formats:

        try:

            parsed = datetime.strptime(
                value,
                date_format
            )

            return parsed.isoformat()

        except ValueError:
            continue

    try:

        parsed = datetime.fromisoformat(
            value.replace("Z", "+00:00")
        )

        return parsed.isoformat()

    except ValueError:

        return value


def normalize_message(row):

    subscriber_id = find_field(
        row,
        "subscriber_id"
    )

    sender = find_field(
        row,
        "sender"
    )

    text = find_field(
        row,
        "text"
    )

    timestamp = find_field(
        row,
        "timestamp"
    )

    if not subscriber_id:
        return None

    if not sender:
        return None

    if not text:
        return None

    if not timestamp:
        return None

    return {
        "subscriber_id":
            subscriber_id,

        "sender":
            normalize_sender(sender),

        "text":
            text,

        "timestamp":
            normalize_timestamp(timestamp),
    }


def group_messages(rows):

    conversations = defaultdict(list)

    skipped = 0

    for row in rows:

        message = normalize_message(row)

        if not message:

            skipped += 1

            continue

        subscriber_id = message.pop(
            "subscriber_id"
        )

        conversations[
            subscriber_id
        ].append(message)

    result = []

    for subscriber_id, messages in conversations.items():

        messages.sort(
            key=lambda message:
                message["timestamp"]
        )

        result.append(
            {
                "subscriber_id":
                    subscriber_id,

                "messages":
                    messages,
            }
        )

    return result, skipped


def normalize_json(data):

    # Already in Creator OS format

    if isinstance(data, dict):

        if "conversations" in data:

            return data["conversations"], 0

        if "messages" in data:

            data = data["messages"]

    # Flat message list

    if isinstance(data, list):

        return group_messages(data)

    raise ValueError(
        "Unsupported JSON structure"
    )


def normalize_csv(content):

    text = content.decode(
        "utf-8-sig"
    )

    reader = csv.DictReader(
        io.StringIO(text)
    )

    rows = list(reader)

    return group_messages(rows)


def normalize_file(
    filename,
    content
):

    filename = filename.lower()

    if filename.endswith(".csv"):

        return normalize_csv(
            content
        )

    if filename.endswith(".json"):

        data = json.loads(
            content.decode("utf-8")
        )

        return normalize_json(
            data
        )

    raise ValueError(
        "Only CSV and JSON files are supported"
    )
