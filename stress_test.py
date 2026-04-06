"""
stress_test.py — Concurrent Booking Stress Test
Simulates 10 clients all trying to book the SAME seat simultaneously.
Expected result: exactly 1 succeeds, 9 fail gracefully.

Usage: python stress_test.py
Run AFTER the server is up and a test user exists (or it auto-creates one).
"""

import socket
import threading
import json
import time

# ─── CONFIG ────────────────────────────────────────────────────────────────────
SERVER_IP   = "172.17.1.96"
PORT        = 9999
NUM_CLIENTS = 5
TARGET_SEAT = "A1"
THEATRE     = "PVR"
TIMING      = "10:00 AM"
TEST_USER   = "stress_user"
TEST_PASS   = "stress123"

results = []
results_lock = threading.Lock()

# ─── HELPERS ────────────────────────────────────────────────────────────────────
def send_recv(sock, payload):
    sock.sendall((json.dumps(payload) + "\n").encode())
    raw = ""
    while not raw.endswith("\n"):
        chunk = sock.recv(4096).decode()
        if not chunk:
            break
        raw += chunk
    return json.loads(raw.strip())

# ─── SETUP: Create a shared test user ───────────────────────────────────────────
def setup_user():
    """Signup once (ignore error if already exists)."""
    try:
        s = socket.socket()
        s.connect((SERVER_IP, PORT))
        send_recv(s, {"action": "signup", "username": TEST_USER, "password": TEST_PASS})
        s.close()
    except Exception as e:
        print(f"[setup] {e}")

# ─── WORKER: Each thread = one client ───────────────────────────────────────────
def worker(client_id):
    try:
        s = socket.socket()
        s.connect((SERVER_IP, PORT))

        # Login
        login_resp = send_recv(s, {
            "action": "login", "username": TEST_USER, "password": TEST_PASS
        })
        if login_resp["status"] != "ok":
            with results_lock:
                results.append((client_id, "LOGIN FAILED"))
            s.close()
            return

        # Try to book the same seat — all at approximately the same time
        book_resp = send_recv(s, {
            "action":    "book",
            "username":  TEST_USER,
            "theatre":   THEATRE,
            "timing":    TIMING,
            "seats":     [TARGET_SEAT],
            "timestamp": time.time()
        })

        seat_result = book_resp.get("data", {}).get(TARGET_SEAT, "unknown")
        with results_lock:
            results.append((client_id, seat_result))

        s.close()

    except Exception as e:
        with results_lock:
            results.append((client_id, f"EXCEPTION: {e}"))

# ─── MAIN ───────────────────────────────────────────────────────────────────────
def main():
    print(f"\n[*] Stress test: {NUM_CLIENTS} clients → same seat ({THEATRE} | {TIMING} | {TARGET_SEAT})")
    setup_user()

    threads = [threading.Thread(target=worker, args=(i+1,)) for i in range(NUM_CLIENTS)]

    # Start all threads as close together as possible
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # ── Summary ──
    print(f"\n{'─'*45}")
    print(f"{'Client':<10} {'Result'}")
    print(f"{'─'*45}")
    success_count = 0
    for cid, result in sorted(results):
        icon = "✓" if "Booked" in result else "✗"
        print(f"  Client {cid:<4}  {icon}  {result}")
        if "Booked" in result:
            success_count += 1
    print(f"{'─'*45}")
    print(f"\n  Successes : {success_count}  (expected: 1)")
    print(f"  Failures  : {NUM_CLIENTS - success_count}  (expected: {NUM_CLIENTS - 1})")
    verdict = "PASS ✓" if success_count == 1 else "FAIL ✗"
    print(f"  Verdict   : {verdict}\n")

if __name__ == "__main__":
    main()
