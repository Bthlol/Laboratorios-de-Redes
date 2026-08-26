"""
Cliente TCP -- propiedad de Persona C.

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

    def connect(self):
        self.sock = socket.create_connection((self.host, self.port))

    def _send_line(self, line: str):
        self.sock.sendall((line + "\n").encode("utf-8"))

    def _read_line(self) -> str:
        # TODO(Persona C): implementar lectura por línea (buffer + split en \n),
        # igual que hace bufio.Scanner en Go. recv() puede entregar
        # fragmentos parciales o varias líneas juntas.
        data = self.sock.recv(4096)
        return data.decode("utf-8", errors="replace").strip()

    def login(self, username: str, password: str) -> bool:
        self._send_line(f"LOGIN {username} {password}")
        response = self._read_line()
        # TODO(Persona C): parsear "OK <token> <puerto_udp>" o "ERROR INVALID CREDENTIALS"
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
        # TODO(Persona C): el ACK/ERROR de esta respuesta puede llegar entremezclado
        # con INCOMING de otros usuarios -- por eso normalmente el ACK también
        # se procesa en el hilo receptor, no acá con una lectura bloqueante directa.

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
            # TODO(Persona C): distinguir "INCOMING <user> <msg>", "ACK",
            # "ERROR ..." y mostrarlos por consola de forma clara.
            print(f"\n[SERVER] {line}")

    def stop(self):
        self._running = False
        if self.sock:
            self.sock.close()
