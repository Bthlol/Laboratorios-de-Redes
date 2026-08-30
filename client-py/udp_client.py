"""
Cliente UDP -- propiedad de Barbie.

Hilo en segundo plano que envía HEARTBEAT <token> cada 3 segundos,
de forma ininterrumpida, mientras la sesión esté activa.
"""
import socket
import threading
import time


class HeartbeatSender:
    def __init__(self, host: str, port: int, token: str, interval: float = 3.0):
        self.host = host
        self.port = port
        self.token = token
        self.interval = interval
        self._running = False
        self._thread: threading.Thread | None = None
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def _loop(self):
        while self._running:
            msg = f"HEARTBEAT {self.token}"
            try:
                
                self._sock.sendto(msg.encode("utf-8"), (self.host, self.port))
            except OSError as e:
                print(f"[UDP] Error al enviar heartbeat: {e}")
            time.sleep(self.interval)

    def stop(self):
        self._running = False
        self._sock.close()
