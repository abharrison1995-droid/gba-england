"""Client for the optional live bridge (bridge_addon.py running in a GUI Blender).

    python Tools/blender/bridge_client.py <script.py>
    python Tools/blender/bridge_client.py -c "import bpy; print(bpy.app.version)"
"""

import json
import socket
import sys
from pathlib import Path

HOST, PORT = "127.0.0.1", 8666


def send(code, timeout=60):
    with socket.create_connection((HOST, PORT), timeout=timeout) as s:
        s.sendall(json.dumps({"code": code}).encode("utf-8"))
        s.shutdown(socket.SHUT_WR)
        chunks = []
        while True:
            data = s.recv(65536)
            if not data:
                break
            chunks.append(data)
    return json.loads(b"".join(chunks).decode("utf-8"))


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(2)
    if args[0] == "-c":
        code = " ".join(args[1:])
    else:
        code = Path(args[0]).read_text(encoding="utf-8")
    try:
        reply = send(code)
    except ConnectionRefusedError:
        print("ERROR: no bridge listening on 127.0.0.1:8666 — is a GUI Blender "
              "running bridge_addon.py?", file=sys.stderr)
        sys.exit(2)
    if reply.get("stdout"):
        print(reply["stdout"], end="")
    if not reply.get("ok"):
        print(reply.get("error", "unknown error"), file=sys.stderr)
        sys.exit(1)
