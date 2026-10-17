"""
Cliente HTTP construido sobre un socket TCP crudo.

"""
import json
import socket


def register(host: str, port: int, username: str, password: str) -> int:
    """Envía POST /register y devuelve el código de estado HTTP (201/409/400)."""
    body = json.dumps({"username": username, "password": password})
    request = (
        f"POST /register HTTP/1.1\r\n"
        f"Host: {host}\r\n"
        f"Content-Type: application/json\r\n"
        f"Content-Length: {len(body)}\r\n"
        f"Connection: close\r\n"
        f"\r\n"
        f"{body}"
    )
    try:
        with socket.create_connection((host, port)) as sock:
            sock.sendall(request.encode("utf-8"))
            response = b""
            while True:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                response += chunk

    except (ConnectionRefusedError, socket.timeout) as e:
        print(f"[HTTP] No se pudo conectar al servidor: {e}")
        return -1

    status_line = response.split(b"\r\n", 1)[0].decode(errors="replace")
    print(f"[HTTP] {status_line}")
    try:
        return int(status_line.split(" ")[1])
    except (IndexError, ValueError):
        return -1


def get_history(host: str, port: int) -> str:
    """GET /history construido a mano sobre socket TCP."""
    request = f"GET /history HTTP/1.1\r\nHost: {host}\r\nConnection: close\r\n\r\n"
    try:
        with socket.create_connection((host, port)) as sock:
            sock.sendall(request.encode("utf-8"))
            response = b""
            while True:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                response += chunk
    except (ConnectionRefusedError, socket.timeout) as e:
        print(f"[HTTP] No se pudo conectar al servidor: {e}")
        return ""

    if b"\r\n\r\n" in response:
        headers, _, body = response.partition(b"\r\n\r\n")
        return body.decode(errors="replace")
    else: 
        return response.decode(errors="replace")
    
