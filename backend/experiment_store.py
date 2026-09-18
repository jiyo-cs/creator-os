import sqlite3
import hashlib


DATABASE = "creator_os.db"


def get_connection():

    connection = sqlite3.connect(
        DATABASE
    )

    connection.row_factory = sqlite3.Row

    return connection


def initialize_experiments():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS experiments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            variant_a TEXT NOT NULL,
            variant_b TEXT NOT NULL,
            status TEXT DEFAULT 'draft',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS experiment_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            experiment_id INTEGER NOT NULL,
            variant TEXT NOT NULL,
            sent INTEGER DEFAULT 0,
            replies INTEGER DEFAULT 0,
            FOREIGN KEY (experiment_id)
                REFERENCES experiments(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS experiment_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            experiment_id INTEGER NOT NULL,
            subscriber_id TEXT NOT NULL,
            variant TEXT NOT NULL,
            event_type TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (experiment_id)
                REFERENCES experiments(id)
        )
    """)

    connection.commit()
    connection.close()


def create_experiment(
    name,
    variant_a,
    variant_b
):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO experiments
        (name, variant_a, variant_b, status)
        VALUES (?, ?, ?, ?)
        """,
        (
            name,
            variant_a,
            variant_b,
            "running",
        )
    )

    experiment_id = cursor.lastrowid

    cursor.execute(
        """
        INSERT INTO experiment_results
        (experiment_id, variant)
        VALUES (?, ?)
        """,
        (
            experiment_id,
            "A",
        )
    )

    cursor.execute(
        """
        INSERT INTO experiment_results
        (experiment_id, variant)
        VALUES (?, ?)
        """,
        (
            experiment_id,
            "B",
        )
    )

    connection.commit()
    connection.close()

    return experiment_id


def get_experiments():

    connection = get_connection()
    cursor = connection.cursor()

    rows = cursor.execute(
        """
        SELECT
            id,
            name,
            variant_a,
            variant_b,
            status,
            created_at
        FROM experiments
        ORDER BY id DESC
        """
    ).fetchall()

    connection.close()

    return [
        dict(row)
        for row in rows
    ]


def get_experiment(
    experiment_id
):

    connection = get_connection()
    cursor = connection.cursor()

    experiment = cursor.execute(
        """
        SELECT
            id,
            name,
            variant_a,
            variant_b,
            status,
            created_at
        FROM experiments
        WHERE id = ?
        """,
        (experiment_id,)
    ).fetchone()

    results = cursor.execute(
        """
        SELECT
            variant,
            sent,
            replies
        FROM experiment_results
        WHERE experiment_id = ?
        ORDER BY variant
        """,
        (experiment_id,)
    ).fetchall()

    connection.close()

    if not experiment:
        return None

    experiment = dict(experiment)

    experiment["results"] = []

    for row in results:

        result = dict(row)

        sent = result["sent"]
        replies = result["replies"]

        result["reply_rate_percent"] = (
            round(
                replies / sent * 100,
                2
            )
            if sent
            else 0
        )

        experiment["results"].append(
            result
        )

    return experiment


def assign_variant(
    experiment_id,
    subscriber_id
):

    connection = get_connection()
    cursor = connection.cursor()

    experiment = cursor.execute(
        """
        SELECT id, status
        FROM experiments
        WHERE id = ?
        """,
        (experiment_id,)
    ).fetchone()

    if not experiment:

        connection.close()

        return None

    existing = cursor.execute(
        """
        SELECT variant
        FROM experiment_events
        WHERE experiment_id = ?
        AND subscriber_id = ?
        AND event_type = 'exposure'
        ORDER BY id ASC
        LIMIT 1
        """,
        (
            experiment_id,
            subscriber_id,
        )
    ).fetchone()

    if existing:

        variant = existing["variant"]

        connection.close()

        return variant

    digest = hashlib.sha256(
        f"{experiment_id}:{subscriber_id}".encode()
    ).hexdigest()

    number = int(
        digest[:8],
        16
    )

    variant = (
        "A"
        if number % 2 == 0
        else "B"
    )

    cursor.execute(
        """
        INSERT INTO experiment_events
        (
            experiment_id,
            subscriber_id,
            variant,
            event_type
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            experiment_id,
            subscriber_id,
            variant,
            "exposure",
        )
    )

    cursor.execute(
        """
        UPDATE experiment_results
        SET sent = sent + 1
        WHERE experiment_id = ?
        AND variant = ?
        """,
        (
            experiment_id,
            variant,
        )
    )

    connection.commit()
    connection.close()

    return variant


def record_reply(
    experiment_id,
    subscriber_id
):

    connection = get_connection()
    cursor = connection.cursor()

    exposure = cursor.execute(
        """
        SELECT variant
        FROM experiment_events
        WHERE experiment_id = ?
        AND subscriber_id = ?
        AND event_type = 'exposure'
        ORDER BY id ASC
        LIMIT 1
        """,
        (
            experiment_id,
            subscriber_id,
        )
    ).fetchone()

    if not exposure:

        connection.close()

        return None

    variant = exposure["variant"]

    existing_reply = cursor.execute(
        """
        SELECT id
        FROM experiment_events
        WHERE experiment_id = ?
        AND subscriber_id = ?
        AND event_type = 'reply'
        LIMIT 1
        """,
        (
            experiment_id,
            subscriber_id,
        )
    ).fetchone()

    if existing_reply:

        connection.close()

        return variant

    cursor.execute(
        """
        INSERT INTO experiment_events
        (
            experiment_id,
            subscriber_id,
            variant,
            event_type
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            experiment_id,
            subscriber_id,
            variant,
            "reply",
        )
    )

    cursor.execute(
        """
        UPDATE experiment_results
        SET replies = replies + 1
        WHERE experiment_id = ?
        AND variant = ?
        """,
        (
            experiment_id,
            variant,
        )
    )

    connection.commit()
    connection.close()

    return variant


