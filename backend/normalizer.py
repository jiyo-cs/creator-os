import csv
import io
import json
import re
from collections import defaultdict
from datetime import datetime, timezone


FIELD_ALIASES = {
    "subscriber_id": [
        "subscriber_id",
        "user_id",
        "user",
        "username",
        "subscriber",
        "customer_id",
        "fan_id",
        "member_id",
    ],
    "sender": [
        "sender",
        "from",
        "author",
        "role",
        "type",
        "sender_type",
        "message_sender",
    ],
    "text": [
        "text",
        "message",
        "content",
        "body",
        "message_text",
    ],
    "timestamp": [
        "timestamp",
        "created_at",
        "created",
        "date",
        "datetime",
        "time",
        "sent_at",
        "created_date",
    ],
}


def clean_string(value):

    if value is None:
        return None

    value = str(value).strip()

    if not value:
        return None

    return value


def normalize_key(value):

    if value is None:
        return ""

    value = str(value).strip().lower()

    value = re.sub(
        r"[\s\-]+",
        "_",
        value
    )

    return value


def find_field(row, field_name):

    aliases = {
        normalize_key(alias)
        for alias in FIELD_ALIASES[field_name]
    }

    for key, value in row.items():

        normalized_key = normalize_key(key)

        if normalized_key in aliases:

            cleaned = clean_string(value)

            if cleaned is not None:
                return cleaned

    return None


def normalize_sender(value):

    value = clean_string(value)

    if not value:
        return None

    value = value.lower()

    creator_values = {
        "creator",
        "owner",
        "admin",
        "me",
        "self",
        "model",
        "account",
        "operator",
        "staff",
        "you",
        "assistant",
    }

    subscriber_values = {
        "subscriber",
        "user",
        "fan",
        "customer",
        "member",
        "client",
        "buyer",
        "follower",
        "them",
        "other",
    }

    if value in creator_values:
        return "creator"

    if value in subscriber_values:
        return "subscriber"

    return value


def normalize_timestamp(value):

    value = clean_string(value)

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
        "%m/%d/%Y %H:%M:%S",
        "%m/%d/%Y %H:%M",
        "%Y/%m/%d %H:%M:%S",
        "%Y/%m/%d %H:%M",
    ]

    for date_format in formats:

        try:

            parsed = datetime.strptime(
                value,
                date_format
            )

            return parsed.replace(
                tzinfo=timezone.utc
            ).isoformat()

        except ValueError:
            continue

    try:

        normalized = value.replace(
            "Z",
            "+00:00"
        )

        parsed = datetime.fromisoformat(
            normalized
        )

        if parsed.tzinfo is None:

            parsed = parsed.replace(
                tzinfo=timezone.utc
            )

        else:

            parsed = parsed.astimezone(
                timezone.utc
            )

        return parsed.isoformat()

    except ValueError:

        return None


def normalize_text(value):

    value = clean_string(value)

    if not value:
        return None

    value = re.sub(
        r"\s+",
        " ",
        value
    )

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

    normalized_sender = normalize_sender(
        sender
    )

    normalized_text = normalize_text(
        text
    )

    normalized_timestamp = normalize_timestamp(
        timestamp
    )

    if not normalized_sender:
        return None

    if not normalized_text:
        return None

    if not normalized_timestamp:
        return None

    return {
        "subscriber_id":
            subscriber_id,

        "sender":
            normalized_sender,

        "text":
            normalized_text,

        "timestamp":
            normalized_timestamp,
    }


def message_fingerprint(message):

    return (
        message["subscriber_id"],
        message["sender"],
        message["text"].strip().lower(),
        message["timestamp"],
    )


def group_messages(rows):

    conversations = defaultdict(list)

    skipped = 0

    seen = set()

    for row in rows:

        if not isinstance(row, dict):

            skipped += 1
            continue

        message = normalize_message(
            row
        )

        if not message:

            skipped += 1
            continue

        fingerprint = message_fingerprint(
            message
        )

        if fingerprint in seen:

            skipped += 1
            continue

        seen.add(fingerprint)

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

    result.sort(
        key=lambda conversation:
            conversation["subscriber_id"]
    )

    return result, skipped


def normalize_json(data):

    if isinstance(data, dict):

        if "conversations" in data:

            raw_conversations = data[
                "conversations"
            ]

            if not isinstance(
                raw_conversations,
                list
            ):
                raise ValueError(
                    "'conversations' must be a list"
                )

            rows = []

            for conversation in raw_conversations:

                if not isinstance(
                    conversation,
                    dict
                ):
                    continue

                subscriber_id = (
                    conversation.get(
                        "subscriber_id"
                    )
                    or conversation.get(
                        "user_id"
                    )
                    or conversation.get(
                        "username"
                    )
                )

                messages = conversation.get(
                    "messages",
                    []
                )

                if not subscriber_id:
                    continue

                for message in messages:

                    if not isinstance(
                        message,
                        dict
                    ):
                        continue

                    rows.append(
                        {
                            **message,
                            "subscriber_id":
                                subscriber_id,
                        }
                    )

            return group_messages(rows)

        if "messages" in data:

            data = data["messages"]

    if isinstance(data, list):

        return group_messages(data)

    raise ValueError(
        "Unsupported JSON structure"
    )


def normalize_csv(content):

    try:

        text = content.decode(
            "utf-8-sig"
        )

    except UnicodeDecodeError:

        text = content.decode(
            "utf-8",
            errors="replace"
        )

    reader = csv.DictReader(
        io.StringIO(text)
    )

    if not reader.fieldnames:

        raise ValueError(
            "CSV file has no header row"
        )

    rows = list(reader)

    if not rows:

        raise ValueError(
            "CSV file contains no data rows"
        )

    return group_messages(rows)


def normalize_file(
    filename,
    content
):

    if not filename:

        raise ValueError(
            "Filename is required"
        )

    filename = filename.lower().strip()

    if filename.endswith(".csv"):

        return normalize_csv(
            content
        )

    if filename.endswith(".json"):

        try:

            data = json.loads(
                content.decode(
                    "utf-8-sig"
                )
            )

        except UnicodeDecodeError:

            raise ValueError(
                "JSON file must be UTF-8 encoded"
            )

        except json.JSONDecodeError:

            raise ValueError(
                "Invalid JSON file"
            )

        return normalize_json(
            data
        )

    raise ValueError(
        "Only CSV and JSON files are supported"
    )
