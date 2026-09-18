import sqlite3
import json


DATABASE = "creator_os.db"


def get_connection():

    connection = sqlite3.connect(
        DATABASE
    )

    connection.row_factory = sqlite3.Row

    return connection


def initialize_database():

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subscriber_id TEXT NOT NULL,
            messages TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    connection.commit()

    connection.close()


def save_conversations(conversations):

    connection = get_connection()

    cursor = connection.cursor()

    for conversation in conversations:

        messages = [
            message.model_dump(mode="json")
            for message in conversation.messages
        ]

        cursor.execute(
            """
            INSERT INTO conversations
            (subscriber_id, messages)
            VALUES (?, ?)
            """,
            (
                conversation.subscriber_id,
                json.dumps(messages),
            ),
        )

    connection.commit()

    connection.close()


def get_conversations():

    connection = get_connection()

    cursor = connection.cursor()

    rows = cursor.execute(
        """
        SELECT
            subscriber_id,
            messages
        FROM conversations
        ORDER BY id DESC
        """
    ).fetchall()

    connection.close()

    conversations = []

    for row in rows:

        conversations.append(
            {
                "subscriber_id":
                    row["subscriber_id"],

                "messages":
                    json.loads(row["messages"]),
            }
        )

    return conversations


def clear_database():

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        "DELETE FROM conversations"
    )

    connection.commit()

    connection.close()