def sync_experiment_results(
    conversations
):

    connection = get_connection()
    cursor = connection.cursor()

    experiments = cursor.execute(
        """
        SELECT
            id,
            variant_a,
            variant_b,
            status
        FROM experiments
        WHERE status = 'running'
        """
    ).fetchall()

    updated = 0

    for experiment in experiments:

        experiment_id = experiment["id"]

        variant_a = (
            experiment["variant_a"]
            .strip()
        )

        variant_b = (
            experiment["variant_b"]
            .strip()
        )

        for conversation in conversations:

            subscriber_id = str(
                conversation.subscriber_id
            )

            messages = sorted(
                conversation.messages,
                key=lambda message:
                    message.timestamp
            )

            for i, message in enumerate(
                messages
            ):

                sender = (
                    message.sender
                    .lower()
                    .strip()
                )

                if sender != "creator":

                    continue

                text = message.text.strip()

                if text == variant_a:

                    variant = "A"

                elif text == variant_b:

                    variant = "B"

                else:

                    continue

                existing_exposure = cursor.execute(
                    """
                    SELECT id
                    FROM experiment_events
                    WHERE experiment_id = ?
                    AND subscriber_id = ?
                    AND event_type = 'exposure'
                    LIMIT 1
                    """,
                    (
                        experiment_id,
                        subscriber_id,
                    )
                ).fetchone()

                if not existing_exposure:

                    cursor.execute(
                        """
                        INSERT INTO experiment_events
                        (
                            experiment_id,
                            subscriber_id,
                            variant,
                            event_type
                        )
                        VALUES (?, ?, ?, ?)
                        """,
                        (
                            experiment_id,
                            subscriber_id,
                            variant,
                            "exposure",
                        )
                    )

                    cursor.execute(
                        """
                        UPDATE experiment_results
                        SET sent = sent + 1
                        WHERE experiment_id = ?
                        AND variant = ?
                        """,
                        (
                            experiment_id,
                            variant,
                        )
                    )

                    updated += 1

                if i + 1 < len(messages):

                    next_message = (
                        messages[i + 1]
                    )

                    next_sender = (
                        next_message.sender
                        .lower()
                        .strip()
                    )

                    if next_sender == "subscriber":

                        existing_reply = cursor.execute(
                            """
                            SELECT id
                            FROM experiment_events
                            WHERE experiment_id = ?
                            AND subscriber_id = ?
                            AND event_type = 'reply'
                            LIMIT 1
                            """,
                            (
                                experiment_id,
                                subscriber_id,
                            )
                        ).fetchone()

                        if not existing_reply:

                            cursor.execute(
                                """
                                INSERT INTO experiment_events
                                (
                                    experiment_id,
                                    subscriber_id,
                                    variant,
                                    event_type
                                )
                                VALUES (?, ?, ?, ?)
                                """,
                                (
                                    experiment_id,
                                    subscriber_id,
                                    variant,
                                    "reply",
                                )
                            )

                            cursor.execute(
                                """
                                UPDATE experiment_results
                                SET replies = replies + 1
                                WHERE experiment_id = ?
                                AND variant = ?
                                """,
                                (
                                    experiment_id,
                                    variant,
                                )
                            )

    connection.commit()

    connection.close()

    return updated
