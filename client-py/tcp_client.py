"""
Cliente TCP -- propiedad de Barbie.

Debe ser totalmente concurrente: un hilo recibe broadcasts sin bloquear
mientras el usuario escribe en la consola (eso se orquesta en main.py).
"""
import socket
import threading


class TCPClient:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.sock: socket.socket | None = None
        self.token: str | None = None
        self.udp_port: int | None = None
        self._recv_thread: threading.Thread | None = None
        self._running = False
        self._buffer = b""

    def connect(self):
        self.sock = socket.create_connection((self.host, self.port))

    def _send_line(self, line: str):
        self.sock.sendall((line + "\n").encode("utf-8"))

    def _read_line(self) -> str:

        while b"\n" not in self._buffer:
            data = self.sock.recv(4096)
            if not data:
                raise OSError("El servidor cerró la conexión")
            self._buffer += data

        line, _, self._buffer = self._buffer.partition(b"\n")
        return line.decode("utf-8", errors="replace").strip()


    def login(self, username: str, password: str) -> bool:
        self._send_line(f"LOGIN {username} {password}")
        response = self._read_line()
        parts = response.split(" ")
        if parts[0] == "OK":
            self.token = parts[1]
            self.udp_port = int(parts[2])
            return True
        print(f"[TCP] Login fallido: {response}")
        return False

    def send_message(self, contenido: str):
        if not self.token:
            raise RuntimeError("no hay sesión activa")
        self._send_line(f"MSG {self.token} {contenido}")


    def start_receiver(self):
        """Lanza el hilo que escucha continuamente el socket TCP (no bloqueante)."""
        self._running = True
        self._recv_thread = threading.Thread(target=self._receive_loop, daemon=True)
        self._recv_thread.start()

    def _receive_loop(self):
        while self._running:
            try:
                line = self._read_line()
            except OSError:
                break
            if not line:
                continue

            partes = line.split(" ", 2)

            if partes[0] == "INCOMING" and len(partes) >= 3:
                user, msg = partes[1], partes[2]
                print(f"\n[INCOMING] {user}: {msg}")
            elif partes[0] == "ACK":
                print(f"\n[TCP] Mensaje enviado (ACK recibido)")
            elif partes[0] == "ERROR":
                print(f"\n[TCP] Error del servidor: {line}")
            else:
                print(f"\n[SERVER] {line}")

    def stop(self):
        self._running = False
        if self.sock:
            self.sock.close()
