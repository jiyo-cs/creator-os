import sqlite3
import json


DATABASE = "creator_os.db"

DEFAULT_WORKSPACE_ID = "default_workspace"
DEFAULT_CREATOR_ID = "default_creator"


def get_connection():

    connection = sqlite3.connect(
        DATABASE
    )

    connection.row_factory = sqlite3.Row

    return connection


def column_exists(
    cursor,
    table_name,
    column_name
):

    columns = cursor.execute(
        f"PRAGMA table_info({table_name})"
    ).fetchall()

    return any(
        column["name"] == column_name
        for column in columns
    )


def initialize_database():

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            workspace_id TEXT NOT NULL DEFAULT 'default_workspace',
            creator_id TEXT NOT NULL DEFAULT 'default_creator',
            subscriber_id TEXT NOT NULL,
            messages TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Safe migration for databases
    # created by the previous version.

    if not column_exists(
        cursor,
        "conversations",
        "workspace_id"
    ):

        cursor.execute("""
            ALTER TABLE conversations
            ADD COLUMN workspace_id TEXT
            NOT NULL
            DEFAULT 'default_workspace'
        """)

    if not column_exists(
        cursor,
        "conversations",
        "creator_id"
    ):

        cursor.execute("""
            ALTER TABLE conversations
            ADD COLUMN creator_id TEXT
            NOT NULL
            DEFAULT 'default_creator'
        """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS
        idx_conversations_workspace
        ON conversations(workspace_id)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS
        idx_conversations_creator
        ON conversations(creator_id)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS
        idx_conversations_subscriber
        ON conversations(subscriber_id)
    """)

    connection.commit()

    connection.close()


def save_conversations(
    conversations,
    workspace_id=DEFAULT_WORKSPACE_ID,
    creator_id=DEFAULT_CREATOR_ID,
):

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
            (
                workspace_id,
                creator_id,
                subscriber_id,
                messages
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                workspace_id,
                creator_id,
                conversation.subscriber_id,
                json.dumps(messages),
            ),
        )

    connection.commit()

    connection.close()


def get_conversations(
    workspace_id=DEFAULT_WORKSPACE_ID,
    creator_id=DEFAULT_CREATOR_ID,
):

    connection = get_connection()

    cursor = connection.cursor()

    rows = cursor.execute(
        """
        SELECT
            subscriber_id,
            messages
        FROM conversations
        WHERE workspace_id = ?
        AND creator_id = ?
        ORDER BY id DESC
        """,
        (
            workspace_id,
            creator_id,
        )
    ).fetchall()

    connection.close()

    conversations = []

    for row in rows:

        conversations.append(
            {
                "subscriber_id":
                    row["subscriber_id"],

                "messages":
                    json.loads(
                        row["messages"]
                    ),
            }
        )

    return conversations


def get_conversation_count(
    workspace_id=DEFAULT_WORKSPACE_ID,
    creator_id=DEFAULT_CREATOR_ID,
):

    connection = get_connection()

    cursor = connection.cursor()

    result = cursor.execute(
        """
        SELECT COUNT(*)
        FROM conversations
        WHERE workspace_id = ?
        AND creator_id = ?
        """,
        (
            workspace_id,
            creator_id,
        )
    ).fetchone()

    connection.close()

    return result[0]


def clear_database(
    workspace_id=DEFAULT_WORKSPACE_ID,
    creator_id=DEFAULT_CREATOR_ID,
):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        DELETE FROM conversations
        WHERE workspace_id = ?
        AND creator_id = ?
        """,
        (
            workspace_id,
            creator_id,
        )
    )

    connection.commit()

    connection.close()
