"""
Database module for AI Lost and Found System
Uses SQLite for lightweight, file-based storage
"""
import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "lost_found.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """Initialize database tables."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with get_connection() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS items (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                type        TEXT NOT NULL CHECK(type IN ('lost', 'found')),
                title       TEXT NOT NULL,
                description TEXT NOT NULL,
                category    TEXT NOT NULL,
                location    TEXT NOT NULL,
                date_occurred TEXT NOT NULL,
                contact_name  TEXT NOT NULL,
                contact_email TEXT NOT NULL,
                contact_phone TEXT,
                image_path    TEXT,
                color         TEXT,
                brand         TEXT,
                status        TEXT DEFAULT 'active' CHECK(status IN ('active','matched','resolved')),
                created_at    TEXT DEFAULT (datetime('now')),
                updated_at    TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS matches (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                lost_id     INTEGER NOT NULL REFERENCES items(id),
                found_id    INTEGER NOT NULL REFERENCES items(id),
                score       REAL NOT NULL,
                status      TEXT DEFAULT 'pending' CHECK(status IN ('pending','confirmed','rejected')),
                created_at  TEXT DEFAULT (datetime('now')),
                UNIQUE(lost_id, found_id)
            );

            CREATE TABLE IF NOT EXISTS notifications (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id     INTEGER REFERENCES items(id),
                match_id    INTEGER REFERENCES matches(id),
                message     TEXT NOT NULL,
                is_read     INTEGER DEFAULT 0,
                created_at  TEXT DEFAULT (datetime('now'))
            );
        """)
    print(f"[DB] Initialized database at {DB_PATH}")


# ── ITEMS ────────────────────────────────────────────────────────────────────

def insert_item(data: dict) -> int:
    sql = """
        INSERT INTO items
            (type, title, description, category, location, date_occurred,
             contact_name, contact_email, contact_phone, image_path, color, brand)
        VALUES
            (:type, :title, :description, :category, :location, :date_occurred,
             :contact_name, :contact_email, :contact_phone, :image_path, :color, :brand)
    """
    with get_connection() as conn:
        cur = conn.execute(sql, data)
        return cur.lastrowid


def get_item(item_id: int) -> dict | None:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()
        return dict(row) if row else None


def get_all_items(item_type: str = None, status: str = "active") -> list[dict]:
    with get_connection() as conn:
        if item_type:
            rows = conn.execute(
                "SELECT * FROM items WHERE type=? AND status=? ORDER BY created_at DESC",
                (item_type, status)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM items WHERE status=? ORDER BY created_at DESC",
                (status,)
            ).fetchall()
        return [dict(r) for r in rows]


def update_item_status(item_id: int, status: str):
    with get_connection() as conn:
        conn.execute(
            "UPDATE items SET status=?, updated_at=datetime('now') WHERE id=?",
            (status, item_id)
        )


def delete_item(item_id: int):
    with get_connection() as conn:
        conn.execute("DELETE FROM items WHERE id=?", (item_id,))


def get_stats() -> dict:
    with get_connection() as conn:
        total_lost   = conn.execute("SELECT COUNT(*) FROM items WHERE type='lost'").fetchone()[0]
        total_found  = conn.execute("SELECT COUNT(*) FROM items WHERE type='found'").fetchone()[0]
        total_matched = conn.execute("SELECT COUNT(*) FROM matches WHERE status='confirmed'").fetchone()[0]
        active_cases = conn.execute("SELECT COUNT(*) FROM items WHERE status='active'").fetchone()[0]
        recent_matches = conn.execute(
            "SELECT COUNT(*) FROM matches WHERE created_at >= datetime('now','-7 days')"
        ).fetchone()[0]
        return {
            "total_lost": total_lost,
            "total_found": total_found,
            "total_matched": total_matched,
            "active_cases": active_cases,
            "recent_matches": recent_matches,
        }


# ── MATCHES ──────────────────────────────────────────────────────────────────

def insert_match(lost_id: int, found_id: int, score: float) -> int:
    sql = """
        INSERT OR IGNORE INTO matches (lost_id, found_id, score)
        VALUES (?, ?, ?)
    """
    with get_connection() as conn:
        cur = conn.execute(sql, (lost_id, found_id, score))
        return cur.lastrowid


def get_matches_for_item(item_id: int) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT m.*, 
                   l.title AS lost_title, l.category AS lost_category, l.location AS lost_location,
                   l.image_path AS lost_image, l.contact_name AS lost_contact, l.contact_email AS lost_email,
                   f.title AS found_title, f.category AS found_category, f.location AS found_location,
                   f.image_path AS found_image, f.contact_name AS found_contact, f.contact_email AS found_email
            FROM matches m
            JOIN items l ON m.lost_id  = l.id
            JOIN items f ON m.found_id = f.id
            WHERE m.lost_id = ? OR m.found_id = ?
            ORDER BY m.score DESC
        """, (item_id, item_id)).fetchall()
        return [dict(r) for r in rows]


def get_all_matches(limit: int = 50) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT m.*,
                   l.title AS lost_title, l.image_path AS lost_image,
                   l.contact_name AS lost_contact, l.contact_email AS lost_email,
                   f.title AS found_title, f.image_path AS found_image,
                   f.contact_name AS found_contact, f.contact_email AS found_email
            FROM matches m
            JOIN items l ON m.lost_id  = l.id
            JOIN items f ON m.found_id = f.id
            ORDER BY m.score DESC
            LIMIT ?
        """, (limit,)).fetchall()
        return [dict(r) for r in rows]


def update_match_status(match_id: int, status: str):
    with get_connection() as conn:
        conn.execute("UPDATE matches SET status=? WHERE id=?", (status, match_id))


def insert_notification(item_id: int, match_id: int, message: str):
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO notifications (item_id, match_id, message) VALUES (?,?,?)",
            (item_id, match_id, message)
        )


def get_notifications(limit: int = 20) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM notifications ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]


def mark_notifications_read():
    with get_connection() as conn:
        conn.execute("UPDATE notifications SET is_read=1")
