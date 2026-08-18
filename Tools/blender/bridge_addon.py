"""OPTIONAL live bridge: run this inside a Blender GUI session to accept bpy
code over a localhost socket, so an agent can drive a Blender you are watching.

Not needed for the normal pipeline (bpy_runner.py is headless and preferred).
Use this only when you want to see the viewport update live.

To start: open Blender > Scripting workspace > New text block > paste this
file (or open it) > Run Script. The console prints "bridge listening".
To stop: quit Blender.

Security: binds 127.0.0.1 only and executes whatever Python it is sent —
never change the bind address.

Protocol: one JSON object per connection: {"code": "..."}.
Reply: {"ok": bool, "stdout": str, "error": str}.
"""

import io
import json
import queue
import socket
import threading
import traceback
from contextlib import redirect_stdout

import bpy

HOST, PORT = "127.0.0.1", 8666
_jobs = queue.Queue()


def _worker(conn):
    try:
        chunks = []
        while True:
            data = conn.recv(65536)
            if not data:
                break
            chunks.append(data)
            if data.rstrip().endswith(b"}"):
                break
        req = json.loads(b"".join(chunks).decode("utf-8"))
        done = threading.Event()
        result = {}
        _jobs.put((req.get("code", ""), result, done))
        done.wait(timeout=60)
        if not result:
            result = {"ok": False, "stdout": "", "error": "timed out"}
        conn.sendall(json.dumps(result).encode("utf-8"))
    except Exception as exc:  # noqa: BLE001 - report anything to the client
        try:
            conn.sendall(json.dumps(
                {"ok": False, "stdout": "", "error": str(exc)}).encode("utf-8"))
        except OSError:
            pass
    finally:
        conn.close()


def _serve():
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((HOST, PORT))
    srv.listen(4)
    print(f"[bridge] listening on {HOST}:{PORT}")
    while True:
        conn, _ = srv.accept()
        threading.Thread(target=_worker, args=(conn,), daemon=True).start()


def _pump():
    """Runs on Blender's main thread; executes queued code where bpy is safe."""
    try:
        while True:
            code, result, done = _jobs.get_nowait()
            buf = io.StringIO()
            try:
                with redirect_stdout(buf):
                    exec(compile(code, "<bridge>", "exec"), {"bpy": bpy})
                result.update(ok=True, stdout=buf.getvalue(), error="")
            except Exception:  # noqa: BLE001 - report anything to the client
                result.update(ok=False, stdout=buf.getvalue(),
                              error=traceback.format_exc())
            done.set()
    except queue.Empty:
        pass
    return 0.1  # re-run the timer every 100 ms


threading.Thread(target=_serve, daemon=True).start()
bpy.app.timers.register(_pump, persistent=True)
