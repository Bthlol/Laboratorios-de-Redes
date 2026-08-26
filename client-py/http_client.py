"""
Cliente HTTP -- propiedad de Persona C.

IMPORTANTE: el enunciado prohíbe usar clientes HTTP de alto nivel
(urllib.request, requests, etc.) para el CLIENTE. Hay que construir
la petición HTTP a mano y enviarla por un socket TCP crudo.
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

    with socket.create_connection((host, port)) as sock:
        sock.sendall(request.encode("utf-8"))
        response = b""
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            response += chunk

    # TODO(Persona C): parsear la línea de estado "HTTP/1.1 <code> ..."
    # y devolver el código como int. También manejar timeouts/errores de conexión.
    status_line = response.split(b"\r\n", 1)[0].decode(errors="replace")
    print(f"[HTTP] {status_line}")
    try:
        return int(status_line.split(" ")[1])
    except (IndexError, ValueError):
        return -1


def get_history(host: str, port: int) -> str:
    """GET /history construido a mano sobre socket TCP."""
    request = f"GET /history HTTP/1.1\r\nHost: {host}\r\nConnection: close\r\n\r\n"
    with socket.create_connection((host, port)) as sock:
        sock.sendall(request.encode("utf-8"))
        response = b""
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            response += chunk
    # TODO(Persona C): separar headers del body y devolver solo el body
    return response.decode(errors="replace")
