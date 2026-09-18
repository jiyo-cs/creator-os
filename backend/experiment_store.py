import sqlite3
import hashlib
from statistics import mean


DATABASE = "creator_os.db"


def get_connection():

    connection = sqlite3.connect(
        DATABASE
    )

    connection.row_factory = sqlite3.Row

    return connection


# =========================================================
# INITIALIZE
# =========================================================

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


# =========================================================
# CREATE EXPERIMENT
# =========================================================

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


# =========================================================
# GET EXPERIMENTS
# =========================================================

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


# =========================================================
# FORMAT SECONDS
# =========================================================

def format_duration(seconds):

    if seconds is None:
        return None

    seconds = int(seconds)

    minutes = seconds // 60
    remaining = seconds % 60

    if minutes == 0:
        return f"{remaining}s"

    if remaining == 0:
        return f"{minutes}m"

    return f"{minutes}m {remaining}s"


# =========================================================
# GET EXPERIMENT DETAILS
# =========================================================

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

    if not experiment:

        connection.close()

        return None

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

    experiment = dict(experiment)

    experiment["results"] = []

    for row in results:

        result = dict(row)

        sent = result["sent"]
        replies = result["replies"]

        reply_rate = (
            replies / sent * 100
            if sent
            else 0
        )

        # -------------------------------------------------
        # Response times
        # -------------------------------------------------

        response_rows = cursor.execute(
            """
            SELECT
                exposure.created_at AS exposure_time,
                reply.created_at AS reply_time
            FROM experiment_events exposure

            INNER JOIN experiment_events reply

                ON reply.experiment_id =
                   exposure.experiment_id

                AND reply.subscriber_id =
                    exposure.subscriber_id

                AND reply.variant =
                    exposure.variant

                AND reply.event_type = 'reply'

            WHERE exposure.experiment_id = ?
            AND exposure.variant = ?
            AND exposure.event_type = 'exposure'
            """,
            (
                experiment_id,
                result["variant"],
            )
        ).fetchall()

        response_times = []

        from datetime import datetime

        for response in response_rows:

            try:

                exposure_time = (
                    datetime.fromisoformat(
                        response["exposure_time"]
                    )
                )

                reply_time = (
                    datetime.fromisoformat(
                        response["reply_time"]
                    )
                )

                difference = (
                    reply_time - exposure_time
                ).total_seconds()

                if difference >= 0:

                    response_times.append(
                        difference
                    )

            except Exception:

                continue

        average_response = (
            mean(response_times)
            if response_times
            else None
        )

        dropoff_rate = (
            100 - reply_rate
            if sent
            else 0
        )

        result["reply_rate_percent"] = round(
            reply_rate,
            2
        )

        result["dropoff_rate_percent"] = round(
            dropoff_rate,
            2
        )

        result["average_response_seconds"] = (
            round(
                average_response,
                2
            )
            if average_response is not None
            else None
        )

        result["average_response_time"] = (
            format_duration(
                average_response
            )
            if average_response is not None
            else None
        )

        result["response_count"] = len(
            response_times
        )

        experiment["results"].append(
            result
        )

    # =====================================================
    # EXPERIMENT INTELLIGENCE
    # =====================================================

    variants = {
        item["variant"]: item
        for item in experiment["results"]
    }

    variant_a = variants.get("A", {})
    variant_b = variants.get("B", {})

    a_sent = variant_a.get(
        "sent",
        0
    )

    b_sent = variant_b.get(
        "sent",
        0
    )

    a_rate = variant_a.get(
        "reply_rate_percent",
        0
    )

    b_rate = variant_b.get(
        "reply_rate_percent",
        0
    )

    total_exposures = (
        a_sent + b_sent
    )

    minimum_sample = 30

    if total_exposures == 0:

        data_quality = 0

    elif total_exposures >= 100:

        data_quality = 100

    else:

        data_quality = round(
            min(
                total_exposures
                / minimum_sample
                * 100,
                100
            ),
            2
        )

    difference = round(
        b_rate - a_rate,
        2
    )

    if total_exposures < minimum_sample:

        recommendation = (
            "Continue collecting data. "
            "The current sample size is "
            "too small for a reliable comparison."
        )

        status = "insufficient_data"

    else:

        if abs(difference) < 3:

            recommendation = (
                "The variants are currently "
                "performing similarly. "
                "Continue monitoring the experiment."
            )

            status = "similar"

        elif difference > 0:

            recommendation = (
                "Variant B currently has a higher "
                "reply rate. Continue collecting "
                "data before making a final decision."
            )

            status = "variant_b_higher"

        else:

            recommendation = (
                "Variant A currently has a higher "
                "reply rate. Continue collecting "
                "data before making a final decision."
            )

            status = "variant_a_higher"

    experiment["intelligence"] = {

        "total_exposures":
            total_exposures,

        "total_replies":
            (
                variant_a.get("replies", 0)
                +
                variant_b.get("replies", 0)
            ),

        "reply_rate_difference":
            difference,

        "data_quality_percent":
            data_quality,

        "minimum_recommended_sample":
            minimum_sample,

        "status":
            status,

        "recommendation":
            recommendation,
    }

    connection.close()

    return experiment


# =========================================================
# ASSIGN VARIANT
# =========================================================

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


# =========================================================
# RECORD REPLY
# =========================================================

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


# =========================================================
# AUTOMATIC SYNC FROM DM EXPORT
# =========================================================

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

                # -----------------------------------------
                # EXPOSURE
                # -----------------------------------------

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
                            event_type,
                            created_at
                        )
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (
                            experiment_id,
                            subscriber_id,
                            variant,
                            "exposure",
                            message.timestamp.isoformat(),
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

                # -----------------------------------------
                # REPLY
                # -----------------------------------------

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
                                    event_type,
                                    created_at
                                )
                                VALUES (?, ?, ?, ?, ?)
                                """,
                                (
                                    experiment_id,
                                    subscriber_id,
                                    variant,
                                    "reply",
                                    next_message.timestamp.isoformat(),
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
