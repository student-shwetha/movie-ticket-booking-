"""
server.py — Movie Ticket Booking Server
Run this on the SERVER laptop.
Usage: python server.py
"""

import socket
import threading
import sqlite3
import json
import hashlib
import time
import os

# ─── CONFIG ────────────────────────────────────────────────────────────────────
HOST = "0.0.0.0"   # Listen on all interfaces (LAN + localhost)
PORT = 9999
DB   = "tickets.db"

# Global mutex — prevents race conditions across threads
lock = threading.Lock()

# ─── THEATRE DATA ───────────────────────────────────────────────────────────────
THEATRES = {
    "PVR": {
        "10:00 AM": ["A1","A2","A3","B1","B2","B3"],
        "02:00 PM": ["A1","A2","A3","B1","B2","B3"],
        "07:00 PM": ["A1","A2","A3","B1","B2","B3"],
    },
    "INOX": {
        "11:00 AM": ["C1","C2","C3","D1","D2","D3"],
        "04:00 PM": ["C1","C2","C3","D1","D2","D3"],
        "08:30 PM": ["C1","C2","C3","D1","D2","D3"],
    },
}

# ─── DATABASE SETUP ─────────────────────────────────────────────────────────────
def init_db():
    """Create tables if they don't exist."""
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            theatre  TEXT NOT NULL,
            time     TEXT NOT NULL,
            seat     TEXT NOT NULL,
            booked_at REAL,
            UNIQUE(theatre, time, seat)   -- prevents double booking at DB level
        )
    """)
    conn.commit()
    conn.close()

# ─── HELPERS ────────────────────────────────────────────────────────────────────
def hash_pw(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def get_conn():
    """Each thread gets its own SQLite connection (thread-safe pattern)."""
    return sqlite3.connect(DB, check_same_thread=False)

def ok(msg, data=None):
    return json.dumps({"status": "ok", "message": msg, "data": data})

def err(msg):
    return json.dumps({"status": "error", "message": msg})

# ─── ACTION HANDLERS ────────────────────────────────────────────────────────────
def handle_signup(conn, username, password):
    try:
        c = conn.cursor()
        c.execute("INSERT INTO users VALUES (?, ?)", (username, hash_pw(password)))
        conn.commit()
        return ok("Signup successful.")
    except sqlite3.IntegrityError:
        return err("Username already exists.")
    except Exception as e:
        return err(str(e))

def handle_login(conn, username, password):
    try:
        c = conn.cursor()
        c.execute("SELECT password FROM users WHERE username=?", (username,))
        row = c.fetchone()
        if row and row[0] == hash_pw(password):
            return ok("Login successful.")
        return err("Invalid username or password.")
    except Exception as e:
        return err(str(e))

def handle_theatres():
    """Return theatre/timing/seat info to the client."""
    return ok("Theatre list", THEATRES)

def handle_available(conn, theatre, timing):
    """Return seats not yet booked for a given theatre+timing."""
    try:
        theatre = theatre.upper()
        if theatre not in THEATRES or timing not in THEATRES[theatre]:
            return err("Invalid theatre or timing.")
        all_seats = THEATRES[theatre][timing]
        c = conn.cursor()
        c.execute(
            "SELECT seat FROM bookings WHERE theatre=? AND time=?",
            (theatre, timing)
        )
        booked = {r[0] for r in c.fetchall()}
        available = [s for s in all_seats if s not in booked]
        return ok("Available seats", available)
    except Exception as e:
        return err(str(e))

def handle_book(conn, username, theatre, timing, seats, client_ts):
    """
    Book one or more seats atomically.
    Uses threading.Lock() for concurrency + SQLite UNIQUE constraint as backup.
    client_ts: timestamp from client (for timestamp-based control demo).
    """
    results = {}
    theatre = theatre.upper()
    seats   = [s.upper() for s in seats]

    if theatre not in THEATRES or timing not in THEATRES[theatre]:
        return err("Invalid theatre or timing.")

    valid_seats = THEATRES[theatre][timing]

    with lock:   # ← Only one thread enters this block at a time
        server_ts = time.time()

        # Timestamp check: reject if client timestamp is >10s stale
        if client_ts and (server_ts - client_ts) > 10:
            return err("Request too stale (timestamp expired). Please retry.")

        c = conn.cursor()
        for seat in seats:
            if seat not in [s.upper() for s in valid_seats]:
                results[seat] = "Invalid seat ID."
                continue
            try:
                c.execute(
                    "INSERT INTO bookings (username, theatre, time, seat, booked_at) VALUES (?,?,?,?,?)",
                    (username, theatre, timing, seat, server_ts)
                )
                conn.commit()
                results[seat] = "Booked successfully."
            except sqlite3.IntegrityError:
                conn.rollback()
                results[seat] = "Already booked by someone else."
            except Exception as e:
                conn.rollback()
                results[seat] = f"Error: {e}"

    return ok("Booking results", results)

def handle_cancel(conn, username, theatre, timing, seats):
    """Cancel one or more bookings. Users can only cancel their own seats."""
    results = {}
    theatre = theatre.upper()
    seats   = [s.upper() for s in seats]

    with lock:
        c = conn.cursor()
        for seat in seats:
            try:
                c.execute(
                    "DELETE FROM bookings WHERE username=? AND theatre=? AND time=? AND seat=?",
                    (username, theatre, timing, seat)
                )
                if c.rowcount == 0:
                    results[seat] = "No booking found (or not yours)."
                else:
                    conn.commit()
                    results[seat] = "Cancelled successfully."
            except Exception as e:
                conn.rollback()
                results[seat] = f"Error: {e}"

    return ok("Cancellation results", results)

def handle_mybookings(conn, username):
    """Show all bookings for the logged-in user."""
    try:
        c = conn.cursor()
        c.execute(
            "SELECT theatre, time, seat FROM bookings WHERE username=? ORDER BY theatre, time",
            (username,)
        )
        rows = [{"theatre": r[0], "time": r[1], "seat": r[2]} for r in c.fetchall()]
        return ok("Your bookings", rows)
    except Exception as e:
        return err(str(e))

# ─── CLIENT THREAD ──────────────────────────────────────────────────────────────
def client_thread(client_sock, addr):
    """Handles one connected client in its own thread."""
    print(f"[+] Connected: {addr}")
    db_conn = get_conn()   # Each thread gets its own DB connection

    try:
        while True:
            raw = client_sock.recv(4096).decode("utf-8").strip()
            if not raw:
                break   # Client disconnected

            try:
                req = json.loads(raw)
            except json.JSONDecodeError:
                client_sock.sendall((err("Bad JSON format.") + "\n").encode())
                continue

            action = req.get("action", "")
            resp   = ""

            if action == "signup":
                resp = handle_signup(db_conn, req["username"], req["password"])

            elif action == "login":
                resp = handle_login(db_conn, req["username"], req["password"])

            elif action == "theatres":
                resp = handle_theatres()

            elif action == "available":
                resp = handle_available(db_conn, req["theatre"], req["timing"])

            elif action == "book":
                resp = handle_book(
                    db_conn,
                    req["username"], req["theatre"], req["timing"],
                    req["seats"],
                    req.get("timestamp")   # optional timestamp
                )

            elif action == "cancel":
                resp = handle_cancel(
                    db_conn,
                    req["username"], req["theatre"], req["timing"],
                    req["seats"]
                )

            elif action == "mybookings":
                resp = handle_mybookings(db_conn, req["username"])

            else:
                resp = err(f"Unknown action: {action}")

            client_sock.sendall((resp + "\n").encode())

    except ConnectionResetError:
        print(f"[-] Client {addr} disconnected abruptly.")
    except Exception as e:
        print(f"[!] Error with {addr}: {e}")
    finally:
        db_conn.close()
        client_sock.close()
        print(f"[-] Disconnected: {addr}")

# ─── MAIN ───────────────────────────────────────────────────────────────────────
def main():
    init_db()
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(20)
    print(f"[*] Server listening on {HOST}:{PORT}")

    while True:
        client_sock, addr = server.accept()
        t = threading.Thread(target=client_thread, args=(client_sock, addr), daemon=True)
        t.start()
        print(f"[*] Active threads: {threading.active_count() - 1}")

if __name__ == "__main__":
    main()
