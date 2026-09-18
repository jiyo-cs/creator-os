import sqlite3
from datetime import datetime


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
        (name, variant_a, variant_b)
        VALUES (?, ?, ?)
        """,
        (
            name,
            variant_a,
            variant_b,
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

    experiment["results"] = [
        dict(row)
        for row in results
    ]

    for result in experiment["results"]:

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

    return experiment
