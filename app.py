import os
import sqlite3
from datetime import datetime, timezone

import psycopg2
import psycopg2.extras

from flask import Flask, flash, g, redirect, render_template, request, url_for


APP_NAME = "PBD Laboratories"
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bioventures.db")
DATABASE_URL = os.environ.get("DATABASE_URL")  # e.g. postgres://user:pass@host:5432/dbname
IS_POSTGRES = bool(DATABASE_URL and DATABASE_URL.startswith("postgres"))


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def get_db():
    db = getattr(g, "_db", None)
    if db is None:
        if IS_POSTGRES:
            # For managed Postgres services, the connection string usually includes SSL requirements.
            db = psycopg2.connect(DATABASE_URL)
        else:
            db = sqlite3.connect(DB_PATH)
            db.row_factory = sqlite3.Row
        g._db = db
    return db


def fetchall(query: str, params=()):
    db = get_db()
    if IS_POSTGRES:
        with db.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(query, params)
            return cur.fetchall()
    cur = db.execute(query, params)
    rows = cur.fetchall()
    return rows


def fetchone(query: str, params=()):
    db = get_db()
    if IS_POSTGRES:
        with db.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(query, params)
            return cur.fetchone()
    cur = db.execute(query, params)
    return cur.fetchone()


def execute(query: str, params=()):
    db = get_db()
    if IS_POSTGRES:
        with db.cursor() as cur:
            cur.execute(query, params)
        db.commit()
        return None
    cur = db.execute(query, params)
    db.commit()
    return cur


def init_db() -> None:
    if IS_POSTGRES:
        db = psycopg2.connect(DATABASE_URL)
        try:
            with db.cursor() as cur:
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS visits (
                      id BIGSERIAL PRIMARY KEY,
                      full_name TEXT NOT NULL,
                      company TEXT,
                      email TEXT,
                      phone TEXT,
                      host_name TEXT NOT NULL,
                      purpose TEXT,
                      badge_name TEXT,
                      checked_in_at TIMESTAMPTZ NOT NULL,
                      checked_out_at TIMESTAMPTZ
                    );
                    """
                )
                cur.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_visits_checked_out_at
                    ON visits(checked_out_at);
                    """
                )
                cur.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_visits_checked_in_at
                    ON visits(checked_in_at);
                    """
                )
            db.commit()
        finally:
            db.close()
        return

    db = sqlite3.connect(DB_PATH)
    try:
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS visits (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              full_name TEXT NOT NULL,
              company TEXT,
              email TEXT,
              phone TEXT,
              host_name TEXT NOT NULL,
              purpose TEXT,
              badge_name TEXT,
              checked_in_at TEXT NOT NULL,
              checked_out_at TEXT
            );
            """
        )
        db.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_visits_checked_out_at
            ON visits(checked_out_at);
            """
        )
        db.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_visits_checked_in_at
            ON visits(checked_in_at);
            """
        )
        db.commit()
    finally:
        db.close()


app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-key-change-me")

# Flask 3 removed before_first_request; initialize eagerly.
init_db()


@app.teardown_appcontext
def _close_db(_exc):
    db = getattr(g, "_db", None)
    if db is not None:
        db.close()


@app.get("/")
def home():
    active = fetchall(
        """
        SELECT *
        FROM visits
        WHERE checked_out_at IS NULL
        ORDER BY checked_in_at DESC
        LIMIT 50
        """,
    )

    recent = fetchall(
        """
        SELECT *
        FROM visits
        WHERE checked_out_at IS NOT NULL
        ORDER BY checked_out_at DESC
        LIMIT 10
        """,
    )

    return render_template(
        "index.html",
        app_name=APP_NAME,
        active=active,
        recent=recent,
    )


@app.post("/check-in")
def check_in():
    full_name = (request.form.get("full_name") or "").strip()
    host_name = (request.form.get("host_name") or "").strip()
    company = (request.form.get("company") or "").strip() or None
    email = (request.form.get("email") or "").strip() or None
    phone = (request.form.get("phone") or "").strip() or None
    purpose = (request.form.get("purpose") or "").strip() or None
    badge_name = (request.form.get("badge_name") or "").strip() or None

    if not full_name or not host_name:
        flash("Please enter your full name and the host you’re visiting.", "error")
        return redirect(url_for("home"))

    checked_in_at = utc_now_iso()

    if IS_POSTGRES:
        row = fetchone(
            """
            INSERT INTO visits (full_name, company, email, phone, host_name, purpose, badge_name, checked_in_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (full_name, company, email, phone, host_name, purpose, badge_name, checked_in_at),
        )
        visit_id = row["id"]
    else:
        cur = execute(
            """
            INSERT INTO visits (full_name, company, email, phone, host_name, purpose, badge_name, checked_in_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (full_name, company, email, phone, host_name, purpose, badge_name, checked_in_at),
        )
        # sqlite: lastrowid available from cursor returned by execute()
        visit_id = cur.lastrowid

    flash("Checked in successfully.", "success")
    return redirect(url_for("badge", visit_id=visit_id))


@app.post("/check-out/<int:visit_id>")
def check_out(visit_id: int):
    now = utc_now_iso()
    if IS_POSTGRES:
        execute(
            """
            UPDATE visits
            SET checked_out_at = %s
            WHERE id = %s AND checked_out_at IS NULL
            """,
            (now, visit_id),
        )
    else:
        execute(
            """
            UPDATE visits
            SET checked_out_at = ?
            WHERE id = ? AND checked_out_at IS NULL
            """,
            (now, visit_id),
        )
    flash("Checked out.", "success")
    return redirect(url_for("home"))


@app.get("/badge/<int:visit_id>")
def badge(visit_id: int):
    if IS_POSTGRES:
        visit = fetchone("SELECT * FROM visits WHERE id = %s", (visit_id,))
    else:
        visit = fetchone("SELECT * FROM visits WHERE id = ?", (visit_id,))
    if visit is None:
        flash("Visit not found.", "error")
        return redirect(url_for("home"))
    return render_template("badge.html", app_name=APP_NAME, visit=visit)


@app.get("/history")
def history():
    q = (request.args.get("q") or "").strip()

    where = ""
    params = []
    if q:
        where = """
          WHERE full_name LIKE ? OR company LIKE ? OR host_name LIKE ? OR email LIKE ?
        """
        like = f"%{q}%"
        params = [like, like, like, like]

    if IS_POSTGRES:
        # Postgres uses %s placeholders, not ? placeholders.
        where_pg = ""
        params_pg = []
        if q:
            where_pg = """
              WHERE full_name LIKE %s OR company LIKE %s OR host_name LIKE %s OR email LIKE %s
            """
            params_pg = [f"%{q}%"] * 4
        rows = fetchall(
            f"""
            SELECT *
            FROM visits
            {where_pg}
            ORDER BY checked_in_at DESC
            LIMIT 200
            """,
            params_pg,
        )
    else:
        rows = fetchall(
            f"""
            SELECT *
            FROM visits
            {where}
            ORDER BY checked_in_at DESC
            LIMIT 200
            """,
            params,
        )

    return render_template("history.html", app_name=APP_NAME, q=q, rows=rows)


if __name__ == "__main__":
    init_db()
    app.run(host="127.0.0.1", port=5000, debug=True, use_reloader=False)

