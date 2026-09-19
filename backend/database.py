import sqlite3
import json
from datetime import datetime, timezone


DATABASE = "creator_os.db"

DEFAULT_WORKSPACE_ID = "default_workspace"
DEFAULT_CREATOR_ID = "default_creator"


def get_connection():

    connection = sqlite3.connect(
        DATABASE
    )

    connection.row_factory = sqlite3.Row

    return connection


def initialize_database():

    connection = get_connection()

    cursor = connection.cursor()

    # =========================
    # WORKSPACES
    # =========================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS workspaces (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    # =========================
    # CREATORS
    # =========================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS creators (
            id TEXT PRIMARY KEY,
            workspace_id TEXT NOT NULL,
            name TEXT NOT NULL,
            platform TEXT NOT NULL DEFAULT 'instagram',
            username TEXT,
            created_at TEXT NOT NULL
        )
    """)

    # =========================
    # USERS
    # =========================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            email TEXT NOT NULL UNIQUE,
            name TEXT,
            created_at TEXT NOT NULL
        )
    """)

    # =========================
    # MEMBERSHIPS
    # =========================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS memberships (
            user_id TEXT NOT NULL,
            workspace_id TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'member',
            PRIMARY KEY (
                user_id,
                workspace_id
            )
        )
    """)

    # =========================
    # CONVERSATIONS
    # =========================

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

    # =========================
    # MIGRATE OLD DATABASE
    # =========================

    columns = cursor.execute(
        "PRAGMA table_info(conversations)"
    ).fetchall()

    column_names = {
        column["name"]
        for column in columns
    }

    if "workspace_id" not in column_names:

        cursor.execute("""
            ALTER TABLE conversations
            ADD COLUMN workspace_id TEXT
            NOT NULL
            DEFAULT 'default_workspace'
        """)

    if "creator_id" not in column_names:

        cursor.execute("""
            ALTER TABLE conversations
            ADD COLUMN creator_id TEXT
            NOT NULL
            DEFAULT 'default_creator'
        """)

    # =========================
    # DEFAULT WORKSPACE
    # =========================

    now = datetime.now(
        timezone.utc
    ).isoformat()

    cursor.execute(
        """
        INSERT OR IGNORE INTO workspaces
        (id, name, created_at)
        VALUES (?, ?, ?)
        """,
        (
            DEFAULT_WORKSPACE_ID,
            "Default Workspace",
            now,
        )
    )

    # =========================
    # DEFAULT CREATOR
    # =========================

    cursor.execute(
        """
        INSERT OR IGNORE INTO creators
        (
            id,
            workspace_id,
            name,
            platform,
            username,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            DEFAULT_CREATOR_ID,
            DEFAULT_WORKSPACE_ID,
            "Default Creator",
            "instagram",
            None,
            now,
        )
    )

    # =========================
    # INDEXES
    # =========================

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

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS
        idx_creators_workspace
        ON creators(workspace_id)
    """)

    connection.commit()

    connection.close()


# =========================
# WORKSPACE
# =========================

def get_workspace(
    workspace_id=DEFAULT_WORKSPACE_ID
):

    connection = get_connection()

    row = connection.execute(
        """
        SELECT *
        FROM workspaces
        WHERE id = ?
        """,
        (workspace_id,)
    ).fetchone()

    connection.close()

    if not row:
        return None

    return dict(row)


# =========================
# CREATOR
# =========================

def get_creator(
    creator_id=DEFAULT_CREATOR_ID
):

    connection = get_connection()

    row = connection.execute(
        """
        SELECT *
        FROM creators
        WHERE id = ?
        """,
        (creator_id,)
    ).fetchone()

    connection.close()

    if not row:
        return None

    return dict(row)


# =========================
# CONVERSATIONS
# =========================

def save_conversations(
    conversations,
    workspace_id=DEFAULT_WORKSPACE_ID,
    creator_id=DEFAULT_CREATOR_ID,
):

    connection = get_connection()

    cursor = connection.cursor()

    for conversation in conversations:

        messages = [
            message.model_dump(
                mode="json"
            )
            for message
            in conversation.messages
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

    rows = connection.execute(
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

    result = connection.execute(
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

    connection.execute(
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
