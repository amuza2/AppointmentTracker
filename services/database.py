import os
import psycopg2
from psycopg2.extras import DictCursor
from models.appointment import Appointment

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS appointments (
    id SERIAL PRIMARY KEY,
    day VARCHAR(20) NOT NULL,
    time VARCHAR(10) NOT NULL,
    city VARCHAR(100) NOT NULL,
    url TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    archived BOOLEAN NOT NULL DEFAULT FALSE,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);
"""

ALTER_TABLE_SQL = """
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'appointments' AND column_name = 'status') THEN
        ALTER TABLE appointments ADD COLUMN status VARCHAR(20) NOT NULL DEFAULT 'pending';
    END IF;
END $$;
"""


def _get_connection():
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise RuntimeError(
            "DATABASE_URL environment variable is not set. "
            "Set it to your PostgreSQL connection string, e.g. "
            "postgresql://user:pass@host:5432/dbname"
        )
    return psycopg2.connect(database_url)


def init_db():
    with _get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(CREATE_TABLE_SQL)
            cur.execute(ALTER_TABLE_SQL)
        conn.commit()


def insert_appointment(day, time, city, url, description):
    with _get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO appointments (day, time, city, url, description) "
                "VALUES (%s, %s, %s, %s, %s) RETURNING id, created_at;",
                (day, time, city, url, description),
            )
            row = cur.fetchone()
        conn.commit()
        return Appointment(
            id=row[0],
            day=day,
            time=time,
            city=city,
            url=url,
            description=description,
            archived=False,
            created_at=str(row[1]) if row[1] else None,
        )


def get_active_appointments():
    with _get_connection() as conn:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute(
                "SELECT * FROM appointments WHERE archived = FALSE "
                "ORDER BY created_at DESC;"
            )
            return [_row_to_appointment(row) for row in cur.fetchall()]


def get_archived_appointments():
    with _get_connection() as conn:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute(
                "SELECT * FROM appointments WHERE archived = TRUE "
                "ORDER BY created_at DESC;"
            )
            return [_row_to_appointment(row) for row in cur.fetchall()]


def archive_appointment(appointment_id):
    with _get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE appointments SET archived = TRUE WHERE id = %s;",
                (appointment_id,),
            )
        conn.commit()


def unarchive_appointment(appointment_id):
    with _get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE appointments SET archived = FALSE WHERE id = %s;",
                (appointment_id,),
            )
        conn.commit()


def delete_appointment(appointment_id):
    with _get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM appointments WHERE id = %s;",
                (appointment_id,),
            )
        conn.commit()


def update_appointment(appointment_id, day, time, city, url, description):
    with _get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE appointments SET day = %s, time = %s, city = %s, url = %s, description = %s "
                "WHERE id = %s;",
                (day, time, city, url, description, appointment_id),
            )
        conn.commit()


def update_appointment_status(appointment_id, status):
    with _get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE appointments SET status = %s WHERE id = %s;",
                (status, appointment_id),
            )
        conn.commit()


def get_upcoming_appointments(within_minutes=60):
    from datetime import datetime, timedelta

    now = datetime.now()
    window_end = now + timedelta(minutes=within_minutes)

    day_map = {
        0: "Monday",
        1: "Tuesday",
        2: "Wednesday",
        3: "Thursday",
        4: "Friday",
        5: "Saturday",
        6: "Sunday",
    }

    today_name = day_map[now.weekday()]
    active = get_active_appointments()
    upcoming = []
    for apt in active:
        if apt.day.lower() != today_name.lower():
            continue
        try:
            apt_hour, apt_min = map(int, apt.time.split(":"))
            apt_datetime = now.replace(hour=apt_hour, minute=apt_min, second=0, microsecond=0)
            if now <= apt_datetime <= window_end:
                upcoming.append(apt)
        except (ValueError, AttributeError):
            continue
    return upcoming


def _row_to_appointment(row):
    return Appointment(
        id=row["id"],
        day=row["day"],
        time=row["time"],
        city=row["city"],
        url=row["url"],
        description=row["description"],
        archived=row["archived"],
        status=row.get("status", "pending"),
        created_at=str(row["created_at"]) if row["created_at"] else None,
    )
